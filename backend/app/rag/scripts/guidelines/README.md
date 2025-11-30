# Application Guidelines Processing Pipeline

실무 가이드라인 PDF → VectorDB 자동화 파이프라인

## 특징

- **OpenAI GPT-4o Vision**: 고품질 OCR + 문서 이해
- **대용량 PDF 지원**: 50MB+ 파일도 배치 처리로 안정적 처리
- **자동 구조화**: LLM이 자동으로 스키마에 맞춰 데이터 추출
- **중복 제거**: Embedding 유사도 기반 자동 중복 감지
- **품질 검증**: 신뢰도 기반 휴먼 리뷰 큐 생성

## 설치

```bash
cd guardcap-rag

# 의존성 설치
pip install -r requirements.txt

# 시스템 의존성 (macOS)
brew install poppler  # PDF 처리용

# 시스템 의존성 (Ubuntu)
sudo apt-get install poppler-utils
```

## 사용법

### Quick Start: 단일 PDF 테스트

특정 PDF 하나만 먼저 테스트하려면:

```bash
cd guardcap-rag

# 테스트 스크립트 실행 (금융보안 거버넌스 가이드)
./scripts/guidelines/test_single_pdf.sh
```

**동작 원리:**
1. 다른 PDF들을 임시로 백업
2. 지정된 PDF만 처리
3. 처리 완료 후 백업 파일 자동 복원

**테스트할 파일 변경:**
`test_single_pdf.sh` 파일에서 `TEST_PDF` 변수 수정:
```bash
TEST_PDF="data/raw_guidelines/(금융보안원) 금융보안 거버넌스 가이드.pdf"
```

---

### Step 1: 환경 설정

**Option A: .env 파일 사용 (권장)**

```bash
# 1. .env.example을 .env로 복사
cp guardcap-rag/.env.example guardcap-rag/.env

# 2. .env 파일 편집 (OpenAI API 키 입력)
vim guardcap-rag/.env  # 또는 원하는 에디터 사용
```

`.env` 파일 내용 예시:
```bash
OPENAI_API_KEY=sk-proj-your-actual-key-here
OPENAI_MODEL=gpt-4o
OPENAI_VISION_MODEL=gpt-4o
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

MAX_PDF_FILES=5
PDF_BATCH_SIZE=10
SIMILARITY_THRESHOLD=0.85
MIN_CONFIDENCE=0.7
```

**Option B: 환경변수 직접 설정**

```bash
export OPENAI_API_KEY='sk-proj-...'
```

### Step 2: PDF 파일 준비

```bash
# PDF 파일을 raw_guidelines 디렉토리에 추가
cp ~/Downloads/개인정보보호_실무가이드.pdf data/raw_guidelines/
```

### Step 3: PDF 처리 (구조화)

```bash
cd guardcap-rag

python scripts/guidelines/process_guidelines.py
```

**출력:**
- `data/staging/application_guides/application_guides.jsonl` - 추출된 가이드라인
- `data/staging/application_guides/application_guides_review.jsonl` - 리뷰 필요 항목

**옵션:**
```bash
# 처리할 파일 개수 제한
MAX_PDF_FILES=3 python scripts/guidelines/process_guidelines.py
```

### Step 4: 중복 제거 및 검증

```bash
python scripts/guidelines/validate_and_dedup.py
```

**출력:**
- `data/staging/application_guides/application_guides_unique.jsonl` - 중복 제거 완료
- `data/staging/application_guides/review_queue.csv` - 휴먼 리뷰 큐 (엑셀로 열기 가능)
- `data/staging/application_guides/duplicates_report.json` - 중복 쌍 리포트

### Step 5: VectorDB 빌드

```bash
python scripts/guidelines/build_guides_vectordb.py
```

**출력:**
- `data/chromadb/application_guides/` - ChromaDB 데이터베이스
- 자동 검색 테스트 실행

## 대용량 PDF 처리

50MB 이상 또는 50페이지 이상 PDF는 자동으로 배치 처리됩니다:

1. PDF를 10페이지 단위로 분할
2. 각 배치를 Zerox로 개별 처리
3. 결과를 자동으로 병합
4. 임시 파일 자동 정리

**성능:**
- 10MB PDF (30페이지): ~2-3분
- 50MB PDF (150페이지): ~10-15분

## 비용 추정

### OpenAI API 비용 (2024년 기준)

| 항목 | 모델 | 비용 |
|------|------|------|
| Vision OCR | gpt-4o | ~$0.03/페이지 |
| 구조화 LLM | gpt-4o | ~$0.01/섹션 |
| Embedding | text-embedding-3-small | ~$0.0001/1K 토큰 |

**예시:**
- 30페이지 PDF: ~$1-2
- 150페이지 PDF (배치 처리): ~$5-8

## 출력 스키마

생성되는 가이드라인의 JSON 구조:

```json
{
  "guide_id": "GUIDE-PIPC-202501-abc123-001",
  "source_authority": "개인정보보호위원회",
  "source_document": "개인정보보호_실무가이드.pdf",
  "publish_date": "2024-01-15",
  "scenario": "외부 고객이 제품 문의를 위해 먼저 이메일을 보낸 경우",
  "context": {
    "sender_type": "external_customer",
    "receiver_type": "internal",
    "email_purpose": "제품 문의",
    "pii_types": ["phone", "email", "name"]
  },
  "interpretation": "고객의 최초 문의는 명시적 동의로 간주...",
  "actionable_directive": "마스킹 예외 처리. 단, 마케팅 포함 시 마스킹 필요.",
  "keywords": ["고객 문의", "견적서", "동의", "개인정보"],
  "related_law_ids": ["개인정보보호법_제15조_1항_1호"],
  "examples": [
    {
      "case_description": "고객이 견적서 요청 이메일 발송",
      "masking_decision": "no_mask",
      "reasoning": "고객의 명시적 동의 존재"
    }
  ],
  "confidence_score": 0.85,
  "reviewed": false
}
```

## 파일 구조

```
guardcap-rag/
├── data/
│   ├── raw_guidelines/           # 입력: PDF 파일
│   ├── staging/application_guides/
│   │   ├── application_guides.jsonl           # Step 3 출력
│   │   ├── application_guides_unique.jsonl    # Step 4 출력 (최종)
│   │   ├── review_queue.csv                   # 휴먼 리뷰 큐
│   │   └── duplicates_report.json             # 중복 리포트
│   ├── chromadb/application_guides/           # Step 5 출력 (VectorDB)
│   └── temp/                                  # 임시 파일 (자동 삭제)
│
└── scripts/guidelines/
    ├── process_guidelines.py        # Step 3: PDF → JSONL
    ├── validate_and_dedup.py        # Step 4: 검증 + 중복 제거
    ├── build_guides_vectordb.py     # Step 5: VectorDB 빌드
    └── README.md                    # 이 문서
```

## 트러블슈팅

### 1. "Zerox failed" 에러

**원인**: Vision API 오류 또는 이미지 변환 실패

**해결책**: 자동으로 PyMuPDF fallback 실행됨. 품질이 낮으면 PDF 파일 확인.

### 2. "OPENAI_API_KEY not set"

```bash
export OPENAI_API_KEY='sk-proj-...'

# 또는 .env 파일에 추가 (프로젝트 루트)
echo "OPENAI_API_KEY=sk-proj-..." >> .env
```

### 3. "poppler not found"

```bash
# macOS
brew install poppler

# Ubuntu
sudo apt-get install poppler-utils
```

### 4. 메모리 부족 (대용량 PDF)

`process_guidelines.py`에서 배치 크기 조정:

```python
self.pdf_processor = LargePDFProcessor(max_pages_per_batch=5)  # 기본값: 10
```

### 5. 검증 실패 ("Missing scenario")

신뢰도가 낮은 경우 자동으로 `review_queue.csv`에 추가됨. 엑셀로 열어 수동 확인.

## 다음 단계

### 기존 RAG 시스템과 통합

VectorDB 빌드 완료 후, `agent/retrievers.py`를 수정하여 통합:

```python
# agent/retrievers.py
class HybridRetriever:
    def __init__(self):
        # 기존 코드...

        # Application Guides ChromaDB 로드
        self.guides_client = chromadb.PersistentClient(
            path="data/chromadb/application_guides"
        )
        self.guides_collection = self.guides_client.get_collection(
            name="application_guides"
        )

    def search_application_guides(self, query: str, context: dict = None, top_k: int = 3):
        # OpenAI Embedding으로 쿼리 변환
        query_embedding = self.get_embedding(query)  # 구현 필요

        # ChromaDB 검색
        results = self.guides_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"sender_type": context.get("sender_type")} if context else None
        )

        return results
```

## 성능 최적화

### 1. 배치 크기 조정

대량 PDF 처리 시:
```python
# validate_and_dedup.py
embeddings = self.get_embeddings(texts, batch_size=200)  # 기본값: 100
```

### 2. 캐싱 활성화

동일 PDF 재처리 방지:
```python
# process_guidelines.py - 추후 구현 예정
# PDF 해시 기반 캐싱 로직
```

### 3. 병렬 처리

여러 PDF 동시 처리:
```bash
# 추후 구현 예정
MAX_WORKERS=4 python scripts/guidelines/process_guidelines.py
```

## FAQ

**Q: 한글 PDF도 지원하나요?**
A: 네, GPT-4o Vision은 한글을 완벽히 지원합니다.

**Q: 스캔한 이미지 PDF도 가능한가요?**
A: 네, Zerox가 자동으로 OCR을 수행합니다.

**Q: Ollama 로컬 모델로 대체 가능한가요?**
A: 구조화 LLM은 가능하지만, Vision OCR은 OpenAI/Claude API 권장 (품질 차이 큼).

**Q: 중복은 어떻게 판단하나요?**
A: Embedding 코사인 유사도 > 0.85인 경우 중복으로 간주. `validate_and_dedup.py`에서 threshold 조정 가능.

**Q: 기존 application_guides.jsonl과 병합하려면?**
A: 두 파일을 합친 후 `validate_and_dedup.py` 실행하면 자동으로 중복 제거됩니다.

## 라이선스

본 프로젝트 라이선스 참조

## 작성자

guardcap-rag 팀
