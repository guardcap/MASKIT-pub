# Quick Start Guide - Application Guidelines Pipeline

실무 가이드라인 PDF를 5분 안에 VectorDB로 변환하는 빠른 시작 가이드

## 🚀 3단계로 시작하기

### 1️⃣ 환경 설정 (1분)

```bash
cd guardcap-rag

# .env 파일 생성
cp .env.example .env

# .env 파일 편집 (OpenAI API 키 입력)
nano .env  # 또는 vim, vscode 등
```

**필수 설정 (.env 파일):**
```bash
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

> 💡 **API 키 발급**: https://platform.openai.com/api-keys

### 2️⃣ PDF 파일 준비 (30초)

```bash
# 샘플 PDF 다운로드 (예시)
mkdir -p data/raw_guidelines

# 실무 가이드라인 PDF를 이 폴더에 복사
cp ~/Downloads/개인정보보호_실무가이드.pdf data/raw_guidelines/
```

### 3️⃣ 파이프라인 실행 (3분)

```bash
# 전체 파이프라인 자동 실행
./scripts/guidelines/run_pipeline.sh
```

**실행 결과:**
```
✅ Found .env file
📂 Found 1 PDF file(s)
📄 Processing: 개인정보보호_실무가이드.pdf
📑 Extracted 15 sections
✅ Saved 15 guides to data/staging/application_guides/application_guides.jsonl
✅ Found 0 duplicate pairs
✅ Remaining: 15 unique guides
✅ Successfully added 15 guides to VectorDB
```

---

## 📂 생성된 파일

파이프라인 실행 후 다음 파일들이 생성됩니다:

```
data/
├── staging/application_guides/
│   ├── application_guides.jsonl              # 원본 추출 데이터
│   ├── application_guides_unique.jsonl       # 중복 제거 완료 (최종)
│   ├── review_queue.csv                      # 휴먼 리뷰 필요 항목
│   └── duplicates_report.json                # 중복 감지 리포트
│
└── chromadb/application_guides/              # VectorDB (검색 가능)
    ├── chroma.sqlite3
    └── ...
```

---

## 🔍 결과 확인

### 1. 추출된 가이드 확인

```bash
# 첫 번째 가이드 보기
head -n 1 data/staging/application_guides/application_guides_unique.jsonl | jq .
```

**출력 예시:**
```json
{
  "guide_id": "GUIDE-PIPC-202501-a1b2c3-001",
  "scenario": "외부 고객이 제품 문의를 위해 먼저 이메일을 보낸 경우",
  "actionable_directive": "마스킹 예외 처리. 고객의 명시적 동의 존재",
  "keywords": ["고객 문의", "견적서", "동의"],
  "confidence_score": 0.85
}
```

### 2. 리뷰 큐 확인 (Excel/Google Sheets로 열기)

```bash
open data/staging/application_guides/review_queue.csv
```

### 3. VectorDB 검색 테스트

파이프라인 실행 시 자동으로 검색 테스트가 실행됩니다:

```
🔍 Testing search: '고객이 먼저 문의한 경우 개인정보 마스킹'
--- Result 1 (distance: 0.1234) ---
Guide ID: GUIDE-PIPC-202501-a1b2c3-001
Scenario: 외부 고객이 제품 문의를 위해...
```

---

## ⚙️ 설정 조정

`.env` 파일에서 다음 옵션을 조정할 수 있습니다:

```bash
# 모델 선택
OPENAI_MODEL=gpt-4o              # 또는 gpt-4, gpt-3.5-turbo
OPENAI_VISION_MODEL=gpt-4o       # Vision OCR 모델
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# 처리 제한
MAX_PDF_FILES=5                  # 한 번에 처리할 최대 파일 수
PDF_BATCH_SIZE=10                # 대용량 PDF 분할 페이지 수

# 품질 설정
SIMILARITY_THRESHOLD=0.85        # 중복 판단 임계값 (0.0-1.0)
MIN_CONFIDENCE=0.7               # 리뷰 큐 신뢰도 기준
```

---

## 💰 예상 비용

| PDF 크기 | 처리 시간 | OpenAI API 비용 |
|----------|-----------|-----------------|
| 20페이지 | ~2분 | ~$0.70 |
| 50페이지 | ~5분 | ~$1.75 |
| 100페이지 | ~10분 | ~$3.50 |

---

## ❓ 문제 해결

### "OPENAI_API_KEY not found"

```bash
# .env 파일 확인
cat .env | grep OPENAI_API_KEY

# 또는 환경변수로 설정
export OPENAI_API_KEY='sk-proj-...'
```

### "No PDF files found"

```bash
# PDF 파일 확인
ls data/raw_guidelines/

# PDF 파일 추가
cp ~/Downloads/*.pdf data/raw_guidelines/
```

### "poppler not found"

```bash
# macOS
brew install poppler

# Ubuntu/Debian
sudo apt-get install poppler-utils
```

### 메모리 부족 (대용량 PDF)

`.env` 파일에서 배치 크기 줄이기:
```bash
PDF_BATCH_SIZE=5  # 기본값: 10
```

---

## 🎯 다음 단계

### 1. RAG 시스템과 통합

생성된 VectorDB를 기존 RAG 시스템에 연결:

```python
# agent/retrievers.py
import chromadb

guides_client = chromadb.PersistentClient(
    path="data/chromadb/application_guides"
)
guides_collection = guides_client.get_collection("application_guides")

# 검색
results = guides_collection.query(
    query_texts=["고객 문의 개인정보"],
    n_results=3
)
```

### 2. 더 많은 가이드라인 추가

```bash
# 개보위 가이드 추가
cp ~/Downloads/개보위_*.pdf data/raw_guidelines/

# 공정위 가이드 추가
cp ~/Downloads/공정위_*.pdf data/raw_guidelines/

# 파이프라인 재실행
./scripts/guidelines/run_pipeline.sh
```

### 3. 품질 검증

```bash
# 리뷰 큐 확인
open data/staging/application_guides/review_queue.csv

# 낮은 신뢰도 항목 수동 수정
# (JSONL 파일 직접 편집 후 재실행)
```

---

## 📚 더 자세한 정보

- **전체 가이드**: [README.md](README.md)
- **아키텍처**: [GUIDELINE_PROCESSING_ARCHITECTURE.md](../../GUIDELINE_PROCESSING_ARCHITECTURE.md)
- **구현 요약**: [GUIDELINES_IMPLEMENTATION_SUMMARY.md](../../GUIDELINES_IMPLEMENTATION_SUMMARY.md)

---

**Happy RAG building!** 🚀

질문이나 이슈는 GitHub Issues에 등록해주세요.
