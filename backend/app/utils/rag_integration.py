"""
RAG 기반 마스킹 결정 통합 모듈
analyzer.py에서 사용할 RAG 검색 및 마스킹 결정 기능
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import asyncio

# RAG 모듈 경로 추가
BASE_DIR = Path(__file__).parent.parent.parent.parent  # enterprise-guardcap 루트
RAG_DIR = BASE_DIR / "backend" / "app" / "rag"
sys.path.insert(0, str(RAG_DIR))

try:
    from agent.retrievers import HybridRetriever
    RAG_AVAILABLE = True
except Exception as e:
    print(f"⚠️ RAG 모듈 로드 실패: {e}")
    RAG_AVAILABLE = False


class RAGMaskingDecisionEngine:
    """
    RAG 기반 마스킹 결정 엔진
    - PII 탐지 결과를 받아서 법령/정책 기반 마스킹 결정 제공
    """

    def __init__(self):
        self.retriever = None
        self.initialized = False

        if RAG_AVAILABLE:
            self._initialize_retriever()

    def _initialize_retriever(self):
        """Retriever 초기화"""
        try:
            # RAG 데이터 경로 설정
            index_base_path = BASE_DIR / "backend" / "app" / "rag" / "data" / "staging"

            if not index_base_path.exists():
                print(f"⚠️ RAG 인덱스 경로가 존재하지 않습니다: {index_base_path}")
                return

            self.retriever = HybridRetriever(index_base_path=str(index_base_path))
            self.initialized = True
            print("✅ RAG Retriever 초기화 완료")

        except Exception as e:
            print(f"❌ RAG Retriever 초기화 실패: {e}")
            self.initialized = False

    def get_masking_decisions(
        self,
        pii_entities: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        PII 엔티티 리스트에 대한 마스킹 결정 반환

        Args:
            pii_entities: PII 엔티티 리스트 [{"text": str, "type": str, "score": float, ...}]
            context: 이메일 맥락 정보 {"sender_type": str, "receiver_type": str, "purpose": str}

        Returns:
            {
                "decisions": [
                    {
                        "entity": {...},
                        "action": "keep" | "mask_partial" | "mask_full" | "block",
                        "reasoning": str,
                        "referenced_guides": List[str],
                        "referenced_laws": List[str],
                        "confidence": float
                    }
                ],
                "rag_enabled": bool,
                "warnings": List[str]
            }
        """
        if not self.initialized or not self.retriever:
            return self._fallback_decisions(pii_entities)

        try:
            return self._rag_based_decisions(pii_entities, context)
        except Exception as e:
            print(f"❌ RAG 기반 결정 실패: {e}, fallback으로 전환")
            return self._fallback_decisions(pii_entities)

    def _rag_based_decisions(
        self,
        pii_entities: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """RAG 기반 마스킹 결정"""
        decisions = []
        warnings = []

        # PII 타입별로 그룹화
        pii_by_type = {}
        for entity in pii_entities:
            entity_type = entity.get("type", "UNKNOWN")
            if entity_type not in pii_by_type:
                pii_by_type[entity_type] = []
            pii_by_type[entity_type].append(entity)

        # 각 PII 타입에 대해 RAG 검색 수행
        for entity_type, entities in pii_by_type.items():
            # 검색 쿼리 생성
            purpose = context.get("purpose", "일반 업무") if context else "일반 업무"
            sender_type = context.get("sender_type", "internal") if context else "internal"
            receiver_type = context.get("receiver_type", "external_customer") if context else "external_customer"

            query = f"{purpose} 상황에서 {sender_type}에서 {receiver_type}로 {entity_type} 처리 방법"

            # 1. 애플리케이션 가이드 검색
            guides = self.retriever.search_application_guides(
                query=query,
                context={"sender_type": sender_type, "receiver_type": receiver_type} if context else None,
                top_k=2
            )

            # 2. 법률/정책 검색
            laws_policies = self.retriever.search_laws_and_policies(query, top_k=3)

            # 각 엔티티에 대한 결정 생성
            for entity in entities:
                decision = self._make_decision_for_entity(
                    entity,
                    entity_type,
                    guides,
                    laws_policies,
                    context
                )
                decisions.append(decision)

        return {
            "decisions": decisions,
            "rag_enabled": True,
            "warnings": warnings
        }

    def _make_decision_for_entity(
        self,
        entity: Dict[str, Any],
        entity_type: str,
        guides: List[Dict],
        laws_policies: Dict[str, List],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """개별 엔티티에 대한 마스킹 결정"""

        # 기본 결정: 보수적 접근
        action = "mask_partial"
        reasoning = []
        referenced_guides = []
        referenced_laws = []
        confidence = 0.5

        # 1. 가이드 우선 적용
        if guides and len(guides) > 0:
            top_guide = guides[0]
            guide_content = top_guide.get("content", {})
            directive = top_guide.get("metadata", {}).get("actionable_directive", "")

            referenced_guides.append(top_guide.get("guide_id", "unknown"))

            # 가이드 지침 해석
            if "마스킹하지 않음" in directive or "공개 가능" in directive:
                action = "keep"
                reasoning.append(f"가이드 지침: {directive}")
                confidence = 0.8
            elif "완전 차단" in directive or "전송 금지" in directive:
                action = "block"
                reasoning.append(f"가이드 지침: {directive}")
                confidence = 0.9
            elif "부분 마스킹" in directive:
                action = "mask_partial"
                reasoning.append(f"가이드 지침: {directive}")
                confidence = 0.85
            elif "전체 마스킹" in directive:
                action = "mask_full"
                reasoning.append(f"가이드 지침: {directive}")
                confidence = 0.85

        # 2. 법률 기반 규칙 (더 엄격한 규칙)
        laws = laws_policies.get("laws", [])
        if laws:
            for law in laws[:2]:
                referenced_laws.append(law.get("id", "unknown"))
                law_content = law.get("content", "")

                # 개인정보보호법 관련 키워드 체크
                if "주민등록번호" in law_content and entity_type in ["RESIDENT_ID", "NATIONAL_ID"]:
                    if action == "keep":
                        action = "block"  # 법률이 가이드보다 우선
                        reasoning.append("법률: 주민등록번호 수집/전송 제한")
                        confidence = 0.95

                if "동의 없이" in law_content and context and not context.get("has_consent", False):
                    if action == "keep":
                        action = "mask_partial"
                        reasoning.append("법률: 동의 없는 개인정보 처리 제한")

        # 3. 민감정보 타입별 기본 규칙 (최후 방어선)
        sensitive_types = {
            "RESIDENT_ID": "block",
            "NATIONAL_ID": "block",
            "PASSPORT": "block",
            "DRIVER_LICENSE": "mask_full",
            "CREDIT_CARD": "mask_partial",
            "BANK_ACCOUNT": "mask_partial"
        }

        if entity_type in sensitive_types:
            fallback_action = sensitive_types[entity_type]
            if action == "keep" and fallback_action in ["block", "mask_full"]:
                action = fallback_action
                reasoning.append(f"기본 규칙: {entity_type}는 {fallback_action} 필요")

        # 추론 문자열 생성
        reasoning_text = " | ".join(reasoning) if reasoning else "기본 보수적 정책 적용"

        return {
            "entity": entity,
            "action": action,
            "reasoning": reasoning_text,
            "referenced_guides": referenced_guides,
            "referenced_laws": referenced_laws,
            "confidence": confidence
        }

    def _fallback_decisions(self, pii_entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """RAG 없이 규칙 기반 폴백 결정"""
        decisions = []

        # 단순 규칙 기반 결정
        for entity in pii_entities:
            entity_type = entity.get("type", "UNKNOWN")

            # 민감정보 타입별 기본 액션
            if entity_type in ["RESIDENT_ID", "NATIONAL_ID", "PASSPORT"]:
                action = "block"
            elif entity_type in ["CREDIT_CARD", "BANK_ACCOUNT", "DRIVER_LICENSE"]:
                action = "mask_full"
            elif entity_type in ["PHONE_NUMBER", "EMAIL", "NAME"]:
                action = "mask_partial"
            else:
                action = "keep"

            decisions.append({
                "entity": entity,
                "action": action,
                "reasoning": f"규칙 기반 기본 정책 (RAG 비활성)",
                "referenced_guides": [],
                "referenced_laws": [],
                "confidence": 0.6
            })

        return {
            "decisions": decisions,
            "rag_enabled": False,
            "warnings": ["RAG 시스템이 초기화되지 않음 - 규칙 기반 폴백 사용"]
        }


# 전역 싱글톤 인스턴스
_rag_engine = None

def get_rag_engine() -> RAGMaskingDecisionEngine:
    """RAG 엔진 싱글톤 인스턴스 반환"""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGMaskingDecisionEngine()
    return _rag_engine
