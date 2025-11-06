# Enterprise GuardCAP - Unified Project

데이터 손실 방지(DLP)를 위한 엔터프라이즈급 통합 솔루션입니다. 모든 서비스(Backend, Frontend, RAG, SMTP)가 단일 프로젝트로 완전히 통합되어 있습니다.

## 📁 프로젝트 구조

```
enterprise-guardcap/
├── backend/                      # 통합 FastAPI 백엔드 서버
│   ├── app/
│   │   ├── main.py              # 메인 FastAPI 앱 (모든 라우트 통합)
│   │   ├── routers/             # DLP/OCR 라우터
│   │   ├── smtp/                # SMTP 기능 (routes/, models/, handlers 포함)
│   │   ├── rag/                 # RAG 시스템 (embeddings, agent, etc)
│   │   └── utils/               # 공유 유틸리티
│   ├── requirements.txt          # 통합 Python 의존성
│   └── README.md
│
├── frontend/                     # 통합 웹 인터페이스
│   ├── script.js                # API_BASE_URL 기반 동적 연결
│   ├── smtp/                    # SMTP 관련 UI 페이지
│   ├── pages/                   # 추가 페이지
│   ├── package.json
│   └── index.html
│
├── wiki/                        # 문서 및 가이드
│   ├── 2_install.md
│   ├── 3_analyzer.md
│   ├── 5_PII_entities.md
│   ├── 7_redactor.md
│   ├── 8_fastapi.md
│   ├── 10_mailproxy.md
│   └── README.md
│
├── .env                         # 통합 환경 설정 (마스킹됨)
├── .gitignore                   # Git 무시 파일 (.env 포함)
└── README.md                    # 이 파일
```

## ✨ 주요 특징

### 통합 Backend (FastAPI)
- **단일 포트 (8000)**: 모든 서비스가 하나의 FastAPI 인스턴스로 실행
- **통합 라우트**:
  - `/api/v1/process` - DLP 분석
  - `/api/v1/ocr` - OCR 처리
  - `/api/v1/smtp` - SMTP 인증 및 사용자 관리
  - `/api/v1/files` - 파일 관리
  - `/api/v1/analyzer` - 분석기
- **SMTP 내장**: aiosmtpd를 통한 내장 SMTP 서버
- **RAG 통합**: LangChain 기반 RAG 시스템

### 통합 Frontend
- **동적 API 연결**: `API_BASE_URL` 환경 변수 기반
- **모든 UI 통합**: DLP/SMTP/분석 대시보드
- **Electron 기반**: 데스크톱 애플리케이션

### 통합 환경 설정
- **단일 .env 파일**: 모든 서비스 설정 중앙화
- **.gitignore 마스킹**: 민감한 정보 보호

## 🚀 빠른 시작

### 1. 환경 설정

프로젝트 루트의 `.env` 파일을 설정하세요:

```bash
# 프로젝트 루트
cat .env  # 설정 확인

# 필수 설정 항목:
# - BACKEND_HOST, BACKEND_PORT
# - MONGODB_URI, DATABASE_NAME
# - SECRET_KEY, DLP_SECRET_KEY
# - RECEIVE_SERVER_* (SMTP 설정)
```

**⚠️ 주의**: `.env` 파일은 `.gitignore`에 포함되어 있어 Git에 커밋되지 않습니다.

### 2. Backend 시작 (모든 서비스 포함)

```bash
cd backend

# Python 가상 환경 설정
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치 (DLP, SMTP, RAG 포함)
pip install -r requirements.txt

# FastAPI 서버 실행 (포트 8000)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 또는
python run.py

# API 문서: http://localhost:8000/docs
```

**포함되는 서비스**:
- ✅ DLP 분석 및 처리
- ✅ SMTP 메일 서버 (포트 2526)
- ✅ 사용자 인증
- ✅ RAG 시스템
- ✅ OCR 처리
- ✅ 파일 관리

### 3. Frontend 시작

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행 (포트 3000)
npm start
# 또는 Electron 앱으로 실행
npm run start  # package.json의 electron 명령
```

**설정**:
- `API_BASE_URL`: Backend API 주소 (기본: http://127.0.0.1:8000)
- `.env` 파일에서 `REACT_APP_API_URL` 설정 가능

### 4. 통합 실행 (권장)

한 터미널에서 모든 서비스를 실행:

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm start
```

이제 모든 서비스가 통합되어 포트 8000(Backend)에서 실행됩니다!

## 📋 통합 서비스 설명

### Backend - FastAPI 통합 서버 (`/backend/app/`)

**포트**: 8000
**기술**: FastAPI, aiosmtpd, Motor (async MongoDB), LangChain

**통합 라우트**:

| 경로 | 기능 | 소스 |
|------|------|------|
| `/api/v1/process` | DLP 문서 처리 및 마스킹 | `routers/process.py` |
| `/api/v1/ocr` | OCR 처리 (Clova API) | `routers/ocr.py` |
| `/api/v1/analyzer` | PII 분석기 | `routers/analyzer.py` |
| `/api/v1/files` | 파일 관리 | `routers/uploads.py` |
| `/api/v1/smtp/auth` | SMTP 로그인/인증 | `smtp/routes/auth.py` |
| `/api/v1/smtp/users` | SMTP 사용자 관리 | `smtp/routes/users.py` |
| `/api/v1/rag/*` | RAG 검색 (추후 확장) | `rag/` |

**포함된 서비스**:
- 🔐 **SMTP 서버**: 포트 2526 (내장)
- 📧 **메일 처리**: DLP 정책 자동 적용
- 🤖 **RAG**: LangGraph 기반 정책 검색
- 🔍 **PII 탐지**: Regex/NLP 기반 민감정보 감지
- 📄 **OCR**: Clova API 연동

**시작 방법**:
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend - 통합 웹 UI (`/frontend/`)

**기술**: Electron, JavaScript, HTML/CSS

**주요 기능**:
- 📊 **DLP 대시보드**: 문서 업로드, 분석, 마스킹
- 👥 **SMTP 관리**: 사용자 관리, 메일 승인/거부
- 📈 **분석 및 로그**: 감지 결과 조회, 통계
- 🔐 **권한 관리**: 관리자/감사자/사용자 역할

**API 연결**:
- 모든 API 호출이 `API_BASE_URL` 환경 변수로 제어됨
- 기본값: `http://127.0.0.1:8000`
- `.env` 파일의 `REACT_APP_API_URL`로 변경 가능

**시작 방법**:
```bash
cd frontend
npm install
npm start  # Electron 앱 실행
```

### Wiki - 문서 (`/wiki/`)

**포함된 문서**:
- `2_install.md` - 설치 및 환경 설정
- `3_analyzer.md` - PII 분석기 설정
- `5_PII_entities.md` - 감지 대상 개인정보 정의
- `7_redactor.md` - 데이터 마스킹 규칙
- `8_fastapi.md` - FastAPI 서버 설정
- `10_mailproxy.md` - SMTP 메일 프록시 상세 가이드
- `11_solutionDLP.md` - 전체 DLP 솔루션 개요

## 🔐 환경 변수 구성

### 필수 변수

```env
# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# Database
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=maskit

# Security
SECRET_KEY=your-secret-key-min-32-chars
DLP_SECRET_KEY=your-dlp-secret-key-min-32-chars

# SMTP
RECEIVE_SERVER_HOST=127.0.0.1
RECEIVE_SERVER_PORT=2526
```

### 선택적 변수

```env
# API 키
CLOVA_OCR_URL=...
CLOVA_OCR_SECRET=...

# 실제 메일 서버 (Gmail, SWU 등)
# RECEIVE_SERVER_HOST=smtp.gmail.com
# RECEIVE_SERVER_PORT=587
# RECEIVE_SERVER_USE_TLS=true
# RECEIVE_SERVER_USERNAME=...
# RECEIVE_SERVER_PASSWORD=...
```

상세한 설정은 프로젝트 루트의 `.env` 파일을 참고하세요.

## 📦 시스템 요구사항

### Backend
- **Python**: 3.8 이상
- **주요 의존성**:
  - FastAPI 0.109.0+
  - Pydantic 2.5.0+
  - Motor 3.3.0+ (async MongoDB)
  - aiosmtpd 1.4.4+ (SMTP 서버)
  - LangChain 0.1.0+ (RAG)
  - Torch 2.0.0+ (NLP)

### Frontend
- **Node.js**: 14 이상
- **주요 의존성**:
  - Electron (데스크톱 앱)
  - 기본 JavaScript (외부 프레임워크 최소화)

### 데이터베이스
- **MongoDB**: 4.0+ (로컬 또는 클라우드 Atlas)

### 선택사항
- **메일 서버**: Gmail, SWU, MailPlug 등 (SMTP 설정)
- **LLM**: Ollama, OpenAI (RAG용)

## 🧪 테스트

각 서비스의 테스트는 해당 디렉토리에서 실행하세요:

```bash
# Backend 테스트
cd backend
pytest

# Frontend 테스트
cd frontend
npm test
```

## 📚 추가 리소스

- **설치 가이드**: `wiki/2_install.md`
- **SMTP 상세 가이드**: `wiki/10_mailproxy.md`
- **DLP 분석기 설정**: `wiki/3_analyzer.md`
- **데이터 마스킹**: `wiki/7_redactor.md`
- **PII 정의**: `wiki/5_PII_entities.md`
- **FastAPI 설정**: `wiki/8_fastapi.md`
- **전체 솔루션 개요**: `wiki/11_solutionDLP.md`

## 🐛 문제 해결

### 포트 충돌
특정 포트가 이미 사용 중인 경우, `.env` 파일에서 포트 번호를 변경하세요.

### MongoDB 연결 실패
MongoDB URI가 올바른지 확인하고, 네트워크 연결을 확인하세요.

### 권한 문제
필요시 폴더 권한을 확인하세요:
```bash
chmod -R 755 ./
```

## 📝 라이센스

프로젝트의 라이센스는 각 서브 폴더를 참고하세요.

## 👥 기여

이 프로젝트에 기여하려면:

1. 로컬 브랜치 생성: `git checkout -b feature/your-feature`
2. 변경 사항 커밋: `git commit -m 'Add your feature'`
3. 브랜치 푸시: `git push origin feature/your-feature`
4. Pull Request 생성

---

**마지막 업데이트**: 2024년 11월 7일
