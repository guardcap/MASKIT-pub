---
layout: default
title: fastapi 라우터 (back)
nav_order: 8
---

# FastAPI 라우터 구조

## 개요
Guardcap은 FastAPI를 기반으로 이메일 처리, 파일 업로드, OCR 추출, PII 분석, PDF 마스킹 등의 기능을 제공합니다.

---

## 1. main.py - 애플리케이션 진입점

### 역할
- FastAPI 애플리케이션 초기화
- CORS 미들웨어 설정
- 정적 파일 서빙 설정
- 모든 라우터 통합

### 주요 설정

```python
# CORS 설정 (모든 출처 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 마운트
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
```

### 포함된 라우터

| 라우터 | 경로 | 용도 |
|--------|------|------|
| uploads | `/api/v1/files` | 파일 업로드 |
| process | `/api/v1/process` | 문서 처리 |
| ocr | `/api/v1/ocr` | OCR 추출 |
| analyzer | `/api/v1/analyzer` | PII 분석 |
| masking_pdf | `/api/v1/process` | PDF 마스킹 |

---

## 2. uploads.py - 파일 업로드 관리

### 주요 엔드포인트

#### `POST /upload_email`
이메일과 첨부파일을 업로드합니다.

**요청 파라미터:**
- `from_email` (string): 발신자 이메일
- `to_email` (string): 수신자 이메일 (쉼표로 구분)
- `subject` (string): 이메일 제목
- `original_body` (string): 이메일 본문
- `attachments` (List[UploadFile]): 첨부 파일 목록

**처리 흐름:**
1. uploads 폴더의 기존 파일 삭제
2. `email_body.txt`에 이메일 본문 저장
3. `email_meta.json`에 메타데이터 저장
4. 첨부파일 저장

#### `GET /files`
업로드된 파일 목록을 조회합니다.

**응답 모델:**
```python
class FileItem(BaseModel):
    id: str          # 파일 ID (file0, file1, ...)
    name: str        # 파일명
    kind: str        # 파일 종류 (email, image, pdf, docx, text)
    path: str        # 상대 경로
```

**필터링:**
- `email_meta.json`은 목록에서 제외
- 파일 확장자에 따라 `kind` 자동 결정

---

## 3. ocr_needed.py - OCR 필요 여부 판단

### 주요 엔드포인트

#### `POST /check-ocr`
파일이 OCR 처리가 필요한지 확인합니다.

**요청:**
```python
class PreflightCheckRequest(BaseModel):
    filename: str
```

**응답:**
```python
class PreflightCheckResponse(BaseModel):
    ocr_needed: bool
```

### OCR 필수 확장자
```
.jpg, .jpeg, .png, .gif, .bmp, .pdf, .heic
```

---

## 4. ocr.py - OCR 텍스트 추출

### 주요 엔드포인트

#### `POST /extract/ocr`
이미지 또는 PDF에서 텍스트와 좌표를 추출합니다.

**요청 파라미터:**
- `file_content` (bytes): 파일 바이너리 데이터
- `file_name` (string): 파일명

**기능:**
- `extract_text_from_file()` 호출
- OCR 엔진을 통해 텍스트 및 좌표 정보 추출
- 결과는 `analyzer.py`에서 PII 분석에 활용

---

## 5. analyzer.py - PII 분석

### 데이터 모델

#### `TextAnalysisRequest`
```python
class TextAnalysisRequest(BaseModel):
    text_content: str              # 분석할 텍스트
    user_request: str = "default"  # 사용자 요청사항
    ocr_data: Optional[Dict] = None # OCR 데이터 (좌표 포함)
```

#### `PIICoordinate`
```python
class PIICoordinate(BaseModel):
    pageIndex: int      # 페이지 번호
    bbox: List[int]     # 바운딩박스 [x1, y1, x2, y2]
    field_text: str     # 해당 위치의 텍스트
```

#### `PIIEntity`
```python
class PIIEntity(BaseModel):
    text: str                              # PII 텍스트
    type: str                              # PII 타입 (주민번호, 신용카드 등)
    score: float                           # 신뢰도 점수
    start_char: int                        # 시작 위치
    end_char: int                          # 종료 위치
    coordinates: Optional[List[PIICoordinate]] = None  # 시각적 좌표
```

#### `TextAnalysisResponse`
```python
class TextAnalysisResponse(BaseModel):
    full_text: str          # 전체 텍스트
    pii_entities: List[PIIEntity]  # 감지된 PII 항목
```

### 주요 엔드포인트

#### `POST /analyze/text`
텍스트에서 PII를 분석합니다.

**처리 흐름:**
1. OCR 데이터가 포함된 텍스트 분석 요청 수신
2. `recognize_pii_in_text()` 호출
3. PII 항목과 좌표 정보 반환

---

## 6. masking_pdf.py - PDF 마스킹

### 데이터 모델

#### `PIIItemFromAnalysis`
```python
class PIIItemFromAnalysis(BaseModel):
    filename: str              # 대상 파일명
    pii_type: str              # PII 타입
    text: str                  # PII 텍스트
    pageIndex: int             # 페이지 번호
    instance_index: int = 0    # 인스턴스 인덱스
    bbox: Optional[List[int]] = None  # 바운딩박스
```

### 주요 엔드포인트

#### `POST /masking/pdf`
클라이언트에서 선택한 PII를 PDF에서 마스킹합니다.

**요청:**
```python
List[PIIItemFromAnalysis]  # PII 항목 리스트
```

**처리 흐름:**
1. 파일별 PII 항목 그룹화
2. 각 파일에 대해 `PdfMaskingEngine.redact_pdf_with_entities()` 실행
3. 마스킹된 파일을 `masked_` 접두사로 저장
4. 마스킹된 파일 경로 반환

**응답:**
```json
{
    "status": "success",
    "masked_files": {
        "original.pdf": "/uploads/masked_original.pdf",
        ...
    }
}
```

**에러 처리:**
- 파일을 찾을 수 없으면 "File not found" 반환
- 마스킹 실패 시 에러 메시지 반환

---

## 7. process.py - 문서 처리 오케스트레이션

### 주요 엔드포인트

#### `POST /documents`
uploads 폴더의 모든 파일을 처리합니다.

**처리 흐름:**
1. 모든 업로드된 파일 조회
2. 각 파일에 대해:
   - `email_body.txt`: 직접 PII 분석
   - OCR 필요 파일: OCR 추출 → PII 분석
   - 기타: 분석 스킵
3. 결과 반환

**응답 예시:**
```json
{
    "message": "Processing started",
    "details": [
        {
            "filename": "document.pdf",
            "status": "ANALYSIS_COMPLETED",
            "ocr_data": {...},
            "analysis_data": {...}
        }
    ]
}
```

#### `POST /approve_and_send`
최종 승인 후 이메일 발송 및 uploads 폴더 정리

**요청:**
```python
class ApproveRequest(BaseModel):
    recipients: List[str]   # 수신자 리스트
    subject: str            # 이메일 제목
    final_body: str         # 최종 본문
    attachments: List[str]  # 첨부파일명 리스트
```

**기능:**
- Naver SMTP를 통해 이메일 발송
- 이메일 발송 성공 후 uploads 폴더 정리
- `clear_uploads_folder()` 함수로 모든 파일 및 디렉토리 삭제

**Naver 설정:**
```python
NAVER_SMTP_SERVER = "smtp.naver.com"
NAVER_SMTP_PORT = 587
SENDER_NAVER_EMAIL = "pblteam01@naver.com"
# SENDER_APP_PASSWORD는 환경변수 NAVER_APP_PASSWORD에서 로드
```

---

## 전체 API 워크플로우

```
1. 파일 업로드 (upload_email)
   ↓
2. 파일 조회 (get_files)
   ↓
3. 문서 처리 (process_documents)
   ├─ OCR 필요 확인 (check_ocr_needed)
   ├─ OCR 추출 (extract_ocr)
   └─ PII 분석 (analyze_text)
   ↓
4. 결과 승인 및 이메일 발송 (approve_and_send_email)
   ↓
5. 폴더 정리 (clear_uploads_folder)
```

