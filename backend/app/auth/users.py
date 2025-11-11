from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime
from app.policy.models import UserResponse, UserUpdate, UserRole
from app.auth.auth_utils import (
    get_current_root_admin,
    get_current_auditor,
    get_current_admin_or_approver,
    get_password_hash
)
from app.database.mongodb import get_database

router = APIRouter(prefix="/users", tags=["사용자 관리"])

@router.get("/", response_model=List[UserResponse])
async def list_users(current_user: dict = Depends(get_current_admin_or_approver)):
    """
    사용자 목록 조회
    - ROOT_ADMIN: 전체 조회
    - AUDITOR: 전체 조회 (읽기 전용)
    - APPROVER: 본인 팀만 조회
    """
    db = get_database()
    
    # APPROVER는 본인 팀만 조회
    if current_user["role"] == UserRole.APPROVER:
        team_name = current_user.get("team_name")
        if not team_name:
            return []
        users = await db.users.find({"team_name": team_name}).to_list(length=1000)
    else:
        # ROOT_ADMIN, AUDITOR는 전체 조회
        users = await db.users.find().to_list(length=1000)
    
    return [UserResponse(**user) for user in users]

@router.get("/{email}", response_model=UserResponse)
async def get_user(email: str, current_user: dict = Depends(get_current_admin_or_approver)):
    """
    특정 사용자 조회
    - ROOT_ADMIN: 전체
    - AUDITOR: 전체 (읽기 전용)
    - APPROVER: 본인 팀만
    """
    db = get_database()
    user = await db.users.find_one({"email": email})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    # APPROVER는 본인 팀만 조회 가능
    if current_user["role"] == UserRole.APPROVER:
        if user.get("team_name") != current_user.get("team_name"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="다른 팀 사용자는 조회할 수 없습니다"
            )
    
    return UserResponse(**user)

@router.patch("/{email}", response_model=UserResponse)
async def update_user(
    email: str, 
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_root_admin)
):
    """
    사용자 정보 수정 (ROOT_ADMIN 전용)
    - 일반 정보: nickname, department, team_name
    - 권한 변경: role (ROOT_ADMIN만 가능)
    - 비밀번호 변경
    """
    db = get_database()
    
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    update_data = user_update.dict(exclude_unset=True)
    
    # 비밀번호 변경 시 해시화
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    update_data["updated_at"] = datetime.utcnow()
    
    await db.users.update_one(
        {"email": email},
        {"$set": update_data}
    )
    
    updated_user = await db.users.find_one({"email": email})
    return UserResponse(**updated_user)

@router.delete("/{email}")
async def delete_user(
    email: str,
    current_user: dict = Depends(get_current_root_admin)
):
    """
    사용자 삭제 (ROOT_ADMIN 전용)
    - 자기 자신은 삭제 불가
    """
    db = get_database()
    
    # 자기 자신은 삭제할 수 없음
    if email == current_user["email"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자기 자신은 삭제할 수 없습니다"
        )
    
    result = await db.users.delete_one({"email": email})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    return {"message": "사용자가 삭제되었습니다"}

@router.patch("/{email}/role", response_model=UserResponse)
async def update_user_role(
    email: str,
    role: UserRole,
    current_user: dict = Depends(get_current_root_admin)
):
    """
    사용자 권한 변경 (ROOT_ADMIN 전용)
    - 자기 자신의 권한은 변경 불가
    - 가능한 권한: root_admin, auditor, policy_admin, approver, user
    """
    db = get_database()
    
    # 자기 자신의 권한은 변경할 수 없음
    if email == current_user["email"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자기 자신의 권한은 변경할 수 없습니다"
        )
    
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    await db.users.update_one(
        {"email": email},
        {"$set": {"role": role, "updated_at": datetime.utcnow()}}
    )
    
    updated_user = await db.users.find_one({"email": email})
    return UserResponse(**updated_user)

@router.get("/stats/summary")
async def get_user_stats(current_user: dict = Depends(get_current_auditor)):
    """
    사용자 통계 조회 (AUDITOR, ROOT_ADMIN)
    - 권한별 사용자 수
    - 팀별 사용자 수
    """
    db = get_database()
    
    # 권한별 집계
    role_stats = await db.users.aggregate([
        {"$group": {"_id": "$role", "count": {"$sum": 1}}}
    ]).to_list(length=100)
    
    # 팀별 집계
    team_stats = await db.users.aggregate([
        {"$match": {"team_name": {"$ne": None}}},
        {"$group": {"_id": "$team_name", "count": {"$sum": 1}}}
    ]).to_list(length=100)
    
    return {
        "role_distribution": {item["_id"]: item["count"] for item in role_stats},
        "team_distribution": {item["_id"]: item["count"] for item in team_stats},
        "total_users": await db.users.count_documents({})
    }