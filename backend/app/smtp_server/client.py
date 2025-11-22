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
        attachments: Optional[List[str]] = None,
        smtp_config: Optional[dict] = None
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
            smtp_config: 사용자 SMTP 설정 (옵션, 없으면 환경변수 사용)

        Returns:
            dict: {"success": bool, "message": str, "sent_at": datetime}
        """
        try:
            # 사용자 SMTP 설정이 제공된 경우 사용
            if smtp_config:
                smtp_host = smtp_config.get('smtp_host', self.smtp_host)
                smtp_port = smtp_config.get('smtp_port', self.smtp_port)
                smtp_user = smtp_config.get('smtp_user', self.smtp_user)
                smtp_password = smtp_config.get('smtp_password', self.smtp_password)
                # DB에서는 smtp_use_tls, smtp_use_ssl로 저장되므로 둘 다 지원
                use_tls = smtp_config.get('smtp_use_tls', smtp_config.get('use_tls', self.use_tls))
                use_ssl = smtp_config.get('smtp_use_ssl', smtp_config.get('use_ssl', self.use_ssl))

                print(f"[SMTP Client] 🔧 사용자 SMTP 설정 사용")
                print(f"  Host: {smtp_host}")
                print(f"  Port: {smtp_port}")
                print(f"  User: {smtp_user}")
            else:
                smtp_host = self.smtp_host
                smtp_port = self.smtp_port
                smtp_user = self.smtp_user
                smtp_password = self.smtp_password
                use_tls = self.use_tls
                use_ssl = self.use_ssl

                print(f"[SMTP Client] 🔧 환경변수 SMTP 설정 사용")

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
                print(f"[SMTP Client] 📎 첨부파일 처리 시작: {len(attachments)}개")

                for idx, attachment in enumerate(attachments):
                    try:
                        # Base64 데이터가 있는 경우 (MongoDB에서 온 경우)
                        if isinstance(attachment, dict) and attachment.get('data'):
                            import base64
                            from email.utils import encode_rfc2231
                            filename = attachment.get('filename', f'attachment_{idx}')
                            content_type = attachment.get('content_type', 'application/octet-stream')
                            base64_data = attachment.get('data')

                            print(f"[SMTP Client] 📦 Base64 첨부파일: {filename}")

                            # Base64 디코딩
                            file_data = base64.b64decode(base64_data)

                            # MIME part 생성
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(file_data)
                            encoders.encode_base64(part)

                            # RFC 2231 형식으로 한글 파일명 인코딩
                            encoded_filename = encode_rfc2231(filename, charset='utf-8')
                            part.add_header(
                                'Content-Disposition',
                                'attachment',
                                filename=('utf-8', '', filename)
                            )
                            msg.attach(part)
                            print(f"[SMTP Client] ✅ Base64 첨부파일 추가: {filename} ({len(file_data)} bytes)")

                        # 파일 경로가 있는 경우
                        else:
                            # dict 형태 또는 string 형태 모두 지원
                            if isinstance(attachment, dict):
                                file_path = attachment.get('filename')
                            else:
                                file_path = attachment

                            # file_path가 None이거나 빈 문자열이면 스킵
                            if not file_path:
                                print(f"[SMTP Client] ⚠️ 첨부파일 경로가 없음: {attachment}")
                                continue

                            # 프로젝트 루트 디렉토리 기준으로 uploads 경로 설정
                            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                            uploads_dir = os.path.join(project_root, 'uploads')

                            # 절대 경로 생성
                            if os.path.isabs(file_path):
                                full_path = file_path
                            elif file_path.startswith('uploads/') or file_path.startswith('uploads\\'):
                                full_path = os.path.join(project_root, file_path)
                            else:
                                full_path = os.path.join(uploads_dir, file_path)

                            print(f"[SMTP Client] 📁 파일 경로: {full_path}")

                            if os.path.exists(full_path):
                                with open(full_path, 'rb') as f:
                                    part = MIMEBase('application', 'octet-stream')
                                    part.set_payload(f.read())
                                    encoders.encode_base64(part)
                                    part.add_header(
                                        'Content-Disposition',
                                        f'attachment; filename={os.path.basename(file_path)}'
                                    )
                                    msg.attach(part)
                                print(f"[SMTP Client] ✅ 파일 첨부파일 추가: {os.path.basename(file_path)} ({os.path.getsize(full_path)} bytes)")
                            else:
                                print(f"[SMTP Client] ❌ 첨부파일 없음: {full_path}")

                    except Exception as e:
                        print(f"[SMTP Client] ❌ 첨부파일 처리 오류: {e}")
                        import traceback
                        traceback.print_exc()

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
            print(f"  Protocol: {'SSL' if use_ssl else 'TLS' if use_tls else 'Plain'}")
            print(f"  SMTP Server: {smtp_host}:{smtp_port}")
            print(f"  Auth User: {smtp_user if smtp_user else '(none)'}")

            # SMTP 서버 연결 (SSL 또는 TLS)
            if use_ssl:
                # SSL 사용 (포트 465)
                print(f"[SMTP Client] SSL 연결 시도: {smtp_host}:{smtp_port}")
                with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
                    # 인증 (설정된 경우)
                    if smtp_user and smtp_password:
                        server.login(smtp_user, smtp_password)

                    # 메일 전송
                    server.send_message(msg)
            else:
                # TLS 또는 Plain SMTP 사용 (포트 587 또는 25)
                print(f"[SMTP Client] SMTP 연결 시도: {smtp_host}:{smtp_port}")
                with smtplib.SMTP(smtp_host, smtp_port) as server:
                    if use_tls:
                        print(f"[SMTP Client] STARTTLS 활성화")
                        server.starttls()

                    # 인증 (설정된 경우)
                    if smtp_user and smtp_password:
                        server.login(smtp_user, smtp_password)

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
