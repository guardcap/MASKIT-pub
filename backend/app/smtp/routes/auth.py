from fastapi import APIRouter, HTTPException, status, Depends
from datetime import timedelta
from app.smtp.models import UserCreate, UserResponse, Token, LoginRequest, UserRole, TokenWithUser

from app.smtp.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.smtp.database import get_database
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["인증"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    """새 사용자 등록"""
    db = get_database()
    
    # 이메일 중복 체크
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일입니다"
        )
    
    # 비밀번호 해시화
    hashed_password = get_password_hash(user.password)
    
    # 사용자 데이터 생성
    user_dict = user.dict()
    user_dict.pop("password")
    user_dict["hashed_password"] = hashed_password
    user_dict["created_at"] = datetime.utcnow()
    user_dict["updated_at"] = datetime.utcnow()
    
    # 첫 사용자는 ROOT_ADMIN으로 설정
    users_count = await db.users.count_documents({})
    if users_count == 0:
        user_dict["role"] = UserRole.ROOT_ADMIN
    
    result = await db.users.insert_one(user_dict)
    
    created_user = await db.users.find_one({"_id": result.inserted_id})
    return UserResponse(**created_user)

# 2. response_model을 Token에서 TokenWithUser로 변경합니다.
@router.post("/login", response_model=TokenWithUser)
async def login(login_data: LoginRequest):
    db = get_database()
    
    user = await db.users.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": UserResponse(**user)
    }

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """현재 로그인한 사용자 정보 조회"""
    return UserResponse(**current_user)