"""
LangGraph 노드 구현
각 노드는 AgentState를 입력받아 업데이트된 상태를 반환
"""
import re
from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage

from agent.state import (
    AgentState,
    DetectedPII,
    EmailContext,
    RetrievedDocument,
    MaskingDecision
)
from agent.retrievers import HybridRetriever
from agent.llm_factory import get_llm


class AgentNodes:
    """LangGraph 노드 컬렉션"""

    def __init__(self, retriever: HybridRetriever, llm_model: str = "llama3"):
        self.retriever = retriever
        self.llm = get_llm(model=llm_model, temperature=0.0)

    def pii_detection_node(self, state: AgentState) -> AgentState:
        """
        노드 1: PII 탐지
        간단한 정규표현식 기반 탐지 (실제로는 NER 모델 사용 권장)
        """
        print("\n[노드 1] PII 탐지 중...")
        email = state['original_email']
        detected_piis = []

        # 이메일 패턴
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for match in re.finditer(email_pattern, email):
            detected_piis.append(DetectedPII(
                entity_type='EMAIL',
                value=match.group(),
                start=match.start(),
                end=match.end(),
                confidence=0.95
            ))

        # 전화번호 패턴
        phone_pattern = r'\b0\d{1,2}-?\d{3,4}-?\d{4}\b'
        for match in re.finditer(phone_pattern, email):
            detected_piis.append(DetectedPII(
                entity_type='PHONE_NUMBER',
                value=match.group(),
                start=match.start(),
                end=match.end(),
                confidence=0.9
            ))

        # 주민등록번호 패턴
        resident_id_pattern = r'\b\d{6}-?[1-4]\d{6}\b'
        for match in re.finditer(resident_id_pattern, email):
            detected_piis.append(DetectedPII(
                entity_type='RESIDENT_ID',
                value=match.group(),
                start=match.start(),
                end=match.end(),
                confidence=0.95
            ))

        # 한글 이름 패턴 (2-4글자)
        name_pattern = r'\b[가-힣]{2,4}(?=\s|님|씨|고객|사원|대리|과장|부장|이사)\b'
        for match in re.finditer(name_pattern, email):
            detected_piis.append(DetectedPII(
                entity_type='NAME',
                value=match.group(),
                start=match.start(),
                end=match.end(),
                confidence=0.8
            ))

        state['detected_piis'] = detected_piis
        print(f"   - {len(detected_piis)}개 PII 탐지 완료")
        for pii in detected_piis:
            print(f"     • {pii.entity_type}: {pii.value}")

        return state

    def context_analysis_node(self, state: AgentState) -> AgentState:
        """
        노드 2: 이메일 맥락 분석
        LLM을 사용하여 발신자, 수신자, 목적 등을 파악
        """
        print("\n[노드 2] 이메일 맥락 분석 중...")

        email = state['original_email']
        detected_piis = state['detected_piis']

        # PII 목록 요약
        pii_summary = ', '.join([f"{pii.entity_type}({pii.value})" for pii in detected_piis[:5]])

        system_prompt = """당신은 이메일 맥락 분석 전문가입니다.
주어진 이메일의 내용을 분석하여 다음 정보를 JSON 형식으로 추출하세요:

1. sender_type: internal, external_customer, external_partner, external_vendor 중 선택
2. receiver_type: internal, external_customer, external_partner, external_vendor 중 선택
3. purpose: 이메일의 목적을 한 문장으로 (예: 고객 문의 답변, 견적서 발송, 마케팅, 계약서 전달 등)
4. has_consent: 수신자의 동의가 명시적으로 있는지 여부 (true/false)
5. business_context: 추가 비즈니스 맥락 (선택사항)

반드시 JSON 형식으로만 답변하세요."""

        user_prompt = f"""다음 이메일을 분석하세요:

이메일 내용:
{email}

탐지된 PII: {pii_summary}
"""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            response = self.llm.invoke(messages)
            response_text = response.content

            # JSON 추출
            import json
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                context_data = json.loads(json_match.group())

                email_context = EmailContext(
                    sender_type=context_data.get('sender_type', 'internal'),
                    receiver_type=context_data.get('receiver_type', 'external_customer'),
                    purpose=context_data.get('purpose', ''),
                    has_consent=context_data.get('has_consent', False),
                    business_context=context_data.get('business_context', '')
                )

                state['email_context'] = email_context
                print(f"   - 맥락 분석 완료:")
                print(f"     • 발신자: {email_context.sender_type}")
                print(f"     • 수신자: {email_context.receiver_type}")
                print(f"     • 목적: {email_context.purpose}")
                print(f"     • 동의 여부: {email_context.has_consent}")
            else:
                print("   - ⚠️ LLM 응답에서 JSON을 찾을 수 없습니다.")
                state['email_context'] = EmailContext(
                    sender_type='internal',
                    receiver_type='external_customer'
                )

        except Exception as e:
            print(f"   - 🚨 맥락 분석 실패: {e}")
            state['email_context'] = EmailContext(
                sender_type='internal',
                receiver_type='external_customer'
            )

        return state

    def routing_node(self, state: AgentState) -> AgentState:
        """
        노드 3: 검색 라우팅
        어떤 정보를 우선적으로 검색할지 결정
        """
        print("\n[노드 3] 검색 라우팅 중...")

        # 이 노드는 다음 노드로 어떤 경로를 택할지 결정하는 메타데이터만 추가
        # 실제 LangGraph에서는 conditional edge로 구현됨

        detected_piis = state.get('detected_piis', [])
        email_context = state.get('email_context')

        # 민감정보 포함 여부 확인
        has_sensitive = any(pii.entity_type in ['RESIDENT_ID', 'PASSPORT', 'DRIVER_LICENSE']
                           for pii in detected_piis)

        # 라우팅 전략 결정
        if has_sensitive:
            state['warnings'] = state.get('warnings', []) + ['민감정보 포함 - 법률 우선 검색']
            print("   - 민감정보 탐지 → 법률 우선 검색")
        elif email_context and email_context.receiver_type.startswith('external'):
            print("   - 외부 수신자 → 가이드 우선 검색")
        else:
            print("   - 일반 케이스 → 통합 검색")

        return state

    def information_retrieval_node(self, state: AgentState) -> AgentState:
        """
        노드 4: 정보 검색
        1순위: 애플리케이션 가이드
        2순위: 법률/정책
        3순위: 과거 사례
        """
        print("\n[노드 4] 정보 검색 중...")

        email = state['original_email']
        email_context = state.get('email_context')
        detected_piis = state.get('detected_piis', [])

        # 검색 쿼리 생성
        pii_types = list(set([pii.entity_type for pii in detected_piis]))
        purpose = email_context.purpose if email_context else "일반 업무"
        query = f"{purpose} 상황에서 {', '.join(pii_types)} 처리 방법"

        print(f"   - 검색 쿼리: {query}")

        # 1. 애플리케이션 가이드 검색 (최우선)
        context_dict = None
        if email_context:
            context_dict = {
                'sender_type': email_context.sender_type,
                'receiver_type': email_context.receiver_type
            }

        guides = self.retriever.search_application_guides(
            query=query,
            context=context_dict,
            top_k=3
        )
        state['retrieved_guides'] = [
            RetrievedDocument(
                doc_id=g['guide_id'],
                source=g['source'],
                content=str(g['content']),
                score=g['score'],
                metadata=g['metadata']
            ) for g in guides
        ]
        print(f"   - 애플리케이션 가이드 {len(guides)}개 검색")

        # 2. 법률/정책 검색
        laws_policies = self.retriever.search_laws_and_policies(query, top_k=5)
        state['retrieved_laws'] = [
            RetrievedDocument(
                doc_id=doc['id'],
                source=doc['source'],
                content=doc['content'],
                score=doc['score'],
                metadata=doc['metadata']
            ) for doc in laws_policies['laws']
        ]
        state['retrieved_policies'] = [
            RetrievedDocument(
                doc_id=doc['id'],
                source=doc['source'],
                content=doc['content'],
                score=doc['score'],
                metadata=doc['metadata']
            ) for doc in laws_policies['policies']
        ]
        print(f"   - 법률 {len(laws_policies['laws'])}개, 정책 {len(laws_policies['policies'])}개 검색")

        # 3. 과거 사례 검색
        filters = {}
        if email_context:
            if email_context.sender_type == 'internal' and email_context.receiver_type == 'internal':
                filters['category'] = '사내'
            else:
                filters['category'] = '사외'

        cases = self.retriever.search_cases(query, filters=filters, top_k=3)
        state['retrieved_cases'] = [
            RetrievedDocument(
                doc_id=case['id'],
                source=case['source'],
                content=case['content'],
                score=case['score'],
                metadata=case['metadata']
            ) for case in cases
        ]
        print(f"   - 과거 사례 {len(cases)}개 검색")

        return state

    def reasoning_and_synthesis_node(self, state: AgentState) -> AgentState:
        """
        노드 5: 추론 및 종합
        모든 정보를 종합하여 각 PII에 대한 마스킹 결정
        """
        print("\n[노드 5] 추론 및 종합 중...")

        email = state['original_email']
        detected_piis = state.get('detected_piis', [])
        email_context = state.get('email_context')
        guides = state.get('retrieved_guides', [])
        laws = state.get('retrieved_laws', [])
        policies = state.get('retrieved_policies', [])
        cases = state.get('retrieved_cases', [])

        # 가이드 정보 요약
        guides_summary = "\n".join([
            f"[가이드 {i+1}] {g.metadata.get('scenario', 'N/A')}\n"
            f"  지침: {g.metadata.get('actionable_directive', 'N/A')}"
            for i, g in enumerate(guides[:2])
        ]) if guides else "검색된 가이드 없음"

        # 법률 정보 요약
        laws_summary = "\n".join([
            f"[법률 {i+1}] {law.content[:100]}..."
            for i, law in enumerate(laws[:2])
        ]) if laws else "검색된 법률 없음"

        # 정책 정보 요약
        policies_summary = "\n".join([
            f"[정책 {i+1}] {policy.content[:100]}..."
            for i, policy in enumerate(policies[:2])
        ]) if policies else "검색된 정책 없음"

        # PII 목록
        pii_list = "\n".join([
            f"{i+1}. {pii.entity_type}: {pii.value}"
            for i, pii in enumerate(detected_piis)
        ])

        system_prompt = """당신은 데이터 보호 전문가입니다.
주어진 이메일에서 탐지된 각 PII에 대해, 제공된 이메일 맥락, 애플리케이션 가이드, 법률, 사내 규칙, 과거 사례를 종합적으로 고려하여 마스킹 여부와 그 이유를 단계별로 설명하세요.

**중요한 우선순위:**
1. 애플리케이션 가이드의 지침을 최우선으로 따라야 합니다.
2. 법률 준수는 필수입니다.
3. 사내 규칙도 고려하되, 법률과 충돌 시 법률 우선입니다.
4. 과거 사례는 참고 자료로 활용합니다.

**각 PII에 대해 다음 형식으로 답변하세요:**
```
PII: [entity_type] [value]
결정: [keep / mask_full / mask_partial / block]
이유: [단계별 추론]
참조: [가이드 ID, 법률 ID 등]
```"""

        user_prompt = f"""다음 이메일의 PII 처리 방법을 결정하세요:

===== 원본 이메일 =====
{email}

===== 이메일 맥락 =====
발신자: {email_context.sender_type if email_context else 'N/A'}
수신자: {email_context.receiver_type if email_context else 'N/A'}
목적: {email_context.purpose if email_context else 'N/A'}
동의 여부: {email_context.has_consent if email_context else 'N/A'}

===== 탐지된 PII =====
{pii_list}

===== 애플리케이션 가이드 =====
{guides_summary}

===== 관련 법률 =====
{laws_summary}

===== 사내 정책 =====
{policies_summary}

각 PII에 대해 마스킹 결정을 내려주세요."""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            response = self.llm.invoke(messages)
            reasoning = response.content

            state['reasoning_steps'] = [reasoning]
            print(f"   - LLM 추론 완료 ({len(reasoning)} 문자)")
            print(f"\n{reasoning[:500]}...\n")

            # 간단한 파싱으로 결정 추출 (실제로는 더 정교한 파싱 필요)
            decisions = []
            for pii in detected_piis:
                # 기본 결정: 가이드가 있으면 따르고, 없으면 보수적으로 마스킹
                action = 'mask_partial'
                referenced_guides = [g.doc_id for g in guides[:1]]
                referenced_laws = [l.doc_id for l in laws[:1]]

                # 가이드에서 명확한 지침이 있으면 따름
                if guides and guides[0].metadata:
                    directive = guides[0].metadata.get('actionable_directive', '')
                    if '예외' in directive or '마스킹하지 않음' in directive:
                        action = 'keep'
                    elif '차단' in directive:
                        action = 'block'

                # 민감정보는 무조건 마스킹/차단
                if pii.entity_type == 'RESIDENT_ID':
                    action = 'block'

                decisions.append(MaskingDecision(
                    pii=pii,
                    action=action,
                    reasoning=f"가이드 및 법률 참조: {reasoning[:200]}...",
                    referenced_guides=referenced_guides,
                    referenced_laws=referenced_laws,
                    confidence=0.85
                ))

            state['masking_decisions'] = decisions

        except Exception as e:
            print(f"   - 🚨 추론 실패: {e}")
            # 실패 시 보수적 기본 결정
            state['masking_decisions'] = [
                MaskingDecision(
                    pii=pii,
                    action='mask_partial',
                    reasoning="LLM 추론 실패로 인한 기본 보수적 처리",
                    referenced_guides=[],
                    referenced_laws=[],
                    confidence=0.5
                ) for pii in detected_piis
            ]

        return state

    def final_decision_node(self, state: AgentState) -> AgentState:
        """
        노드 6: 최종 결정 및 마스킹 적용
        """
        print("\n[노드 6] 최종 결정 및 마스킹 적용 중...")

        email = state['original_email']
        decisions = state.get('masking_decisions', [])

        # 마스킹 적용
        masked_email = email
        offset = 0

        # PII를 역순으로 정렬 (뒤에서부터 치환하여 인덱스 보정 불필요)
        sorted_decisions = sorted(decisions, key=lambda d: d.pii.start, reverse=True)

        block_count = 0
        for decision in sorted_decisions:
            pii = decision.pii
            action = decision.action

            if action == 'block':
                block_count += 1
                masked_value = '[차단됨]'
            elif action == 'mask_full':
                masked_value = '*' * len(pii.value)
            elif action == 'mask_partial':
                if len(pii.value) > 2:
                    masked_value = pii.value[0] + '*' * (len(pii.value) - 2) + pii.value[-1]
                else:
                    masked_value = '*' * len(pii.value)
            else:  # keep
                masked_value = pii.value

            # 치환
            masked_email = masked_email[:pii.start] + masked_value + masked_email[pii.end:]

            print(f"   - {pii.entity_type} '{pii.value}' → '{masked_value}' ({action})")

        state['masked_email'] = masked_email

        # 위험도 평가
        if block_count > 0:
            state['risk_level'] = 'high'
            state['should_block'] = True
        elif any(d.action == 'mask_full' for d in decisions):
            state['risk_level'] = 'medium'
            state['should_block'] = False
        else:
            state['risk_level'] = 'low'
            state['should_block'] = False

        print(f"\n   ✅ 최종 위험도: {state.get('risk_level', 'unknown')}")
        print(f"   ✅ 완전 차단 여부: {state.get('should_block', False)}")

        return state
