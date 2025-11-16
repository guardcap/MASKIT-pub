"""
SMTP 메일 전송 및 이메일 관리 API 라우터
"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional
from datetime import datetime
from bson import ObjectId

from app.database.mongodb import get_database
from app.smtp_server.models import EmailSendRequest, EmailSendResponse, EmailListResponse
from app.smtp_server.client import smtp_client

router = APIRouter(prefix="/smtp", tags=["SMTP Email"])


@router.post("/send", response_model=EmailSendResponse)
async def send_email(email_data: EmailSendRequest):
    """
    SMTP를 통해 이메일 전송

    - **from_email**: 발신자 이메일
    - **to**: 수신자 이메일 (여러 개는 쉼표로 구분)
    - **subject**: 제목
    - **body**: 본문 (HTML 지원)
    - **cc**: 참조 (옵션)
    - **bcc**: 숨은 참조 (옵션)
    """
    try:
        # SMTP 클라이언트를 통해 메일 전송
        result = smtp_client.send_email(
            from_email=email_data.from_email,
            to=email_data.to,
            subject=email_data.subject,
            body=email_data.body,
            cc=email_data.cc,
            bcc=email_data.bcc,
            attachments=email_data.attachments,
            smtp_config=email_data.smtp_config  # 사용자 SMTP 설정 전달
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )

        # MongoDB에 전송 기록 저장
        db = get_database()
        email_record = {
            "from_email": email_data.from_email,
            "to_email": email_data.to,
            "cc": email_data.cc,
            "bcc": email_data.bcc,
            "subject": email_data.subject,
            "original_body": email_data.body,
            "masked_body": None,
            "status": "sent",
            "attachments": email_data.attachments or [],
            "sent_at": result["sent_at"],
            "created_at": datetime.utcnow(),
            "dlp_verified": False,
            "dlp_token": None
        }

        insert_result = await db.emails.insert_one(email_record)

        return EmailSendResponse(
            success=True,
            message=result["message"],
            email_id=str(insert_result.inserted_id),
            sent_at=result["sent_at"]
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"메일 전송 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/emails", response_model=EmailListResponse)
async def get_emails(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 당 항목 수"),
    status_filter: Optional[str] = Query(None, description="상태 필터 (sent, approved, rejected)")
):
    """
    이메일 목록 조회

    - **page**: 페이지 번호 (기본: 1)
    - **page_size**: 페이지 당 항목 수 (기본: 20, 최대: 100)
    - **status_filter**: 상태 필터 (옵션)
    """
    try:
        db = get_database()

        # 필터 조건
        query = {}
        if status_filter:
            query["status"] = status_filter

        # 전체 개수
        total = await db.emails.count_documents(query)

        # 페이징된 이메일 목록
        skip = (page - 1) * page_size
        emails_cursor = db.emails.find(query).sort("created_at", -1).skip(skip).limit(page_size)
        emails = await emails_cursor.to_list(length=page_size)

        # ObjectId를 문자열로 변환
        for email in emails:
            email["_id"] = str(email["_id"])

        return EmailListResponse(
            emails=emails,
            total=total,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"이메일 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/emails/{email_id}")
async def get_email(email_id: str):
    """
    특정 이메일 상세 조회

    - **email_id**: 이메일 ID
    """
    try:
        db = get_database()

        # ObjectId 변환
        try:
            obj_id = ObjectId(email_id)
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="잘못된 이메일 ID 형식입니다"
            )

        email = await db.emails.find_one({"_id": obj_id})

        if not email:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="이메일을 찾을 수 없습니다"
            )

        # ObjectId를 문자열로 변환
        email["_id"] = str(email["_id"])

        return email

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"이메일 조회 중 오류가 발생했습니다: {str(e)}"
        )