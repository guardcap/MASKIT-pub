"""
VectorDB 및 정책 스키마 관리 라우터
- JSONL 파일 관리 (CRUD)
- VectorDB 동기화
- source_document 기반 그룹화
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import json
import chromadb
from chromadb.config import Settings
from openai import OpenAI
import os
from dotenv import load_dotenv
import hashlib
from pydantic import BaseModel

load_dotenv()

router = APIRouter(prefix="/api/vectordb", tags=["VectorDB Management"])

# 경로 설정 - 절대 경로로 변환
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
STAGING_DIR = BASE_DIR / "app" / "rag" / "data" / "staging"
CHROMADB_PATH = BASE_DIR / "app" / "rag" / "data" / "chromadb" / "application_guides"
COLLECTION_NAME = "application_guides"

# 디렉토리 생성
STAGING_DIR.mkdir(parents=True, exist_ok=True)
CHROMADB_PATH.mkdir(parents=True, exist_ok=True)

# OpenAI 클라이언트
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# ChromaDB 클라이언트
chroma_client = chromadb.PersistentClient(path=str(CHROMADB_PATH))


# Pydantic 모델
class PolicyGuide(BaseModel):
    guide_id: str
    source_authority: str
    source_document: str
    scenario: str
    context: Dict[str, Any]
    interpretation: str
    actionable_directive: str
    keywords: List[str]
    related_law_ids: List[str]
    examples: List[Dict[str, Any]]
    confidence_score: float
    reviewed: bool


class PolicyGuideCreate(BaseModel):
    source_authority: str
    source_document: str
    scenario: str
    context: Dict[str, Any]
    interpretation: str
    actionable_directive: str
    keywords: List[str]
    related_law_ids: List[str]
    examples: List[Dict[str, Any]]
    confidence_score: Optional[float] = 0.8
    reviewed: Optional[bool] = False


class PolicyGuideUpdate(BaseModel):
    source_authority: Optional[str] = None
    scenario: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    interpretation: Optional[str] = None
    actionable_directive: Optional[str] = None
    keywords: Optional[List[str]] = None
    related_law_ids: Optional[List[str]] = None
    examples: Optional[List[Dict[str, Any]]] = None
    confidence_score: Optional[float] = None
    reviewed: Optional[bool] = None


def get_embedding(text: str) -> List[float]:
    """OpenAI Embedding 생성"""
    try:
        response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding 생성 실패: {e}")
        return None


def build_search_text(guide: Dict) -> str:
    """검색용 텍스트 구성"""
    parts = [
        f"Scenario: {guide.get('scenario', '')}",
        f"Directive: {guide.get('actionable_directive', '')}",
        f"Interpretation: {guide.get('interpretation', '')}",
        f"Keywords: {', '.join(guide.get('keywords', []))}",
    ]

    for example in guide.get('examples', []):
        parts.append(f"Example: {example.get('case_description', '')}")

    return "\n".join(parts)


def load_all_guides() -> Dict[str, List[Dict]]:
    """
    모든 JSONL 파일을 로드하고 source_document로 그룹화
    Returns: {source_document: [guides...]}
    """
    if not STAGING_DIR.exists():
        return {}

    grouped_guides = {}
    jsonl_files = list(STAGING_DIR.glob("*.jsonl"))

    for jsonl_file in jsonl_files:
        try:
            with open(jsonl_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        guide = json.loads(line)
                        source_doc = guide.get("source_document", "Unknown")

                        if source_doc not in grouped_guides:
                            grouped_guides[source_doc] = []

                        guide["_jsonl_file"] = jsonl_file.name
                        grouped_guides[source_doc].append(guide)
        except Exception as e:
            print(f"파일 로드 실패 {jsonl_file.name}: {e}")

    return grouped_guides


def load_guides_from_file(filename: str) -> List[Dict]:
    """특정 JSONL 파일에서 가이드 로드"""
    file_path = STAGING_DIR / filename
    if not file_path.exists():
        return []

    guides = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                guides.append(json.loads(line))

    return guides


def save_guides_to_file(filename: str, guides: List[Dict]) -> bool:
    """가이드를 JSONL 파일에 저장"""
    try:
        file_path = STAGING_DIR / filename
        with open(file_path, "w", encoding="utf-8") as f:
            for guide in guides:
                # _jsonl_file 필드 제거
                guide_copy = guide.copy()
                guide_copy.pop("_jsonl_file", None)
                f.write(json.dumps(guide_copy, ensure_ascii=False) + "\n")
        return True
    except Exception as e:
        print(f"파일 저장 실패: {e}")
        return False


def sync_to_vectordb(guide: Dict, operation: str = "upsert") -> bool:
    """
    VectorDB에 가이드 동기화
    operation: "upsert", "delete"
    """
    try:
        collection = chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

        guide_id = guide.get("guide_id")

        if operation == "delete":
            collection.delete(ids=[guide_id])
            return True

        # Upsert
        search_text = build_search_text(guide)
        embedding = get_embedding(search_text)

        if not embedding:
            return False

        context = guide.get("context", {}) or {}
        metadata = {
            "guide_id": guide_id,
            "authority": guide.get("source_authority", ""),
            "source_document": guide.get("source_document", ""),
            "scenario": guide.get("scenario", "")[:500],
            "sender_type": context.get("sender_type", ""),
            "receiver_type": context.get("receiver_type", ""),
            "email_purpose": context.get("email_purpose", ""),
            "pii_types": ",".join(context.get("pii_types", [])),
            "confidence_score": str(guide.get("confidence_score", 0.8)),
            "reviewed": str(guide.get("reviewed", False)),
        }

        collection.upsert(
            ids=[guide_id],
            documents=[search_text],
            embeddings=[embedding],
            metadatas=[metadata]
        )

        return True

    except Exception as e:
        print(f"VectorDB 동기화 실패: {e}")
        return False


@router.get("/guides/grouped")
async def get_guides_grouped():
    """source_document로 그룹화된 모든 가이드 조회"""
    try:
        grouped = load_all_guides()

        # 통계 정보 추가
        result = []
        for source_doc, guides in grouped.items():
            result.append({
                "source_document": source_doc,
                "count": len(guides),
                "authorities": list(set(g.get("source_authority", "") for g in guides)),
                "jsonl_files": list(set(g.get("_jsonl_file", "") for g in guides)),
                "guides": guides
            })

        # source_document 이름으로 정렬
        result.sort(key=lambda x: x["source_document"])

        return JSONResponse({
            "success": True,
            "data": {
                "total_source_documents": len(result),
                "total_guides": sum(item["count"] for item in result),
                "groups": result
            }
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"가이드 조회 실패: {str(e)}")


@router.get("/guides/by-source/{source_document}")
async def get_guides_by_source(source_document: str):
    """특정 source_document의 가이드 조회"""
    try:
        grouped = load_all_guides()
        guides = grouped.get(source_document, [])

        return JSONResponse({
            "success": True,
            "data": {
                "source_document": source_document,
                "count": len(guides),
                "guides": guides
            }
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"가이드 조회 실패: {str(e)}")


@router.get("/guides/{guide_id}")
async def get_guide_by_id(guide_id: str):
    """특정 가이드 조회"""
    try:
        grouped = load_all_guides()

        for source_doc, guides in grouped.items():
            for guide in guides:
                if guide.get("guide_id") == guide_id:
                    return JSONResponse({
                        "success": True,
                        "data": guide
                    })

        raise HTTPException(status_code=404, detail="가이드를 찾을 수 없습니다")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"가이드 조회 실패: {str(e)}")


@router.post("/guides")
async def create_guide(guide_data: PolicyGuideCreate):
    """새 가이드 생성"""
    try:
        # guide_id 생성
        timestamp = datetime.now().strftime("%Y%m")
        random_str = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]

        # 해당 source_document의 기존 가이드 개수 확인
        grouped = load_all_guides()
        existing_guides = grouped.get(guide_data.source_document, [])
        guide_index = len(existing_guides)

        authority_code = "UNK"
        if "개인정보보호위원회" in guide_data.source_authority:
            authority_code = "PIPC"
        elif "금융보안원" in guide_data.source_authority:
            authority_code = "FSI"

        guide_id = f"GUIDE-{authority_code}-{timestamp}-{random_str}-{guide_index:03d}"

        # 새 가이드 생성
        new_guide = {
            "guide_id": guide_id,
            **guide_data.model_dump()
        }

        # JSONL 파일명 결정 (source_document 기반)
        safe_filename = guide_data.source_document.replace(" ", "_").replace("/", "_")[:50]
        jsonl_filename = f"application_guides_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_filename}.jsonl"

        # 기존 파일에 추가 또는 새 파일 생성
        target_file = None
        if existing_guides:
            # 기존 파일 중 하나 선택
            target_file = existing_guides[0].get("_jsonl_file")

        if not target_file:
            target_file = jsonl_filename

        # 파일에서 기존 가이드 로드
        all_guides = load_guides_from_file(target_file) if target_file else []
        all_guides.append(new_guide)

        # 파일 저장
        if not save_guides_to_file(target_file, all_guides):
            raise HTTPException(status_code=500, detail="파일 저장 실패")

        # VectorDB 동기화
        sync_to_vectordb(new_guide, "upsert")

        return JSONResponse({
            "success": True,
            "message": "가이드가 성공적으로 생성되었습니다",
            "data": {
                "guide_id": guide_id,
                "jsonl_file": target_file
            }
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"가이드 생성 실패: {str(e)}")


@router.put("/guides/{guide_id}")
async def update_guide(guide_id: str, guide_data: PolicyGuideUpdate):
    """가이드 업데이트"""
    try:
        grouped = load_all_guides()

        target_file = None
        target_guide_index = None

        # 가이드 찾기
        for source_doc, guides in grouped.items():
            for idx, guide in enumerate(guides):
                if guide.get("guide_id") == guide_id:
                    target_file = guide.get("_jsonl_file")
                    target_guide_index = idx

                    # 업데이트 적용
                    update_dict = guide_data.model_dump(exclude_unset=True)
                    guide.update(update_dict)

                    break
            if target_file:
                break

        if not target_file:
            raise HTTPException(status_code=404, detail="가이드를 찾을 수 없습니다")

        # 파일에서 모든 가이드 로드
        all_guides = load_guides_from_file(target_file)

        # 업데이트된 가이드 찾아서 수정
        for i, g in enumerate(all_guides):
            if g.get("guide_id") == guide_id:
                update_dict = guide_data.model_dump(exclude_unset=True)
                all_guides[i].update(update_dict)
                updated_guide = all_guides[i]
                break

        # 파일 저장
        if not save_guides_to_file(target_file, all_guides):
            raise HTTPException(status_code=500, detail="파일 저장 실패")

        # VectorDB 동기화
        sync_to_vectordb(updated_guide, "upsert")

        return JSONResponse({
            "success": True,
            "message": "가이드가 성공적으로 업데이트되었습니다",
            "data": updated_guide
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"가이드 업데이트 실패: {str(e)}")


@router.delete("/guides/{guide_id}")
async def delete_guide(guide_id: str):
    """가이드 삭제"""
    try:
        grouped = load_all_guides()

        target_file = None
        deleted_guide = None

        # 가이드 찾기
        for source_doc, guides in grouped.items():
            for guide in guides:
                if guide.get("guide_id") == guide_id:
                    target_file = guide.get("_jsonl_file")
                    deleted_guide = guide
                    break
            if target_file:
                break

        if not target_file:
            raise HTTPException(status_code=404, detail="가이드를 찾을 수 없습니다")

        # 파일에서 가이드 제거
        all_guides = load_guides_from_file(target_file)
        all_guides = [g for g in all_guides if g.get("guide_id") != guide_id]

        # 파일 저장
        if not save_guides_to_file(target_file, all_guides):
            raise HTTPException(status_code=500, detail="파일 저장 실패")

        # VectorDB에서 삭제
        sync_to_vectordb(deleted_guide, "delete")

        return JSONResponse({
            "success": True,
            "message": "가이드가 성공적으로 삭제되었습니다"
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"가이드 삭제 실패: {str(e)}")


@router.post("/sync/rebuild")
async def rebuild_vectordb():
    """전체 VectorDB 재구축"""
    try:
        # 기존 컬렉션 삭제
        try:
            chroma_client.delete_collection(name=COLLECTION_NAME)
        except:
            pass

        # 새 컬렉션 생성
        collection = chroma_client.create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

        # 모든 가이드 로드
        grouped = load_all_guides()

        total_synced = 0
        for source_doc, guides in grouped.items():
            for guide in guides:
                if sync_to_vectordb(guide, "upsert"):
                    total_synced += 1

        return JSONResponse({
            "success": True,
            "message": f"VectorDB 재구축 완료: {total_synced}개 가이드 동기화"
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"VectorDB 재구축 실패: {str(e)}")


@router.get("/stats")
async def get_vectordb_stats():
    """VectorDB 통계"""
    try:
        grouped = load_all_guides()

        total_guides = sum(len(guides) for guides in grouped.values())
        authorities = set()
        jsonl_files = set()

        for guides in grouped.values():
            for guide in guides:
                authorities.add(guide.get("source_authority", ""))
                jsonl_files.add(guide.get("_jsonl_file", ""))

        # ChromaDB 통계
        try:
            collection = chroma_client.get_collection(name=COLLECTION_NAME)
            vectordb_count = collection.count()
        except:
            vectordb_count = 0

        return JSONResponse({
            "success": True,
            "data": {
                "total_guides": total_guides,
                "total_source_documents": len(grouped),
                "total_jsonl_files": len(jsonl_files),
                "authorities": list(authorities),
                "vectordb_count": vectordb_count,
                "sync_status": "synced" if vectordb_count == total_guides else "out_of_sync"
            }
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 실패: {str(e)}")
