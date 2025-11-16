# MASKIT - React + shadcn/ui 버전

기존 HTML 기반 애플리케이션을 React + TypeScript + shadcn/ui로 변환한 버전입니다.

## 🚀 기술 스택

- **React 19** - UI 라이브러리
- **TypeScript** - 타입 안정성
- **Vite** - 빌드 도구
- **shadcn/ui** - UI 컴포넌트 라이브러리
- **Tailwind CSS** - 스타일링
- **Radix UI** - Headless UI 컴포넌트

## 📦 설치

모든 의존성이 이미 설치되어 있습니다. 추가 설치가 필요한 경우:

```bash
npm install
```

## 🏃 실행

### 개발 서버 실행

```bash
npm run dev
```

브라우저에서 http://localhost:3000 으로 자동으로 열립니다.

### 프로덕션 빌드

```bash
npm run build
```

빌드된 파일은 `dist` 폴더에 생성됩니다.

### 빌드 미리보기

```bash
npm run preview
```

## 📁 프로젝트 구조

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/           # shadcn/ui 컴포넌트
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── input.tsx
│   │   │   ├── label.tsx
│   │   │   └── select.tsx
│   │   └── AppLayout.tsx # 메인 레이아웃 컴포넌트
│   ├── pages/
│   │   ├── LoginPage.tsx     # 로그인 페이지
│   │   └── RegisterPage.tsx  # 회원가입 페이지
│   ├── lib/
│   │   └── utils.ts      # 유틸리티 함수
│   ├── App.tsx           # 메인 앱 컴포넌트
│   ├── main.tsx          # 진입점
│   └── index.css         # 글로벌 스타일
├── index-react.html      # HTML 템플릿
├── vite.config.ts        # Vite 설정
├── tailwind.config.js    # Tailwind CSS 설정
├── tsconfig.json         # TypeScript 설정
└── package.json
```

## 🎨 주요 기능

### 1. 로그인 페이지
- 사용자 정보 입력 폼
- 역할별 빠른 로그인 버튼 (테스트용)
- 회원가입 링크

### 2. 회원가입 페이지
- 이메일, 이름, 팀, 비밀번호 입력
- 비밀번호 확인 검증
- 로그인 페이지로 이동

### 3. 메인 레이아웃
- 반응형 사이드바
- 상단바 (사용자 정보, 로그아웃)
- 메뉴 네비게이션
- 모바일 대응

## 🎨 커스터마이징

### 색상 변경

`src/index.css` 파일에서 CSS 변수를 수정하여 테마 색상을 변경할 수 있습니다:

```css
:root {
  --primary: 20.5 90.2% 48.2%; /* 주요 색상 */
  /* 기타 색상... */
}
```

현재 primary 색상은 요청하신 `20.5 90.2% 48.2%` (주황색 계열)로 설정되어 있습니다.

### 새 컴포넌트 추가

shadcn/ui의 다른 컴포넌트를 추가하려면 공식 문서를 참고하세요:
https://ui.shadcn.com

## 📝 주요 변경사항

기존 HTML/CSS/JavaScript 코드를 다음과 같이 변환했습니다:

1. **구조**: HTML → React 컴포넌트
2. **스타일**: CSS → Tailwind CSS
3. **로직**: JavaScript → TypeScript
4. **UI 컴포넌트**: 커스텀 CSS → shadcn/ui

## 🔄 기존 Electron 앱과의 호환성

기존 Electron 앱은 그대로 유지됩니다:

```bash
# 기존 Electron 앱 실행
npm run electron

# 개발 모드
npm run electron:dev
```

## 🔗 Backend API 연동

### 환경 설정

`.env` 파일에서 backend API URL 설정:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

### API 기능

정책 업로드 페이지에서 다음 기능이 구현되었습니다:

1. **멀티모달 파일 업로드** (PDF, PNG, JPG, JPEG)
2. **실시간 진행률 추적** (Toast 알림)
   - 파일 업로드 진행률
   - Zerox OCR / PyMuPDF 텍스트 추출
   - OpenAI Vision API 이미지 처리
   - VectorDB 임베딩 진행률
   - 가이드라인 추출 상태
3. **백그라운드 Task 폴링**
   - 2초마다 task 상태 확인
   - 실시간 진행률 업데이트

### 사용된 Backend Endpoints

- `POST /api/policies/upload` - 정책 파일 업로드
- `GET /api/policies/tasks/{task_id}/status` - 백그라운드 작업 진행률 조회
- `GET /api/policies/list` - 정책 목록 조회
- `GET /api/policies/{policy_id}` - 정책 상세 조회
- `DELETE /api/policies/{policy_id}` - 정책 삭제
- `GET /api/policies/stats/summary` - 정책 통계

### Toast 알림 시스템

Sonner 라이브러리를 사용하여 다음 알림을 제공합니다:

- ✅ 업로드 시작/완료
- 📊 실시간 진행률 (0-100%)
- ⚠️ 에러 메시지
- ℹ️ 처리 단계별 상태 (OCR, 임베딩, 가이드라인 추출)

## 💡 다음 단계

1. ✅ ~~실제 API 연동~~ (완료)
2. ✅ ~~Toast 알림 시스템~~ (완료)
3. 상태 관리 추가 (React Context 또는 Zustand)
4. 라우팅 개선 (React Router)
5. 폼 검증 강화 (React Hook Form + Zod)
6. 각 페이지별 상세 구현

## 📚 참고 자료

- [React Documentation](https://react.dev)
- [shadcn/ui Documentation](https://ui.shadcn.com)
- [Tailwind CSS Documentation](https://tailwindcss.com)
- [Vite Documentation](https://vitejs.dev)
