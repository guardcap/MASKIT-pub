"""
사용자 관리 API 라우터
- 사용자 목록 조회
- 사용자 권한 변경
- 사용자 삭제
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.database.mongodb import get_database
from app.auth.auth_utils import get_current_user
from app.policy.models import UserResponse, UserRole

router = APIRouter(prefix="/api/v1/users", tags=["사용자 관리"])


@router.get("/", response_model=List[UserResponse])
async def list_users(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    모든 사용자 목록 조회 (ROOT_ADMIN 또는 POLICY_ADMIN만 가능)
    """
    # 권한 확인
    if current_user["role"] not in [UserRole.ROOT_ADMIN, UserRole.POLICY_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="권한이 없습니다. 관리자만 사용자 목록을 조회할 수 있습니다."
        )

    # 모든 사용자 조회
    cursor = db.users.find({})
    users = []
    async for user in cursor:
        users.append(UserResponse(**user))

    return users


@router.patch("/{email}/role")
async def update_user_role(
    email: str,
    role: UserRole,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    사용자 권한 변경 (ROOT_ADMIN만 가능)
    """
    # 권한 확인
    if current_user["role"] != UserRole.ROOT_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="권한이 없습니다. ROOT_ADMIN만 사용자 권한을 변경할 수 있습니다."
        )

    # 사용자 존재 확인
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )

    # 자기 자신의 권한은 변경 불가
    if user["email"] == current_user["email"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자신의 권한은 변경할 수 없습니다"
        )

    # 권한 업데이트
    await db.users.update_one(
        {"email": email},
        {"$set": {"role": role.value}}
    )

    return {
        "success": True,
        "message": f"사용자 {email}의 권한이 {role.value}로 변경되었습니다"
    }


@router.delete("/{email}")
async def delete_user(
    email: str,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """
    사용자 삭제 (ROOT_ADMIN만 가능)
    """
    # 권한 확인
    if current_user["role"] != UserRole.ROOT_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="권한이 없습니다. ROOT_ADMIN만 사용자를 삭제할 수 있습니다."
        )

    # 사용자 존재 확인
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )

    # 자기 자신은 삭제 불가
    if user["email"] == current_user["email"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자신의 계정은 삭제할 수 없습니다"
        )

    # 사용자 삭제
    await db.users.delete_one({"email": email})

    return {
        "success": True,
        "message": f"사용자 {email}가 삭제되었습니다"
    }


@router.get("/me", response_model=UserResponse)
async def get_my_info(current_user: dict = Depends(get_current_user)):
    """
    내 정보 조회 (/auth/me와 동일하지만 경로 통일을 위해 추가)
    """
    return UserResponse(**current_user)
