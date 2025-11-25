"""
감사 로그 API 라우터
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Optional
from datetime import datetime, timedelta

from app.database.mongodb import get_db
from app.auth.auth_utils import get_current_user, get_current_auditor
from .models import AuditEventType, AuditSeverity, AuditLogResponse

router = APIRouter(prefix="/api/audit", tags=["Audit Logs"])


@router.get("/logs")
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    감사 로그 조회 (역할 기반 필터링)

    - **AUDITOR**: 모든 로그 열람 가능
    - **POLICY_ADMIN, SYSTEM_ADMIN**: 본인 메일 관련 + 엔티티 CRUD + 설정 변경
    - **USER**: 본인 메일 관련 로그만
    """
    try:
        user_role = current_user.get("role", "user")
        user_email = current_user["email"]

        # 기본 쿼리
        query = {}

        # 역할 기반 필터링
        if user_role == "auditor" or user_role == "root_admin":
            # Auditor와 Root Admin은 모든 로그 조회 가능
            pass
        elif user_role in ["policy_admin", "system_admin"]:
            # Admin은 본인 관련 + 엔티티/설정 변경 로그
            query["$or"] = [
                {"user_email": user_email},
                {"event_type": {"$in": [
                    AuditEventType.ENTITY_CREATE,
                    AuditEventType.ENTITY_UPDATE,
                    AuditEventType.ENTITY_DELETE,
                    AuditEventType.SETTINGS_UPDATE,
                    AuditEventType.ENV_CHANGE,
                    AuditEventType.VECTOR_STORE_SYNC,
                    AuditEventType.POLICY_UPLOAD,
                ]}},
            ]
        else:
            # 일반 사용자는 본인 메일 관련 로그만
            query["user_email"] = user_email
            query["event_type"] = {"$in": [
                AuditEventType.EMAIL_SEND,
                AuditEventType.EMAIL_READ,
                AuditEventType.EMAIL_COMPOSE,
                AuditEventType.MASKING_DECISION,
            ]}

        # 이벤트 타입 필터
        if event_type:
            query["event_type"] = event_type

        # 심각도 필터
        if severity:
            query["severity"] = severity

        # 날짜 필터
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if end_date:
                date_query["$lte"] = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query["timestamp"] = date_query

        # 검색 필터
        if search:
            query["$or"] = [
                {"action": {"$regex": search, "$options": "i"}},
                {"user_email": {"$regex": search, "$options": "i"}},
                {"resource_id": {"$regex": search, "$options": "i"}},
            ]

        # 전체 개수 조회
        total = await db.audit_logs.count_documents(query)

        # 페이지네이션
        skip = (page - 1) * page_size

        # 로그 조회 (최신순)
        cursor = db.audit_logs.find(query).sort("timestamp", -1).skip(skip).limit(page_size)
        logs = []

        async for log in cursor:
            log["_id"] = str(log["_id"])
            log["timestamp"] = log["timestamp"].isoformat() if isinstance(log["timestamp"], datetime) else log["timestamp"]
            logs.append(log)

        print(f"✅ 감사 로그 조회: {user_email} ({user_role}) - {len(logs)}개 (전체: {total}개)")

        return JSONResponse({
            "success": True,
            "data": {
                "total": total,
                "logs": logs,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        })

    except Exception as e:
        print(f"❌ 감사 로그 조회 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"감사 로그 조회 실패: {str(e)}")


@router.get("/logs/stats")
async def get_audit_stats(
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(get_current_auditor),
    db = Depends(get_db)
):
    """
    감사 로그 통계 (Auditor 전용)

    - 최근 N일간의 로그 통계
    - 이벤트 타입별 집계
    - 사용자별 활동 집계
    """
    try:
        start_date = datetime.utcnow() - timedelta(days=days)

        # 이벤트 타입별 집계
        event_pipeline = [
            {"$match": {"timestamp": {"$gte": start_date}}},
            {"$group": {
                "_id": "$event_type",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]

        event_stats = []
        async for doc in db.audit_logs.aggregate(event_pipeline):
            event_stats.append({
                "event_type": doc["_id"],
                "count": doc["count"]
            })

        # 사용자별 활동 집계
        user_pipeline = [
            {"$match": {"timestamp": {"$gte": start_date}}},
            {"$group": {
                "_id": "$user_email",
                "count": {"$sum": 1},
                "role": {"$first": "$user_role"}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]

        user_stats = []
        async for doc in db.audit_logs.aggregate(user_pipeline):
            user_stats.append({
                "user_email": doc["_id"],
                "role": doc.get("role", "unknown"),
                "count": doc["count"]
            })

        # 심각도별 집계
        severity_pipeline = [
            {"$match": {"timestamp": {"$gte": start_date}}},
            {"$group": {
                "_id": "$severity",
                "count": {"$sum": 1}
            }}
        ]

        severity_stats = []
        async for doc in db.audit_logs.aggregate(severity_pipeline):
            severity_stats.append({
                "severity": doc["_id"],
                "count": doc["count"]
            })

        return JSONResponse({
            "success": True,
            "data": {
                "period_days": days,
                "event_types": event_stats,
                "top_users": user_stats,
                "severity": severity_stats
            }
        })

    except Exception as e:
        print(f"❌ 감사 통계 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"감사 통계 조회 실패: {str(e)}")


@router.get("/logs/export")
async def export_audit_logs(
    start_date: str,
    end_date: str,
    current_user: dict = Depends(get_current_auditor),
    db = Depends(get_db)
):
    """
    감사 로그 내보내기 (Auditor 전용)

    - CSV 형식으로 다운로드
    """
    try:
        query = {
            "timestamp": {
                "$gte": datetime.fromisoformat(start_date.replace('Z', '+00:00')),
                "$lte": datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            }
        }

        cursor = db.audit_logs.find(query).sort("timestamp", -1)
        logs = []

        async for log in cursor:
            logs.append({
                "timestamp": log["timestamp"].isoformat(),
                "event_type": log["event_type"],
                "severity": log["severity"],
                "user_email": log["user_email"],
                "user_role": log["user_role"],
                "action": log["action"],
                "resource_type": log.get("resource_type", ""),
                "resource_id": log.get("resource_id", ""),
                "success": log["success"],
                "ip_address": log.get("ip_address", ""),
            })

        return JSONResponse({
            "success": True,
            "data": {
                "logs": logs,
                "total": len(logs)
            }
        })

    except Exception as e:
        print(f"❌ 감사 로그 내보내기 오류: {e}")
        raise HTTPException(status_code=500, detail=f"감사 로그 내보내기 실패: {str(e)}")
