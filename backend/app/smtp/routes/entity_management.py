"""
엔티티(개인정보 유형) 관리 라우터
- 엔티티 추가/수정/삭제
- 엔티티 목록 조회
- 카테고리별 엔티티 조회
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime
import hashlib

from ..database import get_db
from ..models import EntityType

router = APIRouter(prefix="/api/entities", tags=["Entity Management"])


# 현재 사용자 확인 (정책 관리자 권한)
async def get_current_policy_admin(db = Depends(get_db)):
    """정책 관리자 권한 확인"""
    # TODO: JWT 토큰 검증 로직 추가
    # 임시로 모든 요청 허용
    return None


@router.post("/")
async def create_entity(
    entity_id: str,
    name: str,
    category: str,
    description: str = "",
    regex_pattern: str = "",
    examples: str = "",  # 쉼표로 구분된 예시
    masking_rule: str = "full",
    sensitivity_level: str = "high",
    db = Depends(get_db),
    current_user = Depends(get_current_policy_admin)
):
    """엔티티 생성"""
    try:
        # 중복 확인
        existing = await db["entities"].find_one({"entity_id": entity_id})
        if existing:
            raise HTTPException(status_code=400, detail="이미 존재하는 엔티티 ID입니다")

        # 예시 파싱
        examples_list = [ex.strip() for ex in examples.split(",") if ex.strip()]

        # 엔티티 생성
        entity = EntityType(
            entity_id=entity_id,
            name=name,
            category=category,
            description=description or None,
            regex_pattern=regex_pattern or None,
            examples=examples_list,
            masking_rule=masking_rule,
            sensitivity_level=sensitivity_level,
            is_active=True
        )

        # MongoDB에 저장
        await db["entities"].insert_one(entity.model_dump(mode='json'))

        return JSONResponse({
            "success": True,
            "message": "엔티티가 성공적으로 생성되었습니다",
            "data": entity.model_dump(mode='json')
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"엔티티 생성 실패: {str(e)}")


@router.get("/list")
async def list_entities(
    category: str = None,
    is_active: bool = None,
    db = Depends(get_db)
):
    """엔티티 목록 조회"""
    try:
        # 필터 조건
        query = {}
        if category:
            query["category"] = category
        if is_active is not None:
            query["is_active"] = is_active

        # 엔티티 목록 조회
        cursor = db["entities"].find(query).sort("category", 1).sort("name", 1)

        entities = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            entities.append(doc)

        # 카테고리별 집계
        categories = {}
        for entity in entities:
            cat = entity.get("category", "기타")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(entity)

        return JSONResponse({
            "success": True,
            "data": {
                "entities": entities,
                "total": len(entities),
                "by_category": categories
            }
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"엔티티 목록 조회 실패: {str(e)}")


@router.get("/categories")
async def get_categories(db = Depends(get_db)):
    """카테고리 목록 조회"""
    try:
        # 카테고리별 집계
        pipeline = [
            {"$group": {
                "_id": "$category",
                "count": {"$sum": 1},
                "entities": {"$push": "$name"}
            }},
            {"$sort": {"_id": 1}}
        ]

        cursor = db["entities"].aggregate(pipeline)
        categories = []

        async for doc in cursor:
            categories.append({
                "category": doc["_id"],
                "count": doc["count"],
                "entities": doc["entities"]
            })

        return JSONResponse({
            "success": True,
            "data": categories
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"카테고리 조회 실패: {str(e)}")


@router.get("/{entity_id}")
async def get_entity_detail(
    entity_id: str,
    db = Depends(get_db)
):
    """엔티티 상세 조회"""
    try:
        entity = await db["entities"].find_one({"entity_id": entity_id})

        if not entity:
            raise HTTPException(status_code=404, detail="엔티티를 찾을 수 없습니다")

        entity["_id"] = str(entity["_id"])

        return JSONResponse({
            "success": True,
            "data": entity
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"엔티티 조회 실패: {str(e)}")


@router.put("/{entity_id}")
async def update_entity(
    entity_id: str,
    name: str = None,
    category: str = None,
    description: str = None,
    regex_pattern: str = None,
    examples: str = None,
    masking_rule: str = None,
    sensitivity_level: str = None,
    is_active: bool = None,
    db = Depends(get_db),
    current_user = Depends(get_current_policy_admin)
):
    """엔티티 수정"""
    try:
        # 엔티티 확인
        entity = await db["entities"].find_one({"entity_id": entity_id})
        if not entity:
            raise HTTPException(status_code=404, detail="엔티티를 찾을 수 없습니다")

        # 업데이트 데이터 구성
        update_data = {"updated_at": datetime.utcnow()}

        if name is not None:
            update_data["name"] = name
        if category is not None:
            update_data["category"] = category
        if description is not None:
            update_data["description"] = description
        if regex_pattern is not None:
            update_data["regex_pattern"] = regex_pattern
        if examples is not None:
            examples_list = [ex.strip() for ex in examples.split(",") if ex.strip()]
            update_data["examples"] = examples_list
        if masking_rule is not None:
            update_data["masking_rule"] = masking_rule
        if sensitivity_level is not None:
            update_data["sensitivity_level"] = sensitivity_level
        if is_active is not None:
            update_data["is_active"] = is_active

        # MongoDB 업데이트
        await db["entities"].update_one(
            {"entity_id": entity_id},
            {"$set": update_data}
        )

        return JSONResponse({
            "success": True,
            "message": "엔티티가 성공적으로 수정되었습니다"
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"엔티티 수정 실패: {str(e)}")


@router.delete("/{entity_id}")
async def delete_entity(
    entity_id: str,
    db = Depends(get_db),
    current_user = Depends(get_current_policy_admin)
):
    """엔티티 삭제"""
    try:
        # 엔티티 확인
        entity = await db["entities"].find_one({"entity_id": entity_id})
        if not entity:
            raise HTTPException(status_code=404, detail="엔티티를 찾을 수 없습니다")

        # MongoDB에서 삭제
        await db["entities"].delete_one({"entity_id": entity_id})

        return JSONResponse({
            "success": True,
            "message": "엔티티가 성공적으로 삭제되었습니다"
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"엔티티 삭제 실패: {str(e)}")


@router.post("/seed")
async def seed_default_entities(
    db = Depends(get_db),
    current_user = Depends(get_current_policy_admin)
):
    """기본 엔티티 데이터 시드"""
    default_entities = [
        {
            "entity_id": "phone",
            "name": "전화번호",
            "category": "연락처",
            "description": "휴대전화 및 일반 전화번호",
            "regex_pattern": r"01[016789]-?\d{3,4}-?\d{4}",
            "examples": ["010-1234-5678", "02-123-4567"],
            "masking_rule": "partial",
            "sensitivity_level": "high"
        },
        {
            "entity_id": "email",
            "name": "이메일",
            "category": "연락처",
            "description": "이메일 주소",
            "regex_pattern": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            "examples": ["user@example.com"],
            "masking_rule": "partial",
            "sensitivity_level": "medium"
        },
        {
            "entity_id": "ssn",
            "name": "주민등록번호",
            "category": "식별정보",
            "description": "주민등록번호 (13자리)",
            "regex_pattern": r"\d{6}-?\d{7}",
            "examples": ["991231-1234567"],
            "masking_rule": "full",
            "sensitivity_level": "critical"
        },
        {
            "entity_id": "name",
            "name": "성명",
            "category": "식별정보",
            "description": "한글 이름",
            "regex_pattern": r"[가-힣]{2,4}",
            "examples": ["홍길동", "김철수"],
            "masking_rule": "partial",
            "sensitivity_level": "medium"
        },
        {
            "entity_id": "address",
            "name": "주소",
            "category": "식별정보",
            "description": "도로명주소 및 지번주소",
            "regex_pattern": None,
            "examples": ["서울시 강남구 테헤란로 123"],
            "masking_rule": "partial",
            "sensitivity_level": "high"
        },
        {
            "entity_id": "bank_account",
            "name": "계좌번호",
            "category": "금융정보",
            "description": "은행 계좌번호",
            "regex_pattern": r"\d{3,6}-?\d{2,6}-?\d{2,6}",
            "examples": ["123-456-789012"],
            "masking_rule": "full",
            "sensitivity_level": "critical"
        },
        {
            "entity_id": "card_number",
            "name": "카드번호",
            "category": "금융정보",
            "description": "신용카드/체크카드 번호",
            "regex_pattern": r"\d{4}-?\d{4}-?\d{4}-?\d{4}",
            "examples": ["1234-5678-9012-3456"],
            "masking_rule": "full",
            "sensitivity_level": "critical"
        },
        {
            "entity_id": "passport",
            "name": "여권번호",
            "category": "식별정보",
            "description": "대한민국 여권번호",
            "regex_pattern": r"[A-Z]\d{8}",
            "examples": ["M12345678"],
            "masking_rule": "full",
            "sensitivity_level": "high"
        }
    ]

    try:
        inserted_count = 0
        for entity_data in default_entities:
            # 중복 확인
            existing = await db["entities"].find_one({"entity_id": entity_data["entity_id"]})
            if existing:
                continue

            # 엔티티 생성
            entity = EntityType(**entity_data)
            await db["entities"].insert_one(entity.model_dump(mode='json'))
            inserted_count += 1

        return JSONResponse({
            "success": True,
            "message": f"{inserted_count}개의 기본 엔티티가 생성되었습니다",
            "data": {
                "inserted": inserted_count,
                "total": len(default_entities)
            }
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시드 데이터 생성 실패: {str(e)}")
