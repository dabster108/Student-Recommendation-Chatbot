from aiosmtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
from pathlib import Path
from ..core.config import settings
import ssl

async def send_email(to: str, subject: str, body: str):
    message = MIMEMultipart()
    message["From"] = settings.EMAIL_FROM
    message["To"] = to
    message["Subject"] = subject
    message.attach(MIMEText(body, "html"))
    
    context = ssl.create_default_context()
    
    async with SMTP(
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        use_tls=True,
        tls_context=context
    ) as smtp:
        await smtp.send_message(message)