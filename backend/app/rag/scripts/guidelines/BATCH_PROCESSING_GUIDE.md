# Raw Guidelines 배치 처리 가이드

## 📋 개요

`raw_guidelines` 디렉토리의 모든 PDF 가이드라인을 자동으로 처리하여 VectorDB에 추가합니다.

**지원:**
- ✅ 46개 PDF 파일 자동 처리
- ✅ 자동 발행 기관 감지 (개인정보보호위원회, 금융보안원, KISA 등)
- ✅ Rate Limit 방지 (배치 간 딜레이)
- ✅ 타임스탬프 기반 고유 파일명
- ✅ 상세 처리 로그 및 리포트

---

## 🚀 빠른 시작

### 1단계: 환경 준비

```bash
cd guardcap-rag

# .env 파일이 있는지 확인
cat .env | grep OPENAI_API_KEY

# 없으면 설정
echo "OPENAI_API_KEY=sk-proj-..." >> .env
```

### 2단계: 배치 처리 실행

```bash
# 방법 1: 쉘 스크립트 실행 (권장)
./scripts/guidelines/run_batch_processing.sh

# 방법 2: Python 직접 실행
python scripts/guidelines/batch_process_raw_pdfs.py
```

### 3단계: 결과 확인

```bash
# 로그 보기
tail -f batch_processing.log

# 처리 리포트 확인
cat data/staging/batch_processing_report_*.json | jq .

# VectorDB 통계 확인
sqlite3 data/chromadb/application_guides/chroma.sqlite3 \
  "SELECT COUNT(*) FROM documents;"
```

---

## 📊 처리 과정

### 단계별 흐름

```
Raw Guidelines (46 PDF files)
    ↓
[1] 발행 기관 자동 감지
    ↓
[2] PDF → Markdown (OpenAI Vision + Zerox)
    ↓
[3] 구조화 (Pydantic 검증)
    ↓
[4] JSONL 저장 (타임스탐프 파일명)
    ↓
[5] 모든 파일 병합
    ↓
[6] VectorDB 빌드
    ↓
Result: VectorDB with 1000+ Application Guides
```

### 각 단계의 시간

| 단계 | 처리 | 배치 크기 | 소요 시간 |
|------|------|---------|---------|
| PDF 처리 | 46 PDF | 1개씩 | ~60-90분 |
| Rate Limit 딜레이 | - | 3초/PDF | ~3분 |
| VectorDB 빌드 | 1000+ 가이드 | 50개씩 | ~5-10분 |
| **총 합계** | - | - | **70-105분** |

> **TIP**: 처음 실행 시 1-2시간 소요. 이후 추가 PDF만 처리 시 20-30분.

---

## 🔧 커스터마이징

### 환경 변수 설정 (.env)

```bash
# Vision 모델 선택 (기본: gpt-4o-mini)
OPENAI_VISION_MODEL=gpt-4o-mini  # 빠름, 저렴

# 배치 간 딜레이 (기본: 3초)
PDF_BATCH_DELAY=3                 # Rate Limit 방지

# OpenAI API 키
OPENAI_API_KEY=sk-proj-...
```

### 발행 기관 자동 감지

[batch_process_raw_pdfs.py:47-60](batch_process_raw_pdfs.py#L47-L60)의 `AuthorityDetector` 클래스에서 설정:

```python
AUTHORITY_KEYWORDS = {
    "개인정보보호위원회": ["개인정보", "보호"],
    "금융보안원": ["금융", "보안"],
    "KISA": ["KISA", "정보보호"],
    "공정거래위원회": ["공정거래"],
    # ... 추가 기관
}
```

파일명에 키워드가 포함되면 자동으로 감지됩니다.

---

## 📝 파일별 처리 예시

### 예시 1: 작은 파일 (< 5MB)

```
입력: 개인정보 보호 가이드라인 (온라인 경품행사) (2023. 5.).pdf (2.3MB)
↓
발행 기관: 개인정보보호위원회 (자동 감지)
↓
추출된 가이드: 12개
↓
저장: application_guides_20250111_143025_batch_01.jsonl
```

### 예시 2: 큰 파일 (> 10MB)

```
입력: 금융보안원-금융분야 보안 가이드.pdf (43MB)
↓
발행 기관: 금융보안원 (자동 감지)
↓
자동 분할: 43MB ÷ 10MB = 5개 배치
  - batch_0000_0010.pdf (10 pages)
  - batch_0010_0020.pdf (10 pages)
  - batch_0020_0030.pdf (10 pages)
  - batch_0030_0040.pdf (10 pages)
  - batch_0040_0050.pdf (10 pages)
↓
각 배치 처리 (3초 딜레이)
↓
추출된 가이드: 156개
↓
저장: application_guides_20250111_143025_batch_07.jsonl
```

---

## 📊 출력 파일 구조

### 1. JSONL 파일 (data/staging/)

```
application_guides_20250111_143025_batch_01.jsonl
application_guides_20250111_143025_batch_02.jsonl
...
application_guides_20250111_143025_batch_46.jsonl
```

각 파일 형식:
```json
{
  "guide_id": "GUIDE-001-CUSTOMER-INQUIRY",
  "source_authority": "개인정보보호위원회",
  "source_document": "개인정보 보호 가이드라인 (온라인 경품행사) (2023. 5.).pdf",
  "scenario": "외부 고객이 제품 문의를 위해 먼저 이메일을 보낸 상황",
  "context": {...},
  "interpretation": "...",
  "actionable_directive": "...",
  "keywords": [...],
  "related_law_ids": [...],
  "confidence_score": 0.85,
  ...
}
```

### 2. 처리 리포트 (data/staging/)

```
batch_processing_report_20250111_143025.json
```

형식:
```json
{
  "timestamp": "20250111_143025",
  "total_files": 46,
  "successful": 45,
  "failed": 1,
  "no_data": 0,
  "total_guides_extracted": 1247,
  "vectordb": {
    "status": "success",
    "total_guides": 5832  # 기존 + 신규
  },
  "files": [
    {
      "file": "개인정보 보호 가이드라인 (온라인 경품행사) (2023. 5.).pdf",
      "status": "success",
      "guides_count": 12,
      "output_file": "application_guides_20250111_143025_batch_01.jsonl",
      "authority": "개인정보보호위원회",
      "file_size_mb": 2.3
    },
    ...
  ]
}
```

### 3. 처리 로그 (batch_processing.log)

```
2025-01-11 14:30:25 - INFO - Initialized batch processor
2025-01-11 14:30:25 - INFO - Raw directory: data/raw_guidelines
2025-01-11 14:30:25 - INFO - Output directory: data/staging
2025-01-11 14:30:25 - INFO - Vision model: gpt-4o-mini

2025-01-11 14:30:26 - INFO - Starting batch processing of 46 PDF files...
2025-01-11 14:30:30 - INFO - [1/46] Processing: 개인정보 보호 가이드라인 (온라인 경품행사) (2023. 5.).pdf (2.30MB)
2025-01-11 14:30:30 - INFO - Detected authority: 개인정보보호위원회
2025-01-11 14:31:15 - INFO - ✅ Extracted 12 guides
2025-01-11 14:31:15 - INFO - 💾 Saved to: application_guides_20250111_143025_batch_01.jsonl

...

2025-01-11 16:35:10 - INFO - Building VectorDB from all processed guides...
2025-01-11 16:35:10 - INFO - Loading 1247 guides from staging files
2025-01-11 16:40:15 - INFO - ✅ VectorDB updated with 5832 guides
```

---

## 🔍 모니터링

### 실시간 진행 상황 확인

```bash
# 로그 스트리밍
tail -f batch_processing.log

# 처리 중인 파일 확인
watch -n 5 'ls -l data/staging/*.jsonl | tail -5'

# VectorDB 크기 실시간 확인
watch -n 10 'sqlite3 data/chromadb/application_guides/chroma.sqlite3 "SELECT COUNT(*) FROM documents;"'
```

### CPU/Memory 모니터링

```bash
# macOS
top -o %MEM  # 메모리 사용량 기준 정렬

# Linux
htop
```

---

## 🚨 트러블슈팅

### "Rate limit reached" 에러

**증상:**
```
ERROR: litellm.RateLimitError: Rate limit reached for gpt-4o-mini
```

**해결책:**
```bash
# .env 파일에서 딜레이 증가
PDF_BATCH_DELAY=5  # 3초 → 5초

# 또는 배치 크기 감소
PDF_BATCH_SIZE=5   # 10 → 5
```

### "OPENAI_API_KEY not set" 에러

**해결책:**
```bash
# .env 파일 확인
cat .env | grep OPENAI_API_KEY

# 없으면 설정
echo "OPENAI_API_KEY=sk-proj-YOUR_KEY" >> .env
```

### 특정 파일에서 계속 실패

**원인:** PDF 손상 또는 특수 형식

**해결책:**
1. 로그에서 실패한 파일 확인
2. 해당 파일 검토
3. 필요시 raw_guidelines에서 파일 제거 또는 변환

```bash
# 에러 로그만 보기
grep "Error\|failed" batch_processing.log
```

### VectorDB 빌드 실패

**증상:**
```
ERROR: Error building VectorDB
```

**해결책:**
```bash
# VectorDB 재초기화
rm -rf data/chromadb/application_guides

# 배치 처리 재실행
python scripts/guidelines/batch_process_raw_pdfs.py
```

---

## 📈 성능 최적화

### 1. Vision 모델 선택

**gpt-4o-mini (권장 - 기본값):**
- 속도: 빠름 (2-3배)
- 비용: 저렴
- 정확도: 충분함

**gpt-4o (고품질 필요 시):**
- 속도: 느림
- 비용: 비쌈 (15배)
- 정확도: 매우 높음

```bash
# .env 파일 수정
OPENAI_VISION_MODEL=gpt-4o  # 또는 gpt-4o-mini
```

### 2. 배치 딜레이 조정

```bash
# Free tier (낮은 TPM 제한)
PDF_BATCH_DELAY=5

# Tier 1 (기본)
PDF_BATCH_DELAY=3

# Tier 2+ (높은 TPM 제한)
PDF_BATCH_DELAY=1
```

### 3. 동시 처리 불가 (안정성 우선)

현재: 순차 처리 (한 번에 1개 파일)
- 장점: 안정적, Rate Limit 걱정 없음
- 단점: 느림

향후: 병렬 처리 (여러 파일 동시 처리) 가능

---

## 🎯 다음 단계

### 처리 완료 후

1. **검색 테스트**
   ```bash
   streamlit run streamlit_app/Home.py
   # → 🔍 Search Guidelines 페이지에서 검색
   ```

2. **품질 검증**
   ```bash
   # 낮은 신뢰도 항목 확인
   cat data/staging/batch_processing_report_*.json | jq '.files[] | select(.confidence_score < 0.8)'
   ```

3. **추가 정제 (선택사항)**
   ```bash
   python scripts/guidelines/validate_and_dedup.py
   ```

---

## 📞 지원

### 추가 문서
- [RATE_LIMIT_SOLUTION.md](../../../RATE_LIMIT_SOLUTION.md) - Rate Limit 해결 방법
- [STREAMLIT_INTEGRATION_COMPLETE.md](../../../STREAMLIT_INTEGRATION_COMPLETE.md) - Streamlit UI 사용법

### 로그 위치
- `batch_processing.log` - 상세 처리 로그
- `data/staging/batch_processing_report_*.json` - 처리 리포트

---

**작성일**: 2025-01-11
**버전**: v1.0
**상태**: ✅ 사용 가능
