from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Query
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
from bson import ObjectId

from app.database.mongodb import get_db
from app.auth.auth_utils import get_current_user, get_current_auditor
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

router = APIRouter(prefix="/api/v1/emails", tags=["Emails"])


# ===== Auditor 전용: 전체 메일 로그 조회 API =====

@router.get("/all-logs")
async def get_all_email_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_auditor),  # Auditor 권한 체크
    db = Depends(get_db)
):
    """
    전체 사용자의 메일 전송 로그 조회 (Auditor 전용)
    
    - **skip**: 건너뛸 개수 (페이지네이션)
    - **limit**: 가져올 최대 개수 (기본 100, 최대 1000)
    
    반환 형식:
    ```json
    {
        "success": true,
        "total": 1234,
        "logs": [
            {
                "timestamp": "2025-01-18T12:34:56",
                "email_id": "507f1f77bcf86cd799439011",
                "team_name": "개발팀",
                "user_name": "홍길동",
                "from_email": "hong@example.com",
                "to_email": "recipient@example.com",
                "subject": "제목",
                "status": "approved"
            }
        ]
    }
    ```
    """
    try:
        print(f"[Auditor Logs API] 전체 메일 로그 조회 요청")
        print(f"  Auditor: {current_user['email']}")
        print(f"  Skip: {skip}, Limit: {limit}")
        
        # 전체 메일 개수 조회
        total = await db.emails.count_documents({})
        
        # 최신순으로 정렬하여 메일 로그 조회
        cursor = db.emails.find({}).sort("created_at", -1).skip(skip).limit(limit)
        emails = await cursor.to_list(length=limit)
        
        # 로그 포맷팅
        logs = []
        for email in emails:
            # 사용자 정보 조회 (from_email로)
            user = await db.users.find_one({"email": email.get("from_email")})
            user_name = user.get("nickname") if user else email.get("from_email", "알 수 없음")
            team_name = email.get("team_name") or (user.get("team_name") if user else "팀 없음")
            
            log_entry = {
                "timestamp": email.get("created_at").isoformat() if email.get("created_at") else None,
                "email_id": str(email["_id"]),
                "team_name": team_name,
                "user_name": user_name,
                "from_email": email.get("from_email"),
                "to_email": email.get("to_email"),
                "subject": email.get("subject", "(제목 없음)"),
                "status": email.get("status", "pending"),
                "has_attachments": bool(email.get("attachments")),
                "attachment_count": len(email.get("attachments", []))
            }
            logs.append(log_entry)
        
        print(f"[Auditor Logs API] ✅ {len(logs)}개 로그 조회 완료 (전체: {total}개)")
        
        return {
            "success": True,
            "total": total,
            "skip": skip,
            "limit": limit,
            "logs": logs
        }
        
    except Exception as e:
        print(f"[Auditor Logs API] ❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"메일 로그 조회 실패: {str(e)}"
        )


# ===== 기존 API들 (변경 없음) =====

@router.post("/upload-attachment")
async def upload_attachment(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    첨부파일 업로드 (GridFS 사용)
    """
    try:
        fs = AsyncIOMotorGridFSBucket(db)
        file_data = await file.read()
        
        max_size = 10 * 1024 * 1024
        if len(file_data) > max_size:
            raise HTTPException(status_code=400, detail="파일 크기는 10MB를 초과할 수 없습니다")
        
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
        
        try:
            object_id = ObjectId(file_id)
        except:
            raise HTTPException(status_code=400, detail="잘못된 파일 ID입니다")
        
        try:
            grid_out = await fs.open_download_stream(object_id)
            filename = grid_out.filename
            content_type = grid_out.metadata.get("content_type", "application/octet-stream")
            
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


@router.get("/email/{email_id}/attachments/{file_id}")
async def download_email_attachment(
    email_id: str,
    file_id: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    특정 이메일의 첨부파일 다운로드 (권한 확인)
    """
    try:
        email = await db.emails.find_one({"_id": ObjectId(email_id)})
        
        if not email:
            raise HTTPException(status_code=404, detail="이메일을 찾을 수 없습니다")
        
        if email["from_email"] != current_user["email"] and email["to_email"] != current_user["email"]:
            raise HTTPException(status_code=403, detail="첨부파일 다운로드 권한이 없습니다")
        
        attachment_exists = False
        for att in email.get("attachments", []):
            if isinstance(att, dict) and att.get("file_id") == file_id:
                attachment_exists = True
                break
        
        if not attachment_exists:
            raise HTTPException(status_code=404, detail="이메일에 해당 첨부파일이 없습니다")
        
        fs = AsyncIOMotorGridFSBucket(db)
        
        try:
            object_id = ObjectId(file_id)
        except:
            raise HTTPException(status_code=400, detail="잘못된 파일 ID입니다")
        
        try:
            grid_out = await fs.open_download_stream(object_id)
            filename = grid_out.filename
            content_type = grid_out.metadata.get("content_type", "application/octet-stream")
            
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


class SendEmailRequest(BaseModel):
    """이메일 전송 요청"""
    from_email: EmailStr
    to: str
    subject: str
    body: str
    attachments: List[dict] = []
    masking_applied: bool = False
    masking_decisions: dict = {}


@router.post("/send")
async def send_email(
    request: SendEmailRequest,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    이메일 전송 (임시 저장)
    """
    try:
        recipients = [email.strip() for email in request.to.split(',')]
        email_ids = []
        
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
                attachment_records.append({"filename": att})
        
        for recipient in recipients:
            email_record = {
                "from_email": request.from_email,
                "to_email": recipient,
                "subject": request.subject,
                "body": request.body,
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


@router.get("/my-emails")
async def get_my_emails(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    내가 보낸 이메일 목록 조회
    """
    try:
        query = {"from_email": current_user["email"]}
        cursor = db.emails.find(query).sort("created_at", -1).limit(100)
        emails = []

        async for email in cursor:
            email["_id"] = str(email["_id"])
            email["id"] = str(email["_id"])
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
        query = {"to_email": current_user["email"]}
        
        if status_filter == "unread":
            query["read_at"] = None
        elif status_filter == "read":
            query["read_at"] = {"$ne": None}
        
        cursor = db.emails.find(query).sort("sent_at", -1).limit(100)
        emails = []
        
        async for email in cursor:
            email["_id"] = str(email["_id"])
            email["id"] = str(email["_id"])
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
        try:
            obj_id = ObjectId(email_id)
        except:
            raise HTTPException(status_code=400, detail="잘못된 이메일 ID입니다")
        
        email = await db.emails.find_one({"_id": obj_id})
        
        if not email:
            raise HTTPException(status_code=404, detail="이메일을 찾을 수 없습니다")
        
        user_email = current_user["email"]
        if email.get("from_email") != user_email and email.get("to_email") != user_email:
            if current_user.get("role") not in ["root_admin", "auditor", "approver"]:
                raise HTTPException(status_code=403, detail="이메일 조회 권한이 없습니다")
        
        if email.get("to_email") == user_email and not email.get("read_at"):
            await db.emails.update_one(
                {"_id": obj_id},
                {"$set": {"read_at": datetime.utcnow()}}
            )
            email["read_at"] = datetime.utcnow()
        
        email["_id"] = str(email["_id"])
        email["id"] = str(email["_id"])
        
        print(f"✅ 메일 상세 조회: {email_id} by {user_email}")
        return email
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 메일 상세 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"메일 조회 실패: {str(e)}")