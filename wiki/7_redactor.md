---
layout: default
title: file(image, pdf) redactor
nav_order: 7
---

# 파일 마스킹 (Redactor)

## 개요

Guardcap은 PDF 및 이미지 파일에서 감지된 PII를 자동으로 마스킹합니다.
`UnifiedMaskingEngine`은 PDF와 이미지(PNG, JPG 등) 파일 형식을 모두 지원하는 통합 마스킹 엔진입니다.

---

## 1. 마스킹 엔진 아키텍처

### 전체 흐름

```
입력 파일 (PDF 또는 이미지)
    ↓
UnifiedMaskingEngine
    ├─ 파일 확장자 확인
    │
    ├─ PDF 파일 (.pdf)
    │  ├─ PyMuPDF (fitz) 라이브러리로 열기
    │  ├─ 페이지별 텍스트 검색
    │  ├─ 정확/퍼지/단어별 매칭
    │  └─ 검은색 직사각형으로 마스킹
    │
    └─ 이미지 파일 (.png, .jpg, .jpeg, .bmp, .gif)
       ├─ PIL (Pillow)로 열기
       ├─ OCR bbox 좌표 활용
       ├─ 좌표 유효성 검사
       └─ 검은색 직사각형으로 마스킹
    ↓
마스킹된 파일 저장
```

---

## 2. UnifiedMaskingEngine 클래스

### 초기화

```python
from app.utils.masking_engine import UnifiedMaskingEngine

engine = UnifiedMaskingEngine()
```

**설정:**
- 마스킹 색상: 검은색 `(0, 0, 0)` (RGB)
- 이미지 모드: RGB로 자동 변환
- 바운딩박스 마진: 2px (좌표 여유)

### 주요 메서드

#### `redact_pdf_with_entities()`

PDF 또는 이미지 파일을 마스킹합니다.

**시그니처:**
```python
def redact_pdf_with_entities(
    pdf_path: str,           # 입력 파일 경로
    entities: List[Dict],    # PII 엔티티 리스트
    out_pdf_path: str        # 출력 파일 경로
) → None:
```

**엔티티 형식:**
```python
entities = [
    {
        "text": "010-1234-5678",      # PII 텍스트
        "entity": "PHONE_NUMBER",     # 엔티티 타입
        "pageIndex": 0,                # 페이지 번호
        "instance_index": 0,           # (선택) 인스턴스 인덱스
        "bbox": [100, 100, 200, 120]  # (선택) 바운딩박스 [x1, y1, x2, y2]
    },
    # ...
]
```

**사용 예시:**

```python
from app.utils.masking_engine import UnifiedMaskingEngine

engine = UnifiedMaskingEngine()

# PDF 마스킹
entities = [
    {"text": "010-1234-5678", "entity": "PHONE_NUMBER", "pageIndex": 0},
    {"text": "test@example.com", "entity": "EMAIL", "pageIndex": 0}
]

engine.redact_pdf_with_entities(
    pdf_path="document.pdf",
    entities=entities,
    out_pdf_path="document_masked.pdf"
)

# 이미지 마스킹 (bbox 필수)
entities = [
    {
        "text": "010-1234-5678",
        "entity": "PHONE_NUMBER",
        "pageIndex": 0,
        "bbox": [100, 50, 250, 80]
    }
]

engine.redact_pdf_with_entities(
    pdf_path="image.png",
    entities=entities,
    out_pdf_path="image_masked.png"
)
```

---

## 3. PDF 마스킹 상세

### 3.1 PDF 처리 흐름

```python
def _mask_pdf_file(self, pdf_path: str, entities: List[Dict], out_pdf_path: str):
    """
    1. PDF 파일 열기 (PyMuPDF)
    2. 각 엔티티별 처리
    3. 마스킹 실행
    4. 파일 저장
    """
```

#### 단계별 처리

```
1. PDF 열기
   └─ doc = fitz.open(pdf_path)

2. 각 엔티티 처리
   ├─ 페이지 번호 확인
   ├─ 텍스트 유효성 검사
   └─ 마스킹 메서드 선택

3. 텍스트 검색 및 마스킹
   ├─ 정확한 매칭 (page.search_for)
   ├─ 퍼지 검색 (fuzzy search)
   └─ 단어별 검색 (word by word)

4. 파일 저장
   └─ doc.save(out_pdf_path)
```

### 3.2 텍스트 검색 방법 (3단계)

#### 1단계: 정확한 매칭 (Exact Match)

```python
def _mask_text_in_pdf_page(self, page, search_text: str, entity_type: str, instance_index: int = None):
    """
    page.search_for()로 정확한 문자열 검색
    """
    text_instances = page.search_for(search_text)

    if text_instances:
        if instance_index is not None:
            # 특정 인스턴스만 마스킹
            rect = text_instances[instance_index]
            page.draw_rect(rect, fill=(0, 0, 0))
        else:
            # 모든 인스턴스 마스킹
            for rect in text_instances:
                page.draw_rect(rect, fill=(0, 0, 0))
```

**특징:**
- 가장 빠른 방법
- 100% 정확한 매칭만 인식
- 대소문자 구분

#### 2단계: 퍼지 검색 (Fuzzy Match)

```python
def _fuzzy_search_and_mask_pdf(self, page, search_text: str, entity_type: str):
    """
    정확한 매칭 실패 시 퍼지 검색 수행
    - 텍스트 블록 단위로 비교
    - 부분 일치 허용
    """
```

**매칭 조건:**
```python
def _is_text_match(self, search_text: str, span_text: str) -> bool:
    # 1. 정확한 매칭
    if search_text == span_text:
        return True

    # 2. 대소문자 무시 매칭
    if search_text.lower() == span_text.lower():
        return True

    # 3. 공백 제거 후 매칭
    if search_text.replace(" ", "") == span_text.replace(" ", ""):
        return True

    # 4. 부분 포함 매칭
    if search_text in span_text or span_text in search_text:
        return True

    return False
```

**예시:**
```
search_text = "010-1234-5678"

✓ "010-1234-5678"      → 정확한 매칭
✓ "010-1234-5678 "     → 공백 무시
✓ "010 1234 5678"      → 공백 제거 후 매칭
✓ "[010-1234-5678]"    → 부분 포함 매칭
```

#### 3단계: 단어별 검색 (Word-by-Word)

```python
def _word_by_word_search_pdf(self, page, search_text: str, entity_type: str):
    """
    마지막 수단: 공백 기준으로 단어 분리 후 개별 검색
    """
    words = search_text.split()  # ["010", "1234", "5678"]

    for word in words:
        if len(word.strip()) >= 2:  # 최소 2글자 이상
            text_instances = page.search_for(word.strip())
            if text_instances:
                for rect in text_instances:
                    page.draw_rect(rect, fill=(0, 0, 0))
```

**사용 시나리오:**
- "010-1234-5678"이 "010", "1234", "5678"로 분리되어 저장된 경우
- 각 단어를 개별적으로 마스킹

### 3.3 Instance Index (인스턴스 인덱스)

같은 텍스트가 여러 번 나타날 때 특정 인스턴스만 마스킹:

```python
# 예: "test"가 페이지에 3번 나타남
entities = [
    {
        "text": "test",
        "entity": "KEYWORD",
        "pageIndex": 0,
        "instance_index": 1  # 두 번째 "test"만 마스킹
    }
]

engine.redact_pdf_with_entities(
    pdf_path="document.pdf",
    entities=entities,
    out_pdf_path="document_masked.pdf"
)

# 결과:
# test (마스킹 안 함)
# [███] (마스킹됨 - instance_index: 1)
# test (마스킹 안 함)
```

---

## 4. 이미지 마스킹 상세

### 4.1 이미지 처리 흐름

```python
def _mask_image_file(self, image_path: str, entities: List[Dict], out_image_path: str):
    """
    1. 이미지 열기 (PIL)
    2. RGB 모드로 변환
    3. 각 엔티티의 bbox로 직사각형 그리기
    4. 파일 저장
    """
```

#### 단계별 처리

```
1. 이미지 열기
   ├─ Image.open(image_path)
   └─ RGB 모드로 변환 (필요시)

2. 각 엔티티 처리
   ├─ bbox 추출 [x1, y1, x2, y2]
   ├─ 좌표 유효성 검사
   └─ 검은색 직사각형 그리기

3. 이미지 저장
   ├─ .jpg/.jpeg → JPEG 포맷 (quality=95)
   └─ 기타 → PNG 포맷
```

### 4.2 좌표 유효성 검사

```python
# 이미지 경계를 벗어난 좌표 조정
img_width, img_height = img.size

x1 = max(0, min(x1, img_width))      # 0 ~ width 범위
y1 = max(0, min(y1, img_height))     # 0 ~ height 범위
x2 = max(x1, min(x2, img_width))     # x1 ~ width 범위
y2 = max(y1, min(y2, img_height))    # y1 ~ height 범위
```

**예시:**

```
원본 좌표: [50, 100, 2000, 150]
이미지 크기: 800x600

조정된 좌표: [50, 100, 800, 150]
           └─ x2가 800으로 제한
```

### 4.3 사용 예시

```python
from app.utils.masking_engine import UnifiedMaskingEngine

engine = UnifiedMaskingEngine()

# PNG 이미지 마스킹
entities = [
    {
        "text": "김철수",
        "entity": "NAME",
        "pageIndex": 0,
        "bbox": [100, 150, 250, 180]  # [x1, y1, x2, y2]
    },
    {
        "text": "010-1234-5678",
        "entity": "PHONE_NUMBER",
        "pageIndex": 0,
        "bbox": [100, 200, 300, 230]
    }
]

engine.redact_pdf_with_entities(
    pdf_path="document.png",
    entities=entities,
    out_pdf_path="document_masked.png"
)

# JPG 이미지 마스킹 (자동으로 JPEG 포맷으로 저장)
engine.redact_pdf_with_entities(
    pdf_path="photo.jpg",
    entities=entities,
    out_pdf_path="photo_masked.jpg"
)
```

---

## 5. 호환성 클래스 및 함수

### PdfMaskingEngine (별칭)

```python
from app.utils.masking_engine import PdfMaskingEngine

# UnifiedMaskingEngine과 동일
engine = PdfMaskingEngine()

# 사용 방식은 UnifiedMaskingEngine과 동일
engine.redact_pdf_with_entities(pdf_path, entities, out_pdf_path)
```

### Factory 함수

```python
from app.utils.masking_engine import create_masking_engine

engine = create_masking_engine()
```

---

## 6. 디버깅 메서드

### PDF 텍스트 디버깅

```python
engine = UnifiedMaskingEngine()

# PDF 페이지의 모든 텍스트 출력
engine.debug_pdf_text(pdf_path="document.pdf", page_num=0)

# 출력 예시:
# [디버깅] PDF 페이지 0의 모든 텍스트:
#
# 블록 0:
#   Line 0, Span 0: '이름: ' @ (100, 150, 180, 170)
#   Line 0, Span 1: '김철수' @ (180, 150, 250, 170)
#   Line 1, Span 0: '전화: ' @ (100, 200, 180, 220)
#   Line 1, Span 1: '010-1234-5678' @ (180, 200, 300, 220)
```

**용도:**
- 마스킹할 정확한 텍스트 확인
- bbox 좌표 확인
- 검색 문제 진단

### 이미지 정보 디버깅

```python
# 이미지 기본 정보 출력
engine.debug_image_info(image_path="photo.jpg")

# 출력 예시:
# [디버깅] 이미지 정보:
#   파일: photo.jpg
#   크기: (800, 600)
#   모드: RGB
```

---

## 7. OCR 데이터 통합 마스킹

### 워크플로우

```
1. 파일 업로드
   ↓
2. OCR 추출
   └─ bbox 좌표 획득
   ↓
3. PII 분석
   ├─ 텍스트 탐지
   └─ OCR bbox와 매핑
   ↓
4. 마스킹
   └─ bbox를 이용한 정확한 마스킹
```

### API 통합 예시

```python
from app.routers.uploads import UPLOAD_DIR
from app.routers.ocr import extract_ocr
from app.utils.recognizer_engine import recognize_pii_in_text
from app.utils.masking_engine import UnifiedMaskingEngine

# 1. OCR 추출
file_path = f"{UPLOAD_DIR}/document.pdf"
with open(file_path, "rb") as f:
    file_content = f.read()

ocr_result = await extract_ocr(file_content, "document.pdf")

# 2. PII 분석 (OCR 데이터 포함)
analysis_result = recognize_pii_in_text(
    text_content=ocr_result["full_text"],
    ocr_data=ocr_result
)

# 3. 마스킹용 엔티티 준비
masking_entities = []
for pii in analysis_result["pii_entities"]:
    if pii.get("coordinates"):
        for coord in pii["coordinates"]:
            masking_entities.append({
                "text": pii["text"],
                "entity": pii["type"],
                "pageIndex": coord["pageIndex"],
                "bbox": coord["bbox"]
            })

# 4. 파일 마스킹
engine = UnifiedMaskingEngine()
engine.redact_pdf_with_entities(
    pdf_path=file_path,
    entities=masking_entities,
    out_pdf_path=f"{UPLOAD_DIR}/document_masked.pdf"
)
```

---

## 8. 마스킹 API 통합

### API 엔드포인트: POST /masking/pdf

**요청:**
```json
[
    {
        "filename": "document.pdf",
        "pii_type": "PHONE_NUMBER",
        "text": "010-1234-5678",
        "pageIndex": 0,
        "instance_index": 0,
        "bbox": [100, 150, 250, 180]
    },
    {
        "filename": "document.pdf",
        "pii_type": "EMAIL",
        "text": "test@example.com",
        "pageIndex": 0,
        "instance_index": 0,
        "bbox": [100, 200, 300, 220]
    }
]
```

**응답:**
```json
{
    "status": "success",
    "masked_files": {
        "document.pdf": "/uploads/masked_document.pdf"
    }
}
```

**처리 흐름 (masking_pdf.py):**

```
1. PII 항목을 파일별로 그룹화
2. 각 파일에 대해:
   ├─ 원본 파일 존재 확인
   ├─ UnifiedMaskingEngine으로 마스킹
   ├─ masked_[filename] 이름으로 저장
   └─ 결과 경로 반환
3. 오류 처리 및 로깅
```

### 구현 예시

```python
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from app.utils.masking_engine import UnifiedMaskingEngine
from app.routers.uploads import UPLOAD_DIR

router = APIRouter()

class PIIItemFromAnalysis(BaseModel):
    filename: str
    pii_type: str
    text: str
    pageIndex: int
    instance_index: int = 0
    bbox: Optional[List[int]] = None

@router.post("/masking/pdf")
async def mask_pii_in_pdf(pii_items: List[PIIItemFromAnalysis]):
    """
    클라이언트에서 받은 PII 정보를 기반으로 PDF/이미지 마스킹
    """
    # 파일별 PII 그룹화
    pii_by_file = {}
    for item in pii_items:
        if item.filename not in pii_by_file:
            pii_by_file[item.filename] = []

        entity_data = {
            "entity": item.pii_type,
            "pageIndex": item.pageIndex,
            "text": item.text,
            "instance_index": item.instance_index
        }

        if item.bbox is not None:
            entity_data["bbox"] = item.bbox

        pii_by_file[item.filename].append(entity_data)

    # 파일별 마스킹 수행
    masked_file_paths = {}
    masking_engine = UnifiedMaskingEngine()

    for filename, entities in pii_by_file.items():
        original_file_path = os.path.join(UPLOAD_DIR, filename)

        if not os.path.exists(original_file_path):
            masked_file_paths[filename] = "File not found"
            continue

        masked_filename = f"masked_{filename}"
        masked_file_path = os.path.join(UPLOAD_DIR, masked_filename)

        try:
            masking_engine.redact_pdf_with_entities(
                pdf_path=original_file_path,
                entities=entities,
                out_pdf_path=masked_file_path
            )

            masked_file_paths[filename] = f"/uploads/{masked_filename}"

        except Exception as e:
            masked_file_paths[filename] = f"Masking failed: {str(e)}"

    return {"status": "success", "masked_files": masked_file_paths}
```

---

## 9. 지원 파일 형식

### PDF
- **라이브러리**: PyMuPDF (fitz)
- **지원**: 모든 PDF 버전
- **특징**: 벡터 기반 마스킹, 고품질 유지

### 이미지

| 형식 | 확장자 | 라이브러리 | 저장 형식 |
|------|--------|-----------|---------|
| PNG | .png | PIL | PNG |
| JPEG | .jpg, .jpeg | PIL | JPEG (quality=95) |
| BMP | .bmp | PIL | PNG로 변환 |
| GIF | .gif | PIL | PNG로 변환 |

---

## 10. 성능 및 최적화

### 시간 복잡도

| 작업 | 복잡도 | 주석 |
|------|--------|------|
| PDF 열기 | O(1) | 페이지 로드 후 진행 |
| 텍스트 검색 | O(n×m) | n: 페이지 텍스트 길이, m: 검색어 길이 |
| 마스킹 | O(k) | k: 마스킹할 PII 개수 |
| 파일 저장 | O(p) | p: 총 페이지/픽셀 수 |

### 최적화 팁

```python
# ✓ 효율적: 배치 마스킹
engine = UnifiedMaskingEngine()  # 한 번만 생성
for file_data in batch:
    engine.redact_pdf_with_entities(...)

# ✗ 비효율적: 매번 생성
for file_data in batch:
    engine = UnifiedMaskingEngine()  # 반복 생성
    engine.redact_pdf_with_entities(...)

# ✓ 효율적: 필요한 PII만 마스킹
entities = [pii for pii in all_pii if pii["need_masking"]]

# ✗ 비효율적: 모든 PII를 마스킹 후 필터링
for pii in all_pii:
    engine.redact_pdf_with_entities(...)
```

---

## 11. 에러 처리

### 예외 상황

| 상황 | 처리 | 결과 |
|------|------|------|
| 파일 없음 | FileNotFoundError | "File not found" 반환 |
| 지원 안 하는 형식 | ValueError | 에러 메시지 반환 |
| 페이지 범위 초과 | 건너뜀 | 로그 출력 후 계속 진행 |
| 빈 텍스트 | 건너뜀 | 경고 로그 출력 |
| 마스킹 실패 | Exception 캐치 | traceback 출력 및 에러 반환 |

### 디버깅 팁

```python
# 문제 진단 1: 텍스트가 정말 존재하는가?
engine.debug_pdf_text(pdf_path, page_num=0)

# 문제 진단 2: 이미지 크기는 충분한가?
engine.debug_image_info(image_path)

# 문제 진단 3: 로그 메시지 확인
# [PDF 마스킹] 검색 중: '010-1234-5678' (타입: PHONE_NUMBER, 페이지: 0)
# [PDF 마스킹] 퍼지 검색 시작: '010-1234-5678'
# [PDF 마스킹] 단어별 검색: '010-1234-5678'
# [PDF 마스킹] 텍스트 '010-1234-5678'을 찾을 수 없음
```

---

## 주요 주의사항

### 파일 관리
- 원본 파일은 수정되지 않음
- 마스킹된 파일은 `masked_` 접두사로 저장
- 정기적인 임시 파일 정리 필요

### 마스킹 품질
- PDF: 벡터 기반으로 완벽한 마스킹
- 이미지: 픽셀 기반으로 검은색 박스 그리기
- OCR 오류 시 좌표가 부정확할 수 있음

### 성능 고려사항
- 대용량 PDF (100+ 페이지): 시간 소요
- 이미지: 크기에 따라 처리 시간 변함
- NER 기반 탐지는 추가 시간 필요

### 보안
- 마스킹된 파일의 접근 제어 필요
- 원본 파일 삭제 정책 수립
- 감시 로그 기록 권장