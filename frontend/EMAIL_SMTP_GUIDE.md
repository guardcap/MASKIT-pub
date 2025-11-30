# 이메일 SMTP 연동 가이드

## ✅ 현재 구현 상태

Frontend와 Backend가 완전히 연동되어 있으며, 다음 흐름으로 동작합니다:

```
1. 메일 작성 (WriteEmailPage)
   ↓
2. 파일 첨부 업로드 → POST /api/v1/emails/upload-attachment
   ↓
3. "보내기" 클릭 → 승인자 검토 페이지로 이동 (ApproverReviewPage)
   ↓
4. AI 분석 실행 → POST /api/vectordb/analyze (RAG 가이드라인 검색)
   ↓
5. "마스킹 완료 & 전송" 클릭
   ├─ 1단계: DB 저장 → POST /api/v1/emails/send-approved
   └─ 2단계: SMTP 전송 → POST /api/v1/smtp/send
```

---

## 🔧 SMTP 설정 확인

### Backend SMTP 설정 (`.env` 파일)

현재 활성화된 SMTP 설정:

```bash
# Mailplug SMTP 설정 예시
SMTP_HOST=smtp.mailplug.co.kr
SMTP_PORT=465
SMTP_USE_TLS=false
SMTP_USE_SSL=true
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-password-here
```

### 다른 SMTP 서버 사용 시

`.env` 파일에서 다음 중 하나를 선택하여 주석 해제:

**Gmail:**
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

**Naver:**
```bash
SMTP_HOST=smtp.naver.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USE_SSL=false
SMTP_USER=your-id@naver.com
SMTP_PASSWORD=your-password
```

---

## 🐛 에러 발생 시 확인 사항

### 1. Backend 서버 실행 확인

```bash
# Backend 디렉토리에서
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

Backend가 실행 중이면 다음과 같이 표시됩니다:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 2. MongoDB 실행 확인

```bash
# MongoDB 상태 확인
mongosh

# 또는
brew services list | grep mongodb
```

### 3. SMTP 에러 로그 확인

Backend 콘솔에서 다음과 같은 로그를 확인:

```
[SMTP Client] 메일 전송 시작...
  From: sender@example.com
  To: recipient@example.com
  Subject: Test Email
  Protocol: SSL
  SMTP Server: smtp.mailplug.co.kr:465
  Auth User: yes0823bs@swu.ac.kr
```

**성공 시:**
```
[SMTP Client] ✅ 메일 전송 완료: 2025-01-16 12:34:56
```

**실패 시:**
```
[SMTP Client] ❌ SMTP 인증 실패: (535, b'authentication failed')
[SMTP Client] ❌ SMTP 오류: Connection refused
```

### 4. Frontend 콘솔 확인

브라우저 개발자 도구 (F12) → Console 탭에서 확인:

```javascript
// DB 저장 성공
✅ DB 저장 성공: {success: true, email_ids: [...]}

// SMTP 전송 성공
✅ SMTP 전송 성공: {success: true, sent_at: "..."}

// SMTP 전송 실패 (하지만 DB 저장 완료)
❌ SMTP 전송 실패: {status: 500, result: {...}}
📋 SMTP 에러 상세: SMTP 인증 실패...
💡 Backend 서버 콘솔 로그를 확인하여 SMTP 설정을 점검하세요
```

---

## 🧪 SMTP 테스트 방법

### 방법 1: Frontend에서 테스트

1. Frontend 실행: `npm run dev` (포트 3000)
2. 로그인 후 "메일 쓰기" 클릭
3. 이메일 작성 및 "보내기" 클릭
4. 승인자 검토 페이지에서 "마스킹 완료 & 전송" 클릭
5. Toast 알림과 콘솔 로그 확인

### 방법 2: Backend API 직접 테스트

```bash
curl -X POST "http://localhost:8000/api/v1/smtp/send" \
  -H "Content-Type: application/json" \
  -d '{
    "from_email": "yes0823bs@swu.ac.kr",
    "to": "recipient@example.com",
    "subject": "Test Email from API",
    "body": "<p>This is a test email</p>",
    "cc": null,
    "bcc": null
  }'
```

**성공 응답:**
```json
{
  "success": true,
  "message": "메일이 성공적으로 전송되었습니다",
  "email_id": "60d5ec49f8b3f3a1b8c9d1e2",
  "sent_at": "2025-01-16T12:34:56.789Z"
}
```

**실패 응답:**
```json
{
  "detail": "메일 전송 중 오류가 발생했습니다: SMTP 인증 실패"
}
```

---

## 🔍 일반적인 SMTP 에러 및 해결 방법

### 1. `SMTP 인증 실패 (535, authentication failed)`

**원인:**
- SMTP 계정 정보가 잘못됨
- 2단계 인증이 활성화된 경우 앱 비밀번호 필요

**해결:**
- Gmail: [앱 비밀번호 생성](https://myaccount.google.com/apppasswords)
- Naver: 계정 설정에서 SMTP 사용 활성화
- `.env` 파일의 `SMTP_USER`, `SMTP_PASSWORD` 확인

### 2. `Connection refused`

**원인:**
- SMTP 서버 주소 또는 포트가 잘못됨
- 방화벽이 SMTP 포트를 차단

**해결:**
- `.env`의 `SMTP_HOST`, `SMTP_PORT` 확인
- 방화벽 설정 확인 (포트 465, 587)

### 3. `Timed out`

**원인:**
- 네트워크 연결 문제
- SMTP 서버 응답 없음

**해결:**
- 인터넷 연결 확인
- `ping smtp.mailplug.co.kr` 테스트
- 다른 SMTP 서버로 변경 시도

### 4. `SSL/TLS 에러`

**원인:**
- `SMTP_USE_TLS`와 `SMTP_USE_SSL` 설정이 포트와 맞지 않음

**해결:**
```bash
# 포트 465 → SSL 사용
SMTP_PORT=465
SMTP_USE_SSL=true
SMTP_USE_TLS=false

# 포트 587 → TLS 사용
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USE_SSL=false
```

---

## 📋 API 엔드포인트 요약

| Endpoint | Method | 인증 | 설명 |
|----------|--------|------|------|
| `/api/v1/emails/upload-attachment` | POST | 필요 | 첨부파일 업로드 (GridFS) |
| `/api/v1/emails/send-approved` | POST | 필요 | 승인된 이메일 DB 저장 |
| `/api/v1/smtp/send` | POST | **불필요** | SMTP 이메일 전송 |
| `/api/vectordb/analyze` | POST | 불필요 | RAG 기반 PII 마스킹 분석 |

---

## 🎯 현재 동작 흐름 (성공 케이스)

```
1. 사용자가 이메일 작성 완료
2. WriteEmailPage → ApproverReviewPage로 이동
3. AI 분석 실행 (선택사항)
4. "마스킹 완료 & 전송" 클릭

5. Frontend → Backend: POST /api/v1/emails/send-approved
   ✅ DB에 이메일 저장 (status: "approved")

6. Frontend → Backend: POST /api/v1/smtp/send
   ✅ SMTP 클라이언트가 실제 이메일 전송
   ✅ Backend 콘솔에 "[SMTP Client] ✅ 메일 전송 완료" 표시

7. Toast 알림: "이메일이 성공적으로 전송되었습니다!"
8. 메인 페이지로 복귀
```

---

## 🔧 트러블슈팅 체크리스트

- [ ] Backend 서버 실행 중? (`http://localhost:8000`)
- [ ] MongoDB 실행 중?
- [ ] `.env` 파일의 SMTP 설정 확인
- [ ] SMTP 계정 로그인 가능한지 웹에서 테스트
- [ ] 방화벽에서 SMTP 포트 허용?
- [ ] Backend 콘솔 로그 확인
- [ ] Frontend 콘솔 (F12) 로그 확인
- [ ] `curl` 명령으로 API 직접 테스트

---

## 💡 추가 개선 사항 (선택사항)

1. **첨부파일 SMTP 전송 지원**
   - 현재: DB에만 첨부파일 저장
   - 개선: GridFS에서 첨부파일 읽어 SMTP 전송

2. **재전송 기능**
   - SMTP 실패 시 DB에 저장된 이메일 재전송 버튼

3. **전송 내역 조회**
   - `/api/v1/smtp/emails` 엔드포인트 사용하여 전송 내역 표시

4. **SMTP 설정 UI**
   - Frontend에서 SMTP 서버 설정 변경 가능하도록 개선
