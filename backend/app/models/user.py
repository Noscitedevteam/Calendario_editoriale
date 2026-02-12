from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True)
    email = Column(String(255))
    phone = Column(String(50))
    vat_number = Column(String(50))
    address = Column(Text)
    
    # Subscription
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"))
    subscription_status = Column(String(20), default="trial")  # trial, active, past_due, cancelled
    trial_ends_at = Column(DateTime)
    subscription_starts_at = Column(DateTime)
    subscription_ends_at = Column(DateTime)
    
    # Stripe
    stripe_customer_id = Column(String(255))
    stripe_subscription_id = Column(String(255))
    
    # Enterprise custom
    custom_limits = Column(JSON)
    notes = Column(Text)
    api_key_hash = Column(String(255))
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="organization")
    brands = relationship("Brand", back_populates="organization")
    plan = relationship("SubscriptionPlan", back_populates="organizations")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    role = Column(String(20), default="editor")  # superuser, admin, editor, viewer
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Campi profilo estesi
    phone = Column(String(30))
    company = Column(String(255))
    address = Column(Text)
    city = Column(String(100))
    country = Column(String(100))
    vat_number = Column(String(50))
    notes = Column(Text)
    
    organization = relationship("Organization", back_populates="users")
    
    @property
    def is_superuser(self):
        return self.role == "superuser"
    
    @property
    def is_admin(self):
        return self.role in ["superuser", "admin"]
