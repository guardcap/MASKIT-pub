---
layout: default
title: 사용한 기술 스택 및 시스템 구조
nav_order: 4
---

# 기술 스택 및 시스템 구조

## 전체 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                         사용자                                    │
└────────────────────┬────────────────────────────────────────────┘
                     │
        ┌────────────▼──────────────┐
        │  Electron Desktop App     │
        │  (Frontend)               │
        │  - HTML/CSS/JavaScript    │
        │  - localStorage (Session) │
        └────────────┬──────────────┘
                     │ HTTP/REST API
        ┌────────────▼──────────────┐
        │  FastAPI Backend          │
        │  - Python 3.9+            │
        │  - Async/Await            │
        │  - JWT Authentication     │
        └───────┬──────────┬────────┘
                │          │
     ┌──────────▼─┐    ┌──▼─────────────┐
     │  MongoDB   │    │  AI Services   │
     │  (Atlas)   │    │  - OCR         │
     │            │    │  - NER         │
     └────────────┘    │  - LLM/RAG     │
                       └────────────────┘
```

---

## 프론트엔드 스택

### 핵심 기술

#### Electron
- **버전**: 최신 안정 버전
- **용도**: 크로스 플랫폼 데스크톱 애플리케이션
- **장점**:
  - Windows, macOS, Linux 동시 지원
  - 웹 기술로 네이티브 앱 개발
  - 자동 업데이트 지원

#### HTML5 / CSS3 / JavaScript (ES6+)
- **HTML5**: 시맨틱 마크업
- **CSS3**:
  - Flexbox & Grid 레이아웃
  - CSS Variables
  - 그라디언트 및 애니메이션
- **JavaScript**:
  - ES6+ 문법 (async/await, arrow functions)
  - Fetch API
  - localStorage API

### UI/UX 라이브러리

- **Inter Font**: 가독성 높은 서체
- **커스텀 CSS**: 기업용 디자인 시스템
- **반응형 디자인**: 다양한 화면 크기 지원

### 주요 기능 구현

#### 인증 시스템
```javascript
// JWT 토큰 기반 인증
localStorage.setItem('auth_token', token);
localStorage.setItem('user', JSON.stringify(user));
```

#### 역할 기반 라우팅 (RBAC)
```javascript
// 5가지 역할 지원
- root_admin: 시스템 관리
- policy_admin: 정책 관리
- approver: 메일 승인
- auditor: 감사 및 모니터링
- user: 일반 사용자
```

---

## 백엔드 스택

### 핵심 프레임워크

#### FastAPI
- **버전**: 0.109.0+
- **특징**:
  - Python 3.9+ 기반
  - 자동 OpenAPI 문서 생성 (`/docs`)
  - 고성능 비동기 처리
  - Pydantic 기반 데이터 검증
  - 타입 힌팅 지원

#### Uvicorn
- **버전**: 0.35.0+
- **용도**: ASGI 서버
- **특징**:
  - 비동기 I/O 지원
  - Hot reload 개발 모드
  - 고성능 HTTP 처리

### 데이터베이스

#### MongoDB Atlas
- **드라이버**: Motor (비동기)
- **버전**: 3.3.0+
- **장점**:
  - NoSQL 유연한 스키마
  - 클라우드 기반 (Atlas)
  - 자동 백업 및 복구
  - 확장성 우수

**주요 컬렉션**:
```javascript
{
  users: {
    email: String (unique),
    hashed_password: String,
    nickname: String,
    role: Enum[root_admin, policy_admin, approver, auditor, user],
    created_at: DateTime,
    updated_at: DateTime
  },
  emails: {
    from_email: String,
    to_email: String,
    subject: String,
    body: String,
    status: Enum[pending, approved, rejected],
    attachments: Array,
    created_at: DateTime
  }
}
```

### 보안 및 인증

#### Python-Jose
- **용도**: JWT 토큰 생성 및 검증
- **알고리즘**: HS256
- **토큰 만료**: 1440분 (24시간)

#### Passlib + Bcrypt
- **용도**: 비밀번호 해싱
- **Bcrypt Rounds**: 12
- **특징**: Salt 자동 생성

#### CORS Middleware
- **용도**: 크로스 오리진 요청 허용
- **설정**: 개발 환경에서 모든 오리진 허용
- **프로덕션**: 특정 도메인만 허용

### API 구조

```
/api/v1/
├── smtp/
│   ├── auth/
│   │   ├── POST /register      # 사용자 등록
│   │   ├── POST /login         # 로그인
│   │   └── GET  /me            # 현재 사용자 정보
│   ├── users/                   # 사용자 관리
│   └── emails/                  # 메일 관리
├── dlp/                         # DLP 엔진
└── rag/                         # RAG 시스템
```

---

## AI/ML 스택

### OCR (Optical Character Recognition)

#### Tesseract OCR
- **용도**: 이미지 및 PDF에서 텍스트 추출
- **지원 언어**: 한국어, 영어
- **통합**: `pytesseract` 라이브러리

#### PyZerox
- **버전**: 0.0.7+
- **용도**: PDF OCR 전문 처리
- **특징**: 좌표 기반 텍스트 추출

### NER (Named Entity Recognition)

#### Presidio Analyzer
- **버전**: 2.2.354+
- **용도**: 개인정보 자동 탐지
- **지원 엔티티**:
  - 주민등록번호
  - 전화번호
  - 이메일 주소
  - 신용카드 번호
  - 은행 계좌번호
  - 건강 정보 등

**탐지 가능한 PII**:
```python
SUPPORTED_ENTITIES = [
    "CREDIT_CARD",
    "CRYPTO",
    "EMAIL_ADDRESS",
    "IBAN_CODE",
    "IP_ADDRESS",
    "PERSON",
    "PHONE_NUMBER",
    "US_SSN",
    "KR_RRN"  # 한국 주민등록번호
]
```

#### Presidio Anonymizer
- **버전**: 2.2.354+
- **용도**: PII 마스킹 및 익명화
- **지원 방법**:
  - Replace: 대체 텍스트로 교체
  - Mask: 특정 문자로 마스킹 (예: ***)
  - Hash: 해시값으로 변환
  - Redact: 완전 삭제

### LLM/RAG

#### ChromaDB
- **버전**: 0.5.3+
- **용도**: 벡터 데이터베이스
- **특징**:
  - 정책 문서 임베딩 저장
  - 유사도 기반 검색
  - 메모리 내 처리

#### OpenAI API / LiteLLM
- **용도**:
  - 상황별 마스킹 결정
  - 정책 기반 판단
  - 자연어 처리

---

## 개발 도구

### 버전 관리
- **Git**: 소스 코드 관리
- **.gitignore**: 민감 정보 제외 (.env, venv/)

### 패키지 관리
- **Python**: pip + requirements.txt
- **Node.js**: npm + package.json

### API 테스트
- **Swagger UI**: `/docs` 엔드포인트
- **curl**: 커맨드라인 테스트
- **Postman**: GUI 기반 테스트

### 환경 변수 관리
- **python-dotenv**: .env 파일 로드
- **환경변수**:
  ```
  BACKEND_HOST
  BACKEND_PORT
  MONGODB_URI
  SECRET_KEY
  ALGORITHM
  ACCESS_TOKEN_EXPIRE_MINUTES
  ```

---

## 시스템 요구사항

### 서버 사양 (프로덕션)
- **CPU**: 4 코어 이상
- **RAM**: 8GB 이상
- **Storage**: 20GB 이상 (SSD 권장)
- **OS**: Ubuntu 20.04 LTS 이상

### 클라이언트 사양
- **CPU**: 2 코어 이상
- **RAM**: 4GB 이상
- **OS**: Windows 10/11, macOS 10.15+, Ubuntu 18.04+

---

## 배포 아키텍처

### 개발 환경
```
로컬 머신
├── Backend: localhost:8000
├── Frontend: Electron App
└── Database: MongoDB Atlas (Cloud)
```

### 프로덕션 환경 (권장)
```
┌─────────────────────┐
│   Load Balancer     │
└──────────┬──────────┘
           │
    ┌──────▼──────┐
    │  Nginx      │
    │  (Reverse   │
    │   Proxy)    │
    └──────┬──────┘
           │
    ┌──────▼──────────────┐
    │  FastAPI Instances  │
    │  (Uvicorn Workers)  │
    │  - 4~8 workers      │
    └──────┬──────────────┘
           │
    ┌──────▼──────────────┐
    │  MongoDB Atlas      │
    │  (Replica Set)      │
    └─────────────────────┘
```

---

## 성능 최적화

### 백엔드
- **비동기 처리**: asyncio, Motor 사용
- **Connection Pool**: MongoDB 연결 풀링
- **캐싱**: 반복 쿼리 결과 캐싱
- **파일 업로드**: 스트리밍 처리

### 프론트엔드
- **로컬스토리지**: 세션 데이터 캐싱
- **Lazy Loading**: 필요한 페이지만 로드
- **번들 최적화**: 불필요한 라이브러리 제거

---

## 보안 고려사항

### 데이터 암호화
- **전송**: HTTPS/TLS (프로덕션)
- **저장**: MongoDB 암호화
- **비밀번호**: Bcrypt 해싱

### 인증/인가
- **JWT**: 무상태 토큰 인증
- **RBAC**: 역할 기반 접근 제어
- **세션 만료**: 24시간 후 재로그인

### 보안 헤더
- **CORS**: 허용 도메인 제한
- **Content-Type**: 검증
- **Input Validation**: Pydantic 모델

---

## 확장성

### 수평 확장
- FastAPI 인스턴스 추가
- Load Balancer 사용
- MongoDB Replica Set

### 수직 확장
- 서버 사양 업그레이드
- 메모리 증설
- SSD 스토리지

---

## 모니터링 및 로깅

### 로그 레벨
```python
DEBUG: 개발 단계
INFO: 일반 정보
WARNING: 경고
ERROR: 에러
CRITICAL: 심각한 오류
```

### 모니터링 도구 (권장)
- **Prometheus**: 메트릭 수집
- **Grafana**: 시각화
- **Sentry**: 에러 추적