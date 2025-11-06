"""
LangGraph Agent State 정의
각 노드를 거치며 업데이트될 상태(State) 정의
"""
from typing import TypedDict, List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class DetectedPII:
    """탐지된 PII 정보"""
    entity_type: str  # NAME, EMAIL, PHONE_NUMBER, RESIDENT_ID, etc.
    value: str
    start: int
    end: int
    confidence: float


@dataclass
class EmailContext:
    """이메일 맥락 정보"""
    sender_type: str  # internal, external_customer, external_partner, external_vendor
    receiver_type: str
    sender_dept: Optional[str] = None
    receiver_dept: Optional[str] = None
    purpose: Optional[str] = None  # 문의 답변, 견적서 발송, 마케팅, 계약서 전달 등
    has_consent: bool = False  # 수신자의 동의 여부
    business_context: Optional[str] = None  # 추가 비즈니스 맥락


@dataclass
class RetrievedDocument:
    """검색된 문서"""
    doc_id: str
    source: str  # A_cases, B_policies, C_laws, application_guides
    content: str
    score: float
    metadata: Dict[str, Any]


@dataclass
class MaskingDecision:
    """개별 PII에 대한 마스킹 결정"""
    pii: DetectedPII
    action: str  # keep, mask_full, mask_partial, block
    reasoning: str
    referenced_guides: List[str]  # 참조한 가이드 ID
    referenced_laws: List[str]  # 참조한 법률 ID
    confidence: float


class AgentState(TypedDict):
    """LangGraph Agent의 전체 상태"""
    # 입력
    original_email: str

    # PII 탐지 결과
    detected_piis: List[DetectedPII]

    # 이메일 맥락 분석 결과
    email_context: Optional[EmailContext]

    # 검색 결과
    retrieved_guides: List[RetrievedDocument]
    retrieved_laws: List[RetrievedDocument]
    retrieved_policies: List[RetrievedDocument]
    retrieved_cases: List[RetrievedDocument]

    # 추론 과정
    reasoning_steps: List[str]

    # 최종 결정
    masking_decisions: List[MaskingDecision]

    # 최종 마스킹된 이메일
    masked_email: str

    # 메타데이터
    risk_level: str  # high, medium, low
    should_block: bool  # 완전 차단 여부
    warnings: List[str]  # 경고 메시지
