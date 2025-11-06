from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
import shutil
import json
from typing import List
import asyncio

router = APIRouter()

class FileItem(BaseModel):
    id: str
    name: str
    kind: str
    path: str

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@router.post("/upload_email")
async def upload_email(
    from_email: str = Form(...),
    to_email: str = Form(...),
    subject: str = Form(...),
    original_body: str = Form(...),
    attachments: List[UploadFile] = File([]) 
):
    # 폴더 내용물 삭제 로직
    if os.path.exists(UPLOAD_DIR):
        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')
    
    # 이메일 본문 저장
    with open(os.path.join(UPLOAD_DIR, "email_body.txt"), "w", encoding="utf-8") as f:
        f.write(original_body)

    # <<< --- 이 부분이 누락되었을 가능성이 높습니다 --- >>>
    # 실제 수신자와 제목 정보를 json 파일로 저장합니다.
    meta_data = {
        "recipients": [email.strip() for email in to_email.split(',')],
        "subject": subject
    }
    with open(os.path.join(UPLOAD_DIR, "email_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta_data, f, ensure_ascii=False, indent=4)
    # <<< --------------------------------------------- >>>

    # 첨부파일 저장 로직
    for attachment in attachments:
        if attachment and attachment.filename:
            file_path = os.path.join(UPLOAD_DIR, attachment.filename)
            with open(file_path, "wb") as f:
                f.write(await attachment.read())
            print(f"첨부파일 저장 완료: {attachment.filename}")

    return {"message": "Email data received"}

@router.get("/files", response_model=list[FileItem])
def get_files():
    files_list = []
    
    for i, filename in enumerate(os.listdir(UPLOAD_DIR)):
        # <<< --- 수정된 부분: email_meta.json 파일은 목록에서 제외 --- >>>
        if filename == 'email_meta.json':
            continue
        # <<< ---------------------------------------------------- >>>
        file_kind = "text"
        if filename == "email_body.txt":
            file_kind = "email"
        elif filename.endswith((".png", ".jpg", ".jpeg", ".gif")):
            file_kind = "image"
        elif filename.endswith(".pdf"):
            file_kind = "pdf"
        elif filename.endswith(".docx"):
            file_kind = "docx"
        
        files_list.append(
            FileItem(
                id=f"file{i}",
                name=filename,
                kind=file_kind,
                path=f"/{UPLOAD_DIR}/{filename}"
            )
        )

    return files_list

@router.get("/files/watch")
async def watch_files():
    """Server-Sent Events를 사용한 파일 변경 감시"""
    async def event_generator():
        last_files = set()
        while True:
            try:
                current_files = set(os.listdir(UPLOAD_DIR)) if os.path.exists(UPLOAD_DIR) else set()
                if current_files != last_files:
                    yield f"data: {json.dumps({'files': list(current_files)})}\n\n"
                    last_files = current_files
                await asyncio.sleep(1)
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")