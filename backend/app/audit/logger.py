"""
감사 로그 유틸리티
"""
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import Request

from .models import AuditEventType, AuditSeverity, AuditLog
from app.database.mongodb import get_database


class AuditLogger:
    """감사 로그 작성기"""

    AUDIT_LOG_DIR = "/var/log/audit"
    AUDIT_LOG_FILE = "audit.log"

    @classmethod
    def _ensure_log_directory(cls):
        """로그 디렉토리 생성"""
        try:
            # /var/log/audit 접근 불가 시 로컬 디렉토리 사용
            if not os.access("/var/log", os.W_OK):
                cls.AUDIT_LOG_DIR = str(Path(__file__).parent.parent.parent / "logs" / "audit")

            Path(cls.AUDIT_LOG_DIR).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"⚠️ 감사 로그 디렉토리 생성 실패: {e}")
            # 백업: 프로젝트 루트의 logs 디렉토리 사용
            cls.AUDIT_LOG_DIR = str(Path(__file__).parent.parent.parent / "logs" / "audit")
            Path(cls.AUDIT_LOG_DIR).mkdir(parents=True, exist_ok=True)

    @classmethod
    def _write_to_file(cls, log_entry: Dict[str, Any]):
        """파일에 로그 기록"""
        try:
            cls._ensure_log_directory()
            log_path = Path(cls.AUDIT_LOG_DIR) / cls.AUDIT_LOG_FILE

            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False, default=str) + "\n")

        except Exception as e:
            print(f"⚠️ 감사 로그 파일 기록 실패: {e}")

    @classmethod
    async def _write_to_db(cls, log: AuditLog):
        """MongoDB에 로그 기록"""
        try:
            db = get_database()
            log_dict = log.model_dump()
            await db.audit_logs.insert_one(log_dict)
        except Exception as e:
            print(f"⚠️ 감사 로그 DB 기록 실패: {e}")

    @classmethod
    async def log(
        cls,
        event_type: AuditEventType,
        user_email: str,
        action: str,
        user_role: str = "user",
        severity: AuditSeverity = AuditSeverity.INFO,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ):
        """
        감사 로그 기록

        Args:
            event_type: 이벤트 타입
            user_email: 사용자 이메일
            action: 수행한 작업 설명
            user_role: 사용자 역할
            severity: 심각도
            resource_type: 리소스 타입 (email, entity, policy 등)
            resource_id: 리소스 ID
            details: 추가 상세 정보
            request: FastAPI Request 객체 (IP, User-Agent 추출용)
            success: 성공 여부
            error_message: 에러 메시지
        """
        # IP 주소 및 User-Agent 추출
        ip_address = None
        user_agent = None

        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")

        # 로그 객체 생성
        log = AuditLog(
            timestamp=datetime.utcnow(),
            event_type=event_type,
            severity=severity,
            user_email=user_email,
            user_role=user_role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
        )

        # 파일에 기록
        log_entry = log.model_dump()
        cls._write_to_file(log_entry)

        # DB에 기록
        await cls._write_to_db(log)

        # 콘솔 출력
        severity_emoji = {
            AuditSeverity.INFO: "ℹ️",
            AuditSeverity.WARNING: "⚠️",
            AuditSeverity.ERROR: "❌",
            AuditSeverity.CRITICAL: "🚨",
        }

        emoji = severity_emoji.get(severity, "📝")
        status = "✅" if success else "❌"

        print(
            f"{emoji} [AUDIT] {status} {event_type.value} | "
            f"User: {user_email} ({user_role}) | "
            f"Action: {action}"
        )

        if resource_type and resource_id:
            print(f"        Resource: {resource_type}#{resource_id}")

        if not success and error_message:
            print(f"        Error: {error_message}")

    @classmethod
    async def log_email_send(
        cls,
        user_email: str,
        user_role: str,
        to_emails: list[str],
        subject: str,
        has_attachments: bool = False,
        masked_count: int = 0,
        request: Optional[Request] = None,
    ):
        """이메일 전송 로그"""
        await cls.log(
            event_type=AuditEventType.EMAIL_SEND,
            user_email=user_email,
            user_role=user_role,
            action=f"이메일 전송: {subject}",
            resource_type="email",
            details={
                "to": to_emails,
                "subject": subject,
                "has_attachments": has_attachments,
                "masked_count": masked_count,
            },
            request=request,
        )

    @classmethod
    async def log_masking_decision(
        cls,
        user_email: str,
        user_role: str,
        pii_count: int,
        masked_count: int,
        receiver_type: str,
        cited_guidelines: list[str],
        request: Optional[Request] = None,
    ):
        """마스킹 결정 로그"""
        await cls.log(
            event_type=AuditEventType.MASKING_DECISION,
            user_email=user_email,
            user_role=user_role,
            action=f"마스킹 결정: {masked_count}/{pii_count}개 PII 마스킹",
            resource_type="masking",
            details={
                "pii_count": pii_count,
                "masked_count": masked_count,
                "receiver_type": receiver_type,
                "cited_guidelines": cited_guidelines,
            },
            request=request,
        )

    @classmethod
    async def log_entity_crud(
        cls,
        operation: str,  # create, update, delete, view
        user_email: str,
        user_role: str,
        entity_id: str,
        entity_name: str,
        request: Optional[Request] = None,
    ):
        """엔티티 CRUD 로그"""
        event_map = {
            "create": AuditEventType.ENTITY_CREATE,
            "update": AuditEventType.ENTITY_UPDATE,
            "delete": AuditEventType.ENTITY_DELETE,
            "view": AuditEventType.ENTITY_VIEW,
        }

        await cls.log(
            event_type=event_map.get(operation, AuditEventType.ENTITY_VIEW),
            user_email=user_email,
            user_role=user_role,
            action=f"엔티티 {operation}: {entity_name}",
            resource_type="entity",
            resource_id=entity_id,
            details={"entity_name": entity_name},
            request=request,
        )

    @classmethod
    async def log_settings_change(
        cls,
        user_email: str,
        user_role: str,
        setting_type: str,
        changes: Dict[str, Any],
        request: Optional[Request] = None,
    ):
        """설정 변경 로그"""
        await cls.log(
            event_type=AuditEventType.SETTINGS_UPDATE,
            user_email=user_email,
            user_role=user_role,
            action=f"설정 변경: {setting_type}",
            resource_type="settings",
            details={"setting_type": setting_type, "changes": changes},
            request=request,
            severity=AuditSeverity.WARNING,
        )

    @classmethod
    async def log_vector_store_sync(
        cls,
        user_email: str,
        user_role: str,
        synced_count: int,
        failed_count: int,
        request: Optional[Request] = None,
    ):
        """Vector Store 동기화 로그"""
        await cls.log(
            event_type=AuditEventType.VECTOR_STORE_SYNC,
            user_email=user_email,
            user_role=user_role,
            action=f"Vector Store 동기화: {synced_count}개 성공, {failed_count}개 실패",
            resource_type="system",
            details={"synced": synced_count, "failed": failed_count},
            request=request,
        )

    @classmethod
    async def log_auth_event(
        cls,
        event_type: AuditEventType,
        user_email: str,
        success: bool = True,
        error_message: Optional[str] = None,
        request: Optional[Request] = None,
    ):
        """인증 이벤트 로그"""
        severity = AuditSeverity.INFO if success else AuditSeverity.WARNING

        action_map = {
            AuditEventType.LOGIN: "로그인",
            AuditEventType.LOGOUT: "로그아웃",
            AuditEventType.AUTH_FAIL: "인증 실패",
        }

        await cls.log(
            event_type=event_type,
            user_email=user_email,
            user_role="unknown",
            action=action_map.get(event_type, "인증 이벤트"),
            severity=severity,
            success=success,
            error_message=error_message,
            request=request,
        )
