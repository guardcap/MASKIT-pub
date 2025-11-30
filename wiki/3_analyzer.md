---
layout: default
title: Analyzer Engine 소개
nav_order: 3
---

# Analyzer Engine 소개

`AnalyzerEngine`은 텍스트 내 개인정보(PII) 탐지를 위한 핵심 구성 요소입니다. 이 엔진은 **규칙 기반(REGEX)** 접근 방식과 **모델 기반(NER)** 접근 방식을 결합한 **하이브리드 방식**을 사용하여 탐지 정확도와 범용성을 모두 높이는 것을 목표로 합니다.

제공된 텍스트(및 선택적으로 OCR 데이터)를 입력받아, 탐지된 PII 엔티티의 목록과 위치 정보를 반환합니다.

---

## 핵심 아키텍처: 하이브리드 방식

`AnalyzerEngine`은 두 가지 주요 컴포넌트를 통해 PII를 탐지합니다.

### 1. 규칙 기반 탐지 (RecognizerRegistry)
* 정규식(Regex)이나 특정 로직을 기반으로 패턴이 명확한 PII를 탐지합니다.
* **장점:** 이메일, 전화번호, 주민등록번호, IP 주소 등과 같이 형식이 정해진 데이터에 대해 매우 빠르고 정밀하게 작동합니다.
* **담당 클래스:** `RecognizerRegistry` - 여러 규칙 기반 인식기(`EntityRecognizer`)를 관리합니다.

### 2. 모델 기반 탐지 (NerEngine)
* 미리 학습된 자연어 처리(NLP) 모델(NER - Named Entity Recognition)을 사용하여 PII를 탐지합니다.
* **장점:** 이름, 기관명, 위치 등 문맥 속에서 파악해야 하는 비정형 데이터를 유연하게 탐지할 수 있습니다.
* **담당 클래스:** `NerEngine` - 모델 로딩 및 추론을 수행합니다.
* **사용 모델:** `monologg/koelectra-base-v3-naver-ner` (한국어 특화)

---

## 주요 동작 흐름

PII 탐지 요청이 들어왔을 때의 내부 동작 과정입니다:
```
텍스트 입력
    ↓
[1] 엔진 초기화
    ├─ RecognizerRegistry 로드
    └─ NerEngine 로드
    ↓
[2] 규칙 기반 분석 → regex_group
    ↓
[3] NER 분석 → ner_group
    ↓
[4] 결과 병합 (충돌 해결)
    ├─ 긴 범위 우선
    └─ 같은 범위면 높은 점수 우선
    ↓
[5] 중복 제거 및 정렬
    ↓
[6] (선택) 이미지 입력 시, OCR 좌표 매핑
    ↓
최종 결과 반환
```

### 상세 단계

1. **엔진 초기화**: `AnalyzerEngine`이 생성되면 `RecognizerRegistry`와 `NerEngine`을 초기화합니다.
   * `RecognizerRegistry.load_predefined_recognizers()`를 호출하여 정의된 모든 규칙 기반 인식기를 로드합니다.

2. **규칙 기반 분석**: `RecognizerRegistry.regex_analyze()`가 실행됩니다.
   * 등록된 모든 인식기(Email, Phone, IP 등)가 텍스트를 스캔하여 PII 후보를 찾습니다.

3. **NER 분석**: `NerEngine.ner_analyze()`가 실행됩니다.
   * NLP 모델이 텍스트 전체를 분석하여 문맥에 따른 PII 후보를 찾습니다.

4. **결과 병합 및 충돌 해결**: `_merge_groups` 메서드로 두 결과를 병합합니다.
   * **충돌 해결 우선순위:**
     1. 더 긴 범위(Longer Span)를 가진 엔티티 우선
     2. 범위 길이가 같다면 신뢰도 점수(Score)가 높은 엔티티 우선

5. **최종 정리**: `_dedup_and_sort` 메서드가 완전 중복을 제거하고 시작 위치(`start`) 순으로 정렬합니다.

6. **(선택) OCR 좌표 매핑**: `ocr_data`가 제공된 경우, `find_text_coordinates_in_ocr` 함수가 실행됩니다.
   * `Entity`의 텍스트 위치를 원본 이미지 좌표(`bbox`, `pageIndex`)에 매핑합니다.

7. **결과 반환**: 모든 PII 정보가 포함된 최종 목록이 반환됩니다.

---

## 주요 구성 요소

| 컴포넌트 | 역할 |
|---------|------|
| `AnalyzerEngine` | 규칙 기반 엔진과 NER 엔진을 총괄하는 오케스트레이터 |
| `RecognizerRegistry` | 규칙 기반 인식기(`EntityRecognizer`)를 등록·관리하는 레지스트리 |
| `EntityRecognizer` | 모든 규칙 기반 인식기의 기본 클래스 (예: `EmailRecognizer`) |
| `NerEngine` | 머신러닝 기반 NER 모델 로드 및 텍스트 분석 수행 |
| `Entity` | 탐지된 PII 하나를 나타내는 표준 데이터 객체 |
| `EntityGroup` | `Entity` 객체들의 목록을 관리하는 컨테이너 클래스 |

---

## 지원 엔티티 목록

### 규칙 기반 엔티티 (REGEX)

`RecognizerRegistry`가 기본적으로 로드하는 엔티티 타입입니다:

| 엔티티 타입 | 설명 | 예시 |
|-----------|------|------|
| EMAIL | 이메일 주소 | `user@example.com` |
| PHONE | 한국 전화번호 | `010-1234-5678` |
| RESIDENT_ID | 주민등록번호 | `900101-1234567` |
| BANK_ACCOUNT | 은행 계좌번호 | `123-456-789012` |
| CARD_NUMBER | 신용카드 번호 | `1234-5678-9012-3456` |
| DRIVE | 운전면허 번호 | `11-01-123456-78` |
| PASSPORT | 여권 번호 | `M12345678` |
| IP | IP 주소 (v4/v6) | `192.168.1.1` |
| GPS | GPS 좌표 | `37.5665, 126.9780` |
| MAC | MAC 주소 | `01:23:45:67:89:AB` |

### 모델 기반 엔티티 (NER)

`NerEngine`이 탐지하는 엔티티 타입입니다:

| 엔티티 타입 | 설명 | 특징 |
|-----------|------|------|
| PERSON | 사람 이름 | 문맥 기반 탐지 |
| ORGANIZATION | 기관/조직명 | 문맥 기반 탐지 |
| LOCATION | 위치/지명 | 문맥 기반 탐지 |

---

