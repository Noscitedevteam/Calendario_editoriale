from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class SocialConnection(Base):
    __tablename__ = "social_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(50), nullable=False)  # linkedin, facebook, instagram, google_business
    
    # Token OAuth
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime(timezone=True))
    
    # Info account esterno
    external_account_id = Column(String(255), nullable=False)
    external_account_name = Column(String(255))
    external_account_url = Column(String(500))
    account_type = Column(String(50))  # page, profile, business
    
    # Metadata
    is_active = Column(Boolean, default=True)
    connected_at = Column(DateTime(timezone=True), server_default=func.now())
    connected_by_user_id = Column(Integer, ForeignKey("users.id"))
    last_used_at = Column(DateTime(timezone=True))
    
    # Relationships
    brand = relationship("Brand", back_populates="social_connections")
    connected_by = relationship("User")
    publications = relationship("PostPublication", back_populates="social_connection", cascade="all, delete-orphan")


class PostPublication(Base):
    __tablename__ = "post_publications"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    social_connection_id = Column(Integer, ForeignKey("social_connections.id", ondelete="CASCADE"), nullable=False)
    
    # Stato pubblicazione
    status = Column(String(50), default="pending")  # pending, scheduled, publishing, published, failed
    scheduled_for = Column(DateTime(timezone=True))
    published_at = Column(DateTime(timezone=True))
    
    # Riferimento esterno
    external_post_id = Column(String(255))
    external_post_url = Column(String(500))
    
    # Errori
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    last_retry_at = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    post = relationship("Post", back_populates="publications")
    social_connection = relationship("SocialConnection", back_populates="publications")


class SocialMetric(Base):
    __tablename__ = "social_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    social_connection_id = Column(Integer, ForeignKey("social_connections.id", ondelete="CASCADE"))
    post_publication_id = Column(Integer, ForeignKey("post_publications.id", ondelete="CASCADE"))
    
    # Metriche comuni
    impressions = Column(Integer, default=0)
    reach = Column(Integer, default=0)
    engagement = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    saves = Column(Integer, default=0)
    
    # Metriche account
    followers_count = Column(Integer)
    followers_gained = Column(Integer)
    
    # Periodo
    metric_date = Column(DateTime, nullable=False)
    metric_type = Column(String(20), default="daily")
    
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
    raw_data = Column(JSON)
    
    # Relationships
    social_connection = relationship("SocialConnection", backref="metrics")
    post_publication = relationship("PostPublication", backref="metrics")
