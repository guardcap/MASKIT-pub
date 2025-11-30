# 백그라운드 작업 토스트 알림 시스템

PDF 업로드 및 정책 스키마 생성과 같은 백그라운드 작업의 진행 상황을 실시간으로 추적하고 표시하는 토스트 알림 시스템입니다.

## 🌟 주요 기능

### 1. **실시간 진행 상황 추적**
- 백엔드 API (`/api/policies/tasks/{task_id}/status`)를 3초마다 폴링
- 진행률(%), 현재 단계, 상태를 실시간으로 업데이트
- 스피너 애니메이션과 프로그레스 바로 시각적 피드백

### 2. **페이지 이동 시에도 유지**
- LocalStorage를 통한 작업 상태 저장
- 페이지를 이동하거나 새로고침해도 토스트 알림이 계속 표시됨
- 브라우저를 닫았다가 다시 열어도 진행 중인 작업 복원 (24시간 이내)

### 3. **자동 상태 관리**
- **처리 중**: 파란색 테두리, 스피너, 진행률 표시
- **완료**: 초록색 테두리, ✅ 아이콘, "정책 보기" 버튼
- **실패**: 빨간색 테두리, ❌ 아이콘, 에러 메시지 표시

### 4. **사용자 친화적 UI**
- 우측 상단에 고정된 토스트 컨테이너
- 슬라이드 인/아웃 애니메이션
- 닫기 버튼으로 수동 제거 가능
- 완료/실패 시 10초 후 자동 제거

## 📦 파일 구조

```
frontend/
├── toast-notification.js          # 토스트 알림 시스템 (메인)
├── test-toast.html                 # 테스트 페이지
└── pages/
    ├── policy-add.html             # 정책 추가 페이지 (통합됨)
    ├── dashboard-policy.html       # 대시보드 (통합됨)
    ├── policy-management.html      # 정책 관리 (통합됨)
    └── entity-management.html      # 엔티티 관리 (통합됨)
```

## 🚀 사용 방법

### 1. HTML 페이지에 스크립트 추가

```html
<script src="../toast-notification.js"></script>
```

### 2. 백그라운드 작업 시작 시 토스트 추가

```javascript
// 토스트 매니저 초기화
const toastManager = initBackgroundTaskToast();

// 작업 업로드 후 task_id 받기
const response = await fetch(`${API_BASE}/api/policies/upload`, {
    method: 'POST',
    body: formData
});

const result = await response.json();
const taskId = result.data.task_id;
const title = result.data.title;

// 토스트 알림 추가
if (taskId && toastManager) {
    toastManager.addTask(
        taskId,                                    // 백엔드에서 받은 task_id
        `📄 ${title}`,                              // 표시할 제목
        'PDF 텍스트 추출 및 스키마 생성 중...'      // 초기 설명
    );
}
```

### 3. 자동 진행 상황 추적

`addTask()`를 호출하면 자동으로:
1. 3초마다 `/api/policies/tasks/{task_id}/status` API 호출
2. 응답 데이터로 토스트 UI 업데이트
3. 완료/실패 시 폴링 중지
4. LocalStorage에 상태 자동 저장

## 🎨 토스트 UI 구성

```
┌──────────────────────────────────────┐
│ 🔄 정책문서.pdf                 ✖   │  ← 헤더 (아이콘 + 제목 + 닫기)
├──────────────────────────────────────┤
│ PDF 텍스트 추출 및 스키마 생성 중... │  ← 본문 (현재 단계 설명)
├──────────────────────────────────────┤
│ ████████████░░░░░░░░░░░░░░░░░░░░    │  ← 프로그레스 바 (진행률)
├──────────────────────────────────────┤
│ 처리 중... 45%              2분 전    │  ← 하단 (상태 + 경과 시간)
└──────────────────────────────────────┘

완료 시:
┌──────────────────────────────────────┐
│ ✅ 정책문서.pdf                 ✖   │
├──────────────────────────────────────┤
│ 스키마 생성 및 VectorDB 임베딩 완료  │
├──────────────────────────────────────┤
│ ████████████████████████████████████ │
├──────────────────────────────────────┤
│ 완료!                        3분 전    │
├──────────────────────────────────────┤
│  [정책 보기]           [닫기]        │  ← 액션 버튼
└──────────────────────────────────────┘
```

## 🔧 API 응답 형식

백엔드 API (`/api/policies/tasks/{task_id}/status`)는 다음 형식으로 응답해야 합니다:

```json
{
    "success": true,
    "data": {
        "task_id": "task-123abc",
        "status": "processing",           // "processing" | "completed" | "failed"
        "progress": 45,                   // 0-100
        "current_step": "OpenAI로 스키마 생성 중...",
        "error": null                     // 실패 시 에러 메시지
    }
}
```

## 🧪 테스트

1. **테스트 페이지 열기**
   ```
   http://localhost:3000/test-toast.html
   ```

2. **테스트 시나리오**
   - "처리 중 작업 시뮬레이션" 클릭 → 10초간 0%→100% 진행
   - "완료된 작업 시뮬레이션" 클릭 → 즉시 완료 상태 표시
   - "실패한 작업 시뮬레이션" 클릭 → 2초 후 에러 표시
   - "대시보드로 이동" 클릭 → 다른 페이지에서도 토스트 유지 확인

## 📋 플로우 다이어그램

```
사용자                프론트엔드              백엔드
  │                      │                     │
  │  [PDF 업로드]        │                     │
  ├──────────────────────>                     │
  │                      │  POST /upload       │
  │                      ├────────────────────>│
  │                      │                     │ (파일 저장)
  │                      │  task_id 반환       │ (백그라운드 작업 시작)
  │                      <────────────────────┤
  │                      │                     │
  │  [토스트 생성]       │                     │
  │                      │                     │
  │                      │  [3초마다 폴링]     │
  │                      │  GET /tasks/{id}    │
  │                      ├────────────────────>│
  │                      │  status 반환        │
  │                      <────────────────────┤
  │                      │                     │
  │  [토스트 업데이트]   │                     │
  │  - 진행률 45%         │                     │
  │  - "스키마 생성 중"   │                     │
  │                      │                     │
  │                      │  [폴링 계속...]     │
  │                      │                     │
  │  [페이지 이동]       │                     │
  ├──────────────────────>                     │
  │  dashboard로 이동    │                     │
  │                      │  [LocalStorage]     │
  │                      │  작업 상태 저장     │
  │                      │                     │
  │  [토스트 복원]       │                     │
  │  이전 작업 계속 표시 │  [폴링 재시작]     │
  │                      ├────────────────────>│
  │                      │  status 반환        │
  │                      <────────────────────┤
  │                      │                     │
  │  [완료!]             │                     │
  │  "정책 보기" 버튼    │                     │
```

## 💡 핵심 클래스 및 메서드

### `BackgroundTaskToast` 클래스

#### 주요 메서드

- **`addTask(taskId, title, description)`**
  - 새 백그라운드 작업 추가 및 토스트 생성
  - 자동으로 폴링 시작

- **`startPolling(taskId)`**
  - 3초마다 백엔드 API 호출
  - 응답 데이터로 토스트 업데이트
  - 완료/실패 시 자동으로 폴링 중지

- **`updateToast(taskData)`**
  - 토스트 UI 업데이트 (진행률, 상태, 메시지)
  - 완료/실패 시 액션 버튼 추가

- **`closeToast(taskId)`**
  - 토스트 제거 및 폴링 중지
  - LocalStorage에서도 제거

- **`saveActiveTasks()`**
  - 진행 중인 작업을 LocalStorage에 저장
  - `beforeunload` 이벤트로 자동 호출

- **`restoreActiveTasks()`**
  - 페이지 로드 시 LocalStorage에서 작업 복원
  - 24시간 이상 지난 작업은 무시
  - 복원된 작업의 폴링 자동 재시작

## ⚠️ 주의사항

1. **백엔드 API 필수**
   - `/api/policies/tasks/{task_id}/status` 엔드포인트 구현 필요
   - 3초마다 호출되므로 성능 최적화 필요 (캐싱 권장)

2. **인증 토큰**
   - LocalStorage의 `auth_token` 필요
   - 토큰 없으면 토스트 시스템 초기화 안 됨

3. **브라우저 호환성**
   - LocalStorage 지원 브라우저 필요 (IE 8+)
   - CSS 애니메이션 지원 브라우저 권장

4. **폴링 오버헤드**
   - 여러 작업 동시 진행 시 폴링 부하 증가
   - 완료된 작업은 자동으로 폴링 중지됨

## 🎯 실제 사용 예시

### policy-add.html에서의 통합

```javascript
// 파일 업로드
const formData = new FormData();
formData.append('file', selectedFile);
formData.append('title', title);
formData.append('authority', authority);

const response = await fetch(`${API_BASE}/api/policies/upload`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
});

const result = await response.json();

if (result.success) {
    const taskId = result.data.task_id;
    const policyTitle = result.data.title;

    // 토스트 알림 시작
    if (taskId && toastManager) {
        toastManager.addTask(
            taskId,
            `📄 ${policyTitle}`,
            'PDF 텍스트 추출 및 스키마 생성 중...'
        );
    }

    // 대시보드로 이동 (토스트는 계속 표시됨)
    setTimeout(() => {
        window.location.href = './dashboard-policy.html';
    }, 1000);
}
```

## 🔍 디버깅

### 콘솔 로그

```javascript
// 현재 활성 작업 확인
console.log(backgroundTaskToast.tasks);

// 폴링 상태 확인
console.log(backgroundTaskToast.activePolls);

// LocalStorage 확인
console.log(localStorage.getItem('bgActiveTasks'));
```

### 문제 해결

1. **토스트가 표시되지 않음**
   - `auth_token`이 LocalStorage에 있는지 확인
   - 콘솔에서 `backgroundTaskToast` 객체 확인
   - `initBackgroundTaskToast()` 호출 확인

2. **진행 상황이 업데이트되지 않음**
   - 네트워크 탭에서 API 호출 확인
   - 백엔드 `/api/policies/tasks/{task_id}/status` 응답 확인
   - CORS 에러 확인

3. **페이지 이동 시 토스트가 사라짐**
   - LocalStorage에 `bgActiveTasks` 저장되는지 확인
   - 새 페이지에서 `toast-notification.js` 로드되는지 확인

## 🎨 커스터마이징

### 폴링 간격 변경

```javascript
// toast-notification.js
this.pollInterval = 5000; // 5초로 변경 (기본값: 3000ms)
```

### 자동 제거 시간 변경

```javascript
// 완료/실패 후 자동 제거 시간
setTimeout(() => {
    this.closeToast(taskId);
}, 20000); // 20초로 변경 (기본값: 10000ms)
```

### 스타일 변경

`toast-notification.js` 내부의 `<style>` 태그에서 CSS 수정:

```css
#bgTaskToastContainer {
    top: 80px;        /* 위치 변경 */
    right: 40px;
    max-width: 500px; /* 너비 변경 */
}

.bg-toast {
    border-left-width: 6px; /* 테두리 두께 */
}
```

## 📝 라이선스

이 프로젝트의 일부로 MIT 라이선스를 따릅니다.
