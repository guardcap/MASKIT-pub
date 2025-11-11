from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from app.policy.models import UserCreate, UserResponse, Token, LoginRequest, UserRole
from app.auth.auth_utils import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user
)
from app.database.mongodb import get_database
from datetime import datetime, timedelta

router = APIRouter(prefix="/auth", tags=["인증"])

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    """회원가입"""
    db = get_database()
    
    # 이메일 중복 확인
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 이메일입니다"
        )
    
    # 첫 번째 사용자는 ROOT_ADMIN으로 설정
    user_count = await db.users.count_documents({})
    if user_count == 0:
        user.role = UserRole.ROOT_ADMIN
    
    # 사용자 생성
    user_dict = user.dict()
    user_dict["hashed_password"] = get_password_hash(user_dict.pop("password"))
    user_dict["created_at"] = datetime.utcnow()
    user_dict["updated_at"] = datetime.utcnow()
    
    result = await db.users.insert_one(user_dict)
    
    created_user = await db.users.find_one({"_id": result.inserted_id})
    return UserResponse(**created_user)

@router.post("/login")
async def login(login_data: LoginRequest):
    """로그인"""
    db = get_database()
    
    user = await db.users.find_one({"email": login_data.email})
    if not user or not verify_password(login_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 잘못되었습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user["email"]})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "email": user["email"],
            "nickname": user["nickname"],
            "department": user.get("department"),
            "role": user["role"]
        }
    }

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """현재 로그인한 사용자 정보"""
    return UserResponse(**current_user)

@router.post("/logout")
async def logout():
    """로그아웃 (클라이언트에서 토큰 삭제 필요)"""
    return {"message": "로그아웃되었습니다"}