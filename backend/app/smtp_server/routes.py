"""
SMTP 메일 전송 및 이메일 관리 API 라우터 (수정됨)
"""
from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import Optional, Any # <<< [수정] Any 또는 dict를 위해 추가
from datetime import datetime
from bson import ObjectId

from app.database.mongodb import get_database, SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_USE_TLS, SMTP_USE_SSL # 기본 설정 Import
from app.smtp_server.models import EmailSendRequest, EmailSendResponse, EmailListResponse
from app.smtp_server.client import smtp_client

# [!!! 오류 수정 지점 !!!]
# 'User' 모델을 찾을 수 없으므로, import 라인을 제거하고
# 'get_current_user'가 반환하는 타입을 'dict' 또는 'Any'로 변경합니다.
#
# 아래 from ... import ... 부분을 실제 파일 위치에 맞게 수정해주세요.
from app.auth.auth_utils import get_current_user # <<< [중요] 이 경로는 올바르다고 가정합니다.
# from app.auth.models import User # <<< [수정] 'User' 모델을 찾을 수 없으므로 이 라인을 제거합니다.


router = APIRouter(prefix="/smtp", tags=["SMTP Email"])


@router.post("/send", response_model=EmailSendResponse)
async def send_email(
    email_data: EmailSendRequest, # 1. 이 모델에서 smtp_config 필드 제거 (아래 models.py 참고)
    db: get_database = Depends(),
    # [수정] current_user: User -> current_user: dict
    # get_current_user가 Pydantic 모델이 아닌 dict를 반환한다고 가정합니다.
    current_user: dict = Depends(get_current_user) # 2. 인증된 사용자 정보를 가져옵니다.
):
    """
    SMTP를 통해 이메일 전송 (인증된 사용자의 SMTP 설정 사용)

    - **from_email**: 발신자 이메일
    - **to**: 수신자 이메일 (여러 개는 쉼표로 구분)
    - **subject**: 제목
    - **body**: 본문 (HTML 지원)
    - **cc**: 참조 (옵션)
    - **bcc**: 숨은 참조 (옵션)
    """
    try:
        # 3. DB에서 현재 사용자의 SMTP 설정을 가져옵니다.
        #    (User 모델이 Pydantic이 아닌 dict일 경우: current_user["smtp_config"])
        #    (user.smtp_config는 User 모델 정의에 따라 다릅니다)
        user_smtp_config = current_user.get("smtp_config") 

        # 4. 사용자 설정이 없으면, .env의 기본 설정을 사용합니다.
        if not user_smtp_config or not user_smtp_config.get("smtp_host"):
            print(f"[SMTP Send] 사용자 {current_user.get('email')}의 SMTP 설정이 없어 기본 서버 설정을 사용합니다.")
            smtp_config = {
                "smtp_host": SMTP_HOST,
                "smtp_port": SMTP_PORT,
                "smtp_user": SMTP_USER,
                "smtp_password": SMTP_PASSWORD,
                "smtp_use_tls": SMTP_USE_TLS,
                "smtp_use_ssl": SMTP_USE_SSL,
            }
        else:
            print(f"[SMTP Send] 사용자 {current_user.get('email')}의 저장된 SMTP 설정을 사용합니다.")
            smtp_config = user_smtp_config

        # 5. SMTP 클라이언트를 통해 메일 전송
        result = smtp_client.send_email(
            from_email=email_data.from_email,
            to=email_data.to,
            subject=email_data.subject,
            body=email_data.body,
            cc=email_data.cc,
            bcc=email_data.bcc,
            attachments=email_data.attachments,
            smtp_config=smtp_config  # 4번에서 결정된 SMTP 설정 전달
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )

        # MongoDB에 전송 기록 저장
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
            "dlp_token": None,
            "owner_email": current_user.get("email") # [추가] 누가 보냈는지 기록
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
    status_filter: Optional[str] = Query(None, description="상태 필터 (sent, approved, rejected)"),
    db: get_database = Depends(),
    # [수정] current_user: User -> current_user: dict
    current_user: dict = Depends(get_current_user) # [추가] 인증
):
    """
    이메일 목록 조회 (로그인한 사용자의 이메일만)

    - **page**: 페이지 번호 (기본: 1)
    - **page_size**: 페이지 당 항목 수 (기본: 20, 최대: 100)
    - **status_filter**: 상태 필터 (옵션)
    """
    try:
        # 필터 조건
        query = {
            "owner_email": current_user.get("email") # [수정] 내 이메일만 조회
        }
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
async def get_email(
    email_id: str,
    db: get_database = Depends(),
    # [수정] current_user: User -> current_user: dict
    current_user: dict = Depends(get_current_user) # [추가] 인증
):
    """
    특정 이메일 상세 조회 (본인 이메일만)

    - **email_id**: 이메일 ID
    """
    try:
        # ObjectId 변환
        try:
            obj_id = ObjectId(email_id)
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="잘못된 이메일 ID 형식입니다"
            )

        # [수정] 본인 이메일인지 확인
        query = {
            "_id": obj_id,
            "owner_email": current_user.get("email")
        }
        email = await db.emails.find_one(query)

        if not email:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, # <<< 오타 수정
                detail="이메일을 찾을 수 없거나 권한이 없습니다"
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