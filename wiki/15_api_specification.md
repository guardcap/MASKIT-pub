# API 명세서

GuardCap Enterprise - 이메일 DLP 시스템 API 명세서

## 목차
1. [인증 API](#1-인증-api)
2. [정책 관리 API](#2-정책-관리-api)
3. [엔티티 관리 API](#3-엔티티-관리-api)
4. [VectorDB 관리 API](#4-vectordb-관리-api)
5. [SMTP 이메일 API](#5-smtp-이메일-api)
6. [미구현/미연결 API](#6-미구현미연결-api)

---

## 1. 인증 API

### 1.1 회원가입
**엔드포인트:** `POST /auth/register`

**요청 본문:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "nickname": "홍길동",
  "team_name": "개발팀",
  "role": "user"
}
```

**응답:**
```json
{
  "email": "user@example.com",
  "nickname": "홍길동",
  "team_name": "개발팀",
  "role": "user",
  "created_at": "2024-01-01T00:00:00"
}
```

**프론트엔드 연결:**
- ✅ [RegisterPage.tsx](../frontend/src/pages/RegisterPage.tsx#L78)

---

### 1.2 로그인
**엔드포인트:** `POST /auth/login`

**요청 본문:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**응답:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "email": "user@example.com",
    "nickname": "홍길동",
    "team_name": "개발팀",
    "role": "user"
  }
}
```

**프론트엔드 연결:**
- ✅ [LoginPage.tsx](../frontend/src/pages/LoginPage.tsx#L42)

---

### 1.3 현재 사용자 정보 조회
**엔드포인트:** `GET /auth/me`

**헤더:**
```
Authorization: Bearer {access_token}
```

**응답:**
```json
{
  "email": "user@example.com",
  "nickname": "홍길동",
  "team_name": "개발팀",
  "role": "user",
  "created_at": "2024-01-01T00:00:00"
}
```

**프론트엔드 연결:**
- ❌ **미연결** - 프론트엔드에서 사용되지 않음

---

## 2. 정책 관리 API

### 2.1 정책 파일 업로드
**엔드포인트:** `POST /api/policies/upload`

**요청 (multipart/form-data):**
```
file: [파일]
title: "개인정보보호법 가이드라인"
authority: "개인정보보호위원회"
description: "개인정보 처리 지침"
```

**응답:**
```json
{
  "success": true,
  "message": "정책 파일이 성공적으로 업로드되었습니다.",
  "data": {
    "policy_id": "abc123def456",
    "title": "개인정보보호법 가이드라인",
    "authority": "개인정보보호위원회",
    "file_type": ".pdf",
    "processing_method": "zerox_ocr",
    "metadata": {
      "summary": "정책 요약...",
      "keywords": ["개인정보", "마스킹"]
    },
    "text_length": 15000,
    "created_at": "2024-01-01T00:00:00",
    "task_id": "policy_abc123def456"
  }
}
```

**프론트엔드 연결:**
- ✅ [api.ts - uploadPolicyFile](../frontend/src/lib/api.ts#L110)

---

### 2.2 정책 목록 조회
**엔드포인트:** `GET /api/policies/list`

**쿼리 파라미터:**
- `skip`: 건너뛸 개수 (기본값: 0)
- `limit`: 반환할 개수 (기본값: 50)
- `authority`: 기관 필터 (선택)

**응답:**
```json
{
  "success": true,
  "data": {
    "policies": [
      {
        "policy_id": "abc123",
        "title": "개인정보보호법 가이드라인",
        "authority": "개인정보보호위원회",
        "description": "...",
        "file_type": ".pdf",
        "created_at": "2024-01-01T00:00:00"
      }
    ],
    "total": 10,
    "skip": 0,
    "limit": 50
  }
}
```

**프론트엔드 연결:**
- ✅ [api.ts - getPolicies](../frontend/src/lib/api.ts#L50)
- ✅ [PolicyListPage.tsx](../frontend/src/pages/PolicyListPage.tsx)

---

### 2.3 정책 상세 조회
**엔드포인트:** `GET /api/policies/{policy_id}`

**응답:**
```json
{
  "success": true,
  "data": {
    "policy_id": "abc123",
    "title": "개인정보보호법 가이드라인",
    "authority": "개인정보보호위원회",
    "extracted_text": "전체 텍스트...",
    "metadata": {
      "summary": "...",
      "keywords": ["개인정보"],
      "entity_types": ["주민등록번호"]
    },
    "created_at": "2024-01-01T00:00:00"
  }
}
```

**프론트엔드 연결:**
- ✅ [api.ts - getPolicyDetail](../frontend/src/lib/api.ts#L74)
- ✅ [PolicyDetailPage.tsx](../frontend/src/pages/PolicyDetailPage.tsx)

---

### 2.4 정책 삭제
**엔드포인트:** `DELETE /api/policies/{policy_id}`

**응답:**
```json
{
  "success": true,
  "message": "정책이 성공적으로 삭제되었습니다"
}
```

**프론트엔드 연결:**
- ✅ [api.ts - deletePolicy](../frontend/src/lib/api.ts#L81)

---

### 2.5 정책 통계 조회
**엔드포인트:** `GET /api/policies/stats/summary`

**응답:**
```json
{
  "success": true,
  "data": {
    "total_policies": 25,
    "total_entities": 15,
    "by_authority": {
      "개인정보보호위원회": 10,
      "금융보안원": 8,
      "내부": 7
    },
    "by_file_type": {
      ".pdf": 20,
      ".png": 5
    }
  }
}
```

**프론트엔드 연결:**
- ✅ [api.ts - getPolicyStats](../frontend/src/lib/api.ts#L93)

---

### 2.6 정책 스키마 목록 조회
**엔드포인트:** `GET /api/policies/schemas`

**쿼리 파라미터:**
- `skip`: 건너뛸 개수 (기본값: 0)
- `limit`: 반환할 개수 (기본값: 50)
- `refresh_cache`: 캐시 새로고침 여부 (기본값: false)

**응답:**
```json
{
  "success": true,
  "data": {
    "total": 100,
    "skip": 0,
    "limit": 50,
    "cached": true,
    "cache_expires_in": 3400,
    "schemas": [
      {
        "source_file": "application_guides_20240101.jsonl",
        "line_number": 1,
        "guide_id": "GUIDE-PIPC-202401-abc123-001",
        "scenario": "외부기관에 주민등록번호 전송",
        "actionable_directive": "주민등록번호는 반드시 마스킹"
      }
    ]
  }
}
```

**프론트엔드 연결:**
- ✅ [api.ts - getPolicySchemas](../frontend/src/lib/api.ts#L151)

---

### 2.7 백그라운드 작업 상태 조회
**엔드포인트:** `GET /api/policies/tasks/{task_id}/status`

**응답:**
```json
{
  "success": true,
  "data": {
    "task_id": "policy_abc123",
    "status": "processing",
    "progress": 60,
    "message": "가이드라인 추출 중...",
    "created_at": "2024-01-01T00:00:00"
  }
}
```

**프론트엔드 연결:**
- ✅ [api.ts - getTaskStatus, pollTaskStatus](../frontend/src/lib/api.ts#L178)

---

## 3. 엔티티 관리 API

### 3.1 엔티티 생성
**엔드포인트:** `POST /api/entities/`

**요청 본문 (application/x-www-form-urlencoded):**
```
entity_id=phone
name=전화번호
category=연락처
description=휴대전화 및 일반 전화번호
regex_pattern=01[016789]-?\d{3,4}-?\d{4}
keywords=전화,번호,연락처
examples=010-1234-5678,02-123-4567
masking_rule=partial
sensitivity_level=high
```

**응답:**
```json
{
  "success": true,
  "message": "엔티티가 성공적으로 생성되었습니다",
  "data": {
    "entity_id": "phone",
    "name": "전화번호",
    "category": "연락처"
  }
}
```

**프론트엔드 연결:**
- ✅ [EntityManagementPage.tsx](../frontend/src/pages/EntityManagementPage.tsx#L109)

---

### 3.2 엔티티 목록 조회
**엔드포인트:** `GET /api/entities/list`

**쿼리 파라미터:**
- `category`: 카테고리 필터 (선택)
- `is_active`: 활성 상태 필터 (선택)

**응답:**
```json
{
  "success": true,
  "data": {
    "entities": [
      {
        "entity_id": "phone",
        "name": "전화번호",
        "category": "연락처",
        "is_active": true
      }
    ],
    "total": 15,
    "by_category": {
      "연락처": [...],
      "식별정보": [...]
    }
  }
}
```

**프론트엔드 연결:**
- ✅ [EntityManagementPage.tsx](../frontend/src/pages/EntityManagementPage.tsx#L71)

---

### 3.3 카테고리 목록 조회
**엔드포인트:** `GET /api/entities/categories`

**응답:**
```json
{
  "success": true,
  "data": [
    {
      "category": "연락처",
      "count": 3,
      "entities": ["전화번호", "이메일", "주소"]
    },
    {
      "category": "식별정보",
      "count": 5,
      "entities": ["주민등록번호", "여권번호", "운전면허번호"]
    }
  ]
}
```

**프론트엔드 연결:**
- ❌ **미연결** - 프론트엔드에서 사용되지 않음

---

### 3.4 Recognizer 정보 조회
**엔드포인트:** `GET /api/entities/recognizers`

**응답:**
```json
{
  "success": true,
  "data": {
    "recognizers": [
      {
        "name": "EmailRecognizer",
        "class_name": "EmailRecognizer",
        "entity_types": ["EMAIL"],
        "regex_patterns": [
          {
            "name": "EMAIL_REGEX",
            "pattern": "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"
          }
        ],
        "keywords": [],
        "module_path": "app.utils.recognizer"
      }
    ],
    "total": 10
  }
}
```

**프론트엔드 연결:**
- ✅ [EntityManagementPage.tsx](../frontend/src/pages/EntityManagementPage.tsx#L70)

---

### 3.5 엔티티 상세 조회
**엔드포인트:** `GET /api/entities/{entity_id}`

**응답:**
```json
{
  "success": true,
  "data": {
    "entity_id": "phone",
    "name": "전화번호",
    "category": "연락처",
    "description": "휴대전화 및 일반 전화번호",
    "regex_pattern": "01[016789]-?\\d{3,4}-?\\d{4}",
    "keywords": ["전화", "번호"],
    "examples": ["010-1234-5678"],
    "masking_rule": "partial",
    "sensitivity_level": "high"
  }
}
```

**프론트엔드 연결:**
- ❌ **미연결** - 프론트엔드에서 사용되지 않음

---

### 3.6 엔티티 수정
**엔드포인트:** `PUT /api/entities/{entity_id}`

**요청 본문 (application/x-www-form-urlencoded):**
```
name=휴대전화번호
description=새로운 설명
is_active=true
```

**응답:**
```json
{
  "success": true,
  "message": "엔티티가 성공적으로 수정되었습니다"
}
```

**프론트엔드 연결:**
- ❌ **미연결** - 프론트엔드에서 사용되지 않음

---

### 3.7 엔티티 삭제
**엔드포인트:** `DELETE /api/entities/{entity_id}`

**응답:**
```json
{
  "success": true,
  "message": "엔티티가 성공적으로 삭제되었습니다"
}
```

**프론트엔드 연결:**
- ✅ [EntityManagementPage.tsx](../frontend/src/pages/EntityManagementPage.tsx#L146)

---

### 3.8 기본 엔티티 시드 데이터 생성
**엔드포인트:** `POST /api/entities/seed`

**응답:**
```json
{
  "success": true,
  "message": "8개의 기본 엔티티가 생성되었습니다",
  "data": {
    "inserted": 8,
    "total": 8
  }
}
```

**프론트엔드 연결:**
- ❌ **미연결** - 프론트엔드에서 사용되지 않음

---

## 4. VectorDB 관리 API

### 4.1 가이드 그룹별 조회
**엔드포인트:** `GET /api/vectordb/guides/grouped`

**응답:**
```json
{
  "success": true,
  "data": {
    "total_source_documents": 5,
    "total_guides": 50,
    "groups": [
      {
        "source_document": "개인정보보호법 가이드라인.pdf",
        "count": 25,
        "authorities": ["개인정보보호위원회"],
        "jsonl_files": ["application_guides_20240101.jsonl"],
        "guides": [...]
      }
    ]
  }
}
```

**프론트엔드 연결:**
- ❌ **미연결** - 프론트엔드에서 사용되지 않음

---

### 4.2 특정 소스의 가이드 조회
**엔드포인트:** `GET /api/vectordb/guides/by-source/{source_document}`

**응답:**
```json
{
  "success": true,
  "data": {
    "source_document": "개인정보보호법 가이드라인.pdf",
    "count": 25,
    "guides": [...]
  }
}
```

**프론트엔드 연결:**
- ❌ **미연결** - 프론트엔드에서 사용되지 않음

---

### 4.3 가이드 ID로 조회
**엔드포인트:** `GET /api/vectordb/guides/{guide_id}`

**응답:**
```json
{
  "success": true,
  "data": {
    "guide_id": "GUIDE-PIPC-202401-abc123-001",
    "source_authority": "개인정보보호위원회",
    "source_document": "개인정보보호법 가이드라인.pdf",
    "scenario": "외부기관에 주민등록번호 전송",
    "interpretation": "개인정보보호법 제24조에 따라...",
    "actionable_directive": "주민등록번호는 반드시 전체 마스킹",
    "keywords": ["주민등록번호", "외부전송", "마스킹"],
    "confidence_score": 0.95
  }
}
```

**프론트엔드 연결:**
- ❌ **미연결** - 프론트엔드에서 사용되지 않음

---

### 4.4 가이드 생성
**엔드포인트:** `POST /api/vectordb/guides`

**요청 본문:**
```json
{
  "source_authority": "개인정보보호위원회",
  "source_document": "개인정보보호법 가이드라인.pdf",
  "scenario": "외부기관에 주민등록번호 전송",
  "context": {
    "sender_type": "internal",
    "receiver_type": "external",
    "email_purpose": "업무협조",
    "pii_types": ["주민등록번호"]
  },
  "interpretation": "개인정보보호법 제24조에 따라...",
  "actionable_directive": "주민등록번호는 반드시 전체 마스킹",
  "keywords": ["주민등록번호", "외부전송"],
  "related_law_ids": ["PIPA-24"],
  "examples": [
    {
      "case_description": "외부 공공기관으로 명단 전송",
      "recommended_action": "주민등록번호 완전 마스킹"
    }
  ],
  "confidence_score": 0.95
}
```

**응답:**
```json
{
  "success": true,
  "message": "가이드가 성공적으로 생성되었습니다",
  "data": {
    "guide_id": "GUIDE-PIPC-202401-abc123-001",
    "jsonl_file": "application_guides_20240101_개인정보보호법.jsonl"
  }
}
```

**프론트엔드 연결:**
- ❌ **미연결** - 프론트엔드에서 사용되지 않음

---

### 4.5 가이드 업데이트
**엔드포인트:** `PUT /api/vectordb/guides/{guide_id}`

**요청 본문:**
```json
{
  "scenario": "수정된 시나리오",
  "confidence_score": 0.98,
  "reviewed": true
}
```

**응답:**
```json
{
  "success": true,
  "message": "가이드가 성공적으로 업데이트되었습니다",
  "data": {...}
}
```

**프론트엔드 연결:**
- ❌ **미연결** - 프론트엔드에서 사용되지 않음

---

### 4.6 가이드 삭제
**엔드포인트:** `DELETE /api/vectordb/guides/{guide_id}`

**응답:**
```json
{
  "success": true,
  "message": "가이드가 성공적으로 삭제되었습니다"
}
```

**프론트엔드 연결:**
- ❌ **미연결** - 프론트엔드에서 사용되지 않음

---

### 4.7 VectorDB 재구축
**엔드포인트:** `POST /api/vectordb/sync/rebuild`

**응답:**
```json
{
  "success": true,
  "message": "VectorDB 재구축 완료: 50개 가이드 동기화"
}
```

**프론트엔드 연결:**
- ❌ **미연결** - 프론트엔드에서 사용되지 않음

---

### 4.8 VectorDB 통계
**엔드포인트:** `GET /api/vectordb/stats`

**응답:**
```json
{
  "success": true,
  "data": {
    "total_guides": 50,
    "total_source_documents": 5,
    "total_jsonl_files": 3,
    "authorities": ["개인정보보호위원회", "금융보안원"],
    "vectordb_count": 50,
    "sync_status": "synced"
  }
}
```

**프론트엔드 연결:**
- ❌ **미연결** - 프론트엔드에서 사용되지 않음

---

### 4.9 RAG 기반 이메일 분석
**엔드포인트:** `POST /api/vectordb/analyze`

**요청 본문:**
```json
{
  "email_body": "이메일 본문...",
  "email_subject": "제목",
  "context": {
    "sender_type": "internal",
    "receiver_type": "external",
    "email_purpose": "업무협조"
  },
  "detected_pii": [
    {
      "type": "jumin",
      "value": "991231-1234567"
    }
  ],
  "query": "외부 전송 마스킹"
}
```

**응답:**
```json
{
  "success": true,
  "data": {
    "masking_decisions": {
      "pii_0": {
        "pii_id": "pii_0",
        "type": "jumin",
        "value": "991231-1234567",
        "should_mask": true,
        "masking_method": "full",
        "masked_value": "***",
        "reason": "고유식별정보 외부 전송 금지 (개인정보보호법 제24조)",
        "reasoning": "1. 컨텍스트 확인: external 전송\n2. PII 유형: 주민등록번호...",
        "cited_guidelines": ["개인정보보호법 제24조"],
        "confidence": 0.95,
        "risk_level": "high"
      }
    },
    "summary": "외부 전송으로 분류되어, 1개 개인정보를 마스킹하도록 권장합니다.",
    "relevant_guides": [...],
    "total_guides_found": 5
  }
}
```

**프론트엔드 연결:**
- ✅ [ApproverReviewPage.tsx](../frontend/src/pages/ApproverReviewPage.tsx#L235)

---

## 5. SMTP 이메일 API

### 5.1 이메일 전송
**엔드포인트:** `POST /smtp/send`

**헤더:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**요청 본문:**
```json
{
  "from_email": "sender@example.com",
  "to": "recipient@example.com",
  "subject": "이메일 제목",
  "body": "<html>이메일 본문</html>",
  "cc": "cc@example.com",
  "bcc": "bcc@example.com",
  "attachments": []
}
```

**응답:**
```json
{
  "success": true,
  "message": "이메일이 성공적으로 전송되었습니다",
  "email_id": "507f1f77bcf86cd799439011",
  "sent_at": "2024-01-01T00:00:00"
}
```

**프론트엔드 연결:**
- ⚠️ **부분 연결** - [ApproverReviewPage.tsx](../frontend/src/pages/ApproverReviewPage.tsx#L332)에서 `/api/v1/smtp/send` 경로로 호출 (실제 경로: `/smtp/send`)

---

### 5.2 이메일 목록 조회
**엔드포인트:** `GET /smtp/emails`

**헤더:**
```
Authorization: Bearer {access_token}
```

**쿼리 파라미터:**
- `page`: 페이지 번호 (기본값: 1)
- `page_size`: 페이지 당 항목 수 (기본값: 20, 최대: 100)
- `status_filter`: 상태 필터 (sent, approved, rejected)

**응답:**
```json
{
  "emails": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "from_email": "sender@example.com",
      "to_email": "recipient@example.com",
      "subject": "제목",
      "status": "sent",
      "sent_at": "2024-01-01T00:00:00",
      "owner_email": "user@example.com"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

**프론트엔드 연결:**
- ❌ **미연결** - 프론트엔드에서 사용되지 않음

---

### 5.3 이메일 상세 조회
**엔드포인트:** `GET /smtp/emails/{email_id}`

**헤더:**
```
Authorization: Bearer {access_token}
```

**응답:**
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "from_email": "sender@example.com",
  "to_email": "recipient@example.com",
  "subject": "제목",
  "original_body": "원본 본문",
  "masked_body": "마스킹된 본문",
  "status": "sent",
  "attachments": [],
  "sent_at": "2024-01-01T00:00:00",
  "owner_email": "user@example.com"
}
```

**프론트엔드 연결:**
- ❌ **미연결** - 프론트엔드에서 사용되지 않음

---

## 6. 미구현/미연결 API

### 6.1 프론트엔드에서 호출하지만 백엔드에 없는 API

#### 6.1.1 사용자 관리 API
**❌ 미구현**

프론트엔드에서 호출:
- `GET /api/v1/users/` - 사용자 목록 조회 ([UserManagementPage.tsx:54](../frontend/src/pages/UserManagementPage.tsx#L54))
- `PATCH /api/v1/users/{email}/role` - 사용자 권한 변경 ([UserManagementPage.tsx:80](../frontend/src/pages/UserManagementPage.tsx#L80))
- `DELETE /api/v1/users/{email}` - 사용자 삭제 ([UserManagementPage.tsx:104](../frontend/src/pages/UserManagementPage.tsx#L104))
- `GET /api/users/me` - 내 정보 조회 ([MyPage.tsx:116](../frontend/src/pages/MyPage.tsx#L116))

**구현 필요:**
```python
# backend/app/users/routes.py (신규 생성 필요)

@router.get("/api/v1/users/")
async def list_users():
    """모든 사용자 목록 조회"""
    pass

@router.patch("/api/v1/users/{email}/role")
async def update_user_role(email: str, role: str):
    """사용자 권한 변경"""
    pass

@router.delete("/api/v1/users/{email}")
async def delete_user(email: str):
    """사용자 삭제"""
    pass

@router.get("/api/users/me")
async def get_my_info(current_user = Depends(get_current_user)):
    """내 정보 조회 (이미 /auth/me가 있으므로 라우팅 추가 필요)"""
    pass
```

---

#### 6.1.2 이메일 관리 API
**❌ 미구현**

프론트엔드에서 호출:
- `GET /api/v1/emails/pending` - 승인 대기 이메일 조회 ([PendingApprovalsPage.tsx:37](../frontend/src/pages/PendingApprovalsPage.tsx#L37))
- `POST /api/v1/emails/{email_id}/approve` - 이메일 승인 ([PendingApprovalsPage.tsx:61](../frontend/src/pages/PendingApprovalsPage.tsx#L61))
- `POST /api/v1/emails/{email_id}/reject` - 이메일 거부 ([PendingApprovalsPage.tsx:104](../frontend/src/pages/PendingApprovalsPage.tsx#L104))
- `GET /api/v1/emails/my-emails` - 내가 보낸 이메일 조회 ([SentEmailsPage.tsx:58](../frontend/src/pages/SentEmailsPage.tsx#L58))
- `GET /api/v1/emails/received-emails` - 받은 이메일 조회 ([ReceivedEmailsPage.tsx:61](../frontend/src/pages/ReceivedEmailsPage.tsx#L61))
- `GET /api/v1/emails/email/{email_id}` - 이메일 상세 조회 ([EmailDetailPage.tsx:63](../frontend/src/pages/EmailDetailPage.tsx#L63))
- `GET /api/v1/emails/email/{email_id}/attachments/{file_id}` - 첨부파일 다운로드 ([EmailDetailPage.tsx:127](../frontend/src/pages/EmailDetailPage.tsx#L127))

**구현 필요:**
```python
# backend/app/emails/routes.py (신규 생성 필요)

@router.get("/api/v1/emails/pending")
async def get_pending_emails(current_user = Depends(get_current_user)):
    """승인 대기 중인 이메일 목록"""
    pass

@router.post("/api/v1/emails/{email_id}/approve")
async def approve_email(email_id: str):
    """이메일 승인"""
    pass

@router.post("/api/v1/emails/{email_id}/reject")
async def reject_email(email_id: str, reason: str):
    """이메일 거부"""
    pass

@router.get("/api/v1/emails/my-emails")
async def get_my_emails(current_user = Depends(get_current_user)):
    """내가 보낸 이메일 목록"""
    pass

@router.get("/api/v1/emails/received-emails")
async def get_received_emails(current_user = Depends(get_current_user)):
    """받은 이메일 목록"""
    pass

@router.get("/api/v1/emails/email/{email_id}")
async def get_email_detail(email_id: str):
    """이메일 상세 조회"""
    pass

@router.get("/api/v1/emails/email/{email_id}/attachments/{file_id}")
async def download_attachment(email_id: str, file_id: str):
    """첨부파일 다운로드"""
    pass
```

---

#### 6.1.3 파일 업로드 API
**❌ 미구현**

프론트엔드에서 호출:
- `POST /api/v1/files/upload_email` - 이메일 업로드 ([WriteEmailPage.tsx:196](../frontend/src/pages/WriteEmailPage.tsx#L196))
- `GET /api/v1/files/original_emails/{email_id}` - 원본 이메일 조회 ([ApproverReviewPage.tsx:110](../frontend/src/pages/ApproverReviewPage.tsx#L110))
- `GET /api/v1/emails/attachments/{file_id}` - 첨부파일 다운로드 ([ApproverReviewPage.tsx:165](../frontend/src/pages/ApproverReviewPage.tsx#L165))

**구현 필요:**
```python
# backend/app/files/routes.py (신규 생성 필요)

@router.post("/api/v1/files/upload_email")
async def upload_email(
    file: UploadFile,
    from_email: str,
    to_emails: str,
    subject: str
):
    """이메일 업로드 및 DLP 분석"""
    pass

@router.get("/api/v1/files/original_emails/{email_id}")
async def get_original_email(email_id: str):
    """원본 이메일 조회"""
    pass
```

---

#### 6.1.4 대시보드 통계 API
**❌ 미구현**

프론트엔드에서 호출:
- `GET /api/v1/dashboard/root-admin/stats` - ROOT_ADMIN 통계 ([RootDashboardPage.tsx:48](../frontend/src/pages/RootDashboardPage.tsx#L48))
- `GET /api/v1/dashboard/auditor/stats` - Auditor 통계 ([AuditorDashboardPage.tsx:53](../frontend/src/pages/AuditorDashboardPage.tsx#L53))

**구현 필요:**
```python
# backend/app/dashboard/routes.py (신규 생성 필요)

@router.get("/api/v1/dashboard/root-admin/stats")
async def get_root_admin_stats():
    """ROOT_ADMIN 대시보드 통계"""
    pass

@router.get("/api/v1/dashboard/auditor/stats")
async def get_auditor_stats():
    """Auditor 대시보드 통계"""
    pass
```

---

#### 6.1.5 로그 관리 API
**❌ 미구현**

프론트엔드에서 호출:
- `GET /api/v1/logs/recent` - 최근 로그 조회 ([AuditorDashboardPage.tsx:83](../frontend/src/pages/AuditorDashboardPage.tsx#L83))

**구현 필요:**
```python
# backend/app/logs/routes.py (신규 생성 필요)

@router.get("/api/v1/logs/recent")
async def get_recent_logs(limit: int = 10):
    """최근 로그 조회"""
    pass
```

---

### 6.2 백엔드에 있지만 프론트엔드에서 사용하지 않는 API

#### 6.2.1 인증 API
- ✅ `GET /auth/me` - 현재 사용자 정보 조회 (구현됨, 미사용)

#### 6.2.2 엔티티 관리 API
- ✅ `GET /api/entities/categories` - 카테고리 목록 조회 (구현됨, 미사용)
- ✅ `GET /api/entities/{entity_id}` - 엔티티 상세 조회 (구현됨, 미사용)
- ✅ `PUT /api/entities/{entity_id}` - 엔티티 수정 (구현됨, 미사용)
- ✅ `POST /api/entities/seed` - 기본 엔티티 시드 (구현됨, 미사용)
- ✅ `GET /api/entities/recognizers/{entity_type}` - Recognizer 상세 조회 (구현됨, 미사용)
- ✅ `POST /api/entities/recognizers/cache/clear` - Recognizer 캐시 초기화 (구현됨, 미사용)

#### 6.2.3 VectorDB 관리 API
- ✅ `GET /api/vectordb/guides/grouped` - 가이드 그룹별 조회 (구현됨, 미사용)
- ✅ `GET /api/vectordb/guides/by-source/{source_document}` - 소스별 가이드 조회 (구현됨, 미사용)
- ✅ `GET /api/vectordb/guides/{guide_id}` - 가이드 ID로 조회 (구현됨, 미사용)
- ✅ `POST /api/vectordb/guides` - 가이드 생성 (구현됨, 미사용)
- ✅ `PUT /api/vectordb/guides/{guide_id}` - 가이드 업데이트 (구현됨, 미사용)
- ✅ `DELETE /api/vectordb/guides/{guide_id}` - 가이드 삭제 (구현됨, 미사용)
- ✅ `POST /api/vectordb/sync/rebuild` - VectorDB 재구축 (구현됨, 미사용)
- ✅ `GET /api/vectordb/stats` - VectorDB 통계 (구현됨, 미사용)

#### 6.2.4 SMTP 이메일 API
- ✅ `GET /smtp/emails` - 이메일 목록 조회 (구현됨, 미사용)
- ✅ `GET /smtp/emails/{email_id}` - 이메일 상세 조회 (구현됨, 미사용)

---

## 7. API 경로 불일치

### 7.1 SMTP 전송 API
- **프론트엔드 호출:** `/api/v1/smtp/send`
- **실제 백엔드:** `/smtp/send`
- **수정 필요:** [ApproverReviewPage.tsx:332](../frontend/src/pages/ApproverReviewPage.tsx#L332)

**권장 수정:**
```typescript
// 수정 전
const smtpResponse = await fetch(`${API_BASE_URL}/api/v1/smtp/send`, {

// 수정 후
const smtpResponse = await fetch(`${API_BASE_URL}/smtp/send`, {
```

---

## 8. 요약

### 8.1 구현 완료된 API
- ✅ 인증 API (회원가입, 로그인, 현재 사용자 조회)
- ✅ 정책 관리 API (업로드, 목록, 상세, 삭제, 통계, 스키마, 백그라운드 작업)
- ✅ 엔티티 관리 API (생성, 목록, 카테고리, Recognizer, 상세, 수정, 삭제, 시드)
- ✅ VectorDB 관리 API (가이드 CRUD, 통계, RAG 분석)
- ✅ SMTP 이메일 API (전송, 목록, 상세)

### 8.2 프론트엔드에 연결 필요한 백엔드 API
- `/auth/me` - 현재 사용자 정보 조회
- `/api/entities/categories` - 카테고리 목록 조회
- `/api/entities/{entity_id}` - 엔티티 상세 조회
- `/api/entities/{entity_id}` (PUT) - 엔티티 수정
- `/smtp/emails` - 이메일 목록 조회
- `/smtp/emails/{email_id}` - 이메일 상세 조회
- VectorDB 관리 API 전체 (가이드 CRUD, 통계)

### 8.3 백엔드에 구현 필요한 API
**우선순위 HIGH:**
- 사용자 관리 API (`/api/v1/users/` 전체)
- 이메일 관리 API (`/api/v1/emails/` 전체)
- 파일 업로드 API (`/api/v1/files/` 전체)

**우선순위 MEDIUM:**
- 대시보드 통계 API (`/api/v1/dashboard/` 전체)
- 로그 관리 API (`/api/v1/logs/` 전체)

### 8.4 경로 수정 필요
- SMTP 전송 API 경로 불일치 수정 필요

---

**마지막 업데이트:** 2024-01-01
**버전:** 1.0
