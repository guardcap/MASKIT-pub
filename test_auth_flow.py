#!/usr/bin/env python3
"""
인증 및 이메일 전송 플로우 테스트 스크립트
MongoDB 연결과 토큰 인증을 확인합니다.
"""

import requests
import json

API_BASE = "http://localhost:8000"

def test_mongodb_connection():
    """MongoDB 연결 확인"""
    print("\n" + "="*60)
    print("1. MongoDB 연결 테스트")
    print("="*60)

    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"✅ 서버 상태: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")
        return False

def test_register_user():
    """테스트 사용자 등록"""
    print("\n" + "="*60)
    print("2. 사용자 등록 테스트")
    print("="*60)

    test_user = {
        "email": "test@example.com",
        "password": "password123",
        "nickname": "테스트사용자",
        "team_name": "개발팀",
        "role": "user"
    }

    try:
        response = requests.post(
            f"{API_BASE}/api/auth/register",
            json=test_user
        )

        if response.status_code == 201:
            print(f"✅ 사용자 등록 성공: {test_user['email']}")
            return True
        elif response.status_code == 400:
            error = response.json()
            if "이미 등록된" in error.get("detail", ""):
                print(f"ℹ️  이미 등록된 사용자: {test_user['email']}")
                return True
            else:
                print(f"❌ 등록 실패: {error}")
                return False
        else:
            print(f"❌ 등록 실패 ({response.status_code}): {response.text}")
            return False

    except Exception as e:
        print(f"❌ 등록 오류: {e}")
        return False

def test_login():
    """로그인 및 토큰 획득"""
    print("\n" + "="*60)
    print("3. 로그인 및 토큰 획득 테스트")
    print("="*60)

    login_data = {
        "email": "test@example.com",
        "password": "password123"
    }

    try:
        response = requests.post(
            f"{API_BASE}/api/auth/login",
            json=login_data
        )

        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            user = data.get("user")

            print(f"✅ 로그인 성공!")
            print(f"   토큰: {token[:30]}...")
            print(f"   사용자: {user.get('email')} ({user.get('role')})")

            return token
        else:
            error = response.json()
            print(f"❌ 로그인 실패 ({response.status_code}): {error.get('detail')}")
            return None

    except Exception as e:
        print(f"❌ 로그인 오류: {e}")
        return None

def test_email_send_with_token(token):
    """토큰을 사용한 이메일 전송 테스트"""
    print("\n" + "="*60)
    print("4. 인증된 이메일 전송 테스트")
    print("="*60)

    if not token:
        print("❌ 토큰이 없어 테스트를 건너뜁니다")
        return False

    email_data = {
        "from_email": "test@example.com",
        "to": "recipient@example.com",
        "subject": "테스트 이메일",
        "body": "이것은 인증 테스트용 이메일입니다.",
        "attachments": [],
        "masking_decisions": {}
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.post(
            f"{API_BASE}/api/v1/emails/send-approved",
            json=email_data,
            headers=headers
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 이메일 전송 성공!")
            print(f"   Email ID: {result.get('email_ids')}")
            return True
        else:
            error = response.json()
            print(f"❌ 이메일 전송 실패 ({response.status_code}): {error.get('detail')}")
            return False

    except Exception as e:
        print(f"❌ 이메일 전송 오류: {e}")
        return False

def test_email_send_without_token():
    """토큰 없이 이메일 전송 시도 (실패해야 함)"""
    print("\n" + "="*60)
    print("5. 토큰 없이 이메일 전송 테스트 (401 예상)")
    print("="*60)

    email_data = {
        "from_email": "test@example.com",
        "to": "recipient@example.com",
        "subject": "테스트 이메일",
        "body": "이메일 본문",
        "attachments": [],
        "masking_decisions": {}
    }

    try:
        response = requests.post(
            f"{API_BASE}/api/v1/emails/send-approved",
            json=email_data,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 401:
            print(f"✅ 예상대로 인증 실패 (401)")
            return True
        else:
            print(f"❌ 예상치 못한 응답 ({response.status_code})")
            return False

    except Exception as e:
        print(f"❌ 테스트 오류: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "🔍 "*30)
    print("Enterprise GuardCAP 인증 플로우 테스트")
    print("🔍 "*30)

    # 1. MongoDB 연결 확인
    if not test_mongodb_connection():
        print("\n❌ 서버 연결 실패. 백엔드가 실행 중인지 확인하세요.")
        exit(1)

    # 2. 사용자 등록
    if not test_register_user():
        print("\n❌ 사용자 등록 실패")
        exit(1)

    # 3. 로그인
    token = test_login()
    if not token:
        print("\n❌ 로그인 실패")
        exit(1)

    # 4. 토큰으로 이메일 전송
    test_email_send_with_token(token)

    # 5. 토큰 없이 이메일 전송 (실패해야 함)
    test_email_send_without_token()

    print("\n" + "="*60)
    print("✅ 모든 테스트 완료!")
    print("="*60 + "\n")
