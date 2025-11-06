# app/routers/masking_pdf.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os

from ..utils.masking_engine import PdfMaskingEngine
from ..routers.uploads import UPLOAD_DIR

router = APIRouter()

class PIIItemFromAnalysis(BaseModel):
    filename: str
    pii_type: str
    text: str
    pageIndex: int
    instance_index: int = 0
    bbox: Optional[List[int]] = None

@router.post("/masking/pdf")
async def mask_pii_in_pdf(pii_items: List[PIIItemFromAnalysis]):
    """
    클라이언트에서 받은 PII 정보를 사용하여 PDF 또는 이미지 파일을 마스킹합니다.
    """
    
    print(f"[마스킹 API] 받은 PII 항목 수: {len(pii_items)}")
    
    pii_by_file = {}
    for item in pii_items:
        print(f"[마스킹 API] 처리 중: {item.pii_type} '{item.text}' in {item.filename}")
        
        if item.filename not in pii_by_file:
            pii_by_file[item.filename] = []
        
        entity_data = {
            "entity": item.pii_type,
            "pageIndex": item.pageIndex,
            "text": item.text,
            "instance_index": item.instance_index
        }
        
        if item.bbox is not None:
            entity_data["bbox"] = item.bbox
        
        pii_by_file[item.filename].append(entity_data)
    
    masked_file_paths = {}
    masking_engine = PdfMaskingEngine()
    
    for filename, entities in pii_by_file.items():
        original_file_path = os.path.join(UPLOAD_DIR, filename)
        
        if not os.path.exists(original_file_path):
            print(f"[마스킹 API] 파일을 찾을 수 없음: {original_file_path}")
            masked_file_paths[filename] = "File not found"
            continue
        
        file_ext = os.path.splitext(filename)[1]
        masked_filename = f"masked_{filename}"
        masked_file_path = os.path.join(UPLOAD_DIR, masked_filename)
        
        try:
            print(f"[마스킹 API] 파일 마스킹 시작: {filename}")
            for entity in entities:
                if 'bbox' in entity:
                    print(f"  - {entity['entity']}: '{entity['text']}' at page {entity['pageIndex']} bbox {entity['bbox']}")
                else:
                    print(f"  - {entity['entity']}: '{entity['text']}' at page {entity['pageIndex']} instance {entity['instance_index']}")
            
            masking_engine.redact_pdf_with_entities(
                pdf_path=original_file_path,
                entities=entities,
                out_pdf_path=masked_file_path
            )
            
            masked_file_paths[filename] = f"/uploads/{masked_filename}"
            print(f"[마스킹 API] 마스킹 완료: {masked_filename}")
        
        except Exception as e:
            print(f"[마스킹 API] 마스킹 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            masked_file_paths[filename] = f"Masking failed: {str(e)}"

    return {"status": "success", "masked_files": masked_file_paths}