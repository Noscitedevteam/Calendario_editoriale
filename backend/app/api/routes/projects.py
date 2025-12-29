from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import date

from app.core.database import get_db
from app.models.project import Project, ProjectStatus
from app.models.brand import Brand
from app.api.routes.auth import get_current_user
from app.models.user import User

router = APIRouter()

class ProjectCreate(BaseModel):
    brand_id: int
    name: str
    start_date: date
    end_date: date
    platforms: List[str] = []
    posts_per_week: dict = {}
    themes: List[str] = []
    brief: Optional[str] = ""
    custom_prompt: Optional[str] = ""
    reference_urls: List[str] = []
    target_audience: Optional[str] = ""
    content_pillars: List[str] = []
    competitors: List[str] = []
    special_dates: List[dict] = []

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    platforms: Optional[List[str]] = None
    posts_per_week: Optional[dict] = None
    themes: Optional[List[str]] = None
    brief: Optional[str] = None
    custom_prompt: Optional[str] = None
    status: Optional[str] = None
    reference_urls: Optional[List[str]] = None
    target_audience: Optional[str] = None
    content_pillars: Optional[List[str]] = None
    competitors: Optional[List[str]] = None
    special_dates: Optional[List[dict]] = None

def project_to_dict(p: Project) -> dict:
    return {
        "id": p.id,
        "brand_id": p.brand_id,
        "name": p.name,
        "start_date": str(p.start_date),
        "end_date": str(p.end_date),
        "platforms": p.platforms or [],
        "posts_per_week": p.posts_per_week or {},
        "themes": p.themes or [],
        "brief": p.brief or "",
        "custom_prompt": p.custom_prompt or "",
        "status": p.status.value if p.status else "draft",
        "reference_urls": p.reference_urls or [],
        "target_audience": p.target_audience or "",
        "content_pillars": p.content_pillars or [],
        "competitors": p.competitors or [],
        "special_dates": p.special_dates or [],
        "buyer_personas": p.buyer_personas
    }

@router.get("/")
def list_projects(
    brand_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Project)
    if brand_id:
        query = query.filter(Project.brand_id == brand_id)
    projects = query.all()
    return [project_to_dict(p) for p in projects]

@router.get("/{project_id}")
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project_to_dict(project)

@router.post("/")
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    brand = db.query(Brand).filter(Brand.id == project.brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    db_project = Project(
        brand_id=project.brand_id,
        name=project.name,
        start_date=project.start_date,
        end_date=project.end_date,
        platforms=project.platforms,
        posts_per_week=project.posts_per_week,
        themes=project.themes,
        brief=project.brief,
        custom_prompt=project.custom_prompt,
        reference_urls=project.reference_urls,
        target_audience=project.target_audience,
        content_pillars=project.content_pillars,
        competitors=project.competitors,
        special_dates=project.special_dates,
        status=ProjectStatus.draft
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return project_to_dict(db_project)

@router.put("/{project_id}")
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_data = project_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key == "status" and value:
            setattr(project, key, ProjectStatus(value))
        else:
            setattr(project, key, value)
    
    db.commit()
    db.refresh(project)
    return project_to_dict(project)

@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db.delete(project)
    db.commit()
    return {"message": "Project deleted successfully"}
