"""
FastAPI Pydantic 모델 정의
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class EmailMaskingRequest(BaseModel):
    """이메일 마스킹 요청"""
    email: str = Field(..., description="원본 이메일 텍스트")
    llm_model: Optional[str] = Field("llama3", description="사용할 LLM 모델")


class PIIDecision(BaseModel):
    """개별 PII 마스킹 결정"""
    pii_type: str
    pii_value: str
    action: str  # keep, mask_full, mask_partial, block
    reasoning: str
    confidence: float


class EmailMaskingResponse(BaseModel):
    """이메일 마스킹 응답"""
    original_email: str
    masked_email: str
    risk_level: str  # high, medium, low
    should_block: bool
    detected_piis_count: int
    masking_decisions: List[PIIDecision]
    retrieved_guides_count: int
    retrieved_laws_count: int
    warnings: List[str] = []


class HealthCheckResponse(BaseModel):
    """헬스체크 응답"""
    status: str
    retriever_initialized: bool
    llm_available: bool
