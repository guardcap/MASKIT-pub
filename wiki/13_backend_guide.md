---
layout: default
title: Backend Guide
nav_order: 14
---
# Backend Guide

FastAPI 기반의 통합 백엔드 서버 가이드입니다.

## 구조

```
backend/
├── app/
│   ├── main.py                 # FastAPI 메인 앱
│   ├── routers/                # DLP/OCR 라우터
│   ├── smtp/                   # SMTP 모듈
│   ├── rag/                    # RAG 시스템
│   └── utils/                  # 공유 유틸리티
├── requirements.txt
└── run.py
```

## 시작 방법

### 1. 가상 환경 설정

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 서버 실행

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 문서: http://localhost:8000/docs

## API 엔드포인트

### DLP/OCR API
- `GET /api/v1/files/files` - 파일 목록
- `POST /api/v1/files/upload` - 파일 업로드
- `POST /api/v1/process/documents` - 문서 처리 및 PII 분석
- `POST /api/v1/analyzer/analyze` - PII 분석

### SMTP API
- `POST /api/v1/smtp/auth/login` - 로그인
- `POST /api/v1/smtp/auth/register` - 회원가입
- `GET /api/v1/smtp/users` - 사용자 목록

### 엔티티 관리 API
- `GET /api/entities/recognizers` - Recognizer 목록
- `POST /api/entities/` - 엔티티 생성
- `PUT /api/entities/{entity_id}` - 엔티티 수정
- `DELETE /api/entities/{entity_id}` - 엔티티 삭제

### 정책 관리 API
- `GET /api/vectordb/guides/grouped` - 정책 스키마 조회
- `POST /api/vectordb/sync/rebuild` - VectorDB 재구축

자세한 내용은 `/docs` (Swagger UI)를 참고하세요.
