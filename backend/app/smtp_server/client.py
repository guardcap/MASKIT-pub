"""
SMTP 클라이언트를 사용한 메일 전송 유틸리티
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List
from datetime import datetime


class SMTPEmailClient:
    """SMTP를 통한 이메일 전송 클라이언트 (TLS/SSL 지원)"""

    def __init__(self):
        # 환경 변수에서 SMTP 설정 읽기
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        self.use_ssl = os.getenv('SMTP_USE_SSL', 'false').lower() == 'true'

    def send_email(
        self,
        from_email: str,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> dict:
        """
        SMTP를 통해 이메일 전송

        Args:
            from_email: 발신자 이메일
            to: 수신자 이메일 (여러 개는 쉼표로 구분)
            subject: 제목
            body: 본문 (HTML 지원)
            cc: 참조 (옵션)
            bcc: 숨은 참조 (옵션)
            attachments: 첨부파일 경로 리스트 (옵션)

        Returns:
            dict: {"success": bool, "message": str, "sent_at": datetime}
        """
        try:
            # MIMEMultipart 메시지 생성
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to
            msg['Subject'] = subject

            if cc:
                msg['Cc'] = cc
            if bcc:
                msg['Bcc'] = bcc

            # 본문 추가 (HTML)
            msg.attach(MIMEText(body, 'html'))

            # 첨부파일 추가
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename={os.path.basename(file_path)}'
                            )
                            msg.attach(part)

            # 수신자 리스트 생성
            recipients = [email.strip() for email in to.split(',')]
            if cc:
                recipients.extend([email.strip() for email in cc.split(',')])
            if bcc:
                recipients.extend([email.strip() for email in bcc.split(',')])

            # SMTP 서버 연결 및 전송
            print(f"[SMTP Client] 메일 전송 시작...")
            print(f"  From: {from_email}")
            print(f"  To: {to}")
            print(f"  Subject: {subject}")
            print(f"  Protocol: {'SSL' if self.use_ssl else 'TLS' if self.use_tls else 'Plain'}")
            print(f"  SMTP Server: {self.smtp_host}:{self.smtp_port}")
            print(f"  Auth User: {self.smtp_user if self.smtp_user else '(none)'}")

            # SMTP 서버 연결 (SSL 또는 TLS)
            if self.use_ssl:
                # SSL 사용 (포트 465)
                print(f"[SMTP Client] SSL 연결 시도: {self.smtp_host}:{self.smtp_port}")
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                    # 인증 (설정된 경우)
                    if self.smtp_user and self.smtp_password:
                        server.login(self.smtp_user, self.smtp_password)

                    # 메일 전송
                    server.send_message(msg)
            else:
                # TLS 또는 Plain SMTP 사용 (포트 587 또는 25)
                print(f"[SMTP Client] SMTP 연결 시도: {self.smtp_host}:{self.smtp_port}")
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    if self.use_tls:
                        print(f"[SMTP Client] STARTTLS 활성화")
                        server.starttls()

                    # 인증 (설정된 경우)
                    if self.smtp_user and self.smtp_password:
                        server.login(self.smtp_user, self.smtp_password)

                    # 메일 전송
                    server.send_message(msg)

            sent_at = datetime.utcnow()
            print(f"[SMTP Client] ✅ 메일 전송 완료: {sent_at}")

            return {
                "success": True,
                "message": "메일이 성공적으로 전송되었습니다",
                "sent_at": sent_at
            }

        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP 인증 실패: {str(e)}"
            print(f"[SMTP Client] ❌ {error_msg}")
            return {
                "success": False,
                "message": error_msg,
                "sent_at": None
            }

        except smtplib.SMTPException as e:
            error_msg = f"SMTP 오류: {str(e)}"
            print(f"[SMTP Client] ❌ {error_msg}")
            return {
                "success": False,
                "message": error_msg,
                "sent_at": None
            }

        except Exception as e:
            error_msg = f"메일 전송 실패: {str(e)}"
            print(f"[SMTP Client] ❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": error_msg,
                "sent_at": None
            }


# 싱글톤 인스턴스
smtp_client = SMTPEmailClient()
