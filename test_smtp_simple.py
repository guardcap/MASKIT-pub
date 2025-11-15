#!/usr/bin/env python3
"""
SMTP 연결 테스트 스크립트 (dotenv 없이)
"""
import smtplib

# 직접 설정
SMTP_HOST = "smtp.mailplug.co.kr"
SMTP_PORT = 465
SMTP_USER = "yes0823bs@swu.ac.kr"
SMTP_PASSWORD = "EweE4k^^oYu:eF0$91<q"

print("=" * 60)
print("SMTP 연결 테스트")
print("=" * 60)
print(f"SMTP_HOST: {SMTP_HOST}")
print(f"SMTP_PORT: {SMTP_PORT}")
print(f"SMTP_USER: {SMTP_USER}")
print(f"SMTP_PASSWORD: {'*' * len(SMTP_PASSWORD)}")
print("=" * 60)

try:
    print(f"\n[1] SSL 모드로 SMTP 서버 연결 시도: {SMTP_HOST}:{SMTP_PORT}")
    server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10)
    print("✅ SSL 연결 성공")

    print(f"\n[2] EHLO 전송 중...")
    server.ehlo()
    print("✅ EHLO 성공")

    print(f"\n[3] 인증 시도 중... (User: {SMTP_USER})")
    server.login(SMTP_USER, SMTP_PASSWORD)
    print("✅ 인증 성공!")

    server.quit()
    print("\n" + "=" * 60)
    print("🎉 SMTP 연결 테스트 성공!")
    print("=" * 60)

except smtplib.SMTPAuthenticationError as e:
    print(f"\n❌ 인증 실패:")
    print(f"   {e}")
    print("\n가능한 원인:")
    print("1. 사용자명 또는 비밀번호가 잘못되었습니다.")
    print("2. 메일플러그 설정에서 SMTP 사용이 비활성화되어 있습니다.")
    print("3. 2단계 인증이 활성화된 경우 앱 비밀번호를 사용해야 합니다.")
    exit(1)

except smtplib.SMTPConnectError as e:
    print(f"\n❌ 연결 실패:")
    print(f"   {e}")
    print("\n가능한 원인:")
    print("1. SMTP 서버 주소나 포트가 잘못되었습니다.")
    print("2. 방화벽이 연결을 차단하고 있습니다.")
    exit(1)

except Exception as e:
    print(f"\n❌ 오류 발생:")
    print(f"   유형: {type(e).__name__}")
    print(f"   내용: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
