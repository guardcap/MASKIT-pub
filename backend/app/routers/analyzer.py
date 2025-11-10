from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from ..utils.recognizer_engine import recognize_pii_in_text
from ..smtp.database import get_db

router = APIRouter()

class TextAnalysisRequest(BaseModel):
    text_content: str
    user_request: str = "default"
    ocr_data: Optional[Dict] = None  # OCR 좌표 데이터 추가

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

class TextAnalysisResponse(BaseModel):
    full_text: str
    pii_entities: List[PIIEntity]

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