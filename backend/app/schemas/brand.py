from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class BrandBase(BaseModel):
    name: str
    sector: Optional[str] = None
    tone_of_voice: Optional[str] = None
    brand_values: Optional[str] = None
    description: Optional[str] = None
    website_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    instagram_url: Optional[str] = None
    facebook_url: Optional[str] = None
    target_audience: Optional[str] = None
    unique_selling_points: Optional[str] = None

class BrandCreate(BrandBase):
    pass

class BrandUpdate(BrandBase):
    name: Optional[str] = None

class BrandResponse(BrandBase):
    id: int
    organization_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class BrandDocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
