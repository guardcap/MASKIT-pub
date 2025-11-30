#!/usr/bin/env python3
"""
SMTP 연결 테스트 스크립트
"""
import smtplib
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경변수 읽기
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
USE_TLS = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
USE_SSL = os.getenv('SMTP_USE_SSL', 'false').lower() == 'true'

print("=" * 60)
print("SMTP 연결 테스트")
print("=" * 60)
print(f"SMTP_HOST: {SMTP_HOST}")
print(f"SMTP_PORT: {SMTP_PORT}")
print(f"SMTP_USER: {SMTP_USER}")
print(f"SMTP_PASSWORD: {'*' * len(SMTP_PASSWORD) if SMTP_PASSWORD else '(empty)'}")
print(f"USE_TLS: {USE_TLS}")
print(f"USE_SSL: {USE_SSL}")
print("=" * 60)

if not SMTP_USER or not SMTP_PASSWORD:
    print("\n❌ SMTP_USER 또는 SMTP_PASSWORD가 설정되지 않았습니다.")
    exit(1)

try:
    print(f"\n[1] SMTP 서버 연결 시도: {SMTP_HOST}:{SMTP_PORT}")

    if USE_SSL:
        # SSL 연결 (포트 465)
        print("[2] SSL 모드로 연결 중...")
        server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10)
        print("✅ SSL 연결 성공")
    else:
        # 일반 SMTP 연결 (포트 587 또는 25)
        print("[2] 일반 SMTP로 연결 중...")
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
        print("✅ SMTP 연결 성공")

        if USE_TLS:
            print("[3] STARTTLS 시작 중...")
            server.starttls()
            print("✅ STARTTLS 성공")

    # EHLO 명령
    print(f"[4] EHLO 전송 중...")
    server.ehlo()
    print("✅ EHLO 성공")

    # 인증 시도
    print(f"[5] 인증 시도 중... (User: {SMTP_USER})")
    server.login(SMTP_USER, SMTP_PASSWORD)
    print("✅ 인증 성공!")

    # 연결 종료
    server.quit()
    print("\n" + "=" * 60)
    print("🎉 SMTP 연결 테스트 성공!")
    print("=" * 60)

except smtplib.SMTPAuthenticationError as e:
    print(f"\n❌ 인증 실패: {e}")
    print("\n가능한 원인:")
    print("1. 사용자명 또는 비밀번호가 잘못되었습니다.")
    print("2. 2단계 인증이 활성화된 경우 앱 비밀번호를 사용해야 합니다.")
    print("3. SMTP 액세스가 비활성화되어 있을 수 있습니다.")
    exit(1)

except smtplib.SMTPConnectError as e:
    print(f"\n❌ 연결 실패: {e}")
    print("\n가능한 원인:")
    print("1. SMTP 서버 주소나 포트가 잘못되었습니다.")
    print("2. 방화벽이 연결을 차단하고 있습니다.")
    exit(1)

except smtplib.SMTPException as e:
    print(f"\n❌ SMTP 오류: {e}")
    exit(1)

except Exception as e:
    print(f"\n❌ 예상치 못한 오류: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
