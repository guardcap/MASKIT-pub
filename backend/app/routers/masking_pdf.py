# app/routers/masking_pdf.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import base64

from ..utils.masking_engine import PdfMaskingEngine
from ..routers.uploads import UPLOAD_DIR
from ..models.email import MaskedEmailData, MaskedEmailResponse, AttachmentData
from ..database.mongodb import get_db

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


# ==================== 마스킹된 이메일 MongoDB 저장 API ====================

class SaveMaskedEmailRequest(BaseModel):
    email_id: str
    from_email: str
    to_emails: List[str]
    subject: str
    masked_body: str
    masked_attachment_filenames: List[str] = []
    masking_decisions: dict = {}
    pii_masked_count: int = 0


@router.post("/masking/save-masked-email")
async def save_masked_email(
    request: SaveMaskedEmailRequest,
    db = Depends(get_db)
):
    """
    마스킹된 이메일을 MongoDB의 masked_emails 컬렉션에 저장
    """
    try:
        # 마스킹된 첨부파일들을 Base64로 읽어서 저장
        masked_attachments_data = []

        for filename in request.masked_attachment_filenames:
            file_path = os.path.join(UPLOAD_DIR, filename)

            if os.path.exists(file_path):
                # 파일 읽기
                with open(file_path, 'rb') as f:
                    file_content = f.read()

                # Base64 인코딩
                encoded_content = base64.b64encode(file_content).decode('utf-8')

                # 파일 확장자로 content_type 추정
                content_type = "application/octet-stream"
                if filename.lower().endswith('.pdf'):
                    content_type = "application/pdf"
                elif filename.lower().endswith(('.jpg', '.jpeg')):
                    content_type = "image/jpeg"
                elif filename.lower().endswith('.png'):
                    content_type = "image/png"

                masked_attachments_data.append({
                    "filename": filename,
                    "content_type": content_type,
                    "size": len(file_content),
                    "data": encoded_content
                })

                print(f"✅ 마스킹된 첨부파일 인코딩: {filename} ({len(file_content)} bytes)")
            else:
                print(f"⚠️ 마스킹된 파일을 찾을 수 없음: {file_path}")

        # MaskedEmailData 객체 생성
        masked_email = MaskedEmailData(
            email_id=request.email_id,
            from_email=request.from_email,
            to_emails=request.to_emails,
            subject=request.subject,
            masked_body=request.masked_body,
            masked_attachments=[
                AttachmentData(**att) for att in masked_attachments_data
            ],
            masking_decisions=request.masking_decisions,
            pii_masked_count=request.pii_masked_count,
            created_at=datetime.utcnow()
        )

        # MongoDB에 저장
        result = await db.masked_emails.insert_one(masked_email.model_dump())

        print(f"✅ MongoDB에 마스킹된 이메일 저장 완료: {request.email_id}")

        return {
            "success": True,
            "message": "마스킹된 이메일이 성공적으로 저장되었습니다",
            "email_id": request.email_id,
            "masked_attachments_count": len(masked_attachments_data),
            "pii_masked_count": request.pii_masked_count
        }

    except Exception as e:
        print(f"❌ 마스킹된 이메일 저장 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"마스킹된 이메일 저장 실패: {str(e)}")


# ==================== 마스킹된 이메일 조회 API ====================

@router.get("/masking/masked-email/{email_id}")
async def get_masked_email(
    email_id: str,
    db = Depends(get_db)
):
    """
    MongoDB에서 마스킹된 이메일 조회
    """
    try:
        masked_email = await db.masked_emails.find_one({"email_id": email_id})

        if not masked_email:
            raise HTTPException(status_code=404, detail="마스킹된 이메일을 찾을 수 없습니다")

        # _id 제거 (직렬화 오류 방지)
        masked_email.pop('_id', None)

        print(f"✅ 마스킹된 이메일 조회: {email_id}")

        return MaskedEmailResponse(
            success=True,
            message="마스킹된 이메일 조회 성공",
            data=MaskedEmailData(**masked_email)
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 마스킹된 이메일 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"마스킹된 이메일 조회 실패: {str(e)}")