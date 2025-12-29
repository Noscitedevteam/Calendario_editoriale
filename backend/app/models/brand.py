from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Brand(Base):
    __tablename__ = "brands"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    sector = Column(String(100))
    target_audience = Column(Text)
    tone_of_voice = Column(String(100))
    brand_values = Column(JSON)
    website = Column(String(500))
    website_url = Column(String(500))
    linkedin_url = Column(String(500))
    instagram_url = Column(String(500))
    facebook_url = Column(String(500))
    unique_selling_points = Column(Text)
    colors = Column(String(255))
    style_guide = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    organization = relationship("Organization", back_populates="brands")
    projects = relationship("Project", back_populates="brand", cascade="all, delete-orphan")
