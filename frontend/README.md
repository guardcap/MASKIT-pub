# Enterprise GuardCAP - Frontend

통합 웹 사용자 인터페이스 및 Electron 데스크톱 애플리케이션입니다.

## 📋 구조

```
frontend/
├── index.js              # Electron 메인 프로세스
├── index.html            # 메인 HTML 파일
├── script.js             # DLP 대시보드 로직 (API_BASE_URL 기반)
├── app.js                # 애플리케이션 초기화
├── auth.js               # 인증 로직
├── router.js             # 페이지 라우팅
├── style.css             # 스타일
├── smtp/                 # SMTP 관련 UI 페이지
│   ├── login.html
│   ├── dashboard-*.html
│   └── pages/
├── pages/                # 추가 페이지
└── package.json
```

## 🚀 시작 방법

### 1. 의존성 설치

```bash
cd frontend
npm install
```

### 2. Backend 실행 (필수)

Frontend는 Backend API(`http://127.0.0.1:8000`)와 통신합니다.

```bash
# 다른 터미널에서
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend 실행

```bash
npm start  # Electron 앱 실행
```

## 🔧 환경 변수

### 루트 `.env` 파일에서 설정:

```env
# Frontend API 연결 설정
REACT_APP_API_URL=http://127.0.0.1:8000
REACT_APP_API_TIMEOUT=30000
```

Frontend의 `script.js`에서:
```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';
```

## 📱 주요 페이지

### DLP 대시보드 (`index.html`)
- 문서 업로드 및 분석
- PII 탐지 및 마스킹
- 결과 확인 및 다운로드

### SMTP 관리 (`smtp/` 폴더)
- `login.html` - 사용자 로그인
- `dashboard-admin.html` - 관리자 대시보드
- `dashboard-user.html` - 일반 사용자 대시보드
- `user-management.html` - 사용자 관리
- `pending-approvals.html` - 메일 승인/거부
- `email-detail.html` - 메일 상세 조회

## 🔌 API 연결

모든 API 호출은 `API_BASE_URL`을 기반으로 합니다:

```javascript
// 예: 파일 목록 조회
fetch(`${API_BASE_URL}/api/v1/files/files`)

// 예: SMTP 로그인
fetch(`${API_BASE_URL}/api/v1/smtp/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username, password })
})
```

## 🎨 Electron 설정

`index.js`에서 Electron 창 설정:

```javascript
const mainWindow = new BrowserWindow({
  width: 1400,
  height: 900,
  webPreferences: {
    nodeIntegration: true,
    contextIsolation: false
  }
});
```

## 🧪 개발

### 개발 모드 실행
```bash
npm run dev
```

### 개발 도구 열기
- Electron 창에서 `F12` 또는 `Cmd+Option+I` (Mac)

## 📦 빌드 (선택사항)

현재 빌드 설정은 준비 중입니다.

## 🔗 관련 문서

- [루트 README](../README.md) - 전체 프로젝트 정보
- [Backend 정보](../backend/README.md) - 서버 API 문서
- [SMTP 가이드](../wiki/10_mailproxy.md) - SMTP 상세 가이드

## ⚙️ 트러블슈팅

### "Cannot find module" 오류
```bash
# node_modules 재설치
rm -rf node_modules package-lock.json
npm install
```

### Backend 연결 실패
- Backend가 포트 8000에서 실행 중인지 확인
- `.env` 파일에서 `REACT_APP_API_URL` 확인
- 브라우저 개발 도구에서 네트워크 탭 확인

### Electron 앱이 열리지 않음
```bash
# 전역 electron 설치
npm install -g electron

# 또는 로컬 실행
npx electron .
```

---

**마지막 업데이트**: 2024년 11월 7일
