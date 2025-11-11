---
layout: default
title: Wiki Home
nav_order: 1
---

# Enterprise GuardCAP (MASKIT) - Wiki Documentation

기업용 DLP (Data Loss Prevention) 솔루션 **MASKIT**의 공식 문서입니다.

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
├── wiki/                        # 문서 및 가이드 (이 디렉토리)
│   ├── 2_install.md
│   ├── 3_analyzer.md
│   ├── 5_PII_entities.md
│   ├── 7_redactor.md
│   ├── 8_fastapi.md
│   ├── 10_mailproxy.md
│   └── README.md (이 파일)
│
├── .env                         # 통합 환경 설정 (마스킹됨)
├── .gitignore                   # Git 무시 파일 (.env 포함)
├── QUICK_START.md               # 빠른 시작 가이드
└── README.md                    # 프로젝트 루트 README
```

## 문서 구성

이 위키에는 다음과 같은 문서들이 포함되어 있습니다:

1. **[Overview](index.md)** - MASKIT 서비스 개요 및 주요 기능
2. **[설치 및 사용법](2_install.md)** - 시스템 설치 및 역할별 사용 가이드
3. **[Analyzer](3_analyzer.md)** - PII 분석 엔진 설명
4. **[기술 스택](4_techstack.md)** - 사용된 기술 스택 및 시스템 아키텍처
5. **[PII Entities](5_PII_entities.md)** - 탐지 가능한 개인정보 엔티티 목록
6. **[LLM](6_LLM.md)** - LLM/RAG 기반 정책 관리 시스템
7. **[Redactor](7_redactor.md)** - 마스킹 및 익명화 엔진
8. **[FastAPI](8_fastapi.md)** - 백엔드 API 문서
9. **[User Interface](9_userinterface.md)** - 프론트엔드 UI 가이드
10. **[Mail Proxy](10_mailproxy.md)** - SMTP 프록시 서버 구조
11. **[Solution DLP](11_solutionDLP.md)** - DLP 솔루션 통합 가이드
12. **[System Architecture](12_system_architecture.md)** - 시스템 아키텍처 및 데이터 흐름
13. **[Backend Guide](13_backend_guide.md)** - 백엔드 개발 가이드
14. **[Frontend Guide](14_frontend_guide.md)** - 프론트엔드 개발 가이드

## ✨ 주요 특징

### 통합 Backend (FastAPI)
- **단일 포트 (8000)**: 모든 서비스가 하나의 FastAPI 인스턴스로 실행
- **통합 라우트**:
  - `/api/v1/process` - DLP 분석
  - `/api/v1/ocr` - OCR 처리
  - `/api/v1/smtp` - SMTP 인증 및 사용자 관리
  - `/api/v1/files` - 파일 관리
  - `/api/v1/analyzer` - 분석기
  - `/api/entities` - 엔티티 관리
  - `/api/vectordb` - 정책 스키마 관리
- **SMTP 내장**: aiosmtpd를 통한 내장 SMTP 서버
- **RAG 통합**: LangChain 기반 RAG 시스템

### 통합 Frontend
- **동적 API 연결**: `API_BASE_URL` 환경 변수 기반
- **모든 UI 통합**: DLP/SMTP/분석 대시보드
- **Electron 기반**: 데스크톱 애플리케이션
- **역할 기반 대시보드**: Root Admin, Policy Admin, Auditor, Approver, User

### 통합 환경 설정
- **단일 .env 파일**: 모든 서비스 설정 중앙화
- **.gitignore 마스킹**: 민감한 정보 보호

## 빠른 시작

MASKIT을 처음 사용하시나요? 다음 순서로 읽어보세요:

1. **[QUICK_START.md](../QUICK_START.md)** - 빠른 시작 가이드 (설치 및 실행)
2. **[서비스 개요](index.md)** - MASKIT이 무엇인지 이해하기
3. **[설치 및 사용법](2_install.md)** - 시스템 설치 및 첫 로그인
4. **[기술 스택](4_techstack.md)** - 시스템 아키텍처 이해하기

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

## 📚 추가 리소스

- **빠른 시작**: `../QUICK_START.md`
- **설치 가이드**: `2_install.md`
- **SMTP 상세 가이드**: `10_mailproxy.md`
- **DLP 분석기 설정**: `3_analyzer.md`
- **데이터 마스킹**: `7_redactor.md`
- **PII 정의**: `5_PII_entities.md`
- **FastAPI 설정**: `8_fastapi.md`
- **전체 솔루션 개요**: `11_solutionDLP.md`

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

---

**마지막 업데이트**: 2024년 11월 11일
