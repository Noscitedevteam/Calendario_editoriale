from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.models.brand import Brand
from app.api.routes.auth import get_current_user
from app.models.user import User

router = APIRouter()

class BrandCreate(BaseModel):
    name: str
    sector: Optional[str] = ""
    tone_of_voice: Optional[str] = ""
    brand_values: Optional[str] = ""
    description: Optional[str] = ""
    target_audience: Optional[str] = ""
    colors: Optional[str] = ""
    style_guide: Optional[str] = ""

class BrandUpdate(BaseModel):
    name: Optional[str] = None
    sector: Optional[str] = None
    tone_of_voice: Optional[str] = None
    brand_values: Optional[str] = None
    description: Optional[str] = None
    target_audience: Optional[str] = None
    colors: Optional[str] = None
    style_guide: Optional[str] = None

@router.get("/")
def list_brands(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.project import Project
    from app.models.post import Post
    
    # Filter by user's organization_id
    brands = db.query(Brand).filter(Brand.organization_id == current_user.organization_id).all()
    
    result = []
    for b in brands:
        # Count projects for this brand
        projects_count = db.query(Project).filter(Project.brand_id == b.id).count()
        
        # Count posts for all projects of this brand
        posts_count = db.query(Post).join(Project).filter(Project.brand_id == b.id).count()
        
        result.append({
            "id": b.id,
            "name": b.name,
            "sector": b.sector,
            "tone_of_voice": b.tone_of_voice,
            "brand_values": b.brand_values,
            "description": b.description,
            "target_audience": b.target_audience,
            "colors": b.colors,
            "style_guide": b.style_guide,
            "website": b.website if hasattr(b, 'website') else None,
            "projects_count": projects_count,
            "posts_count": posts_count
        })
    
    return result

@router.get("/{brand_id}")
def get_brand(
    brand_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    brand = db.query(Brand).filter(
        Brand.id == brand_id,
        Brand.organization_id == current_user.organization_id
    ).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return {
        "id": brand.id,
        "name": brand.name,
        "sector": brand.sector,
        "tone_of_voice": brand.tone_of_voice,
        "brand_values": brand.brand_values,
        "description": brand.description,
        "target_audience": brand.target_audience,
        "colors": brand.colors,
        "style_guide": brand.style_guide
    }

@router.post("/")
def create_brand(
    brand: BrandCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User has no organization")
    
    db_brand = Brand(
        organization_id=current_user.organization_id,
        name=brand.name,
        sector=brand.sector,
        tone_of_voice=brand.tone_of_voice,
        brand_values=brand.brand_values,
        description=brand.description,
        target_audience=brand.target_audience,
        colors=brand.colors,
        style_guide=brand.style_guide
    )
    db.add(db_brand)
    db.commit()
    db.refresh(db_brand)
    return {"id": db_brand.id, "name": db_brand.name}

@router.put("/{brand_id}")
def update_brand(
    brand_id: int,
    brand_update: BrandUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    brand = db.query(Brand).filter(
        Brand.id == brand_id,
        Brand.organization_id == current_user.organization_id
    ).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    update_data = brand_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(brand, key, value)
    
    db.commit()
    db.refresh(brand)
    return {"id": brand.id, "name": brand.name}

@router.delete("/{brand_id}")
def delete_brand(
    brand_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    brand = db.query(Brand).filter(
        Brand.id == brand_id,
        Brand.organization_id == current_user.organization_id
    ).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    db.delete(brand)
    db.commit()
    return {"message": "Brand deleted"}
