import asyncio
from services.email_service import email_service

async def test():
    await email_service.send_publication_reminder(
        user_email="sandrello@noscite.it",
        user_name="Stefano",
        post_title="Test Post",
        platform="LinkedIn",
        scheduled_time="Domani alle 10:00",
        post_id=1
    )
    print("Email inviata!")

asyncio.run(test())
