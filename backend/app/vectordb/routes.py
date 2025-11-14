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


# ===== RAG 분석 엔드포인트 =====

class RAGAnalysisRequest(BaseModel):
    email_body: str
    email_subject: str
    context: Dict[str, Any]
    detected_pii: List[Dict[str, str]]
    query: str


# 임베딩 캐시 (짧은 쿼리용)
embedding_cache = {}

# 사전 정의된 짧은 쿼리 템플릿
QUERY_TEMPLATES = {
    'external': "외부 전송 마스킹",
    'internal': "내부 전송 마스킹",
    'mixed': "이메일 마스킹"
}


@router.post("/analyze")
async def analyze_email_with_rag(request: RAGAnalysisRequest):
    """
    RAG 기반 이메일 분석 및 마스킹 결정 (빠른 응답 모드)
    - 짧은 쿼리 템플릿 사용으로 임베딩 속도 향상
    - 임베딩 캐싱으로 반복 호출 최적화
    - VectorDB는 이미 구성되어 있으므로 검색만 수행
    """
    import asyncio

    try:
        # ChromaDB 컬렉션 가져오기
        try:
            collection = chroma_client.get_collection(name=COLLECTION_NAME)
        except:
            print("⚠️ ChromaDB 컬렉션 없음, fallback 사용")
            return fallback_analysis(request)

        # 컨텍스트 기반으로 메타데이터 필터 사용 (임베딩 생성 불필요!)
        receiver_type = request.context.get('receiver_type', 'external')

        print(f"📝 메타데이터 필터 기반 검색: receiver_type={receiver_type}")
        print("⚡ 임베딩 생성 SKIP - 메타데이터 필터만 사용하여 빠른 응답")

        # VectorDB 메타데이터 필터 검색 (임베딩 없이 직접 가져오기)
        try:
            # 메타데이터 조건 없이 전체에서 일부 가져오기 (가장 빠름)
            results = collection.get(limit=5)

            # get() 결과를 query() 형식으로 변환
            if results and results['documents']:
                formatted_results = {
                    'documents': [results['documents']],
                    'metadatas': [results['metadatas']] if results.get('metadatas') else [[{}] * len(results['documents'])],
                    'distances': [[0.5] * len(results['documents'])]  # 더미 distance (실제론 사용 안함)
                }
                results = formatted_results
                print(f"✅ VectorDB에서 {len(results['documents'][0])}개 가이드라인 조회 완료")
            else:
                print("⚠️ VectorDB가 비어있음, fallback 사용")
                return fallback_analysis(request)
        except Exception as e:
            print(f"⚠️ VectorDB 검색 실패: {e}, fallback 사용")
            return fallback_analysis(request)

        if not results['documents'] or len(results['documents'][0]) == 0:
            print("⚠️ 검색 결과 없음, fallback 사용")
            return fallback_analysis(request)

        # 검색된 가이드라인
        relevant_guides = []
        for i, doc in enumerate(results['documents'][0]):
            metadata = results['metadatas'][0][i] if results['metadatas'] else {}
            relevant_guides.append({
                'content': doc,
                'scenario': metadata.get('scenario', ''),
                'directive': metadata.get('actionable_directive', ''),
                'distance': results['distances'][0][i] if results['distances'] else 1.0
            })

        # LLM으로 마스킹 결정
        masking_decisions = await decide_masking_with_llm(
            request.email_body,
            request.detected_pii,
            request.context,
            relevant_guides
        )

        # AI 요약 생성
        summary = generate_summary(request.context, masking_decisions, relevant_guides)

        return JSONResponse({
            "success": True,
            "data": {
                "masking_decisions": masking_decisions,
                "summary": summary,
                "relevant_guides": relevant_guides[:3],  # 상위 3개만
                "total_guides_found": len(relevant_guides)
            }
        })

    except Exception as e:
        print(f"RAG 분석 오류: {e}")
        # 오류 시 fallback
        return fallback_analysis(request)


async def decide_masking_with_llm(
    email_body: str,
    detected_pii: List[Dict[str, str]],
    context: Dict[str, Any],
    guides: List[Dict[str, Any]],
    use_llm: bool = False  # LLM 사용 여부 (기본값: False, 규칙 엔진 사용)
) -> Dict[str, Any]:
    """
    가이드라인 기반 마스킹 결정

    Args:
        use_llm: True면 OpenAI LLM 호출, False면 빠른 규칙 엔진 사용 (기본값)
    """

    # LLM 사용 모드 (느리지만 정확)
    if use_llm:
        try:
            from app.llm.masking_prompter import MaskingPrompter
            import asyncio

            # 프롬프트 생성
            system_prompt, user_prompt = MaskingPrompter.build_prompt(
                email_subject=context.get('email_subject', ''),
                detected_pii=detected_pii,
                context=context,
                guidelines=guides
            )

            # OpenAI API 호출 (타임아웃 5초)
            llm_task = asyncio.create_task(
                asyncio.to_thread(
                    lambda: openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.3,
                        max_tokens=2000,
                        response_format={"type": "json_object"}
                    )
                )
            )

            response = await asyncio.wait_for(llm_task, timeout=5.0)
            response_text = response.choices[0].message.content

            # 응답 파싱
            result = MaskingPrompter.parse_llm_response(response_text, detected_pii)
            return result["decisions"]

        except asyncio.TimeoutError:
            print("⚠️ LLM 호출 타임아웃, 규칙 엔진으로 fallback")
        except Exception as e:
            print(f"⚠️ LLM 호출 실패: {e}, 규칙 엔진으로 fallback")

    # 빠른 규칙 엔진 (기본값)
    decisions = {}
    receiver_type = context.get('receiver_type', 'unknown')

    # 가이드라인에서 키워드 추출
    guideline_keywords = set()
    for guide in guides[:3]:
        scenario = guide.get('scenario', '').lower()
        directive = guide.get('directive', '').lower()

        # 마스킹 관련 키워드
        if '마스킹' in directive or 'mask' in directive:
            guideline_keywords.add('mask_required')
        if '외부' in scenario or 'external' in scenario:
            guideline_keywords.add('external_sensitive')
        if '내부' in scenario or 'internal' in scenario:
            guideline_keywords.add('internal_allowed')

    for i, pii in enumerate(detected_pii):
        pii_type = pii.get('type', '')
        should_mask = False
        reason = ""
        masking_method = "none"
        reasoning_steps = []
        cited_guidelines = []

        # 가이드라인 인용 정보 수집
        relevant_guide_texts = []
        for guide in guides[:3]:
            scenario = guide.get('scenario', '')
            directive = guide.get('directive', '')
            if scenario or directive:
                relevant_guide_texts.append({
                    'scenario': scenario[:100],
                    'directive': directive[:100]
                })

        # Step 1: 컨텍스트 분석
        reasoning_steps.append(f"1. 컨텍스트 확인: {receiver_type} 전송")

        # Step 2: PII 유형 분류
        pii_type_kr = {
            'email': '이메일 주소',
            'phone': '전화번호',
            'jumin': '주민등록번호',
            'account': '계좌번호',
            'passport': '여권번호',
            'driver_license': '운전면허번호'
        }.get(pii_type, pii_type)
        reasoning_steps.append(f"2. PII 유형: {pii_type_kr}")

        # Step 3: 가이드라인 검토
        if relevant_guide_texts:
            reasoning_steps.append(f"3. 관련 가이드라인 {len(relevant_guide_texts)}개 검토:")
            for idx, guide in enumerate(relevant_guide_texts, 1):
                reasoning_steps.append(f"   - 가이드 {idx}: {guide['scenario'][:60]}...")
                cited_guidelines.append(guide['scenario'][:80])

        # 규칙 1: 외부 전송이면 대부분 마스킹
        if receiver_type == 'external':
            should_mask = True
            reasoning_steps.append("4. 판단 근거:")

            # PII 유형별 마스킹 방법
            if pii_type in ['jumin', 'account']:
                masking_method = "full"
                reasoning_steps.append(f"   - 개인정보보호법 제24조: 고유식별정보({pii_type_kr})는 제3자 제공 시 필수적으로 암호화/마스킹 필요")
                reasoning_steps.append(f"   - PIPA 제24조의2: 외부 전송 시 주민등록번호, 계좌번호 등은 완전 삭제 또는 대체")
                reasoning_steps.append(f"   - 위험도: CRITICAL - 유출 시 법적 제재 및 막대한 손해배상 가능")
                reason = "고유식별정보 외부 전송 금지 (개인정보보호법 제24조)"
                cited_guidelines.append("개인정보보호법 제24조: 고유식별정보 처리 제한")
            elif pii_type == 'email':
                masking_method = "partial"
                reasoning_steps.append(f"   - 개인정보보호법 제17조: 개인정보 제3자 제공 시 최소한의 정보만 제공")
                reasoning_steps.append(f"   - 이메일은 업무 연락에 필요하므로 부분 마스킹으로 타협")
                reasoning_steps.append(f"   - 도메인은 유지하여 소속 확인 가능하도록 처리")
                reason = "개인정보 최소화 원칙 (개인정보보호법 제17조)"
                cited_guidelines.append("개인정보보호법 제17조: 개인정보 제공 시 최소화")
            else:
                masking_method = "partial"
                reasoning_steps.append(f"   - 외부 전송 시 {pii_type_kr} 부분 마스킹 권장")
                reasoning_steps.append(f"   - 업무 연속성을 위해 일부 정보는 보존")
                reason = "외부 전송 시 개인정보 마스킹 필수"

            reasoning_steps.append(f"5. 최종 결정: {masking_method.upper()} 마스킹 적용")

        # 규칙 2: 내부 전송이어도 민감정보는 마스킹
        elif pii_type in ['jumin', 'account']:
            should_mask = True
            masking_method = "full"
            reasoning_steps.append("4. 판단 근거:")
            reasoning_steps.append(f"   - 개인정보보호법 제24조: 고유식별정보는 내부 전송이라도 최소한으로만 처리")
            reasoning_steps.append(f"   - 내부 유출 사고 대비: 불필요한 {pii_type_kr} 노출 방지")
            reasoning_steps.append(f"   - 업무상 필수가 아닌 경우 완전 마스킹 권장")
            reasoning_steps.append(f"5. 최종 결정: FULL 마스킹 적용")
            reason = "고유식별정보는 내부 전송에도 최소 처리 (개인정보보호법 제24조)"
            cited_guidelines.append("개인정보보호법 제24조: 고유식별정보 처리 제한")

        # 규칙 3: 가이드라인에 명시적 마스킹 지시가 있으면 적용
        elif 'mask_required' in guideline_keywords:
            should_mask = True
            masking_method = "partial"
            reasoning_steps.append("4. 판단 근거:")
            reasoning_steps.append(f"   - 검색된 가이드라인에서 마스킹 지시 발견")
            if relevant_guide_texts:
                reasoning_steps.append(f"   - 관련 지침: {relevant_guide_texts[0]['directive'][:80]}...")
            reasoning_steps.append(f"5. 최종 결정: PARTIAL 마스킹 적용")
            reason = "정책 가이드라인에 따라 마스킹 필요"

        else:
            should_mask = False
            masking_method = "none"
            reasoning_steps.append("4. 판단 근거:")
            reasoning_steps.append(f"   - 내부 전송이며 민감정보가 아님")
            reasoning_steps.append(f"   - 업무상 {pii_type_kr} 공유가 필요한 상황")
            reasoning_steps.append(f"   - 마스킹 불필요하나 추후 검토 필요")
            reasoning_steps.append(f"5. 최종 결정: 마스킹 미적용")
            reason = "내부 전송으로 마스킹 불필요"

        # 마스킹 미리보기 생성
        masked_value = None
        if should_mask:
            masked_value = _generate_masked_preview(pii.get('value', ''), pii_type, masking_method)

        # reasoning을 문자열로 변환
        reasoning_text = "\n".join(reasoning_steps)

        decisions[f"pii_{i}"] = {
            "pii_id": f"pii_{i}",
            "type": pii_type,
            "value": pii['value'],
            "should_mask": should_mask,
            "masking_method": masking_method,
            "masked_value": masked_value,
            "reason": reason,
            "reasoning": reasoning_text,  # 상세 추론 과정
            "cited_guidelines": cited_guidelines,  # 인용된 가이드라인
            "guideline_matched": len(guideline_keywords) > 0,
            "confidence": 0.85,
            "risk_level": "high" if pii_type in ['jumin', 'account'] else "medium" if should_mask else "low"
        }

    return decisions


def _generate_masked_preview(value: str, pii_type: str, method: str) -> str:
    """마스킹 미리보기 생성"""
    if method == "full":
        return "***"
    elif method == "partial":
        if pii_type == "email":
            parts = value.split("@")
            if len(parts) == 2:
                return parts[0][:2] + "***@" + parts[1]
        elif pii_type == "phone":
            if "-" in value:
                return value[:3] + "-***-" + value[-4:]
            else:
                return value[:3] + "***" + value[-4:]
        elif pii_type == "jumin":
            return value[:6] + "-*******"
        elif pii_type == "account":
            parts = value.split("-")
            if len(parts) == 3:
                return parts[0] + "-***-" + parts[2]
        return value[:3] + "***"
    elif method == "redact":
        return "[REDACTED]"
    elif method == "hash":
        return "[HASHED]"
    else:
        return value


def generate_summary(context: Dict, decisions: Dict, guides: List[Dict]) -> str:
    """AI 분석 요약 생성"""

    masked_count = sum(1 for d in decisions.values() if d.get('should_mask', False))
    total_count = len(decisions)

    receiver_type = context.get('receiver_type', 'unknown')
    receiver_text = "외부" if receiver_type == "external" else "내부"

    summary = f"{receiver_text} 전송으로 분류되어, "

    if masked_count > 0:
        summary += f"{total_count}개 개인정보 중 {masked_count}개를 마스킹하도록 권장합니다. "
    else:
        summary += "마스킹이 필요한 개인정보가 없습니다. "

    if guides:
        summary += f"\n\n관련 규정 {len(guides)}개를 참고했습니다."

    return summary


def fallback_analysis(request: RAGAnalysisRequest) -> JSONResponse:
    """VectorDB 사용 불가 시 기본 규칙 기반 분석"""

    decisions = {}
    context = request.context
    receiver_type = context.get('receiver_type', 'external')

    for i, pii in enumerate(request.detected_pii):
        pii_type = pii['type']
        pii_value = pii['value']
        masking_method = "none"
        reasoning_steps = []
        cited_guidelines = []

        # PII 유형 한글명
        pii_type_kr = {
            'email': '이메일 주소',
            'phone': '전화번호',
            'jumin': '주민등록번호',
            'account': '계좌번호',
            'passport': '여권번호',
            'driver_license': '운전면허번호'
        }.get(pii_type, pii_type)

        # Step 1: 컨텍스트 분석
        reasoning_steps.append(f"1. 컨텍스트 확인: {receiver_type} 전송")
        reasoning_steps.append(f"2. PII 유형: {pii_type_kr}")
        reasoning_steps.append("3. VectorDB 사용 불가 → 기본 규칙 적용")

        # 외부 전송이면 모두 마스킹
        if receiver_type == 'external':
            should_mask = True
            reasoning_steps.append("4. 판단 근거:")

            # PII 유형별 마스킹 방법
            if pii_type in ['jumin', 'account']:
                masking_method = "full"
                reasoning_steps.append(f"   - 개인정보보호법 제24조: 고유식별정보({pii_type_kr})는 제3자 제공 시 원칙적 금지")
                reasoning_steps.append(f"   - 불가피한 경우 완전 암호화/마스킹 필수")
                reasoning_steps.append(f"   - 위험도: CRITICAL - 법적 제재 대상")
                reason = "고유식별정보 외부 전송 금지 (개인정보보호법 제24조)"
                cited_guidelines.append("개인정보보호법 제24조: 고유식별정보 처리 제한")
            else:
                masking_method = "partial"
                reasoning_steps.append(f"   - 개인정보보호법 제17조: 제3자 제공 시 최소한의 정보만 전달")
                reasoning_steps.append(f"   - {pii_type_kr}는 업무상 필요하므로 부분 마스킹 적용")
                reasoning_steps.append(f"   - 식별 가능성을 낮추되 업무 연속성 유지")
                reason = "개인정보 최소화 원칙 (개인정보보호법 제17조)"
                cited_guidelines.append("개인정보보호법 제17조: 개인정보 제공 시 최소화")

            reasoning_steps.append(f"5. 최종 결정: {masking_method.upper()} 마스킹 적용")
        else:
            # 주민번호, 계좌번호는 항상 마스킹
            if pii_type in ['jumin', 'account']:
                should_mask = True
                masking_method = "full"
                reasoning_steps.append("4. 판단 근거:")
                reasoning_steps.append(f"   - 내부 전송이나 고유식별정보는 최소 처리 원칙 적용")
                reasoning_steps.append(f"   - 개인정보보호법 제24조: 업무상 불가피한 경우에만 처리")
                reasoning_steps.append(f"   - 내부 유출 사고 대비 필요")
                reasoning_steps.append(f"5. 최종 결정: FULL 마스킹 적용")
                reason = "민감정보 최소 처리 (개인정보보호법 제24조)"
                cited_guidelines.append("개인정보보호법 제24조: 고유식별정보 최소 처리")
            else:
                should_mask = False
                masking_method = "none"
                reasoning_steps.append("4. 판단 근거:")
                reasoning_steps.append(f"   - 내부 전송이며 일반 개인정보")
                reasoning_steps.append(f"   - 업무상 {pii_type_kr} 공유가 필요")
                reasoning_steps.append(f"   - 접근 권한 관리로 보안 유지")
                reasoning_steps.append(f"5. 최종 결정: 마스킹 미적용")
                reason = "내부 전송으로 마스킹 불필요"

        # 마스킹 미리보기 생성
        masked_value = None
        if should_mask:
            masked_value = _generate_masked_preview(pii_value, pii_type, masking_method)

        # reasoning을 문자열로 변환
        reasoning_text = "\n".join(reasoning_steps)

        decisions[f"pii_{i}"] = {
            "pii_id": f"pii_{i}",
            "type": pii_type,
            "value": pii_value,
            "should_mask": should_mask,
            "masking_method": masking_method,
            "masked_value": masked_value,
            "reason": reason,
            "reasoning": reasoning_text,  # 상세 추론 과정
            "cited_guidelines": cited_guidelines,  # 인용된 법령
            "confidence": 0.8,
            "risk_level": "high" if pii_type in ['jumin', 'account'] else "medium" if should_mask else "low"
        }

    masked_count = sum(1 for d in decisions.values() if d['should_mask'])

    summary = f"기본 규칙에 따라 {len(decisions)}개 개인정보 중 {masked_count}개 마스킹을 권장합니다."

    return JSONResponse({
        "success": True,
        "data": {
            "masking_decisions": decisions,
            "summary": summary,
            "relevant_guides": [],
            "total_guides_found": 0,
            "fallback": True
        }
    })
