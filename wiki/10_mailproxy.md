---
layout: default
title: 메일 프록시 원리
nav_order: 10
---

# 메일 프록시 (Mail Proxy)

## 개요

Guardcap의 메일 프록시는 **SMTP 프로토콜 기반의 이메일 검사 게이트웨이**입니다.
사용자의 이메일 클라이언트와 메일 서버 사이에 위치하여, 송신되는 모든 이메일을 자동으로 DLP(Data Loss Prevention) 검사에 등록합니다.

---

## 1. 기획 배경 및 필요성

### 1.1 문제 정의

**기존의 문제점:**
- 직원들이 실수로 개인정보를 포함한 이메일을 송신할 수 있음
- 사후 대응만 가능하여 피해가 발생함
- 수동 검사는 비용이 크고 비효율적
- 외부로 나가는 이메일을 사전에 검사할 수 없음

### 1.2 솔루션: 투명한 프록시 게이트웨이

**설계 원칙:**
```
┌─────────────────────────────────────────────────────────────┐
│ 사용자가 알지 못하는 사이에 자동 검사                          │
├─────────────────────────────────────────────────────────────┤
│ 이메일 송신 흐름을 방해하지 않음                             │
├─────────────────────────────────────────────────────────────┤
│ 모든 송신 메일을 동일하게 처리                                │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Guardcap 메일 프록시의 특징

| 특징 | 설명 |
|------|------|
| **투명성** | 사용자 개입 없이 자동 작동 |
| **범용성** | 모든 이메일 클라이언트 지원 |
| **비차단성** | 이메일 송신을 지연시키지 않음 |
| **포괄성** | 본문, 첨부파일, 메타데이터 모두 검사 |
| **실시간성** | 송신 즉시 검사 등록 |

---

## 2. SMTP 프로토콜 개요

### 2.1 SMTP란?

**SMTP (Simple Mail Transfer Protocol)**
- 이메일을 송신하기 위한 표준 프로토콜
- TCP 포트 25, 587, 465 등에서 작동
- 클라이언트 → 메일 서버 방향의 일방향 통신
- RFC 5321 표준

### 2.2 SMTP 통신 흐름

```
이메일 클라이언트              SMTP 프록시              메일 서버
       │                          │                        │
       │ CONNECT (포트 2525)       │                        │
       ├─────────────────────────→│                        │
       │                          │ CONNECT (포트 25)       │
       │                          ├──────────────────────→ │
       │                          │ ← READY (220)         │
       │                          │                        │
       │ ← READY (220)            │                        │
       │                          │                        │
       │ MAIL FROM: sender@...    │                        │
       ├─────────────────────────→│ MAIL FROM: sender@...  │
       │                          ├──────────────────────→ │
       │                          │ ← OK (250)            │
       │ ← OK (250)               │                        │
       │                          │                        │
       │ RCPT TO: recipient@...   │                        │
       ├─────────────────────────→│ RCPT TO: recipient@... │
       │                          ├──────────────────────→ │
       │                          │ ← OK (250)            │
       │ ← OK (250)               │                        │
       │                          │                        │
       │ DATA                     │                        │
       ├─────────────────────────→│ DATA                   │
       │                          ├──────────────────────→ │
       │ (메일 본문 + 첨부파일)      │                        │
       ├─────────────────────────→│ (메일 본문 + 첨부파일)   │
       │                          ├──────────────────────→ │
       │ .                        │ .                      │
       ├─────────────────────────→│ ├──────────────────────→ │
       │                          │ ← OK (250)            │
       │ ← OK (250)               │                        │
       │                          │                        │
       │ QUIT                     │                        │
       ├─────────────────────────→│ QUIT                   │
       │                          ├──────────────────────→ │
       │                          │ ← BYE (221)           │
       │ ← BYE (221)              │                        │
       │                          │                        │
```

### 2.3 SMTP 명령어

| 명령어 | 용도 | 예시 |
|--------|------|------|
| MAIL FROM | 발신자 지정 | `MAIL FROM:<user@example.com>` |
| RCPT TO | 수신자 지정 | `RCPT TO:<recipient@example.com>` |
| DATA | 본문 시작 | `DATA` |
| . | 본문 종료 | `.` (한 줄에만) |
| QUIT | 연결 종료 | `QUIT` |

---

## 3. Guardcap 메일 프록시 아키텍처

### 3.1 전체 구조

```
┌──────────────────────────────────────────────────────────────┐
│ 사용자의 이메일 클라이언트                                      │
│ (Outlook, Gmail, Thunderbird 등)                             │
└──────────────────────────────────────────────────────────────┘
                            │
                            │ SMTP 연결
                            │ (localhost:2525)
                            ↓
┌──────────────────────────────────────────────────────────────┐
│           FastApiProxyHandler (Python)                        │
├──────────────────────────────────────────────────────────────┤
│ 1. SMTP 메시지 수신                                            │
│    └─ envelope.content (바이너리 SMTP 메시지)                  │
│ 2. 메시지 파싱                                                │
│    ├─ message_from_bytes() 사용                              │
│    ├─ policy.default 적용                                    │
│    └─ RFC 표준 준수                                           │
│ 3. 이메일 구성요소 추출                                       │
│    ├─ From (발신자)                                          │
│    ├─ To (수신자)                                            │
│    ├─ Subject (제목)                                         │
│    ├─ Body (본문)                                            │
│    └─ Attachments (첨부파일)                                 │
│ 4. FastAPI 서버로 전송                                       │
│    └─ POST /api/v1/files/upload_email                       │
│ 5. 응답 반환                                                  │
│    └─ "250 OK: Registered for DLP approval"                 │
└──────────────────────────────────────────────────────────────┘
                            │
                            │ SMTP 응답
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ 사용자의 이메일 클라이언트 (계속 작동)                           │
└──────────────────────────────────────────────────────────────┘
                            │
                            │ 실제 메일 서버로 전송
                            │ (smtp.gmail.com, smtp.naver.com 등)
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ FastAPI 백엔드 (비동기 처리)                                   │
├──────────────────────────────────────────────────────────────┤
│ 1. 메일 데이터 저장                                           │
│ 2. OCR 추출 (필요시)                                          │
│ 3. PII 분석 (recognizer_engine)                              │
│ 4. 분석 결과 반환                                             │
└──────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ DLP 대시보드 / 사용자 검토 인터페이스                            │
├──────────────────────────────────────────────────────────────┤
│ - 감지된 PII 항목 표시                                        │
│ - 사용자 승인/거부 선택                                       │
│ - 마스킹 옵션 제공                                            │
│ - 최종 발송 또는 차단                                         │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 프록시 위치 설정

**로컬 환경:**
```
호스트 머신의 이메일 클라이언트 설정:
- SMTP 서버: 127.0.0.1 (localhost)
- SMTP 포트: 2525 (Guardcap 프록시)
```

**네트워크 환경:**
```
호스트 머신의 이메일 클라이언트 설정:
- SMTP 서버: [프록시 서버 IP]
- SMTP 포트: 2525 (Guardcap 프록시)

프록시 서버에서 실제 메일 서버로:
- SMTP 서버: smtp.gmail.com, smtp.naver.com 등
- SMTP 포트: 587 또는 25
```

---

## 4. FastApiProxyHandler 상세 분석

### 4.1 클래스 구조

```python
class FastApiProxyHandler:
    """aiosmtpd 라이브러리 기반 SMTP 핸들러"""
    async def handle_DATA(self, server, session, envelope):
        """
        SMTP DATA 명령 수신 시 호출
        - server: SMTP 서버 객체
        - session: SMTP 세션 정보
        - envelope: SMTP 메시지 봉투 (From, To, 본문 포함)
        """
```

### 4.2 핵심 메서드: handle_DATA()

#### 단계 1: 메시지 파싱

```python
from email import message_from_bytes, policy

# SMTP 바이너리 메시지를 Python 이메일 객체로 변환
mail = message_from_bytes(envelope.content, policy=policy.default)
```

**policy.default의 역할:**
- RFC 5322 표준을 엄격히 준수
- 유니코드 처리 자동화
- 헤더 파싱 최적화
- 이전 버전 호환성 유지

#### 단계 2: 본문 추출

```python
# get_body()로 가장 적합한 본문 부분 선택
body_part = mail.get_body(preferencelist=('plain', 'html'))
if body_part:
    body = body_part.get_content()
```

**선택 순서:**
```
1. text/plain (일반 텍스트) 선호
2. text/html (HTML) 대체
3. 기타 MIME 타입은 선택하지 않음
```

**특징:**
- 멀티파트 메시지 자동 처리
- MIME 타입별 최적 본문 선택
- 인코딩 자동 변환

#### 단계 3: 첨부파일 추출

```python
attachments = []
for part in mail.iter_attachments():
    attachments.append({
        "filename": part.get_filename(),
        "data": part.get_payload(decode=True),
        "content_type": part.get_content_type()
    })
```

**추출 정보:**

| 필드 | 용도 | 예시 |
|------|------|------|
| filename | 파일명 | `document.pdf` |
| data | 파일 바이너리 | `b'\x25\x50\x44\x46...'` |
| content_type | MIME 타입 | `application/pdf` |

**iter_attachments()의 특징:**
- 첨부파일만 선택적으로 추출
- 본문에 포함된 이미지 제외
- 바이너리 자동 디코딩

#### 단계 4: FastAPI로 데이터 전송

```python
form_data = {
    'from_email': mail.get('From'),
    'to_email': mail.get('To'),
    'subject': mail.get('Subject'),
    'original_body': body,
}

files_list = []
for att in attachments:
    files_list.append(
        ('attachments', (att['filename'], att['data'], att['content_type']))
    )

response = requests.post(
    FASTAPI_REGISTER_URL,
    data=form_data,
    files=files_list
)
```

**전송 형식: multipart/form-data**

```
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="from_email"

user@example.com
------WebKitFormBoundary
Content-Disposition: form-data; name="to_email"

recipient@example.com
------WebKitFormBoundary
Content-Disposition: form-data; name="subject"

Project Report
------WebKitFormBoundary
Content-Disposition: form-data; name="original_body"

Dear Mr. ...
------WebKitFormBoundary
Content-Disposition: form-data; name="attachments"; filename="document.pdf"
Content-Type: application/pdf

[바이너리 PDF 데이터]
------WebKitFormBoundary--
```

#### 단계 5: 응답 반환

```python
return '250 OK: Registered for DLP approval'
```

**SMTP 응답 코드:**
- `250`: 메시지 수락됨 (성공)
- `500`: 내부 에러 (재전송 권장 없음)

---

## 5. 데이터 흐름 상세

### 5.1 전체 흐름도

```
사용자가 이메일 송신
        │
        ↓
[프록시 단계]
┌─────────────────────────────────────┐
│ 1. SMTP 연결 (localhost:2525)        │
├─────────────────────────────────────┤
│ 2. MAIL FROM / RCPT TO 명령 수신     │
├─────────────────────────────────────┤
│ 3. DATA 명령으로 본문 수신            │
│    └─ envelope.content 저장         │
├─────────────────────────────────────┤
│ 4. message_from_bytes() 파싱        │
├─────────────────────────────────────┤
│ 5. 메타데이터 + 본문 + 첨부파일 추출 │
├─────────────────────────────────────┤
│ 6. FastAPI POST 요청                │
├─────────────────────────────────────┤
│ 7. SMTP 응답 반환 (250 OK)           │
└─────────────────────────────────────┘
        │
        ↓
[FastAPI 단계]
┌─────────────────────────────────────┐
│ 1. upload_email() 엔드포인트 수신    │
├─────────────────────────────────────┤
│ 2. 메일 데이터 저장 (uploads 폴더)   │
│    ├─ email_body.txt                │
│    ├─ email_meta.json               │
│    └─ attachments (첨부파일)        │
├─────────────────────────────────────┤
│ 3. 클라이언트에 응답 (비동기)        │
└─────────────────────────────────────┘
        │
        ↓
[백그라운드 단계]
┌─────────────────────────────────────┐
│ 1. 사용자가 대시보드에서 파일 검토   │
├─────────────────────────────────────┤
│ 2. POST /api/v1/process로 분석 요청 │
│    └─ OCR + PII 탐지                │
├─────────────────────────────────────┤
│ 3. 결과 화면에 표시                  │
├─────────────────────────────────────┤
│ 4. 사용자 승인/거부 선택             │
│    ├─ 승인: POST /approve_and_send  │
│    │         → 이메일 송신 + 마스킹  │
│    └─ 거부: 메일 폐기                │
└─────────────────────────────────────┘
```

### 5.2 데이터 형식 변환

```
[원본 SMTP 형식]
From: sender@example.com
To: recipient@example.com
Subject: Important Data
Content-Type: multipart/mixed

This is the body.

--boundary
Content-Disposition: attachment; filename="data.xlsx"
Content-Transfer-Encoding: base64

UEsDBBQACAAIAGd...
--boundary--
        │
        ├─ message_from_bytes()
        ├─ policy.default 적용
        │
        ↓
[Python 객체 형식]
mail.get('From')          → 'sender@example.com'
mail.get('To')            → 'recipient@example.com'
mail.get('Subject')       → 'Important Data'
mail.get_body()           → 'This is the body.'
mail.iter_attachments()   → [Part1, Part2, ...]
        │
        │
        ↓
[FastAPI multipart/form-data 형식]
form_data:
  - from_email: 'sender@example.com'
  - to_email: 'recipient@example.com'
  - subject: 'Important Data'
  - original_body: 'This is the body.'

files:
  - ('attachments', ('data.xlsx', b'PK\x03\x04...', 'application/vnd.ms-excel'))
        │
        │
        ↓
[FastAPI 서버 저장 형식]
uploads/
├─ email_body.txt         → 'This is the body.'
├─ email_meta.json        → {"recipients": [...], "subject": "..."}
└─ data.xlsx              → 원본 바이너리 파일
```

---

## 6. 설정 및 실행

### 6.1 주요 설정

```python
PROXY_HOST = '127.0.0.1'  # 프록시 리스닝 주소
PROXY_PORT = 2525          # 프록시 포트 (표준: 25, 587)
FASTAPI_REGISTER_URL = "http://127.0.0.1:8000/api/v1/files/upload_email"
                           # FastAPI 백엔드 주소
```

**포트 선택 가이드:**

| 포트 | 용도 | 특징 |
|------|------|------|
| 25 | SMTP (legacy) | 권한 필요, 일부 ISP 차단 |
| 587 | SMTP TLS | 권장, 인증 필요 |
| 2525 | 테스트/프록시 | 권한 불필요, 로컬 개발 용 |
| 465 | SMTPS (암호화) | 레거시 |

**로컬 개발: 2525 사용**
**프로덕션: 25 또는 587 권장**

### 6.2 실행 방법

```python
async def main():
    controller = Controller(
        FastApiProxyHandler(),
        hostname=PROXY_HOST,
        port=PROXY_PORT
    )
    print(f"Python SMTP Proxy가 {PROXY_HOST}:{PROXY_PORT} 에서 시작됩니다...")
    controller.start()
    try:
        while True:
            await asyncio.sleep(1)  # 무한 실행
    except KeyboardInterrupt:
        controller.stop()

if __name__ == '__main__':
    asyncio.run(main())
```

**실행:**
```bash
python proxy.py
# 출력: Python SMTP Proxy가 127.0.0.1:2525 에서 시작됩니다...
```

### 6.3 이메일 클라이언트 설정 (Outlook 예시)

```
파일 → 옵션 → 고급 → 계정 설정 → 나의 이메일 계정

SMTP 서버:     127.0.0.1
포트:          2525
암호화:        없음
인증:          (선택사항)
```

---

## 7. 에러 처리

### 7.1 예외 상황

```python
try:
    # SMTP 메시지 파싱
    mail = message_from_bytes(envelope.content, policy=policy.default)
    # ... 처리 ...
    response = requests.post(FASTAPI_REGISTER_URL, ...)
    response.raise_for_status()

    return '250 OK: Registered for DLP approval'

except Exception as e:
    print(f"[Python Proxy] ❌ 에러 발생: {e}")
    return '500 Could not process email'
```

### 7.2 처리 가능한 에러

| 에러 | 원인 | 대응 |
|------|------|------|
| 잘못된 SMTP 형식 | 클라이언트 버그 | 500 반환, 로그 기록 |
| FastAPI 서버 오류 | 백엔드 다운 | 500 반환, 재시도 권장 |
| 첨부파일 파싱 실패 | 손상된 파일 | 본문은 처리, 첨부파일 스킵 |
| 메모리 부족 | 매우 큰 첨부파일 | 500 반환, 파일 크기 제한 권장 |

### 7.3 로깅

```python
# 성공 시
print(f"[Python Proxy] ✅ FastAPI 서버 등록 완료 (To: {form_data['to_email']}, 첨부파일 {len(attachments)}개)")

# 실패 시
print(f"[Python Proxy] ❌ 에러 발생: {e}")
```

---

## 8. 보안 고려사항

### 8.1 SMTP 보안

**현재 설정의 한계:**
```python
PROXY_HOST = '127.0.0.1'  # localhost만 허용 (안전)
PROXY_PORT = 2525          # 암호화 없음 (개발 환경)
```

**프로덕션 권장사항:**

| 항목 | 개발 환경 | 프로덕션 |
|------|---------|---------|
| **호스트** | 127.0.0.1 | 0.0.0.0 + 방화벽 |
| **포트** | 2525 | 25 또는 587 |
| **암호화** | 없음 | TLS/SSL (필수) |
| **인증** | 없음 | SMTP 인증 (필수) |
| **로깅** | 기본 | 상세 감시 로깅 |
| **모니터링** | 없음 | 실시간 알람 |

### 8.2 데이터 보호

**프록시 단계:**
- 모든 이메일이 메모리에 로드됨
- 개인정보 노출 가능성 있음
- 프록시 서버의 접근 제어 필수

**FastAPI 단계:**
- uploads 폴더에 일시 저장
- 사용자 승인 후 삭제
- 정기적인 임시 파일 정리

**권장사항:**
```python
# 1. 이메일 저장 기간 제한
max_email_retention = 24  # hours

# 2. 민감 정보 마스킹 (로그)
def mask_email(email):
    parts = email.split('@')
    return f"{parts[0][:2]}***@{parts[1]}"

# 3. 암호화된 저장소 사용
encrypted_storage = True

# 4. 감시 로깅
audit_log_enabled = True
```

### 8.3 스팸/악용 방지

```python
# Rate limiting (예시)
from collections import defaultdict
import time

email_throttle = defaultdict(list)

async def handle_DATA(self, server, session, envelope):
    sender = mail.get('From')
    now = time.time()

    # 최근 1시간 내 발송 건수 체크
    recent = [t for t in email_throttle[sender] if now - t < 3600]
    if len(recent) > 100:  # 1시간 100건 제한
        return '429 Too Many Requests'

    email_throttle[sender].append(now)
    # ... 계속 처리 ...
```

---

## 9. 성능 최적화

### 9.1 병목 지점 분석

```
1. 메시지 파싱 (message_from_bytes)
   - 큰 메일: 100MB 이상 시 시간 소요
   - 대안: 스트리밍 파서

2. 첨부파일 추출 (iter_attachments)
   - 많은 첨부파일: 선형 시간
   - 최적화: 병렬 처리

3. FastAPI 전송 (requests.post)
   - 네트워크 지연: 가장 큰 지연 원인
   - 최적화: aiohttp 사용 (비동기)

4. 메모리 사용
   - 전체 이메일을 메모리에 로드
   - 최적화: 스트리밍 방식
```

### 9.2 최적화 예시

```python
# ✗ 동기 요청 (차단)
response = requests.post(FASTAPI_REGISTER_URL, ...)

# ✓ 비동기 요청 (논블로킹)
import aiohttp

async def send_to_fastapi(form_data, files):
    async with aiohttp.ClientSession() as session:
        async with session.post(FASTAPI_REGISTER_URL, data=form_data) as resp:
            return await resp.text()
```

### 9.3 성능 지표

| 메트릭 | 목표 | 현재 |
|--------|------|------|
| 응답 시간 | < 1초 | ~2초 (네트워크 포함) |
| 처리량 | 100개/분 | 60개/분 |
| 메모리 (50MB 메일) | < 150MB | ~200MB |

---

## 10. 실제 사용 예시

### 10.1 완전한 워크플로우

```
1️⃣ 직원 이메일 준비
   └─ To: customer@example.com
   └─ Subject: Contract
   └─ Body: 계약서 내용 + 주민번호 실수로 포함
   └─ Attachments: signature.pdf

2️⃣ 프록시 처리 (자동)
   ├─ SMTP 요청 수신 (localhost:2525)
   ├─ 메시지 파싱
   ├─ FastAPI POST 요청
   └─ "250 OK" 응답

3️⃣ FastAPI 저장
   ├─ email_body.txt 저장
   ├─ email_meta.json 저장
   ├─ signature.pdf 저장
   └─ "Message OK" 응답

4️⃣ 사용자 검토 (대시보드)
   ├─ 메일 내용 표시
   ├─ PII 감지: 주민번호 하이라이트
   └─ "승인" 클릭

5️⃣ 최종 처리
   ├─ POST /approve_and_send
   ├─ 주민번호 마스킹
   ├─ 이메일 발송 (수신자에게)
   └─ uploads 폴더 정리
```

### 10.2 로그 예시

```
[Python Proxy] Python SMTP Proxy가 127.0.0.1:2525 에서 시작됩니다...
[Python Proxy] 메일 수신 완료. FastAPI 서버로 등록합니다...
[Python Proxy] ✅ FastAPI 서버 등록 완료 (To: customer@example.com, 첨부파일 1개)

[FastAPI] POST /api/v1/files/upload_email 수신
[FastAPI] email_body.txt 저장됨
[FastAPI] email_meta.json 저장됨
[FastAPI] signature.pdf 저장됨

[대시보드] 새 메일 도착: customer@example.com
[분석] POST /api/v1/process 실행
[분석] RESIDENT_ID 감지: 주민번호 (신뢰도: 1.0)
[분석] 분석 결과 반환

[사용자] 대시보드에서 승인 클릭
[최종] POST /approve_and_send 실행
[마스킹] 주민번호 마스킹
[발송] customer@example.com에 발송
[정리] uploads 폴더 정리 완료
```

---

## 11. 트러블슈팅

### 11.1 프록시 연결 안 됨

**증상:**
```
이메일 클라이언트 오류: "SMTP 서버에 연결할 수 없습니다"
```

**진단:**
```bash
# 프록시 실행 확인
ps aux | grep proxy.py

# 포트 리스닝 확인
netstat -an | grep 2525
# 또는
lsof -i :2525
```

**해결:**
```python
# proxy.py 재실행
python proxy.py

# FastAPI 서버도 실행 중인지 확인
curl http://127.0.0.1:8000/docs
```

### 11.2 FastAPI 응답 없음

**증상:**
```
[Python Proxy] ❌ 에러 발생: Connection refused
```

**원인:**
- FastAPI 서버 다운
- 잘못된 URL

**해결:**
```bash
# FastAPI 서버 실행
python -m uvicorn main:app --reload --port 8000

# URL 확인
echo "http://127.0.0.1:8000/api/v1/files/upload_email"
```

### 11.3 첨부파일 손실

**증상:**
```
uploads 폴더에 첨부파일이 없음
```

**원인:**
- iter_attachments()가 첨부파일 선택하지 못함
- MIME 타입 문제

**해결:**
```python
# 디버깅 추가
for part in mail.iter_attachments():
    print(f"파일명: {part.get_filename()}")
    print(f"MIME: {part.get_content_type()}")

# 모든 파트 검사 (임시)
for part in mail.iter_parts():
    if part.get_content_disposition() == 'attachment':
        print(f"발견된 첨부파일: {part.get_filename()}")
```

---

## 주요 주의사항

### 설치 및 의존성

```bash
# 필수 라이브러리
pip install aiosmtpd
pip install requests
```

### 운영 중 주의사항

1. **프록시 서버 가용성**
   - 프록시 다운 시 모든 이메일 송신 불가
   - 별도 모니터링 및 자동 재시작 필요

2. **저장소 용량**
   - uploads 폴더 용량 관리 필수
   - 정기적인 정리 스크립트 필요

3. **네트워크 보안**
   - 프록시 서버 접근 제어 필수
   - 방화벽 설정으로 로컬만 허용

4. **성능 모니터링**
   - 응답 시간 추적
   - 메모리 사용량 모니터링
   - 에러율 감시

5. **백업 및 복구**
   - 이메일 데이터 백업 정책
   - 장애 발생 시 복구 절차 수립