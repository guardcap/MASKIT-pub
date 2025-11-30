from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime,timedelta
from enum import Enum
def get_kst_now():
    """한국 표준시(KST) 반환"""
    return datetime.utcnow() + timedelta(hours=9)
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
    phone_number: Optional[str] = None  # 전화번호
    profile_photo: Optional[str] = None  # 프로필 사진 URL

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    department: Optional[str] = None
    team_name: Optional[str] = None
    role: Optional[UserRole] = None
    password: Optional[str] = None
    phone_number: Optional[str] = None
    profile_photo: Optional[str] = None

class UserSelfUpdate(BaseModel):
    """사용자 본인 프로필 수정용 (role, team_name 제외)"""
    nickname: Optional[str] = None
    department: Optional[str] = None
    password: Optional[str] = None
    phone_number: Optional[str] = None
    profile_photo: Optional[str] = None

class UserInDB(UserBase):
    hashed_password: str
    created_at: datetime = Field(default_factory=get_kst_now)
    updated_at: datetime = Field(default_factory=get_kst_now)

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

class PolicyMetadata(BaseModel):
    """정책 메타데이터"""
    summary: Optional[str] = None
    keywords: List[str] = []
    entity_types: List[str] = []
    scenarios: List[str] = []
    directives: List[str] = []

class PolicyDocument(BaseModel):
    """정책 문서 모델"""
    policy_id: str
    title: str
    authority: str  # 발행 기관
    description: Optional[str] = None

    # 파일 정보
    original_filename: str
    saved_filename: str
    file_type: str  # .pdf, .png, .jpg 등
    file_size_mb: float

    # 처리 정보
    processing_method: str  # zerox_ocr, pymupdf, vision_api
    extracted_text: str
    metadata: Optional[PolicyMetadata] = None

    # 생성 정보
    created_by: Optional[str] = None  # 생성자 이메일
    created_at: datetime = Field(default_factory=get_kst_now)
    updated_at: datetime = Field(default_factory=get_kst_now)

class PolicyResponse(BaseModel):
    """정책 응답 모델 (전체 텍스트 제외)"""
    policy_id: str
    title: str
    authority: str
    description: Optional[str] = None
    file_type: str
    file_size_mb: float
    processing_method: str
    metadata: Optional[PolicyMetadata] = None
    created_at: datetime
    updated_at: datetime

class AttachmentInfo(BaseModel):
    """첨부파일 정보"""
    filename: str
    content_type: str
    size: int
    hash: str  # SHA256

class EntityType(BaseModel):
    """엔티티(개인정보) 유형"""
    entity_id: str  # 고유 ID (예: "phone", "email", "ssn")
    name: str  # 표시 이름 (예: "전화번호", "이메일")
    category: str  # 카테고리 (예: "연락처", "식별정보", "금융정보")
    description: Optional[str] = None
    regex_pattern: Optional[str] = None  # 정규식 패턴
    keywords: List[str] = []  # 키워드 (컨텍스트 분석용)
    examples: List[str] = []  # 예시
    masking_rule: str = "full"  # full, partial, hash (레거시)
    sensitivity_level: str = "high"  # low, medium, high, critical
    # 마스킹 상세 설정
    masking_type: str = "full"      # full(전체), partial(부분), custom(커스텀 패턴)
    masking_char: str = "*"          # 마스킹 문자 (*, #, X, ●)
    masking_pattern: Optional[str] = None  # 커스텀 패턴 (예: "###-##-*****")
    is_active: bool = True
    created_at: datetime = Field(default_factory=get_kst_now)
    updated_at: datetime = Field(default_factory=get_kst_now)


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
    created_at: datetime = Field(default_factory=get_kst_now)
    received_at: Optional[datetime] = None  # 프록시가 메일을 받은 시간

    # DLP 검증 정보
    dlp_verified: bool = False  # 토큰 검증 완료 여부
    dlp_verified_at: Optional[datetime] = None
    dlp_policy_violation: Optional[str] = None  # DLP 정책 위반 사항

    # 승인/반려
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    reject_reason: Optional[str] = None