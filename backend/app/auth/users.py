from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime, timedelta
from app.policy.models import UserResponse, UserUpdate, UserRole
from app.auth.auth_utils import (
    get_current_root_admin,
    get_current_admin_or_approver,
    get_current_user,
    get_password_hash
)
from app.database.mongodb import get_database

router = APIRouter(prefix="/users", tags=["사용자 관리"])

# 한국 시간 헬퍼 함수
def get_kst_now():
    """한국 표준시(KST) 반환"""
    return datetime.utcnow() + timedelta(hours=9)

@router.get("/", response_model=List[UserResponse])
async def list_users(
    current_user: dict = Depends(get_current_admin_or_approver),
    db = Depends(get_database)
):
    """
    사용자 목록 조회
    - ROOT_ADMIN: 전체 조회
    - AUDITOR: 전체 조회 (읽기 전용)
    - APPROVER: 본인 팀만 조회
    """
    try:
        print(f"[API] 사용자 목록 조회 시작 - Role: {current_user.get('role')}")
        
        # APPROVER는 본인 팀만 조회
        if current_user["role"] == UserRole.APPROVER:
            team_name = current_user.get("team_name")
            if not team_name:
                return []
            users = await db.users.find({"team_name": team_name}).to_list(length=1000)
        else:
            # ROOT_ADMIN, AUDITOR는 전체 조회
            users = await db.users.find().to_list(length=1000)
        
        print(f"[API] 조회된 사용자 수: {len(users)}")
        
        # UserResponse로 변환
        user_responses = []
        for user in users:
            try:
                user_responses.append(UserResponse(**user))
            except Exception as e:
                print(f"[API] 사용자 변환 실패: {user.get('email')} - {e}")
                continue
        
        return user_responses
    
    except Exception as e:
        print(f"[API] 사용자 목록 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.patch("/{email}/role", response_model=UserResponse)
async def update_user_role(
    email: str,
    role_data: UserUpdate,  # 요청 본문에서 role 받기
    current_user: dict = Depends(get_current_root_admin),
    db = Depends(get_database)
):
    """
    사용자 권한 변경 (ROOT_ADMIN 전용)
    - 자기 자신의 권한은 변경 불가
    """
    try:
        # URL 디코딩
        from urllib.parse import unquote
        email = unquote(email)
        
        print(f"\n[API] ===== 권한 변경 요청 시작 =====")
        print(f"[API] 대상 이메일: {email}")
        print(f"[API] 새 역할: {role_data.role}")
        print(f"[API] 현재 사용자: {current_user['email']}")
        
        # 자기 자신의 권한은 변경할 수 없음
        if email == current_user["email"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="자기 자신의 권한은 변경할 수 없습니다"
            )
        
        # 사용자 존재 확인
        user = await db.users.find_one({"email": email})
        if not user:
            print(f"[API] ❌ 사용자를 찾을 수 없음: {email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
        
        print(f"[API] 기존 역할: {user.get('role')}")
        
        # 권한 업데이트
        result = await db.users.update_one(
            {"email": email},
            {"$set": {
                "role": role_data.role,
                "updated_at": get_kst_now()
            }}
        )
        
        print(f"[API] 업데이트 결과 - matched: {result.matched_count}, modified: {result.modified_count}")
        
        if result.modified_count == 0:
            print(f"[API] ⚠️ 권한 변경 없음 (이미 동일한 역할)")
        else:
            print(f"[API] ✅ 권한 변경 완료: {email} -> {role_data.role}")
        
        # 업데이트된 사용자 정보 반환
        updated_user = await db.users.find_one({"email": email})
        print(f"[API] 업데이트 후 역할: {updated_user.get('role')}")
        print(f"[API] ===== 권한 변경 요청 완료 =====\n")
        
        return UserResponse(**updated_user)
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] ❌ 권한 변경 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"권한 변경 중 오류가 발생했습니다: {str(e)}"
        )

@router.delete("/{email}")
async def delete_user(
    email: str,
    current_user: dict = Depends(get_current_root_admin),
    db = Depends(get_database)
):
    """
    사용자 삭제 (ROOT_ADMIN 전용)
    - 자기 자신은 삭제 불가
    """
    try:
        print(f"[API] 사용자 삭제 요청: {email}")
        
        # 자기 자신은 삭제할 수 없음
        if email == current_user["email"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="자기 자신은 삭제할 수 없습니다"
            )
        
        # 사용자 삭제
        result = await db.users.delete_one({"email": email})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
        
        print(f"[API] 사용자 삭제 완료: {email}")
        return {"message": "사용자가 삭제되었습니다", "email": email}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[API] 사용자 삭제 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 삭제 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    현재 로그인한 사용자 정보 조회
    """
    return UserResponse(**current_user)