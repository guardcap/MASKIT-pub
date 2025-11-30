---
layout: default
title: 탐지 가능한 엔티티
nav_order: 5
---

# PII 엔티티 (탐지 대상)

## 개요

Guardcap은 텍스트에서 개인식별정보(PII: Personally Identifiable Information)를 자동으로 탐지합니다.
규칙 기반(정규표현식)과 NER(Named Entity Recognition) 기반의 이중 엔진을 통해 높은 정확도의 PII 탐지를 제공합니다.

---

## 1. 탐지 아키텍처

### 이중 엔진 구조

```
입력 텍스트
    ↓
┌───────────────────────────────────────┐
│    RecognizerRegistry (규칙 기반)      │ ← 정규표현식 패턴 매칭
├───────────────────────────────────────┤
│    NerEngine (NER 기반)                │ ← 기계학습 기반 인식
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│ AnalyzerEngine (통합 및 중복 제거)     │
├───────────────────────────────────────┤
│ - 겹치는 엔티티 병합                    │
│ - 신뢰도 점수 기반 우선순위 결정       │
│ - 위치 기반 정렬                      │
└───────────────────────────────────────┘
    ↓
EntityGroup (최종 결과)
```

---

## 2. 탐지 가능한 엔티티 타입

### 2.1 한국 신분증 정보

#### ResidentID (주민등록번호)
- **패턴**: `XXXXXX-XXXXXXX` (13자리)
- **예시**: `900101-1234567`
- **인식기**: `RecognizerRegistry` (규칙 기반)
- **신뢰도**: 매우 높음 (정규표현식)

#### DriverLicense (운전면허번호)
- **패턴**: `XX-XX-XXXXXX` (12자리)
- **예시**: `12-34-567890`
- **인식기**: `RecognizerRegistry` (규칙 기반)
- **신뢰도**: 매우 높음

#### Passport (여권번호)
- **패턴**: 영문자 + 숫자 조합
- **예시**: `M12345678`
- **인식기**: `RecognizerRegistry` (규칙 기반)
- **신뢰도**: 높음

### 2.2 금융 정보

#### CardNumber (신용카드번호)
- **패턴**: `XXXX-XXXX-XXXX-XXXX` (16자리) 또는 `XXXXXXXXXXXX`
- **예시**: `1234-5678-9012-3456`
- **인식기**: `RecognizerRegistry` (규칙 기반)
- **신뢰도**: 매우 높음
- **검증**: Luhn 알고리즘 적용 가능

#### BankAccount (계좌번호)
- **패턴**: 은행별 계좌 형식
- **예시**: `123-456-789012`, `1234567890`
- **인식기**: `RecognizerRegistry` (규칙 기반)
- **신뢰도**: 높음
- **형식**: 은행마다 상이함

### 2.3 연락처 정보

#### PhoneNumber (휴대폰번호)
- **패턴**:
  - `010-XXXX-XXXX`
  - `02-XXXX-XXXX` (지역번호)
  - `0XX-XXXX-XXXX` (특수번호)
- **예시**: `010-1234-5678`, `02-1234-5678`
- **인식기**: `RecognizerRegistry` (규칙 기반)
- **신뢰도**: 매우 높음

#### Email (이메일주소)
- **패턴**: `user@domain.com`
- **예시**: `john.doe@example.com`
- **인식기**: `RecognizerRegistry` (규칙 기반)
- **신뢰도**: 매우 높음

### 2.4 네트워크 정보

#### IPAddress (IP주소)
- **패턴**:
  - IPv4: `XXX.XXX.XXX.XXX`
  - IPv6: 16진수 형식
- **예시**: `192.168.1.1`, `2001:0db8::1`
- **인식기**: `RecognizerRegistry` (규칙 기반)
- **신뢰도**: 높음

#### MACAddress (MAC주소)
- **패턴**: `XX:XX:XX:XX:XX:XX` 또는 `XX-XX-XX-XX-XX-XX`
- **예시**: `00:1A:2B:3C:4D:5E`
- **인식기**: `RecognizerRegistry` (규칙 기반)
- **신뢰도**: 높음

### 2.5 위치정보

#### GPS (GPS좌표)
- **패턴**: 위도/경도 좌표
- **예시**: `37.4979° N, 127.0276° E`
- **인식기**: `RecognizerRegistry` (규칙 기반)
- **신뢰도**: 높음

### 2.6 기타 정보 (NER 기반)

#### NAME (인물명)
- **예시**: `김철수`, `John Smith`
- **인식기**: `NerEngine` (기계학습 기반)
- **신뢰도**: 중간~높음 (문맥에 따라 변함)

#### ORGANIZATION (단체명)
- **예시**: `한국은행`, `Microsoft Corp`
- **인식기**: `NerEngine` (기계학습 기반)
- **신뢰도**: 중간~높음

#### LOCATION (지역명)
- **예시**: `서울`, `New York`
- **인식기**: `NerEngine` (기계학습 기반)
- **신뢰도**: 중간~높음

---

## 3. Entity 데이터 구조

### Entity 클래스

```python
class Entity:
    entity: str              # 엔티티 타입 (예: "EMAIL", "PHONE_NUMBER")
    score: float             # 신뢰도 점수 (0.0 ~ 1.0)
    word: str                # 인식된 텍스트
    start: int               # 텍스트 내 시작 위치
    end: int                 # 텍스트 내 종료 위치
    pageIndex: int           # 페이지 번호 (OCR 결과)
    bbox: Tuple[int, int, int, int]  # 바운딩박스 (x1, y1, x2, y2)
```

### EntityGroup 클래스

```python
class EntityGroup:
    entities: List[Entity]   # 엔티티 목록

    # 메서드
    filter_by_type(entity_type: str) → List[Entity]
    group_by_page() → Dict[int, List[Entity]]
    to_dict() → List[Dict]
```

---

## 4. 탐지 엔진 상세 설명

### 4.1 RecognizerRegistry (규칙 기반)

**특징:**
- 정규표현식(Regex) 패턴 매칭
- 빠른 속도, 높은 정확도
- 거짓 양성(False Positive) 낮음

**포함된 인식기:**

| 인식기 | 담당 엔티티 | 패턴 유형 |
|--------|-----------|---------|
| EmailRecognizer | EMAIL | 정규표현식 |
| PhoneRecognizer | PHONE_NUMBER | 정규표현식 |
| ResidentIDRecognizer | RESIDENT_ID | 정규표현식 |
| CardNumberRecognizer | CARD_NUMBER | 정규표현식 |
| BankAccountRecognizer | ACCOUNT_NUMBER | 정규표현식 |
| DriverLicenseRecognizer | DRIVER_LICENSE | 정규표현식 |
| PassportRecognizer | PASSPORT | 정규표현식 |
| IPRecognizer | IP_ADDRESS | 정규표현식 |
| GPSRecognizer | GPS | 정규표현식 |
| MACRecognizer | MAC_ADDRESS | 정규표현식 |

**사용 예시:**

```python
from app.utils.recognizer_registry import RecognizerRegistry

registry = RecognizerRegistry()
registry.load_predefined_recognizers()

# 텍스트 분석
entity_group = registry.regex_analyze("제 번호는 010-1234-5678 입니다")

# 결과
for entity in entity_group.entities:
    print(f"{entity.entity}: {entity.word} (신뢰도: {entity.score})")
    # 출력: PHONE_NUMBER: 010-1234-5678 (신뢰도: 1.0)
```

### 4.2 NerEngine (NER 기반)

**특징:**
- 기계학습 기반 (Named Entity Recognition)
- 문맥을 고려한 인식
- 명시적 패턴이 없는 정보도 인식 가능
- 약간의 거짓 양성 가능

**모델:**
- spacy 기반 NER 모델
- 다국어 지원 (영어, 한국어 등)

**사용 예시:**

```python
from app.utils.ner.NER_engine import NerEngine

nlp_engine = NerEngine()

# 텍스트 분석
entity_group = nlp_engine.ner_analyze("김철수는 삼성전자의 개발자입니다")

# 결과
for entity in entity_group.entities:
    print(f"{entity.entity}: {entity.word} (신뢰도: {entity.score})")
    # 출력: PERSON: 김철수 (신뢰도: 0.95)
    # 출력: ORGANIZATION: 삼성전자 (신뢰도: 0.92)
```

### 4.3 AnalyzerEngine (통합 엔진)

**역할:**
1. 규칙 기반 결과 수집
2. NER 기반 결과 수집
3. 겹치는 엔티티 병합 (최적화)
4. 중복 제거
5. 위치 기반 정렬

**병합 알고리즘:**

```
두 엔진 결과에서 겹치는 엔티티 발견:
├─ 같은 타입 && 범위 겹침
│  ├─ 길이 비교: 긴 것 우선
│  ├─ 길이 같음: 신뢰도 높은 것 우선
│  └─ 결과: 우수한 엔티티 선택
└─ 겹치지 않음: 모두 포함
```

**사용 예시:**

```python
from app.utils.recognizer_engine import AnalyzerEngine

analyzer = AnalyzerEngine()

# 텍스트 분석
result = analyzer.analyze("010-1234-5678로 연락주세요")

# 결과 (규칙 + NER 통합)
for entity in result.entities:
    print(f"{entity.entity}: {entity.word} (신뢰도: {entity.score:.2f})")
```

---

## 5. OCR 데이터와의 통합

### 좌표 매핑

PII 탐지 시 OCR 데이터가 제공되면 다음과 같이 좌표를 매핑합니다:

```python
def find_text_coordinates_in_ocr(
    text: str,                    # 전체 텍스트
    start_pos: int,               # PII 시작 위치
    end_pos: int,                 # PII 종료 위치
    ocr_pages: List[Dict]         # OCR 페이지 데이터
) → List[Dict]:
    """
    반환 형식:
    [
        {
            "pageIndex": 0,
            "bbox": [x1, y1, x2, y2],
            "field_text": "감지된 텍스트",
            "vertices": [...]
        }
    ]
    """
```

### 좌표 매핑 흐름

```
1. PII 텍스트 위치 (start_pos, end_pos)
   ↓
2. OCR 필드와 비교
   ├─ 정확한 위치 매칭 확인
   ├─ 필드 내부 매칭 확인
   └─ 부분 매칭 확인
   ↓
3. BoundingPoly 좌표 추출
   ├─ 정점(vertices) 수집
   ├─ x, y 최솟값/최댓값 계산
   └─ 마진 추가 (2px)
   ↓
4. bbox 형식으로 변환
   [x_min, y_min, x_max, y_max]
```

---

## 6. 신뢰도 점수 (Confidence Score)

### 점수 범위

| 범위 | 신뢰도 | 설명 |
|------|--------|------|
| 0.95 ~ 1.0 | 매우 높음 | 정규표현식 정확 매칭, 확실한 PII |
| 0.80 ~ 0.95 | 높음 | NER 기반 고신뢰도, 거의 확실함 |
| 0.60 ~ 0.80 | 중간 | NER 기반 중간 신뢰도, 검토 필요 |
| < 0.60 | 낮음 | 거짓 양성 가능, 신중히 검토 필요 |

### 신뢰도 결정 요소

**규칙 기반 (RecognizerRegistry):**
- 정규표현식 정확 매칭 → 신뢰도 1.0
- 부분 매칭 → 신뢰도 0.85 ~ 0.95

**NER 기반 (NerEngine):**
- 모델 확률점수 그대로 사용 (0.0 ~ 1.0)
- 일반적으로 0.6 ~ 0.98 범위

---

## 7. 인식 성능 비교

### 규칙 기반 vs NER 기반

| 특성 | 규칙 기반 | NER 기반 |
|------|---------|---------|
| **정확도** | 매우 높음 | 높음 |
| **재현율** | 중간 | 높음 |
| **속도** | 매우 빠름 | 느림 (모델 추론) |
| **거짓 양성** | 거의 없음 | 있을 수 있음 |
| **거짓 음성** | 있을 수 있음 | 적음 |
| **명시적 패턴** | 필요 | 불필요 |
| **문맥 고려** | 없음 | 있음 |

### 예시: "010-5555-5555"를 이메일로 인식

```
텍스트: "Mr. John Smith, call me at 010-5555-5555"

❌ 규칙 기반만 사용:
   - PHONE_NUMBER 감지 (정확)
   - 숫자 패턴이 EMAIL처럼 보이지 않음

✓ NER 기반만 사용:
   - NAME (John Smith) 감지
   - 문맥상 "010-5555-5555"는 전화번호로 인식

✓✓ 통합 엔진 사용:
   - 규칙: PHONE_NUMBER (신뢰도 1.0)
   - NER: PHONE_NUMBER (신뢰도 0.92)
   - 결과: PHONE_NUMBER 하나만 반환 (최적화)
```

---

## 8. 실제 사용 예시

### 이메일 본문 분석

```python
from app.utils.recognizer_engine import recognize_pii_in_text

email_body = """
안녕하세요.

제 개인정보는 다음과 같습니다.
- 이름: 김철수
- 휴대폰: 010-1234-5678
- 이메일: kim.chulsu@company.com
- 계좌번호: 123-456-789012

감사합니다.
"""

result = recognize_pii_in_text(email_body)

# 결과
for pii in result["pii_entities"]:
    print(f"[{pii['type']}] {pii['text']} (신뢰도: {pii['score']:.2f})")
    print(f"  위치: {pii['start_char']} ~ {pii['end_char']}")
```

**출력:**
```
[PHONE_NUMBER] 010-1234-5678 (신뢰도: 1.00)
  위치: 45 ~ 57
[EMAIL] kim.chulsu@company.com (신뢰도: 1.00)
  위치: 63 ~ 85
[ACCOUNT_NUMBER] 123-456-789012 (신뢰도: 1.00)
  위치: 91 ~ 105
[PERSON] 김철수 (신뢰도: 0.96)
  위치: 28 ~ 31
```

### OCR 데이터와 함께 분석

```python
from app.utils.recognizer_engine import recognize_pii_in_text

ocr_data = {
    "full_text": "이름: 김철수\n전화: 010-1234-5678",
    "pages": [
        {
            "pageIndex": 0,
            "fields": [
                {
                    "text": "이름: 김철수",
                    "boundingPoly": {
                        "vertices": [
                            {"x": 100, "y": 100},
                            {"x": 200, "y": 100},
                            {"x": 200, "y": 120},
                            {"x": 100, "y": 120}
                        ]
                    }
                },
                {
                    "text": "전화: 010-1234-5678",
                    "boundingPoly": {
                        "vertices": [
                            {"x": 100, "y": 150},
                            {"x": 300, "y": 150},
                            {"x": 300, "y": 170},
                            {"x": 100, "y": 170}
                        ]
                    }
                }
            ]
        }
    ]
}

result = recognize_pii_in_text(
    text_content=ocr_data["full_text"],
    ocr_data=ocr_data
)

# 결과에는 좌표 정보도 포함됨
for pii in result["pii_entities"]:
    print(f"[{pii['type']}] {pii['text']}")
    if pii.get("coordinates"):
        for coord in pii["coordinates"]:
            print(f"  페이지 {coord['pageIndex']}: {coord['bbox']}")
```

---

## 주요 주의사항

### 거짓 양성 (False Positive) 방지

- 이름, 장소명 등 일반정보는 민감도 낮음
- 금융정보, 신분증번호 등은 민감도 높음
- 사용자가 최종 검토 및 승인 필요

### 거짓 음성 (False Negative) 대비

- 변형된 형식 (예: 공백 제거된 번호)은 인식 어려울 수 있음
- 타이핑 오류가 있는 정보는 인식 불가능할 수 있음
- 사용자 정의 규칙 추가 권장

### 성능 최적화

```python
# ✓ 효율적: 배치 처리
texts = [text1, text2, text3]
for text in texts:
    result = recognize_pii_in_text(text)

# ✗ 비효율적: NER 엔진을 매번 초기화
analyzer = AnalyzerEngine()  # 한 번만 생성
for text in texts:
    result = analyzer.analyze(text)
```