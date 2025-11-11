---
layout: default
title: Frontend Guide
nav_order: 15
---
# Frontend Guide

Electron 기반의 프론트엔드 가이드입니다.

## 구조

```
frontend/
├── index.html              # 인증 진입점
├── index.js                # Electron 메인 프로세스
├── script.js               # 글로벌 스크립트
├── style.css               # 글로벌 스타일
├── smtp/                   # SMTP 관련 페이지
│   ├── login.html
│   ├── register.html
│   ├── dashboard-admin.html
│   ├── dashboard-policy-admin.html
│   ├── dashboard-approver.html
│   ├── dashboard-auditor.html
│   ├── dashboard-user.html
│   └── pages/              # 관리 페이지
│       ├── entity-management.html
│       ├── policy-management.html
│       ├── dlp-statistics.html
│       └── decision-logs.html
├── pages/                  # 기타 페이지
└── package.json
```

## 시작 방법

### 1. 의존성 설치

```bash
cd frontend
npm install
```

### 2. 실행

```bash
npm start  # Electron 앱 실행
```

## 주요 기능

### 역할 기반 대시보드

사용자 역할에 따라 다른 대시보드로 자동 라우팅됩니다:

- **root_admin**: 시스템 관리자 (사용자/팀 관리)
- **policy_admin**: 정책 관리자 (엔티티/정책 CRUD)
- **approver**: 승인자 (메일 승인/반려)
- **auditor**: 감사자 (읽기 전용 통계)
- **user**: 일반 사용자 (메일 작성)

### 인증 플로우

1. 사용자가 `index.html` 접속
2. localStorage에서 `auth_token` 확인
3. 토큰 있으면 역할에 맞는 대시보드로 이동
4. 토큰 없으면 `login.html`로 리다이렉트

### API 연결

모든 API 호출은 `API_BASE_URL` 환경 변수 사용:
- 기본값: `http://127.0.0.1:8000`
- 각 HTML 파일에서 `const API_BASE = 'http://127.0.0.1:8000';`로 설정

### 주요 페이지

#### 엔티티 관리 (`smtp/pages/entity-management.html`)
- Recognizer 목록 조회
- 커스텀 엔티티 추가 (regex, keywords)
- 엔티티 수정/삭제
- 캐시 관리

#### 정책 관리 (`smtp/pages/policy-management.html`)
- VectorDB 정책 스키마 관리
- source_document별 그룹화
- CRUD 및 VectorDB 동기화

#### DLP 통계 (`smtp/pages/dlp-statistics.html`)
- 탐지 통계
- 차트 및 그래프

#### 결정 로그 (`smtp/pages/decision-logs.html`)
- 승인/반려 히스토리
- 타임라인 뷰

## 개발 팁

### 로컬 스토리지
```javascript
// 토큰 저장
localStorage.setItem('auth_token', token);
localStorage.setItem('user', JSON.stringify(user));

// 토큰 조회
const token = localStorage.getItem('auth_token');
const user = JSON.parse(localStorage.getItem('user'));
```

### API 호출 예시
```javascript
const response = await fetch(`${API_BASE}/api/entities/recognizers`, {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

### 대시보드 돌아가기
모든 관리 페이지에는 "← 대시보드" 버튼이 있어 역할에 맞는 대시보드로 이동합니다.
