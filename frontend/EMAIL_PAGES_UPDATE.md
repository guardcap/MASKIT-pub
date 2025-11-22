# 이메일 페이지 통합 완료

## 변경 사항

### ✅ 새로 추가된 페이지
- **AllEmailsPage.tsx**: 보낸 메일과 받은 메일을 통합한 전체 메일함

### ⚠️ Deprecated (사용 중단)
다음 페이지들은 더 이상 사용되지 않으며, AllEmailsPage로 대체되었습니다:
- `SentEmailsPage.tsx` - 보낸 메일함 (개별)
- `ReceivedEmailsPage.tsx` - 받은 메일함 (개별)

## 주요 기능

### AllEmailsPage 특징
1. **통합 보기**: 보낸 메일과 받은 메일을 하나의 리스트로 표시
2. **방향 표시**: 각 메일에 보냄/받음 아이콘 표시
3. **다중 필터링**:
   - 방향 필터: 전체 / 보낸 메일 / 받은 메일
   - 상태 필터: 전체 / 대기 / 완료 / 반려
   - 읽음 필터: 전체 / 읽지 않음 / 읽음
4. **통합 검색**: 제목, 보낸 사람, 받는 사람 통합 검색
5. **통계 카드**:
   - 전체 메일 수
   - 보낸 메일 수 (파란색)
   - 받은 메일 수 (초록색)
   - 읽지 않은 메일 수 (주황색)

## 테이블 컬럼

| 컬럼 | 설명 |
|------|------|
| • | 읽지 않은 메일 표시 (파란 점) |
| 구분 | 보냄/받음 아이콘 |
| 제목 | 이메일 제목 + 첨부파일 아이콘 |
| 보낸이 | from_email |
| 받는이 | to_email |
| 상태 | 대기/완료/반려 배지 |
| 날짜 | 생성/전송 시간 |
| 첨부 | 첨부파일 개수 배지 |

## 라우팅 변경

### App.tsx
```tsx
// 기존
import { SentEmailsPage } from '@/pages/SentEmailsPage'
import { ReceivedEmailsPage } from '@/pages/ReceivedEmailsPage'

// 변경 후
import { AllEmailsPage } from '@/pages/AllEmailsPage'
```

### 사이드바 메뉴
```tsx
// 기존
- 보낸 메일함
- 받은 메일함

// 변경 후
- 전체 메일함
```

### UserDashboardPage
```tsx
// 기존
<Button onClick={() => onNavigate?.('my-emails')}>보낸 메일함</Button>
<Button onClick={() => onNavigate?.('received-emails')}>받은 메일함</Button>

// 변경 후
<Button onClick={() => onNavigate?.('all-emails')}>전체 메일함</Button>
```

## API 엔드포인트

AllEmailsPage는 두 개의 API를 병렬로 호출합니다:
1. `GET /api/v1/emails/my-emails` - 보낸 메일
2. `GET /api/v1/emails/received-emails` - 받은 메일

두 결과를 병합하여 시간순(최신순)으로 정렬합니다.

## 마이그레이션 가이드

### 기존 코드를 사용하는 경우

**변경 전:**
```tsx
// 보낸 메일함으로 이동
onNavigate?.('my-emails')

// 받은 메일함으로 이동
onNavigate?.('received-emails')
```

**변경 후:**
```tsx
// 전체 메일함으로 이동 (보낸/받은 메일 통합)
onNavigate?.('all-emails')
```

### 필터링이 필요한 경우

AllEmailsPage에서 기본 제공되는 "방향 필터"를 사용:
- `전체` - 모든 메일 표시
- `보낸 메일` - 보낸 메일만 표시
- `받은 메일` - 받은 메일만 표시

## 스타일 가이드

### 방향 표시
- **보낸 메일**: 파란색 화살표 (↗) + "보냄" 라벨
- **받은 메일**: 초록색 화살표 (↙) + "받음" 라벨

### 읽지 않은 메일
- 왼쪽에 파란 점 표시
- 행 배경색: `bg-blue-50/30`
- 제목: 볼드체 (`font-semibold`)

## 향후 개선 사항
1. ~~보낸/받은 메일함 통합~~ ✅ 완료
2. 메일 검색 고도화 (첨부파일명, 본문 검색)
3. 라벨/태그 시스템
4. 대량 작업 (일괄 삭제, 읽음 처리)
5. 정렬 옵션 (날짜, 제목, 발신자)
