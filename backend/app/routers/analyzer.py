from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from ..utils.recognizer_engine import recognize_pii_in_text
from ..utils.rag_integration import get_rag_engine
from ..database.mongodb import get_db

router = APIRouter()

class EmailContext(BaseModel):
    """이메일 맥락 정보"""
    sender_type: str = "internal"  # internal, external_customer, external_partner
    receiver_type: str = "external_customer"
    purpose: str = "일반 업무"
    has_consent: bool = False

class TextAnalysisRequest(BaseModel):
    text_content: str
    user_request: str = "default"
    ocr_data: Optional[Dict] = None  # OCR 좌표 데이터 추가
    email_context: Optional[EmailContext] = None  # 이메일 맥락 정보 추가
    enable_rag: bool = True  # RAG 활성화 여부

class PIICoordinate(BaseModel):
    pageIndex: int
    bbox: List[int]  # [x1, y1, x2, y2]
    field_text: str

class PIIEntity(BaseModel):
    text: str
    type: str
    score: float
    start_char: int
    end_char: int
    coordinates: Optional[List[PIICoordinate]] = None  # OCR 좌표 정보 추가

class MaskingDecision(BaseModel):
    """마스킹 결정 정보"""
    action: str  # keep, mask_partial, mask_full, block
    reasoning: str
    referenced_guides: List[str]
    referenced_laws: List[str]
    confidence: float

class PIIEntityWithDecision(PIIEntity):
    """마스킹 결정이 포함된 PII 엔티티"""
    masking_decision: Optional[MaskingDecision] = None

class TextAnalysisResponse(BaseModel):
    full_text: str
    pii_entities: List[PIIEntity]

class TextAnalysisWithRAGResponse(BaseModel):
    """RAG 기반 분석 응답"""
    full_text: str
    pii_entities: List[PIIEntityWithDecision]
    rag_enabled: bool
    warnings: List[str] = []

@router.post("/analyze/text", response_model=TextAnalysisResponse)
async def analyze_text(request: TextAnalysisRequest, db = Depends(get_db)):
    """
    추출된 텍스트에서 PII를 분석하고 탐지합니다.
    OCR 데이터가 있으면 좌표 정보도 함께 반환합니다.
    커스텀 엔티티도 MongoDB에서 자동 로드됩니다.
    """
    # OCR 데이터와 DB 클라이언트를 포함하여 텍스트 분석 로직 호출
    analysis_result = await recognize_pii_in_text(
        request.text_content,
        request.ocr_data,
        db_client=db
    )

    return analysis_result

@router.post("/analyze/text-with-rag", response_model=TextAnalysisWithRAGResponse)
async def analyze_text_with_rag(request: TextAnalysisRequest, db = Depends(get_db)):
    """
    RAG 기반 PII 분석 및 마스킹 결정

    1. PII 탐지 (규칙 기반 + NER)
    2. RAG 검색 (애플리케이션 가이드, 법률, 정책)
    3. 마스킹 결정 (법령 기반)

    Args:
        request: 분석 요청 (텍스트, 맥락 정보, RAG 활성화 여부)

    Returns:
        마스킹 결정이 포함된 PII 분석 결과
    """
    # 1. PII 탐지
    analysis_result = await recognize_pii_in_text(
        request.text_content,
        request.ocr_data,
        db_client=db
    )

    pii_entities = analysis_result.get("pii_entities", [])

    # 2. RAG 기반 마스킹 결정
    if request.enable_rag and pii_entities:
        rag_engine = get_rag_engine()

        # 맥락 정보를 딕셔너리로 변환
        context = None
        if request.email_context:
            context = {
                "sender_type": request.email_context.sender_type,
                "receiver_type": request.email_context.receiver_type,
                "purpose": request.email_context.purpose,
                "has_consent": request.email_context.has_consent
            }

        # RAG 기반 마스킹 결정 획득
        rag_result = rag_engine.get_masking_decisions(pii_entities, context)

        # PII 엔티티에 결정 정보 병합
        entities_with_decisions = []
        for decision_data in rag_result.get("decisions", []):
            entity = decision_data["entity"]
            decision = MaskingDecision(
                action=decision_data["action"],
                reasoning=decision_data["reasoning"],
                referenced_guides=decision_data["referenced_guides"],
                referenced_laws=decision_data["referenced_laws"],
                confidence=decision_data["confidence"]
            )

            entity_with_decision = PIIEntityWithDecision(
                **entity,
                masking_decision=decision
            )
            entities_with_decisions.append(entity_with_decision)

        return TextAnalysisWithRAGResponse(
            full_text=analysis_result.get("full_text", ""),
            pii_entities=entities_with_decisions,
            rag_enabled=rag_result.get("rag_enabled", False),
            warnings=rag_result.get("warnings", [])
        )
    else:
        # RAG 비활성화 또는 PII 없음
        entities_with_decisions = [
            PIIEntityWithDecision(**entity, masking_decision=None)
            for entity in pii_entities
        ]

        return TextAnalysisWithRAGResponse(
            full_text=analysis_result.get("full_text", ""),
            pii_entities=entities_with_decisions,
            rag_enabled=False,
            warnings=["RAG가 비활성화되었거나 PII가 없음"]
        )