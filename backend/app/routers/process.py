from fastapi import APIRouter
from pydantic import BaseModel
import os
import json
import shutil  # <<<--- 추가
from pathlib import Path  # <<<--- 추가

# 이 import들은 실제 프로젝트 경로와 파일에 맞게 존재해야 합니다.
from ..routers.uploads import get_files, UPLOAD_DIR
from ..routers.ocr_needed import check_ocr_needed, PreflightCheckRequest
from ..routers.ocr import extract_ocr
from ..utils.recognizer_engine import recognize_pii_in_text

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
from typing import List

router = APIRouter()

@router.post("/documents")
async def process_documents():
    file_list = get_files()
    results = []
    
    for file_item in file_list:
        if file_item.name == "email_body.txt":
            file_path = os.path.join(UPLOAD_DIR, file_item.name)
            
            with open(file_path, "r", encoding="utf-8") as f:
                email_content = f.read()

            analysis_result = recognize_pii_in_text(email_content)
            
            if isinstance(analysis_result, dict):
                analysis_result['original_text'] = email_content

            results.append({
                "filename": "email 본문",
                "status": "ANALYSIS_COMPLETED",
                "analysis_data": analysis_result
            })
            continue

        ocr_needed_data = check_ocr_needed(PreflightCheckRequest(filename=file_item.name))

        if ocr_needed_data.get("ocr_needed", False):
            file_path = os.path.join(UPLOAD_DIR, file_item.name)
            
            if not os.path.exists(file_path):
                results.append({"filename": file_item.name, "status": "Error", "message": "File not found"})
                continue
                
            with open(file_path, "rb") as f:
                file_content = f.read()

            ocr_result = await extract_ocr(file_content=file_content, file_name=file_item.name)
            
            analysis_text = ""
            if isinstance(ocr_result, str):
                analysis_text = ocr_result
            elif isinstance(ocr_result, dict):
                analysis_text = ocr_result.get("full_text", "")

            analysis_result = recognize_pii_in_text(analysis_text, ocr_result)
            
            if isinstance(analysis_result, dict):
                analysis_result['original_text'] = analysis_text

            results.append({
                "filename": file_item.name,
                "status": "ANALYSIS_COMPLETED",
                "ocr_data": ocr_result,
                "analysis_data": analysis_result
            })
        
        else:
            results.append({
                "filename": file_item.name,
                "status": "ANALYSIS_SKIPPED",
                "message": "OCR 및 분석이 필요하지 않은 파일"
            })

    return {"message": "Processing started", "details": results}

# --- 네이버 계정 정보 ---
NAVER_SMTP_SERVER = "smtp.naver.com"
NAVER_SMTP_PORT = 587
SENDER_NAVER_ID = "pblteam01"
SENDER_NAVER_EMAIL = "pblteam01@naver.com"
SENDER_APP_PASSWORD = os.getenv("NAVER_APP_PASSWORD")

class ApproveRequest(BaseModel):
    recipients: List[str]
    subject: str
    final_body: str
    attachments: List[str]

def clear_uploads_folder():
    """uploads 폴더의 모든 파일과 하위 디렉토리를 삭제합니다."""
    try:# 현재 파일 기준 상대경로로 uploads 폴더 찾기
        # process.py는 app/routers/에 있고, uploads는 프로젝트 루트에 있음
        current_file = Path(__file__)  # app/routers/process.py
        project_root = current_file.parent.parent.parent  # Guardcap-dev/
        upload_path = project_root / "uploads"
        print(f"🔍 정리 대상 경로: {upload_path.absolute()}")
        
        if not upload_path.exists():
            print(f"⚠️ uploads 폴더가 존재하지 않습니다: {upload_path}")
            return False
            
        deleted_count = 0
        for item in upload_path.iterdir():
            try:
                if item.is_file():
                    item.unlink()
                    print(f"🗑️ 파일 삭제됨: {item.name}")
                    deleted_count += 1
                elif item.is_dir():
                    shutil.rmtree(item)
                    print(f"🗑️ 디렉토리 삭제됨: {item.name}")
                    deleted_count += 1
            except Exception as item_error:
                print(f"⚠️ {item.name} 삭제 실패: {item_error}")
        
        print(f"✅ uploads 폴더 정리 완료 (삭제된 항목: {deleted_count}개)")
        return True
        
    except Exception as e:
        print(f"❗️ uploads 폴더 정리 중 오류 발생: {e}")
        return False

@router.post("/approve_and_send")
async def approve_and_send_email(request: ApproveRequest):
    if not SENDER_APP_PASSWORD:
        return {"error": "네이버 앱 비밀번호가 서버 환경 변수에 설정되지 않았습니다."}
    
    try:
        msg = MIMEMultipart()
        msg["Subject"] = Header(request.subject, 'utf-8')
        msg["From"] = SENDER_NAVER_EMAIL
        msg["To"] = ", ".join(request.recipients)
        
        msg.attach(MIMEText(request.final_body, 'plain', 'utf-8'))
        
        for filename in request.attachments:
            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{Header(filename, "utf-8").encode()}"')
                msg.attach(part)

        with smtplib.SMTP(NAVER_SMTP_SERVER, NAVER_SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SENDER_NAVER_ID, SENDER_APP_PASSWORD)
            smtp.send_message(msg)
            
        print(f"✅ 최종 메일을 {request.recipients} (으)로 성공적으로 발송했습니다.")
        
        # ✅ 메일 발송 성공 후 uploads 폴더 비우기
        clear_uploads_folder()
        
        return {"message": "Email sent successfully"}

    except Exception as e:
        print(f"❗️ 네이버 메일 발송 중 오류 발생: {e}")
        return {"error": str(e)}