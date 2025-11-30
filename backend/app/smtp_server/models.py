from pydantic import BaseModel, EmailStr
from typing import List, Optional, Any
from datetime import datetime

# [추가] SMTP 설정을 DB에 저장하기 위한 모델
# (SettingsPage.tsx와 필드 이름이 같아야 함)
class SMTPSettings(BaseModel):
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False # SettingsPage에도 이 필드를 추가하는 것이 좋습니다.

# [오류 수정]
# 아래 라인은 models.py 파일이 자기 자신을 import 하려고 해서 순환 참조 오류를 일으켰습니다.
# from app.smtp_server.models import EmailSendRequest, EmailSendResponse, EmailListResponse # EmailSendRequest 모델도 수정 필요
# 위 라인을 제거합니다.

class EmailSendRequest(BaseModel):
    """
    이메일 전송 요청 모델 (smtp_config 제거됨)
    """
    from_email: EmailStr
    to: str  # 쉼표로 구분된 이메일 목록
    subject: str
    body: str
    cc: Optional[str] = None
    bcc: Optional[str] = None
    attachments: Optional[List[dict]] = None
    masked_email_id: Optional[str] = None  # 마스킹된 이메일 ID (MongoDB)
    use_masked_email: bool = False  # 마스킹된 이메일 사용 여부

    # [제거] 이 필드는 더 이상 클라이언트가 보내지 않음
    # smtp_config: Optional[SMTPSettings] = None 

class EmailSendResponse(BaseModel):
    success: bool
    message: str
    email_id: str
    sent_at: datetime

class EmailListResponse(BaseModel):
    emails: List[dict]
    total: int
    page: int
    page_size: int