from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Numeric, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # basic, standard, pro, enterprise
    display_name = Column(String(100), nullable=False)
    price_monthly = Column(Numeric(10, 2), nullable=False)
    price_yearly = Column(Numeric(10, 2))
    
    # Limiti
    max_brands = Column(Integer, nullable=False, default=1)
    max_users = Column(Integer, nullable=False, default=1)
    monthly_calendar_generations = Column(Integer, nullable=False, default=3)
    monthly_text_tokens = Column(Integer, nullable=False, default=50000)
    monthly_images = Column(Integer, nullable=False, default=20)
    
    # Features
    has_export_excel = Column(Boolean, default=False)
    has_activity_log = Column(Boolean, default=False)
    has_advanced_roles = Column(Boolean, default=False)
    has_api_access = Column(Boolean, default=False)
    has_crm_integration = Column(Boolean, default=False)
    has_auto_publishing = Column(Boolean, default=False)
    has_analytics = Column(Boolean, default=False)
    has_ab_testing = Column(Boolean, default=False)
    
    # Overage
    allows_overage = Column(Boolean, default=False)
    overage_price_per_1k_tokens = Column(Numeric(10, 4))
    overage_price_per_image = Column(Numeric(10, 4))
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    organizations = relationship("Organization", back_populates="plan")


class UsageTracking(Base):
    __tablename__ = "usage_tracking"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # Contatori
    calendar_generations_used = Column(Integer, default=0)
    text_tokens_used = Column(Integer, default=0)
    images_generated = Column(Integer, default=0)
    
    # Overage
    overage_tokens = Column(Integer, default=0)
    overage_images = Column(Integer, default=0)
    overage_cost = Column(Numeric(10, 2), default=0)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization")
