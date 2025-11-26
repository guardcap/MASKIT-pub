"""
감사 로그 모델
"""
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class AuditEventType(str, Enum):
    """감사 이벤트 타입"""
    # 메일 관련
    EMAIL_COMPOSE = "email_compose"
    EMAIL_SEND = "email_send"
    EMAIL_READ = "email_read"
    EMAIL_DELETE = "email_delete"

    # 마스킹 관련
    MASKING_DECISION = "masking_decision"
    MASKING_APPLY = "masking_apply"
    MASKING_BYPASS = "masking_bypass"

    # 엔티티 관련
    ENTITY_CREATE = "entity_create"
    ENTITY_UPDATE = "entity_update"
    ENTITY_DELETE = "entity_delete"
    ENTITY_VIEW = "entity_view"

    # 설정 관련
    SETTINGS_UPDATE = "settings_update"
    ENV_CHANGE = "env_change"
    SMTP_CONFIG = "smtp_config"

    # 시스템 관련
    VECTOR_STORE_SYNC = "vector_store_sync"
    POLICY_UPLOAD = "policy_upload"
    POLICY_UPDATE = "policy_update"  # ✅ 추가
    POLICY_DELETE = "policy_delete"

    # 인증 관련
    LOGIN = "login"
    LOGOUT = "logout"
    AUTH_FAIL = "auth_fail"

    # 권한 관련
    PERMISSION_DENIED = "permission_denied"
    ROLE_CHANGE = "role_change"


class AuditSeverity(str, Enum):
    """감사 로그 심각도"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLog(BaseModel):
    """감사 로그 모델"""
    timestamp: datetime
    event_type: AuditEventType
    severity: AuditSeverity
    user_email: str
    user_role: str
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Dict[str, Any] = {}
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None

    class Config:
        use_enum_values = True


class AuditLogResponse(BaseModel):
    """감사 로그 응답"""
    total: int
    logs: list[Dict[str, Any]]
    page: int
    page_size: int
