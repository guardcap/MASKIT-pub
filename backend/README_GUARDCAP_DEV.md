# GuardCap - 개인정보 필터링 엔진

GuardCap은 문서나 텍스트 내의 민감한 개인정보를 자동으로 탐지하고, 상황에 맞게 적절한 마스킹 처리를 수행하는 엔진입니다.

## 주요 기능

- 개인정보 자동 탐지 (NER 기반)
- 상황 기반 마스킹 결정 (RAG + LLM)
- 정책/규정 기반 처리
- 마스킹 자동화

## 시작하기

### 요구사항

```bash
pip install -r requirements.txt
```

### 환경 설정

```python
# config.py에서 설정 가능
OLLAMA_MODEL = "llama3"  # 사용할 LLM 모델
```

## API 엔드포인트

### Base URL
```
http://localhost:8000/api/v1
```

### 엔드포인트

#### 1. 텍스트 분석
```http
POST /analyzer/analyze/text
```
텍스트에서 개인정보를 탐지합니다.

**Request Body:**
```json
{
    "text_content": "분석할 텍스트 내용",
    "user_request": "default",
    "ocr_data": {} // 선택적 OCR 좌표 데이터
}
```

**Response:**
```json
{
    "full_text": "원본 텍스트",
    "pii_entities": [
        {
            "text": "010-1234-5678",
            "type": "PHONE_NUMBER",
            "score": 0.99,
            "start_char": 0,
            "end_char": 13,
            "coordinates": [
                {
                    "pageIndex": 1,
                    "bbox": [100, 150, 200, 170],
                    "field_text": "010-1234-5678"
                }
            ]
        }
    ]
}
```

#### 2. PDF 마스킹
```http
POST /process/masking/pdf
```
PDF 파일 내의 개인정보를 마스킹 처리합니다.

**Request Body:**
```json
[
    {
        "filename": "example.pdf",
        "pii_type": "PHONE_NUMBER",
        "text": "010-1234-5678",
        "pageIndex": 1,
        "instance_index": 0,
        "bbox": [100, 150, 200, 170]
    }
]
```

**Response:**
```json
{
    "status": "success",
    "masked_files": {
        "example.pdf": "/uploads/masked_example.pdf"
    }
}
```

#### 3. 파일 업로드
```http
POST /files/upload
```

#### 4. OCR 처리
```http
POST /ocr/process
```

## 라이브러리 사용법

### 1. 개인정보 탐지 및 마스킹

```python
from utils.entity import Entity, EntityGroup
from utils.filtering_LLM.models import Meta
from utils.filtering_LLM.core import run

# 1) 메타데이터 설정
meta = Meta(
    sender_team="고객서비스팀",
    sender_role="상담사",
    recipient_domain="external",
    purpose="민원처리",
    audience="external",
    jurisdiction="KR"
)

# 2) 탐지된 민감정보
entity_group = EntityGroup([
    Entity(
        entity="PHONE_NUMBER",
        score=0.99,
        word="010-1234-5678",
        start=15,
        end=28,
        pageIndex=1
    ),
    Entity(
        entity="EMAIL",
        score=0.98,
        word="user@example.com",
        start=45,
        end=68,
        pageIndex=1
    )
])

# 3) 마스킹 처리 실행
def get_context_pack(queries, filters):
    # RAG 시스템 연동
    ...

masked_group = run(meta, entity_group, get_context_pack)

# 4) 결과 확인
for entity in masked_group.entities:
    print(f"원본: {entity.word}")
    print(f"마스킹 방식: {entity.masking_method}")
    print(f"마스킹 옵션: {entity.masking_format}")
```

### 요청/응답 구조

#### 1. 메타데이터 (Meta)

```json
{
    "sender_team": "고객서비스팀",
    "sender_role": "상담사",
    "recipient_domain": "external",
    "recipient_role": "고객",
    "purpose": "민원처리",
    "audience": "external",
    "jurisdiction": "KR"
}
```

#### 2. 민감정보 (Entity)

```json
{
    "entity": "PHONE_NUMBER",
    "score": 0.99,
    "word": "010-1234-5678",
    "start": 15,
    "end": 28,
    "pageIndex": 1,
    "bbox": [100, 150, 200, 170]
}
```

#### 3. 마스킹 결과

```json
{
    "entity": "PHONE_NUMBER",
    "word": "010-1234-5678",
    "masking_method": "mask_partial",
    "masking_format": {
        "keep_last": 4,
        "separator": "-",
        "mask_char": "*"
    }
}
```

### 마스킹 방식

- `keep`: 원본 유지
- `mask_partial`: 부분 마스킹
- `mask_full`: 전체 마스킹
- `generalize`: 일반화
- `pseudonymize`: 가명화
- `tokenize`: 토큰화
- `hash`: 해시처리

### 공개 범위 (audience)

- `external`: 외부 공개
- `internal_public`: 내부 공개
- `internal_limited`: 제한적 내부 공개

## 주의사항

1. **보안 정책 준수**
   - 외부 공개 시 더 엄격한 마스킹 적용
   - 불확실한 경우 보수적 처리

2. **일관성**
   - 동일 유형의 정보는 일관되게 처리
   - 정책 기반 결정 우선

3. **성능**
   - RAG 시스템 연동 필요
   - LLM 서비스 필요

## 라이선스

Copyright © 2025 GuardCap
