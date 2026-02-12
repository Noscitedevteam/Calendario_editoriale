from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.notification import Notification
from app.models.post import Post
from app.models.project import Project
from app.models.user import User


def create_notification(
    db: Session,
    user_id: int,
    type: str,
    title: str,
    message: Optional[str] = None,
    post_id: Optional[int] = None,
    project_id: Optional[int] = None,
    brand_id: Optional[int] = None
) -> Notification:
    """Crea una nuova notifica"""
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        post_id=post_id,
        project_id=project_id,
        brand_id=brand_id
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def notify_post_published(db: Session, post: Post, project: Project):
    """Notifica pubblicazione riuscita"""
    # Trova gli utenti dell'organizzazione del brand
    from app.models.brand import Brand
    brand = db.query(Brand).filter(Brand.id == project.brand_id).first()
    if not brand:
        return
    
    users = db.query(User).filter(User.organization_id == brand.organization_id).all()
    
    platform_icons = {
        "instagram": "📸",
        "facebook": "👥", 
        "linkedin": "💼",
        "google": "📍"
    }
    icon = platform_icons.get(post.platform, "📱")
    
    for user in users:
        create_notification(
            db=db,
            user_id=user.id,
            type="post_published",
            title=f"{icon} Post pubblicato su {post.platform.title()}",
            message=post.content[:100] + "..." if len(post.content) > 100 else post.content,
            post_id=post.id,
            project_id=project.id,
            brand_id=brand.id
        )


def notify_post_failed(db: Session, post: Post, project: Project, error: str):
    """Notifica pubblicazione fallita"""
    from app.models.brand import Brand
    brand = db.query(Brand).filter(Brand.id == project.brand_id).first()
    if not brand:
        return
    
    users = db.query(User).filter(User.organization_id == brand.organization_id).all()
    
    for user in users:
        create_notification(
            db=db,
            user_id=user.id,
            type="post_failed",
            title=f"❌ Pubblicazione fallita su {post.platform.title()}",
            message=f"Errore: {error[:150]}",
            post_id=post.id,
            project_id=project.id,
            brand_id=brand.id
        )
