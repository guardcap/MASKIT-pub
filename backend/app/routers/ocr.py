# app/routers/ocr.py

from fastapi import APIRouter
from ..utils.ocr_extractor import extract_text_from_file

router = APIRouter()

# 👈🏻 여기를 수정합니다. file_content: bytes와 file_name: str을 받도록 변경합니다.
@router.post("/extract/ocr")
async def extract_ocr(file_content: bytes, file_name: str):
    """
    이미지나 PDF 파일에서 텍스트와 좌표를 추출합니다.
    """
    # 👈🏻 ocr_extractor의 함수를 호출하고 file_name 인자를 전달합니다.
    ocr_result = extract_text_from_file(file_content, file_name)
    
    return ocr_result