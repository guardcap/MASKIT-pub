---
layout: default
title: MASKIT 설치 및 사용법
nav_order: 2
---

# MASKIT 설치 및 사용법

## 시스템 요구사항

### 필수 소프트웨어
- **Python**: 3.9 이상
- **Node.js**: 14.0 이상
- **MongoDB**: Atlas 클라우드 계정 또는 로컬 설치
- **Git**: 최신 버전

### 권장 사양
- **OS**: macOS, Linux, Windows 10/11
- **RAM**: 최소 8GB
- **저장공간**: 최소 2GB

---

## 설치 방법

### 1. 저장소 클론

```bash
git clone https://github.com/your-org/enterprise-guardcap.git
cd enterprise-guardcap
```

### 2. 백엔드 설정

#### 2.1 Python 가상환경 생성

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

#### 2.2 백엔드 의존성 설치

```bash
pip install -r backend/requirements.txt
```

#### 2.3 환경변수 설정

프로젝트 루트에 `.env` 파일 생성:

```env
# Backend Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# MongoDB
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=maskit

# JWT Security
SECRET_KEY=your-secret-key-minimum-32-characters-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Frontend
REACT_APP_API_URL=http://127.0.0.1:8000
```

⚠️ **보안 주의**: `.env` 파일은 절대 Git에 커밋하지 마세요!

### 3. 프론트엔드 설정

#### 3.1 Node.js 의존성 설치

```bash
cd frontend
npm install
```

#### 3.2 Electron 앱 설정

`package.json`이 이미 설정되어 있습니다.

---

## 실행 방법

### 백엔드 서버 실행

```bash
cd /path/to/enterprise-guardcap
source venv/bin/activate
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

서버가 정상 실행되면 다음 메시지가 표시됩니다:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
✅ MongoDB 연결 완료
```

### 프론트엔드 실행

#### 방법 1: 브라우저에서 실행
```bash
# frontend/index.html 파일을 브라우저에서 직접 열기
open frontend/index.html  # macOS
```

#### 방법 2: Electron 데스크톱 앱 실행
```bash
cd frontend
npm start
```

---

## 사용 방법

### 1. 초기 로그인

애플리케이션을 처음 실행하면 로그인 페이지가 표시됩니다.

#### 테스트 계정 사용하기

개발 및 테스트를 위해 5개의 테스트 계정이 준비되어 있습니다:

| 역할 | 이메일 | 비밀번호 | 대시보드 |
|------|--------|----------|----------|
| 시스템 관리자 | admin@test.com | admin123 | 시스템 설정 |
| 정책 관리자 | policy@test.com | policy123 | 정책 관리 |
| 승인자 | approver@test.com | approver123 | 승인 대시보드 |
| 감사자 | auditor@test.com | auditor123 | 감사 대시보드 |
| 일반 사용자 | user@test.com | user123 | 메일 목록 |

로그인 페이지 하단의 **테스트 계정 버튼**을 클릭하면 자동으로 로그인됩니다.

### 2. 역할별 기능

#### 2.1 일반 사용자 (user)

**메일 작성 및 전송**
1. 대시보드 우측 하단의 **✉️ 메일 작성** 버튼 클릭
2. 받는 사람, 제목, 본문 입력
3. 필요시 파일 첨부 (드래그 앤 드롭 지원)
4. **▶ 보내기** 버튼 클릭

**메일 목록 확인**
- **전체**: 모든 메일 보기
- **승인 대기**: 관리자 승인 대기 중인 메일
- **승인 완료**: 승인되어 전송된 메일
- **반려**: 승인 거부된 메일

#### 2.2 승인자 (approver)

**메일 승인 프로세스**
1. 승인 대기 메일 목록에서 메일 선택
2. 본문 및 첨부파일 검토
3. DLP 정책 위반 사항 확인
4. **승인** 또는 **반려** 버튼 클릭
   - 승인: 메일이 외부로 전송됨
   - 반려: 발신자에게 재작성 요청

#### 2.3 정책 관리자 (policy_admin)

**DLP 정책 관리**
- 정책 생성/수정/삭제
- 엔티티 관리 (정규식, 키워드)
- 정책 테스트 및 시뮬레이션
- 정책 적용 통계 확인

#### 2.4 감사자 (auditor)

**감사 및 로그 확인**
- 전체 메일 이력 조회 (읽기 전용)
- 전체 로그 확인
- 통계 및 리포트 생성
- 정책 조회 (읽기 전용)

#### 2.5 시스템 관리자 (root_admin)

**시스템 설정**
- 사용자 계정 생성/수정/삭제
- 역할 할당
- 시스템 통계 확인
- 팀 및 부서 관리

### 3. API 문서 확인

백엔드 서버 실행 후, 브라우저에서 다음 주소로 접속:

```
http://localhost:8000/docs
```

Swagger UI를 통해 모든 API 엔드포인트를 확인하고 테스트할 수 있습니다.

---

## 문제 해결

### 백엔드가 시작되지 않을 때

**증상**: `ModuleNotFoundError` 발생
```bash
# 해결방법
pip install -r backend/requirements.txt
```

**증상**: MongoDB 연결 실패
```bash
# 해결방법
# .env 파일의 MONGODB_URI 확인
# MongoDB Atlas 콘솔에서 IP 화이트리스트 확인
```

### 프론트엔드가 로드되지 않을 때

**증상**: 로그인 후 대시보드로 이동하지 않음
```bash
# 해결방법
# 브라우저 개발자 도구 열기 (F12)
# Console 탭에서 에러 확인
# localStorage 초기화: localStorage.clear()
```

**증상**: API 호출 실패 (CORS 에러)
```bash
# 해결방법
# backend/app/main.py에서 CORS 설정 확인
# 백엔드 서버가 실행 중인지 확인
```

### 로그인 문제

**증상**: "이메일 또는 비밀번호가 올바르지 않습니다"
```bash
# 해결방법
# 테스트 계정 비밀번호 확인
# 백엔드 서버 로그 확인
# MongoDB에 사용자 데이터 존재 확인
```

---

## 추가 리소스

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [MongoDB Atlas 가이드](https://www.mongodb.com/docs/atlas/)
- [Electron 공식 문서](https://www.electronjs.org/docs/latest)

---

## 개발자 팁

### 개발 모드 실행

**백엔드 Hot Reload**
```bash
uvicorn app.main:app --reload
```

**프론트엔드 개발자 도구**
- Electron 앱에서 자동으로 DevTools가 열립니다
- `Cmd+Option+I` (macOS) 또는 `Ctrl+Shift+I` (Windows/Linux)

### 데이터베이스 초기화

```bash
# MongoDB 컬렉션 삭제 (주의!)
# MongoDB Compass 또는 Atlas 콘솔에서 수동으로 삭제
```

### 로그 확인

**백엔드 로그**
```bash
# 터미널에서 uvicorn 실행 시 실시간 로그 확인
tail -f /tmp/backend.log  # 백그라운드 실행 시
```

**프론트엔드 로그**
```bash
# 브라우저 개발자 도구 Console 탭
# Electron 앱: View > Toggle Developer Tools
``` 