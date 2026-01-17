from fastapi_mail import FastMail, MessageSchema, MessageType, ConnectionConfig
from pydantic import EmailStr
from typing import List, Optional
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME", "Noscite Calendar"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent.parent / "templates" / "email"
)

class EmailService:
    def __init__(self):
        self.fastmail = FastMail(conf)
    
    async def send_email(
        self,
        recipients: List[EmailStr],
        subject: str,
        template_name: str,
        template_body: dict
    ):
        message = MessageSchema(
            subject=subject,
            recipients=recipients,
            template_body=template_body,
            subtype=MessageType.html
        )
        await self.fastmail.send_message(message, template_name=template_name)
    
    async def send_publication_reminder(
        self,
        user_email: str,
        user_name: str,
        post_title: str,
        platform: str,
        scheduled_time: str,
        post_id: int
    ):
        await self.send_email(
            recipients=[user_email],
            subject=f"Promemoria: Post in programma su {platform}",
            template_name="publication_reminder.html",
            template_body={
                "user_name": user_name,
                "post_title": post_title,
                "platform": platform,
                "scheduled_time": scheduled_time,
                "post_id": post_id,
                "dashboard_url": os.getenv("FRONTEND_URL", "https://calendar.noscite.it")
            }
        )
    
    async def send_publication_success(
        self,
        user_email: str,
        user_name: str,
        post_title: str,
        platform: str,
        post_url: str = None
    ):
        await self.send_email(
            recipients=[user_email],
            subject=f"Post pubblicato su {platform}",
            template_name="publication_success.html",
            template_body={
                "user_name": user_name,
                "post_title": post_title,
                "platform": platform,
                "post_url": post_url,
                "dashboard_url": os.getenv("FRONTEND_URL", "https://calendar.noscite.it")
            }
        )
    
    async def send_publication_failed(
        self,
        user_email: str,
        user_name: str,
        post_title: str,
        platform: str,
        error_message: str,
        post_id: int
    ):
        await self.send_email(
            recipients=[user_email],
            subject=f"Errore pubblicazione su {platform}",
            template_name="publication_failed.html",
            template_body={
                "user_name": user_name,
                "post_title": post_title,
                "platform": platform,
                "error_message": error_message,
                "post_id": post_id,
                "dashboard_url": os.getenv("FRONTEND_URL", "https://calendar.noscite.it")
            }
        )

email_service = EmailService()
