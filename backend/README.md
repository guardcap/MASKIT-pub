# Enterprise GuardCAP - Backend

FastAPI 기반의 통합 백엔드 서버입니다. DLP(Data Loss Prevention), SMTP 메일 처리, RAG 시스템을 모두 포함합니다.

## 📋 구조

```
backend/
├── app/
│   ├── main.py                 # FastAPI 메인 앱 (모든 라우트 통합)
│   ├── routers/                # DLP/OCR 라우터
│   │   ├── uploads.py          # 파일 업로드 및 관리
│   │   ├── process.py          # DLP 문서 처리
│   │   ├── ocr.py              # OCR 처리 (Clova API)
│   │   ├── analyzer.py         # PII 분석기
│   │   └── masking_pdf.py      # PDF 마스킹
│   ├── smtp/                   # SMTP 모듈 (내장 메일 서버)
│   │   ├── main.py             # SMTP 메인 앱
│   │   ├── routes/             # SMTP 라우터
│   │   │   ├── auth.py         # 로그인/인증
│   │   │   └── users.py        # 사용자 관리
│   │   ├── models.py           # 데이터 모델
│   │   ├── database.py         # MongoDB 연결
│   │   ├── smtp_handler.py     # SMTP 서버 핸들러
│   │   └── integrity.py        # 무결성 검증
│   ├── rag/                    # RAG 시스템
│   │   ├── agent/              # LangGraph 에이전트
│   │   │   ├── graph.py        # 그래프 정의
│   │   │   ├── nodes.py        # 노드 구현
│   │   │   ├── state.py        # 상태 관리
│   │   │   └── llm_factory.py  # LLM 팩토리
│   │   ├── retrievers.py       # 검색 모듈
│   │   ├── main_agent.py       # 메인 에이전트
│   │   └── scripts/            # 유틸리티 스크립트
│   ├── utils/                  # 공유 유틸리티
│   ├── test/                   # 테스트 코드
│   └── __init__.py
├── requirements.txt            # Python 의존성
├── run.py                       # 실행 스크립트 (선택사항)
└── README.md                   # 이 파일
```

## 🚀 시작 방법

### 1. 환경 설정

프로젝트 루트의 `.env` 파일 확인:

```bash
# 루트에서
cat .env

# 필수 항목:
# BACKEND_HOST=0.0.0.0
# BACKEND_PORT=8000
# MONGODB_URI=...
# SECRET_KEY=...
# DLP_SECRET_KEY=...
```

### 2. Python 가상 환경 설정

```bash
cd backend

# 가상 환경 생성
python -m venv venv

# 활성화
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 3. FastAPI 서버 실행

```bash
# uvicorn으로 실행 (권장)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 또는 run.py 사용
python run.py

# API 문서
http://localhost:8000/docs
```

## 📡 API 엔드포인트

### DLP/OCR API

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/v1/files/files` | 파일 목록 조회 |
| POST | `/api/v1/files/upload` | 파일 업로드 |
| POST | `/api/v1/process/documents` | 문서 처리 및 PII 분석 |
| POST | `/api/v1/process/masking/pdf` | PDF 마스킹 |
| POST | `/api/v1/ocr/process` | OCR 처리 |
| POST | `/api/v1/analyzer/analyze` | PII 분석 |

### SMTP API

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/v1/smtp/auth/register` | 회원가입 |
| POST | `/api/v1/smtp/auth/login` | 로그인 |
| GET | `/api/v1/smtp/users` | 사용자 목록 |
| PUT | `/api/v1/smtp/users/{email}` | 사용자 수정 |
| DELETE | `/api/v1/smtp/users/{email}` | 사용자 삭제 |

### 상태 확인

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/` | API 정보 |
| GET | `/health` | 헬스 체크 |
| GET | `/docs` | Swagger 문서 |

## 🔐 환경 변수

### 필수 변수

```env
# FastAPI 설정
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
DEBUG=true

# MongoDB 설정
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=maskit

# JWT/보안
SECRET_KEY=your-secret-key-min-32-chars
DLP_SECRET_KEY=your-dlp-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# SMTP 서버 설정
RECEIVE_SERVER_HOST=127.0.0.1
RECEIVE_SERVER_PORT=2526
RECEIVE_SERVER_USE_TLS=false
```

### 선택적 변수

```env
# OCR (Clova API)
CLOVA_OCR_URL=https://...
CLOVA_OCR_SECRET=...

# 실제 메일 서버 (Gmail, SWU 등)
# RECEIVE_SERVER_HOST=smtp.gmail.com
# RECEIVE_SERVER_PORT=587
# RECEIVE_SERVER_USE_TLS=true
# RECEIVE_SERVER_USERNAME=...
# RECEIVE_SERVER_PASSWORD=...

# RAG/LLM
# RAG_API_URL=...
# LLM_PROVIDER=ollama
```

## 🔧 기술 스택

### Core Framework
- **FastAPI** 0.109.0+ - 웹 프레임워크
- **Uvicorn** - ASGI 서버
- **Pydantic** 2.5.0+ - 데이터 검증

### Database & Async
- **Motor** 3.3.0+ - Async MongoDB 드라이버
- **PyMongo** 4.6.0+ - MongoDB 파이썬 드라이버
- **aiosmtpd** 1.4.4+ - 비동기 SMTP 서버

### NLP & RAG
- **LangChain** 0.1.0+ - LLM 프레임워크
- **LangGraph** - 에이전트 그래프
- **Transformers** 4.45.0+ - Hugging Face 모델
- **Sentence Transformers** 3.0.0+ - 임베딩 모델
- **ChromaDB** 0.5.3+ - 벡터 DB

### Security & Auth
- **python-jose** - JWT 토큰 처리
- **passlib** - 비밀번호 해싱
- **cryptography** - 암호화

### PDF Processing
- **PyPDF** - PDF 읽기/쓰기
- **pdf2image** - PDF 이미지 변환
- **Pillow** - 이미지 처리
- **PyMuPDF** - 고급 PDF 처리

## 📊 주요 기능

### DLP (Data Loss Prevention)
- 문서 업로드 및 분석
- PII(개인식별정보) 자동 탐지
- 정규식 및 NLP 기반 패턴 매칭
- 데이터 마스킹 및 숨김
- PDF 마스킹 지원

### SMTP & 메일
- 내장 SMTP 메일 서버 (포트 2526)
- 메일 수신 및 필터링
- DLP 정책 자동 적용
- 메일 승인/거부 워크플로우
- 사용자 역할 관리

### RAG (Retrieval Augmented Generation)
- 정책 문서 검색
- LLM 기반 쿼리 응답
- 컨텍스트 기반 분석
- LangGraph 에이전트

### OCR
- Clova API 연동
- 이미지 텍스트 추출
- PDF OCR 처리

## 🧪 테스트

```bash
# 모든 테스트 실행
pytest

# 특정 테스트 실행
pytest app/test/test_routers.py

# 커버리지 보고서
pytest --cov=app
```

## 🐛 문제 해결

### MongoDB 연결 실패

```
Error: cannot connect to database
```

**해결책**:
1. MongoDB URI 확인: `echo $MONGODB_URI`
2. 네트워크 연결 확인
3. MongoDB Atlas 화이트리스트 확인 (클라우드 사용 시)

### SMTP 포트 충돌

```
Error: Address already in use
```

**해결책**:
1. 다른 포트 사용: `.env`에서 `RECEIVE_SERVER_PORT` 변경
2. 실행 중인 프로세스 종료: `lsof -i :2526`

### Torch/GPU 관련 오류

```
Error: No module named 'torch'
```

**해결책**:
- CPU 버전: `pip install torch --index-url https://download.pytorch.org/whl/cpu`
- GPU 버전: CUDA 버전에 맞춰 설치

## 📚 관련 문서

- [루트 README](../README.md) - 전체 프로젝트
- [Frontend 정보](../frontend/README.md) - 웹 UI
- [SMTP 가이드](../wiki/10_mailproxy.md) - 메일 시스템
- [DLP 분석기](../wiki/3_analyzer.md) - 분석기 설정
- [FastAPI 설정](../wiki/8_fastapi.md) - 서버 설정

## 🔗 API 문서

서버 실행 후 다음 주소에서 확인:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

**마지막 업데이트**: 2024년 11월 7일
