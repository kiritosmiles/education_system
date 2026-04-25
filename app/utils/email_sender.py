import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
from app.config import get_settings

settings = get_settings()


async def send_email(
    to_email: str,
    subject: str,
    content: str,
    html: bool = False,
    attachments: Optional[List[dict]] = None,
) -> bool:
    msg = MIMEMultipart()
    msg["From"] = settings.SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject

    content_type = "html" if html else "plain"
    msg.attach(MIMEText(content, content_type, "utf-8"))

    if attachments:
        for att in attachments:
            part = MIMEBase(att.get("maintype", "application"), att.get("subtype", "octet-stream"))
            part.set_payload(att["content"])
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f'attachment; filename="{att["filename"]}"')
            msg.attach(part)

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=True,
        )
        return True
    except Exception as e:
        print(f"发送邮件失败: {e}")
        return False
