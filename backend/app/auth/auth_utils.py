from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.policy.models import TokenData, UserRole
from app.database.mongodb import get_database
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
security = HTTPBearer(auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증이 필요합니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보를 확인할 수 없습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    db = get_database()
    user = await db.users.find_one({"email": token_data.email})
    if user is None:
        raise credentials_exception
    return user

# ===== 새로운 권한 체크 함수들 =====

async def get_current_root_admin(current_user: dict = Depends(get_current_user)):
    """ROOT_ADMIN 권한 체크"""
    if current_user["role"] != UserRole.ROOT_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ROOT 관리자 권한이 필요합니다"
        )
    return current_user

async def get_current_auditor(current_user: dict = Depends(get_current_user)):
    """AUDITOR 권한 체크"""
    if current_user["role"] not in [UserRole.ROOT_ADMIN, UserRole.AUDITOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="감사자 권한이 필요합니다"
        )
    return current_user

async def get_current_policy_admin(current_user: dict = Depends(get_current_user)):
    """POLICY_ADMIN 권한 체크"""
    if current_user["role"] not in [UserRole.ROOT_ADMIN, UserRole.POLICY_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="정책 관리자 권한이 필요합니다"
        )
    return current_user

async def get_current_approver(current_user: dict = Depends(get_current_user)):
    """APPROVER 권한 체크"""
    if current_user["role"] not in [UserRole.ROOT_ADMIN, UserRole.AUDITOR, UserRole.APPROVER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="승인자 권한이 필요합니다"
        )
    return current_user

async def get_current_admin_or_approver(current_user: dict = Depends(get_current_user)):
    """관리 권한 체크 (ROOT_ADMIN, AUDITOR, POLICY_ADMIN, APPROVER)"""
    if current_user["role"] == UserRole.USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    return current_user

# 레거시 지원 (기존 코드 호환)
async def get_current_admin_user(current_user: dict = Depends(get_current_user)):
    """레거시: 모든 관리 권한 허용"""
    return await get_current_admin_or_approver(current_user)