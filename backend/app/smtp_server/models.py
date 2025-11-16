"""
SMTP 메일 전송을 위한 Pydantic 모델
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime


class SMTPConfig(BaseModel):
    """사용자 SMTP 설정 모델"""
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    use_tls: bool = True
    use_ssl: bool = False


class EmailSendRequest(BaseModel):
    """메일 전송 요청 모델"""
    from_email: EmailStr
    to: str  # 여러 이메일을 쉼표로 구분
    subject: str
    body: str
    cc: Optional[str] = None
    bcc: Optional[str] = None
    attachments: Optional[List[str]] = None  # 첨부파일 경로 리스트
    smtp_config: Optional[Dict[str, Any]] = None  # 사용자 SMTP 설정 (선택)

    class Config:
        json_schema_extra = {
            "example": {
                "from_email": "sender@company.com",
                "to": "recipient@example.com",
                "subject": "테스트 메일",
                "body": "<p>메일 본문입니다.</p>",
                "cc": "cc@example.com",
                "bcc": "bcc@example.com",
                "smtp_config": {
                    "smtp_host": "smtp.gmail.com",
                    "smtp_port": 587,
                    "smtp_user": "user@gmail.com",
                    "smtp_password": "app_password",
                    "use_tls": True,
                    "use_ssl": False
                }
            }
        }


class EmailSendResponse(BaseModel):
    """메일 전송 응답 모델"""
    success: bool
    message: str
    email_id: Optional[str] = None
    sent_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "메일이 성공적으로 전송되었습니다",
                "email_id": "507f1f77bcf86cd799439011",
                "sent_at": "2025-11-14T12:00:00"
            }
        }


class EmailListResponse(BaseModel):
    """이메일 목록 응답 모델"""
    emails: List[dict]
    total: int
    page: int
    page_size: int
