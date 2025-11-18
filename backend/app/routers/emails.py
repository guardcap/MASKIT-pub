from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Query
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
from bson import ObjectId

from app.database.mongodb import get_db
from app.auth.auth_utils import get_current_user
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

router = APIRouter(prefix="/api/v1/emails", tags=["Emails"])

# ===== 첨부파일 업로드 API =====

@router.post("/upload-attachment")
async def upload_attachment(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    첨부파일 업로드 (GridFS 사용)
    - write-email.html에서 파일 선택 시 호출
    - GridFS에 파일 저장 후 file_id 반환
    """
    try:
        # GridFS 버킷 생성
        fs = AsyncIOMotorGridFSBucket(db)
        
        # 파일 읽기
        file_data = await file.read()
        
        # 파일 크기 제한 (예: 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(file_data) > max_size:
            raise HTTPException(status_code=400, detail="파일 크기는 10MB를 초과할 수 없습니다")
        
        # GridFS에 저장
        file_id = await fs.upload_from_stream(
            file.filename,
            file_data,
            metadata={
                "content_type": file.content_type,
                "uploaded_by": current_user["email"],
                "uploaded_at": datetime.utcnow(),
                "size": len(file_data)
            }
        )
        
        print(f"✅ 파일 업로드 성공: {file.filename} (ID: {file_id})")
        
        return {
            "success": True,
            "file_id": str(file_id),
            "filename": file.filename,
            "size": len(file_data),
            "content_type": file.content_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 파일 업로드 오류: {e}")
        raise HTTPException(status_code=500, detail=f"파일 업로드 실패: {str(e)}")


# ===== 첨부파일 다운로드 API (일반) =====

@router.get("/attachments/{file_id}")
async def download_attachment(
    file_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    첨부파일 다운로드
    """
    try:
        fs = AsyncIOMotorGridFSBucket(db)
        
        # 파일 ID 유효성 검사
        try:
            object_id = ObjectId(file_id)
        except:
            raise HTTPException(status_code=400, detail="잘못된 파일 ID입니다")
        
        # 파일 다운로드
        try:
            grid_out = await fs.open_download_stream(object_id)
            filename = grid_out.filename
            content_type = grid_out.metadata.get("content_type", "application/octet-stream")
            
            # ✅ async generator로 chunk 단위로 읽기
            async def file_iterator():
                while True:
                    chunk = await grid_out.readchunk()
                    if not chunk:
                        break
                    yield chunk
            
            print(f"✅ 파일 다운로드 시작: {filename} (ID: {file_id})")
            
            return StreamingResponse(
                file_iterator(),
                media_type=content_type,
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"'
                }
            )
            
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 파일 다운로드 오류: {e}")
        raise HTTPException(status_code=500, detail=f"파일 다운로드 실패: {str(e)}")


# ===== 이메일별 첨부파일 다운로드 (권한 확인 포함) =====

@router.get("/email/{email_id}/attachments/{file_id}")
async def download_email_attachment(
    email_id: str,
    file_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    특정 이메일의 첨부파일 다운로드 (권한 확인)
    - 이메일 발신자/수신자만 다운로드 가능
    """
    try:
        # 이메일 확인
        email = await db.emails.find_one({"_id": ObjectId(email_id)})
        
        if not email:
            raise HTTPException(status_code=404, detail="이메일을 찾을 수 없습니다")
        
        # 권한 확인
        if email["from_email"] != current_user["email"] and email["to_email"] != current_user["email"]:
            raise HTTPException(status_code=403, detail="첨부파일 다운로드 권한이 없습니다")
        
        # 첨부파일 확인
        attachment_exists = False
        for att in email.get("attachments", []):
            if isinstance(att, dict) and att.get("file_id") == file_id:
                attachment_exists = True
                break
        
        if not attachment_exists:
            raise HTTPException(status_code=404, detail="이메일에 해당 첨부파일이 없습니다")
        
        # 파일 다운로드
        fs = AsyncIOMotorGridFSBucket(db)
        
        try:
            object_id = ObjectId(file_id)
        except:
            raise HTTPException(status_code=400, detail="잘못된 파일 ID입니다")
        
        try:
            grid_out = await fs.open_download_stream(object_id)
            filename = grid_out.filename
            content_type = grid_out.metadata.get("content_type", "application/octet-stream")
            
            # ✅ async generator로 chunk 단위로 읽기
            async def file_iterator():
                while True:
                    chunk = await grid_out.readchunk()
                    if not chunk:
                        break
                    yield chunk
            
            print(f"✅ 이메일 첨부파일 다운로드 시작: {filename} (Email: {email_id}, User: {current_user['email']})")
            
            return StreamingResponse(
                file_iterator(),
                media_type=content_type,
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"'
                }
            )
            
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 이메일 첨부파일 다운로드 오류: {e}")
        raise HTTPException(status_code=500, detail=f"첨부파일 다운로드 실패: {str(e)}")


# ===== 이메일 전송 Request Models =====

class SendEmailRequest(BaseModel):
    """이메일 전송 요청"""
    from_email: EmailStr
    to: str  # 쉼표로 구분된 이메일들
    subject: str
    body: str
    attachments: List[dict] = []  # [{"file_id": "...", "filename": "...", "size": 123}]
    masking_applied: bool = False
    masking_decisions: dict = {}  # 마스킹 결정사항


# ===== 이메일 전송 APIs =====

@router.post("/send")
async def send_email(
    request: SendEmailRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    이메일 전송 (임시 저장)
    - attachments에 file_id가 포함된 경우 GridFS 파일과 연결
    """
    try:
        recipients = [email.strip() for email in request.to.split(',')]
        email_ids = []
        
        # 첨부파일 정보 처리
        attachment_records = []
        for att in request.attachments:
            if isinstance(att, dict) and att.get("file_id"):
                attachment_records.append({
                    "file_id": att["file_id"],
                    "filename": att.get("filename", "unknown"),
                    "size": att.get("size", 0),
                    "content_type": att.get("content_type", "application/octet-stream")
                })
            elif isinstance(att, str):
                # 하위 호환성: 파일명만 있는 경우
                attachment_records.append({"filename": att})
        
        for recipient in recipients:
            email_record = {
                "from_email": request.from_email,
                "to_email": recipient,
                "subject": request.subject,
                "body": request.body,  # 마스킹된 본문
                "attachments": attachment_records,
                "team_name": current_user.get("team_name"),
                "masking_decisions": request.masking_decisions,
                "created_at": datetime.utcnow(),
                "sent_at": datetime.utcnow(),
                "read_at": None,
            }

            result = await db.emails.insert_one(email_record)
            email_ids.append(str(result.inserted_id))

        print(f"✅ 이메일 전송: {len(recipients)}명, 첨부파일: {len(attachment_records)}개")

        return JSONResponse({
            "success": True,
            "message": f"{len(recipients)}명의 수신자에게 이메일이 전송되었습니다",
            "email_ids": email_ids,
            "data": {
                "from": request.from_email,
                "to": recipients,
                "subject": request.subject,
                "sent_at": datetime.utcnow().isoformat(),
                "attachments": len(attachment_records)
            }
        })
        
    except Exception as e:
        print(f"❌ 이메일 전송 오류: {e}")
        raise HTTPException(status_code=500, detail=f"이메일 전송 실패: {str(e)}")




# ===== 메일함 조회 APIs =====

@router.get("/my-emails")
async def get_my_emails(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    내가 보낸 이메일 목록 조회
    """
    try:
        # 쿼리 조건
        query = {"from_email": current_user["email"]}

        # 이메일 목록 조회
        cursor = db.emails.find(query).sort("created_at", -1).limit(100)
        emails = []

        async for email in cursor:
            email["_id"] = str(email["_id"])
            email["id"] = str(email["_id"])  # 프론트엔드 호환성
            emails.append(email)

        print(f"✅ 보낸 메일 조회: {current_user['email']} - {len(emails)}개")
        return emails

    except Exception as e:
        print(f"❌ 보낸 메일 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"메일 조회 실패: {str(e)}")


@router.get("/received-emails")
async def get_received_emails(
    status_filter: Optional[str] = Query(None, description="read/unread"),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    내가 받은 이메일 목록 조회
    """
    try:
        # 쿼리 조건
        query = {"to_email": current_user["email"]}
        
        if status_filter == "unread":
            query["read_at"] = None
        elif status_filter == "read":
            query["read_at"] = {"$ne": None}
        
        # 이메일 목록 조회
        cursor = db.emails.find(query).sort("sent_at", -1).limit(100)
        emails = []
        
        async for email in cursor:
            email["_id"] = str(email["_id"])
            email["id"] = str(email["_id"])  # 프론트엔드 호환성
            # read 상태 추가 (read_at이 있으면 읽음)
            email["read"] = email.get("read_at") is not None
            emails.append(email)

        print(f"✅ 받은 메일 조회: {current_user['email']} - {len(emails)}개")
        return emails
        
    except Exception as e:
        print(f"❌ 받은 메일 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"메일 조회 실패: {str(e)}")


@router.get("/email/{email_id}")
async def get_email_detail(
    email_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    이메일 상세 조회 (권한 확인 포함)
    """
    try:
        # ObjectId 변환
        try:
            obj_id = ObjectId(email_id)
        except:
            raise HTTPException(status_code=400, detail="잘못된 이메일 ID입니다")
        
        # 이메일 조회
        email = await db.emails.find_one({"_id": obj_id})
        
        if not email:
            raise HTTPException(status_code=404, detail="이메일을 찾을 수 없습니다")
        
        # 권한 확인 (발신자 또는 수신자만 조회 가능)
        user_email = current_user["email"]
        if email.get("from_email") != user_email and email.get("to_email") != user_email:
            # 관리자는 모든 메일 조회 가능
            if current_user.get("role") not in ["root_admin", "auditor", "approver"]:
                raise HTTPException(status_code=403, detail="이메일 조회 권한이 없습니다")
        
        # 받은 메일인 경우 읽음 처리
        if email.get("to_email") == user_email and not email.get("read_at"):
            await db.emails.update_one(
                {"_id": obj_id},
                {"$set": {"read_at": datetime.utcnow()}}
            )
            email["read_at"] = datetime.utcnow()
        
        # ObjectId를 문자열로 변환
        email["_id"] = str(email["_id"])
        email["id"] = str(email["_id"])
        
        print(f"✅ 메일 상세 조회: {email_id} by {user_email}")
        return email
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 메일 상세 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"메일 조회 실패: {str(e)}")


