from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ROOT_ADMIN = "root_admin"      # 시스템 관리자 (팀/사용자 관리)
    AUDITOR = "auditor"            # 감사자 (모든 로그/통계 읽기 전용)
    POLICY_ADMIN = "policy_admin"  # 정책 관리자 (엔티티/정책 CRUD)
    APPROVER = "approver"          # 승인자 (팀 소속 메일 승인/반려)
    USER = "user"                  # 일반 사용자 (메일 작성)

class TeamBase(BaseModel):
    """팀 기본 모델"""
    team_name: str
    description: Optional[str] = None
    approver_email: Optional[str] = None  # 해당 팀의 승인자

class TeamCreate(TeamBase):
    pass

class TeamResponse(TeamBase):
    created_at: datetime
    updated_at: datetime

class UserBase(BaseModel):
    email: EmailStr
    nickname: str
    department: Optional[str] = None
    team_name: Optional[str] = None  # 소속 팀 (USER, APPROVER용)
    role: UserRole = UserRole.USER

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    department: Optional[str] = None
    team_name: Optional[str] = None
    role: Optional[UserRole] = None
    password: Optional[str] = None

class UserInDB(UserBase):
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserResponse(UserBase):
    created_at: datetime
    updated_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenWithUser(Token):
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class EmailStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class AttachmentInfo(BaseModel):
    """첨부파일 정보"""
    filename: str
    content_type: str
    size: int
    hash: str  # SHA256


class EmailRecord(BaseModel):
    """DLP 메일 레코드"""
    from_email: str
    to_email: str
    subject: str
    original_body: str
    masked_body: Optional[str] = None
    status: EmailStatus = EmailStatus.PENDING

    # 첨부파일
    attachments: List[AttachmentInfo] = []

    # 팀/사용자 정보
    team_name: Optional[str] = None  # 발신자의 팀

    # 무결성 검증 필드
    content_hash: str  # 메일 전체 내용의 SHA256 해시
    dlp_token: str     # HMAC-SHA256 토큰 (프록시 → 수신 서버 전송 검증용)

    # 타임스탬프
    created_at: datetime = Field(default_factory=datetime.utcnow)
    received_at: Optional[datetime] = None  # 프록시가 메일을 받은 시간

    # DLP 검증 정보
    dlp_verified: bool = False  # 토큰 검증 완료 여부
    dlp_verified_at: Optional[datetime] = None
    dlp_policy_violation: Optional[str] = None  # DLP 정책 위반 사항

    # 승인/반려
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    reject_reason: Optional[str] = None