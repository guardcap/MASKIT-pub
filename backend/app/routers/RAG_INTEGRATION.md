# RAG 통합 가이드

## 📋 개요

`analyzer.py`에 RAG(Retrieval-Augmented Generation) 기반 마스킹 결정 시스템이 통합되었습니다.

## 🔧 변경 사항

### 1. 새로운 엔드포인트

#### **기존**: `/api/v1/analyzer/analyze/text`
- PII 탐지만 수행
- 마스킹 결정 없음

#### **신규**: `/api/v1/analyzer/analyze/text-with-rag`
- PII 탐지 + RAG 기반 마스킹 결정
- 법령/가이드 참조 정보 포함

### 2. 추가된 모듈

#### `backend/app/utils/rag_integration.py`
- RAG 기반 마스킹 결정 엔진
- ChromaDB를 사용한 법령/정책 검색
- 가이드 우선 → 법률 참조 → 기본 규칙 순으로 결정

## 📡 API 사용법

### 요청 예시

```bash
curl -X POST "http://localhost:8000/api/v1/analyzer/analyze/text-with-rag" \
  -H "Content-Type: application/json" \
  -d '{
    "text_content": "고객 홍길동님의 주민등록번호는 123456-1234567이고 연락처는 010-1234-5678입니다.",
    "email_context": {
      "sender_type": "internal",
      "receiver_type": "external_customer",
      "purpose": "고객 문의 답변",
      "has_consent": false
    },
    "enable_rag": true
  }'
```

### 응답 예시

```json
{
  "full_text": "고객 홍길동님의 주민등록번호는 123456-1234567이고 연락처는 010-1234-5678입니다.",
  "pii_entities": [
    {
      "text": "홍길동",
      "type": "NAME",
      "score": 0.95,
      "start_char": 3,
      "end_char": 6,
      "masking_decision": {
        "action": "mask_partial",
        "reasoning": "가이드 지침: 고객명은 부분 마스킹 | 기본 규칙: 외부 전송 시 마스킹 필요",
        "referenced_guides": ["guide_001"],
        "referenced_laws": ["law_002"],
        "confidence": 0.85
      }
    },
    {
      "text": "123456-1234567",
      "type": "RESIDENT_ID",
      "score": 0.98,
      "start_char": 17,
      "end_char": 31,
      "masking_decision": {
        "action": "block",
        "reasoning": "법률: 주민등록번호 수집/전송 제한 | 기본 규칙: RESIDENT_ID는 block 필요",
        "referenced_guides": [],
        "referenced_laws": ["law_003"],
        "confidence": 0.95
      }
    },
    {
      "text": "010-1234-5678",
      "type": "PHONE_NUMBER",
      "score": 0.92,
      "start_char": 38,
      "end_char": 51,
      "masking_decision": {
        "action": "mask_partial",
        "reasoning": "가이드 지침: 연락처는 부분 마스킹 가능",
        "referenced_guides": ["guide_002"],
        "referenced_laws": [],
        "confidence": 0.8
      }
    }
  ],
  "rag_enabled": true,
  "warnings": []
}
```

## 🎯 마스킹 액션 종류

| 액션 | 설명 | 예시 |
|------|------|------|
| `keep` | 마스킹하지 않음 | 홍길동 → 홍길동 |
| `mask_partial` | 부분 마스킹 | 홍길동 → 홍*동 |
| `mask_full` | 전체 마스킹 | 123456 → ****** |
| `block` | 완전 차단 (전송 금지) | 123456-1234567 → [차단됨] |

## 🔍 RAG 결정 우선순위

1. **애플리케이션 가이드** (최우선)
   - 조직 내부 정책 및 지침
   - 시나리오별 구체적 행동 지침

2. **법률/규제**
   - 개인정보보호법
   - 신용정보법 등

3. **기본 규칙** (폴백)
   - 민감정보 타입별 기본 정책

## 🛠️ 맥락(Context) 정보

### `email_context` 파라미터

```json
{
  "sender_type": "internal | external_customer | external_partner | external_vendor",
  "receiver_type": "internal | external_customer | external_partner | external_vendor",
  "purpose": "고객 문의 답변 | 마케팅 | 계약서 전달 | ...",
  "has_consent": true | false
}
```

### 맥락별 마스킹 정책 예시

| 송신자 → 수신자 | 동의 여부 | 정책 |
|----------------|----------|------|
| internal → external_customer | ❌ | 엄격한 마스킹 |
| internal → external_customer | ✅ | 완화된 정책 |
| internal → internal | - | 최소 마스킹 |
| external_vendor → internal | - | 보안 강화 |

## 🚨 Fallback 동작

RAG 시스템이 초기화 실패하거나 ChromaDB를 찾을 수 없는 경우:

1. 규칙 기반 폴백 정책 적용
2. `rag_enabled: false` 반환
3. `warnings` 배열에 경고 메시지 포함

```json
{
  "rag_enabled": false,
  "warnings": ["RAG 시스템이 초기화되지 않음 - 규칙 기반 폴백 사용"]
}
```

## 📂 파일 구조

```
backend/app/
├── routers/
│   └── analyzer.py              # RAG 통합된 분석 API
├── utils/
│   ├── rag_integration.py       # RAG 마스킹 결정 엔진
│   └── recognizer_engine.py     # PII 탐지 엔진
└── rag/
    ├── agent/
    │   └── retrievers.py        # HybridRetriever (ChromaDB)
    └── data/
        ├── chromadb/            # VectorDB
        └── staging/             # JSONL 가이드
```

## 🧪 테스트 방법

### 1. RAG 시스템 상태 확인

```bash
# ChromaDB 데이터 확인
ls -la backend/app/rag/data/chromadb/application_guides/

# JSONL 가이드 확인
ls -la backend/app/rag/data/staging/*.jsonl
```

### 2. 간단한 테스트

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/analyzer/analyze/text-with-rag",
    json={
        "text_content": "테스트 텍스트: 홍길동, 010-1234-5678",
        "enable_rag": True
    }
)

print(response.json())
```

### 3. 맥락 정보 포함 테스트

```python
response = requests.post(
    "http://localhost:8000/api/v1/analyzer/analyze/text-with-rag",
    json={
        "text_content": "계약서 발송: 고객명 김철수, 계좌번호 123-456-789",
        "email_context": {
            "sender_type": "internal",
            "receiver_type": "external_customer",
            "purpose": "계약서 전달",
            "has_consent": True
        },
        "enable_rag": True
    }
)

print(response.json())
```

## 🔧 문제 해결

### RAG가 초기화되지 않는 경우

1. ChromaDB 경로 확인:
   ```bash
   ls backend/app/rag/data/chromadb/application_guides/
   ```

2. JSONL 가이드 파일 확인:
   ```bash
   ls backend/app/rag/data/staging/*.jsonl
   ```

3. 필요한 Python 패키지 설치:
   ```bash
   pip install chromadb sentence-transformers konlpy rank-bm25
   ```

### 경로 문제 발생 시

모든 경로가 절대 경로로 수정되었습니다:
- `background_tasks.py`: BASE_DIR 기반 절대 경로
- `policy/routes.py`: BASE_DIR 기반 절대 경로
- `rag_integration.py`: BASE_DIR 기반 절대 경로

더 이상 루트에 `app/rag/data` 디렉토리가 잘못 생성되지 않습니다.

## 📝 향후 개선 사항

1. **LLM 추론 통합**: 현재는 규칙 기반이지만, LLM을 활용한 고도화된 추론 가능
2. **캐싱**: 동일한 PII 타입/맥락에 대한 결정 캐싱
3. **A/B 테스트**: RAG vs 규칙 기반 비교
4. **사용자 피드백**: 마스킹 결정에 대한 사용자 수정 및 학습

## 🤝 기여

질문이나 개선 사항은 팀 슬랙 채널 또는 이슈 트래커에 등록해주세요.
