"""
사용자 설정 관리 API
- 이메일 기본 설정
- SMTP 서버 설정
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional
from pydantic import BaseModel, EmailStr

from app.database.mongodb import get_database
from app.auth.auth_utils import get_current_user

router = APIRouter(prefix="/api/settings", tags=["Settings"])


# ===== Pydantic 모델 정의 =====

class EmailSettings(BaseModel):
    default_email: EmailStr


class SMTPSettings(BaseModel):
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False


class AllSettingsResponse(BaseModel):
    email_settings: Optional[EmailSettings] = None
    smtp_settings: Optional[SMTPSettings] = None


# ===== API 엔드포인트 =====

@router.get("/all", response_model=AllSettingsResponse)
async def get_all_settings(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    사용자의 모든 설정 조회
    - 이메일 기본 설정
    - SMTP 서버 설정
    """
    try:
        email_settings = None
        smtp_settings = None

        # 사용자 문서에서 설정 가져오기
        if "email_settings" in current_user and current_user["email_settings"]:
            email_settings = EmailSettings(**current_user["email_settings"])

        if "smtp_config" in current_user and current_user["smtp_config"]:
            smtp_settings = SMTPSettings(**current_user["smtp_config"])

        return AllSettingsResponse(
            email_settings=email_settings,
            smtp_settings=smtp_settings
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"설정 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/email")
async def save_email_settings(
    settings: EmailSettings,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    이메일 기본 설정 저장
    """
    try:
        # 사용자 문서 업데이트
        result = await db.users.update_one(
            {"email": current_user["email"]},
            {"$set": {"email_settings": settings.dict()}}
        )

        if result.modified_count == 0 and result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )

        return {
            "success": True,
            "message": "이메일 설정이 저장되었습니다",
            "settings": settings.dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"이메일 설정 저장 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/smtp")
async def save_smtp_settings(
    settings: SMTPSettings,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    SMTP 서버 설정 저장
    """
    try:
        print(f"\n[Settings] ===== SMTP 설정 저장 시작 =====")
        print(f"[Settings] 사용자 이메일: {current_user['email']}")
        print(f"[Settings] 저장할 설정: {dict((k, v if k != 'smtp_password' else '***') for k, v in settings.dict().items())}")

        # 사용자 문서 업데이트
        result = await db.users.update_one(
            {"email": current_user["email"]},
            {"$set": {"smtp_config": settings.dict()}}
        )

        print(f"[Settings] matched_count: {result.matched_count}")
        print(f"[Settings] modified_count: {result.modified_count}")

        if result.modified_count == 0 and result.matched_count == 0:
            print(f"[Settings] ❌ 사용자를 찾을 수 없습니다!")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )

        print(f"[Settings] ✅ SMTP 설정 저장 완료")
        print(f"[Settings] ===== SMTP 설정 저장 끝 =====\n")

        return {
            "success": True,
            "message": "SMTP 설정이 저장되었습니다",
            "settings": {
                **settings.dict(),
                "smtp_password": "***"  # 비밀번호는 응답에서 숨김
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SMTP 설정 저장 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/smtp/test")
async def test_smtp_connection(
    settings: SMTPSettings,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    SMTP 연결 테스트
    - 현재 입력된 설정으로 테스트 (저장하지 않음)
    """
    import smtplib

    try:
        # 제공된 설정 사용
        smtp_config = settings.dict()

        smtp_host = smtp_config.get("smtp_host")
        smtp_port = smtp_config.get("smtp_port", 587)
        smtp_user = smtp_config.get("smtp_user")
        smtp_password = smtp_config.get("smtp_password")
        use_tls = smtp_config.get("smtp_use_tls", True)
        use_ssl = smtp_config.get("smtp_use_ssl", False)

        print(f"[SMTP Test] 연결 테스트 시작...")
        print(f"  Host: {smtp_host}:{smtp_port}")
        print(f"  User: {smtp_user}")
        print(f"  TLS: {use_tls}, SSL: {use_ssl}")
        print(f"  Password 존재: {bool(smtp_password)}")

        # SMTP 서버 연결 테스트
        if use_ssl:
            # SSL 사용 (포트 465)
            print(f"[SMTP Test] SSL 모드로 연결 시도...")
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30) as server:
                print(f"[SMTP Test] SSL 연결 성공")
                server.set_debuglevel(0)  # 디버그 레벨 설정
                if smtp_user and smtp_password:
                    print(f"[SMTP Test] 로그인 시도 중...")
                    server.login(smtp_user, smtp_password)
                    print(f"[SMTP Test] 로그인 성공")
                server.noop()  # 연결 확인
        else:
            # TLS 또는 Plain SMTP (포트 587, 25)
            print(f"[SMTP Test] SMTP 모드로 연결 시도...")
            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
                print(f"[SMTP Test] SMTP 연결 성공")
                server.set_debuglevel(0)  # 디버그 레벨 설정
                server.ehlo()
                print(f"[SMTP Test] EHLO 성공")
                if use_tls:
                    print(f"[SMTP Test] STARTTLS 시작...")
                    server.starttls()
                    print(f"[SMTP Test] STARTTLS 성공")
                    server.ehlo()
                if smtp_user and smtp_password:
                    print(f"[SMTP Test] 로그인 시도 중...")
                    server.login(smtp_user, smtp_password)
                    print(f"[SMTP Test] 로그인 성공")
                server.noop()  # 연결 확인

        print(f"[SMTP Test] ✅ 연결 성공")

        return {
            "success": True,
            "message": "SMTP 서버 연결에 성공했습니다",
            "details": {
                "host": smtp_host,
                "port": smtp_port,
                "user": smtp_user,
                "tls": use_tls,
                "ssl": use_ssl
            }
        }

    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"인증 실패: 이메일 또는 비밀번호가 올바르지 않습니다. {str(e)}"
        print(f"[SMTP Test] ❌ {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_msg
        )

    except smtplib.SMTPConnectError as e:
        error_msg = f"서버 연결 실패: SMTP 서버 주소를 확인하세요. {str(e)}"
        print(f"[SMTP Test] ❌ {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error_msg
        )

    except TimeoutError as e:
        error_msg = f"연결 시간 초과: 서버 주소나 포트를 확인하세요. 방화벽이 차단하고 있을 수 있습니다."
        print(f"[SMTP Test] ❌ {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=error_msg
        )

    except smtplib.SMTPException as e:
        error_msg = f"SMTP 오류: {str(e)}"
        print(f"[SMTP Test] ❌ {error_msg}")
        # SSL/TLS 설정 힌트 추가
        hint = ""
        if smtp_port == 465 and not use_ssl:
            hint = " (포트 465는 SSL을 사용해야 합니다)"
        elif smtp_port == 587 and not use_tls:
            hint = " (포트 587은 TLS를 사용해야 합니다)"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg + hint
        )

    except Exception as e:
        error_msg = f"연결 테스트 실패: {str(e)}"
        error_type = type(e).__name__
        print(f"[SMTP Test] ❌ [{error_type}] {error_msg}")
        import traceback
        traceback.print_exc()

        # 일반적인 오류에 대한 힌트
        hint = ""
        if "timed out" in str(e).lower():
            hint = " 서버 주소나 포트 번호를 확인하세요. 방화벽이나 네트워크 설정을 확인해야 할 수 있습니다."
        elif "connection refused" in str(e).lower():
            hint = " 서버가 해당 포트에서 연결을 거부했습니다. 포트 번호를 확인하세요."

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg + hint
        )
