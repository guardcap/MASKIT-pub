"""
백그라운드 작업 처리
- 정책 가이드라인 추출
- VectorDB 임베딩 생성
- 작업 상태 관리
"""

import asyncio
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path
import json
import os
from dotenv import load_dotenv

# OpenAI imports
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# ChromaDB imports
try:
    import chromadb
    from sentence_transformers import SentenceTransformer
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

load_dotenv()

# 작업 상태 저장
task_status: Dict[str, Dict] = {}

# VectorDB 설정 - 절대 경로 사용
BASE_DIR = Path(__file__).parent.parent.parent.parent  # enterprise-guardcap 루트
CHROMA_DB_DIR = BASE_DIR / "backend" / "app" / "rag" / "data" / "chromadb"
CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)

# JSONL 저장 디렉토리 (RAG staging) - 절대 경로 사용
STAGING_DIR = BASE_DIR / "backend" / "app" / "rag" / "data" / "staging"
STAGING_DIR.mkdir(parents=True, exist_ok=True)

# 환경 변수에서 설정값 로드
PDF_BATCH_SIZE = int(os.getenv("PDF_BATCH_SIZE", "10"))
PDF_BATCH_DELAY = int(os.getenv("PDF_BATCH_DELAY", "3"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.85"))


class LargePDFProcessor:
    """대용량 PDF 최적화 처리기"""

    def __init__(self, max_pages_per_batch: int = None):
        self.max_pages_per_batch = max_pages_per_batch or PDF_BATCH_SIZE

    def split_text_by_length(self, text: str, max_length: int = 8000) -> list:
        """텍스트를 길이로 분할"""
        if len(text) <= max_length:
            return [text]

        # 문단 단위로 분할
        paragraphs = text.split('\n\n')
        batches = []
        current_batch = ""

        for para in paragraphs:
            if len(current_batch) + len(para) <= max_length:
                current_batch += para + '\n\n'
            else:
                if current_batch:
                    batches.append(current_batch)
                current_batch = para + '\n\n'

        if current_batch:
            batches.append(current_batch)

        return batches


class GuidelineExtractor:
    """가이드라인 추출 및 구조화"""

    def __init__(self):
        if OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                print(f"[DEBUG] OpenAI API 키 발견: {api_key[:10]}...")
                self.client = AsyncOpenAI(api_key=api_key)
                self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
                print(f"[DEBUG] 사용할 모델: {self.model}")
            else:
                print("[ERROR] OPENAI_API_KEY 환경 변수가 설정되지 않았습니다")
                self.client = None
        else:
            print("[ERROR] OpenAI 라이브러리를 사용할 수 없습니다")
            self.client = None

        self.pdf_processor = LargePDFProcessor()

    async def extract_guidelines(self, policy_text: str, policy_title: str, authority: str) -> list:
        """정책 텍스트에서 가이드라인 추출 (배치 처리 지원)"""
        if not self.client:
            return []

        # 텍스트가 8000자 이상이면 배치 처리
        if len(policy_text) > 8000:
            return await self._extract_guidelines_batch(policy_text, policy_title, authority)
        else:
            return await self._extract_guidelines_single(policy_text, policy_title, authority)

    async def _extract_guidelines_single(self, policy_text: str, policy_title: str, authority: str) -> list:
        """단일 배치로 가이드라인 추출"""
        prompt = f"""
다음 정책 문서에서 실무 가이드라인을 추출하세요.

정책 제목: {policy_title}
발행 기관: {authority}

문서 내용:
{policy_text[:8000]}

각 가이드라인은 다음 형식의 JSON 배열로 반환하세요:
[
  {{
    "scenario": "적용 상황 (100자 이내)",
    "context": {{
      "sender_type": "internal/external_customer/partner/regulatory",
      "receiver_type": "internal/external_customer/partner/regulatory",
      "email_purpose": "견적서/문의/보고 등",
      "pii_types": ["phone", "email", "name" 등]
    }},
    "interpretation": "법적 해석 및 배경 설명",
    "actionable_directive": "실행 지침 (명확하게)",
    "keywords": ["키워드1", "키워드2", ...],
    "related_law_ids": ["법률ID1", "법률ID2", ...],
    "examples": [
      {{
        "case_description": "사례 설명",
        "masking_decision": "mask/no_mask/partial_mask",
        "reasoning": "판단 근거"
      }}
    ]
  }}
]

최대 10개의 가이드라인을 추출하세요.
반드시 유효한 JSON 배열만 반환하세요.
"""

        try:
            print(f"[DEBUG] OpenAI 요청 시작 - 모델: {self.model}")
            print(f"[DEBUG] 텍스트 길이: {len(policy_text)} 자")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            content = response.choices[0].message.content.strip()
            print(f"[DEBUG] OpenAI 응답 받음, 길이: {len(content)} 자")

            # JSON 추출
            import re
            content = re.sub(r'^```json\s*', '', content)
            content = re.sub(r'\s*```$', '', content)

            guidelines = json.loads(content)
            print(f"[DEBUG] JSON 파싱 성공, {len(guidelines)}개 가이드라인 추출")

            # 메타데이터 추가
            for i, guide in enumerate(guidelines):
                guide["guide_id"] = f"{authority[:4].upper()}-{policy_title[:20]}-{i:03d}"
                guide["source_authority"] = authority
                guide["source_document"] = policy_title
                guide["confidence_score"] = 0.8

            return guidelines

        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON 파싱 실패: {e}")
            print(f"[ERROR] 응답 내용: {content[:500]}")
            return []
        except Exception as e:
            print(f"[ERROR] 가이드라인 추출 실패: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def _extract_guidelines_batch(self, policy_text: str, policy_title: str, authority: str) -> list:
        """대용량 텍스트를 배치로 나누어 가이드라인 추출"""
        # 텍스트를 배치로 분할
        batches = self.pdf_processor.split_text_by_length(policy_text, max_length=8000)

        print(f"대용량 정책 문서: {len(policy_text)}자 → {len(batches)}개 배치로 분할")

        all_guidelines = []

        for batch_idx, batch_text in enumerate(batches):
            print(f"배치 {batch_idx + 1}/{len(batches)} 처리 중...")

            # 각 배치에서 가이드라인 추출
            batch_guidelines = await self._extract_guidelines_single(
                batch_text,
                f"{policy_title} (Part {batch_idx + 1})",
                authority
            )

            all_guidelines.extend(batch_guidelines)

            # API 레이트 리밋 방지를 위한 딜레이 (마지막 배치 제외)
            if batch_idx < len(batches) - 1:
                print(f"다음 배치 처리 전 {PDF_BATCH_DELAY}초 대기...")
                await asyncio.sleep(PDF_BATCH_DELAY)

        # 중복 제거 및 ID 재할당
        unique_guidelines = []
        seen_scenarios = set()

        for i, guide in enumerate(all_guidelines):
            scenario = guide.get("scenario", "")
            if scenario and scenario not in seen_scenarios:
                # ID 재할당
                guide["guide_id"] = f"{authority[:4].upper()}-{policy_title[:20]}-{i:03d}"
                unique_guidelines.append(guide)
                seen_scenarios.add(scenario)

        print(f"총 {len(all_guidelines)}개 추출 → 중복 제거 후 {len(unique_guidelines)}개")

        return unique_guidelines


class VectorDBManager:
    """VectorDB 관리"""

    def __init__(self):
        if not CHROMADB_AVAILABLE:
            self.client = None
            self.collection = None
            self.model = None
            return

        try:
            self.client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))

            # 컬렉션 가져오기 또는 생성
            try:
                self.collection = self.client.get_collection("application_guides")
            except:
                self.collection = self.client.create_collection(
                    name="application_guides",
                    metadata={"hnsw:space": "cosine"}
                )

            # 임베딩 모델 로드
            model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
            self.model = SentenceTransformer(model_name)

        except Exception as e:
            print(f"VectorDB 초기화 실패: {e}")
            self.client = None
            self.collection = None
            self.model = None

    def add_guidelines(self, guidelines: list):
        """가이드라인을 VectorDB에 추가"""
        if not self.collection or not self.model:
            return False

        try:
            documents = []
            metadatas = []
            ids = []

            for guide in guidelines:
                # 텍스트 생성 (검색용)
                doc_text = f"""
                시나리오: {guide.get('scenario', '')}
                해석: {guide.get('interpretation', '')}
                지침: {guide.get('actionable_directive', '')}
                키워드: {', '.join(guide.get('keywords', []))}
                """.strip()

                documents.append(doc_text)

                # 메타데이터 (JSON 직렬화 가능한 형태로)
                metadata = {
                    "guide_id": guide.get("guide_id", ""),
                    "source_authority": guide.get("source_authority", ""),
                    "source_document": guide.get("source_document", ""),
                    "scenario": guide.get("scenario", ""),
                    "actionable_directive": guide.get("actionable_directive", ""),
                    "keywords": json.dumps(guide.get("keywords", []), ensure_ascii=False),
                }

                # context 처리
                if "context" in guide and guide["context"]:
                    context = guide["context"]
                    metadata["sender_type"] = context.get("sender_type", "")
                    metadata["receiver_type"] = context.get("receiver_type", "")
                    metadata["email_purpose"] = context.get("email_purpose", "")

                metadatas.append(metadata)
                ids.append(guide["guide_id"])

            # 임베딩 생성
            embeddings = self.model.encode(documents, show_progress_bar=False)

            # VectorDB에 추가
            self.collection.add(
                embeddings=embeddings.tolist(),
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

            return True

        except Exception as e:
            print(f"VectorDB 추가 실패: {e}")
            return False


def save_guidelines_to_jsonl(guidelines: list, policy_id: str, policy_title: str) -> bool:
    """
    가이드라인을 JSONL 파일로 staging 디렉토리에 저장
    """
    try:
        # 파일명 생성 (정책 제목 기반)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in policy_title)
        safe_title = safe_title.replace(' ', '_')[:50]

        filename = f"application_guides_{timestamp}_{safe_title}_{policy_id}.jsonl"
        file_path = STAGING_DIR / filename

        # JSONL 형식으로 저장 (각 가이드라인을 한 줄씩)
        with open(file_path, "w", encoding="utf-8") as f:
            for guide in guidelines:
                json_line = json.dumps(guide, ensure_ascii=False)
                f.write(json_line + "\n")

        print(f"[INFO] JSONL 파일 저장 완료: {file_path}")
        print(f"[INFO] {len(guidelines)}개 가이드라인 저장됨")

        return True

    except Exception as e:
        print(f"[ERROR] JSONL 파일 저장 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def process_policy_background(policy_id: str, policy_data: dict, db):
    """
    백그라운드에서 정책 처리
    1. 가이드라인 추출
    2. VectorDB 임베딩
    """
    task_id = f"policy_{policy_id}"

    # 작업 시작
    task_status[task_id] = {
        "status": "processing",
        "progress": 0,
        "message": "가이드라인 추출 중...",
        "started_at": datetime.utcnow().isoformat(),
        "policy_id": policy_id
    }

    try:
        # 1. 가이드라인 추출 (0% → 50%)
        extractor = GuidelineExtractor()

        # 텍스트 크기 확인
        text_length = len(policy_data.get("extracted_text", ""))
        if text_length > 8000:
            task_status[task_id]["message"] = f"대용량 문서 ({text_length}자) 배치 처리 중..."

        task_status[task_id]["progress"] = 10

        guidelines = await extractor.extract_guidelines(
            policy_data.get("extracted_text", ""),
            policy_data.get("title", ""),
            policy_data.get("authority", "")
        )

        task_status[task_id]["progress"] = 50
        task_status[task_id]["message"] = f"{len(guidelines)}개 가이드라인 추출 완료"

        if not guidelines:
            task_status[task_id]["status"] = "completed"
            task_status[task_id]["progress"] = 100
            task_status[task_id]["message"] = "가이드라인을 추출하지 못했습니다"
            task_status[task_id]["completed_at"] = datetime.utcnow().isoformat()
            return

        # 2. JSONL 파일로 저장 (50% → 60%)
        task_status[task_id]["progress"] = 55
        task_status[task_id]["message"] = "JSONL 파일 저장 중..."

        jsonl_saved = save_guidelines_to_jsonl(
            guidelines,
            policy_id,
            policy_data.get("title", "")
        )

        task_status[task_id]["progress"] = 60

        # 3. MongoDB에 가이드라인 저장 (60% → 70%)
        task_status[task_id]["message"] = "MongoDB에 가이드라인 저장 중..."

        # 정책에 가이드라인 추가
        await db["policies"].update_one(
            {"policy_id": policy_id},
            {"$set": {"guidelines": guidelines, "guidelines_count": len(guidelines)}}
        )

        task_status[task_id]["progress"] = 70

        # 4. VectorDB 임베딩 (70% → 95%)
        task_status[task_id]["message"] = "VectorDB 임베딩 생성 중..."

        vectordb = VectorDBManager()
        success = vectordb.add_guidelines(guidelines)

        task_status[task_id]["progress"] = 95

        # 5. 완료 (100%)
        task_status[task_id]["status"] = "completed"
        task_status[task_id]["progress"] = 100
        task_status[task_id]["message"] = f"{len(guidelines)}개 가이드라인이 JSONL 및 VectorDB에 추가되었습니다"
        task_status[task_id]["completed_at"] = datetime.utcnow().isoformat()
        task_status[task_id]["guidelines_count"] = len(guidelines)
        task_status[task_id]["jsonl_saved"] = jsonl_saved
        task_status[task_id]["vectordb_success"] = success

    except Exception as e:
        task_status[task_id]["status"] = "failed"
        task_status[task_id]["progress"] = 0
        task_status[task_id]["message"] = f"오류 발생: {str(e)}"
        task_status[task_id]["completed_at"] = datetime.utcnow().isoformat()
        print(f"백그라운드 작업 실패: {e}")


def get_task_status(task_id: str) -> Optional[Dict]:
    """작업 상태 조회"""
    return task_status.get(task_id)


def clear_old_tasks(max_age_seconds: int = 3600):
    """오래된 작업 삭제 (1시간 이상)"""
    now = datetime.utcnow()
    to_delete = []

    for task_id, task in task_status.items():
        if "completed_at" in task:
            completed_at = datetime.fromisoformat(task["completed_at"])
            age = (now - completed_at).total_seconds()
            if age > max_age_seconds:
                to_delete.append(task_id)

    for task_id in to_delete:
        del task_status[task_id]
