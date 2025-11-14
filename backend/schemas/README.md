# 스키마 정의 (Interface Contract)

이 디렉토리는 PII 마스킹 시스템의 데이터 계약(Contract)을 정의합니다.

## 파일 구조

```
schemas/
├── pii_analysis_request.schema.json   # VectorDB 검색 + LLM 분석 요청
├── masking_decision.schema.json       # LLM 마스킹 결정 응답
├── guideline.schema.json              # VectorDB에 저장되는 가이드라인
└── llm_prompt_template.json           # LLM 프롬프트 템플릿
```

## 1. PII Analysis Request

**파일**: `pii_analysis_request.schema.json`

**용도**: 프론트엔드 → 백엔드 API 요청 시 사용

**주요 필드**:
- `email_id`: 이메일 고유 식별자
- `detected_pii[]`: 자동 탐지된 PII 목록
  - `pii_id`, `type`, `value`, `position`, `confidence`
- `context`: 이메일 컨텍스트
  - `sender_type`, `receiver_type`, `purpose`, `regulations`
- `metadata`: 이메일 메타데이터
  - `timestamp`, `has_attachments`, `user_id`, `ip_address`

**예시**:
```json
{
  "email_id": "email_20250114_001",
  "email_subject": "신규 고객 계약 정보 전달",
  "detected_pii": [
    {
      "pii_id": "pii_0",
      "type": "email",
      "value": "hong@customer.com",
      "position": {"start": 100, "end": 118},
      "confidence": 0.98
    }
  ],
  "context": {
    "sender_type": "internal",
    "receiver_type": "external",
    "purpose": ["contract"],
    "regulations": ["PIPA"]
  },
  "metadata": {
    "timestamp": "2025-01-14T10:30:00Z",
    "has_attachments": false
  }
}
```

## 2. Masking Decision

**파일**: `masking_decision.schema.json`

**용도**: 백엔드 API → 프론트엔드 응답 시 사용

**주요 필드**:
- `email_id`: 이메일 고유 식별자
- `decisions`: PII별 마스킹 결정 (키: `pii_id`)
  - `should_mask`, `masking_method`, `masked_value`, `reason`, `risk_level`, `confidence`
- `summary`: 마스킹 결정 요약 (사람이 읽을 수 있는 형태)
- `relevant_guidelines[]`: 참고한 가이드라인 목록
- `analysis_metadata`: 분석 메타데이터

**마스킹 방법**:
- `full`: 완전 마스킹 (예: `***`)
- `partial`: 부분 마스킹 (예: `ho***@customer.com`)
- `hash`: 해시 (예: `[HASHED]`)
- `redact`: 삭제 (예: `[REDACTED]`)
- `none`: 마스킹 안함

**예시**:
```json
{
  "email_id": "email_20250114_001",
  "decisions": {
    "pii_0": {
      "pii_id": "pii_0",
      "type": "email",
      "value": "hong@customer.com",
      "should_mask": true,
      "masking_method": "partial",
      "masked_value": "ho***@customer.com",
      "reason": "외부 전송 시 이메일 부분 마스킹 권장 (PIPA 제17조)",
      "confidence": 0.95,
      "risk_level": "medium",
      "guideline_ids": ["GUIDE_PIPA_017"]
    }
  },
  "summary": "외부 전송으로 분류되어, 4개 개인정보 중 3개를 마스킹하도록 권장합니다.",
  "relevant_guidelines": [
    {
      "guide_id": "GUIDE_PIPA_017",
      "scenario": "외부 전송 시 개인정보 최소화",
      "directive": "필요한 최소한의 개인정보만 제공",
      "relevance_score": 0.92
    }
  ]
}
```

## 3. Guideline Schema

**파일**: `guideline.schema.json`

**용도**: VectorDB에 저장되는 가이드라인 데이터

**주요 필드**:
- `guide_id`: 가이드라인 고유 ID (예: `GUIDE_PIPA_017`)
- `scenario`: 적용 시나리오
- `actionable_directive`: 실행 가능한 지시문
- `source_document`: 출처 문서 (예: 개인정보보호법, GDPR)
- `pii_types[]`: 적용되는 PII 유형
- `masking_recommendation`: 마스킹 권장 수준 (`required`/`recommended`/`optional`)
- `risk_level`: 위반 시 위험도
- `tags[]`: 분류 태그

**예시**:
```json
{
  "guide_id": "GUIDE_PIPA_017",
  "scenario": "외부 제3자에게 개인정보를 제공하는 경우",
  "actionable_directive": "필요한 최소한의 개인정보만 제공하고, 주민등록번호 등 민감정보는 반드시 마스킹",
  "source_document": "개인정보보호법",
  "article_number": "제17조",
  "pii_types": ["jumin", "account", "email", "phone"],
  "masking_recommendation": "required",
  "risk_level": "high",
  "tags": ["external", "jumin", "account"]
}
```

## 4. LLM Prompt Template

**파일**: `llm_prompt_template.json`

**용도**: LLM에게 마스킹 결정을 요청할 때 사용하는 프롬프트 템플릿

**주요 필드**:
- `system_prompt`: LLM의 역할 정의
- `user_prompt_template`: 사용자 프롬프트 템플릿 (변수 포함)
- `output_format`: LLM 응답 형식
- `few_shot_examples[]`: Few-shot learning 예제

## 워크플로우

```
1. 프론트엔드: PII 탐지
   ↓
2. 프론트엔드 → 백엔드: POST /api/vectordb/analyze
   (pii_analysis_request.schema.json 형식)
   ↓
3. 백엔드: VectorDB 검색 (짧은 쿼리 사용)
   - "외부 전송 마스킹" 또는 "내부 전송 마스킹"
   - 이미 구축된 VectorDB에서 가이드라인 검색
   ↓
4. 백엔드: 마스킹 결정
   - Option A: 빠른 규칙 엔진 (기본값, 1-2초)
   - Option B: LLM 호출 (느림, 3-5초, 더 정확)
   ↓
5. 백엔드 → 프론트엔드: JSON 응답
   (masking_decision.schema.json 형식)
   ↓
6. 프론트엔드: 마스킹 항목 자동 선택 + 사용자 확인
```

## 성능 최적화

### 임베딩 캐싱
짧은 쿼리 템플릿만 사용하여 임베딩을 캐싱:
- `"외부 전송 마스킹"` (external)
- `"내부 전송 마스킹"` (internal)
- `"이메일 마스킹"` (mixed)

### 규칙 엔진 우선
- 기본값: 빠른 규칙 엔진 사용 (1-2초)
- 옵션: `use_llm=true` 파라미터로 LLM 호출 (3-5초)

### VectorDB 검색 최적화
- VectorDB는 이미 구축되어 있음 (가이드라인 임베딩 완료)
- 검색 시에는 짧은 쿼리만 임베딩 (10-20자)
- 상위 3-5개 가이드라인만 검색

## 검증

스키마 검증은 Pydantic 또는 jsonschema 라이브러리를 사용:

```python
import jsonschema

# 스키마 로드
with open('pii_analysis_request.schema.json') as f:
    schema = json.load(f)

# 데이터 검증
jsonschema.validate(instance=request_data, schema=schema)
```

## 버전 관리

스키마 변경 시 버전을 명시하고 호환성을 유지:
- 버전 형식: `v1`, `v2`, ...
- 파일명: `{name}.v{version}.schema.json`
- 현재 버전: `v1` (버전 접미사 생략)
