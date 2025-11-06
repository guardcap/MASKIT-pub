"""
DLP 메일 무결성 검증 모듈
HMAC 토큰 기반 메일 변조 검증
"""

import hmac
import hashlib
import os
from datetime import datetime
from email import message_from_bytes, policy

# 환경변수에서 시크릿 키 로드 (기본값은 개발용)
DLP_SECRET_KEY = os.getenv(
    "DLP_SECRET_KEY",
    "dlp-secret-key-min-32-characters-for-production-use"
)

def create_integrity_token(email_content: bytes) -> str:
    """
    메일 원본 내용으로부터 HMAC-SHA256 토큰 생성

    이 토큰은:
    - 메일이 프록시에서 수신 서버로 전송되는 과정에서 변조되지 않았음을 증명
    - 메일 헤더와 본문, 첨부파일 모두를 포함한 전체 내용으로 생성

    Args:
        email_content: 메일 원본 바이너리 내용 (envelope.content)

    Returns:
        HMAC-SHA256 해시 (16진수 문자열)
    """
    token = hmac.new(
        DLP_SECRET_KEY.encode('utf-8'),
        email_content,
        hashlib.sha256
    ).hexdigest()

    return token


def verify_integrity_token(email_content: bytes, token: str) -> bool:
    """
    저장된 토큰으로 메일 무결성 검증

    시간 공격(timing attack) 방지를 위해 hmac.compare_digest 사용

    Args:
        email_content: 메일 원본 바이너리 내용
        token: 검증할 토큰 (16진수 문자열)

    Returns:
        토큰이 일치하면 True, 변조되었으면 False
    """
    expected_token = create_integrity_token(email_content)

    # hmac.compare_digest: 타이밍 공격 방지
    # 토큰 길이가 다르면 False 반환 (길이 유출 방지)
    return hmac.compare_digest(expected_token, token)


def get_content_hash(email_content: bytes) -> str:
    """
    메일 원본의 SHA256 해시 생성 (참고용)

    MongoDB 저장 시 추가 검증 정보로 사용 가능

    Args:
        email_content: 메일 원본 바이너리 내용

    Returns:
        SHA256 해시 (16진수 문자열)
    """
    return hashlib.sha256(email_content).hexdigest()


def get_attachment_hash(attachment_data: bytes) -> str:
    """
    첨부파일의 SHA256 해시 생성

    각 첨부파일의 무결성을 개별적으로 검증하기 위해 사용

    Args:
        attachment_data: 첨부파일 바이너리 데이터

    Returns:
        SHA256 해시 (16진수 문자열)
    """
    return hashlib.sha256(attachment_data).hexdigest()


def create_email_metadata(email_content: bytes) -> dict:
    """
    메일로부터 메타데이터 추출 및 무결성 정보 생성

    Args:
        email_content: 메일 원본 바이너리 내용

    Returns:
        메타데이터 딕셔너리:
        {
            'from_email': str,
            'to_email': str,
            'subject': str,
            'body': str,
            'content_hash': str,  # 전체 메일 해시
            'dlp_token': str,     # 무결성 검증 토큰
            'attachments': List[dict]  # 첨부파일 정보
        }
    """
    try:
        mail = message_from_bytes(email_content, policy=policy.default)

        # 본문 추출
        body = ""
        body_part = mail.get_body(preferencelist=('plain', 'html'))
        if body_part:
            body = body_part.get_content()

        # 첨부파일 추출
        attachments = []
        for part in mail.iter_attachments():
            att_data = part.get_payload(decode=True)
            attachments.append({
                "filename": part.get_filename(),
                "content_type": part.get_content_type(),
                "size": len(att_data),
                "hash": get_attachment_hash(att_data)
            })

        # 메타데이터 구성
        metadata = {
            'from_email': mail.get('From'),
            'to_email': mail.get('To'),
            'subject': mail.get('Subject'),
            'body': body,
            'content_hash': get_content_hash(email_content),
            'dlp_token': create_integrity_token(email_content),
            'attachments': attachments,
            'timestamp': datetime.utcnow().isoformat()
        }

        return metadata

    except Exception as e:
        raise ValueError(f"메일 메타데이터 추출 실패: {str(e)}")
