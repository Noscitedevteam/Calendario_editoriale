"""
Noscite Calendar - Public API
API REST per integrazioni esterne (MCP, CRM, automazioni).
Autenticazione via X-API-Key header.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, timezone
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.api_key_auth import get_api_key_user, require_scope
from app.models.user import User
from app.models.brand import Brand
from app.models.project import Project, ProjectStatus
from app.models.post import Post

router = APIRouter()

# ========================
# SCHEMAS
# ========================

class BrandOut(BaseModel):
    id: int
    name: str
    sector: Optional[str] = None
    description: Optional[str] = None
    tone_of_voice: Optional[str] = None
    website: Optional[str] = None
    class Config:
        from_attributes = True

class ProjectOut(BaseModel):
    id: int
    brand_id: int
    name: str
    start_date: date
    end_date: date
    platforms: Optional[list] = None
    posts_per_week: Optional[dict] = None
    status: str
    class Config:
        from_attributes = True

class PostOut(BaseModel):
    id: int
    project_id: int
    platform: str
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    hashtags: Optional[list] = None
    pillar: Optional[str] = None
    post_type: Optional[str] = None
    content_type: Optional[str] = None
    visual_suggestion: Optional[str] = None
    cta: Optional[str] = None
    call_to_action: Optional[str] = None
    image_url: Optional[str] = None
    is_carousel: Optional[bool] = False
    status: Optional[str] = None
    publication_status: Optional[str] = None
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class PostCreateInput(BaseModel):
    project_id: int
    platform: str = Field(..., description="instagram, linkedin, facebook, google_business")
    scheduled_date: date
    scheduled_time: Optional[str] = "09:00"
    title: Optional[str] = None
    content: str
    hashtags: Optional[List[str]] = []
    pillar: Optional[str] = None
    post_type: Optional[str] = "educational"
    content_type: Optional[str] = "post"  # post, story, reel
    visual_suggestion: Optional[str] = None
    cta: Optional[str] = None
    call_to_action: Optional[str] = None

class PostUpdateInput(BaseModel):
    content: Optional[str] = None
    title: Optional[str] = None
    hashtags: Optional[List[str]] = None
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = None
    platform: Optional[str] = None
    pillar: Optional[str] = None
    post_type: Optional[str] = None
    content_type: Optional[str] = None
    visual_suggestion: Optional[str] = None
    cta: Optional[str] = None
    call_to_action: Optional[str] = None
    status: Optional[str] = None

class BulkPostCreateInput(BaseModel):
    posts: List[PostCreateInput]

class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

# ========================
# HELPERS
# ========================

def get_user_brands_query(db: Session, user: User):
    return db.query(Brand).filter(Brand.organization_id == user.organization_id)

def verify_brand_access(db: Session, user: User, brand_id: int) -> Brand:
    brand = get_user_brands_query(db, user).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand non trovato")
    return brand

def verify_project_access(db: Session, user: User, project_id: int) -> Project:
    project = db.query(Project).join(Brand).filter(
        Project.id == project_id,
        Brand.organization_id == user.organization_id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")
    return project

def verify_post_access(db: Session, user: User, post_id: int) -> Post:
    post = db.query(Post).join(Project).join(Brand).filter(
        Post.id == post_id,
        Brand.organization_id == user.organization_id
    ).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post non trovato")
    return post

# ========================
# BRANDS
# ========================

@router.get("/brands", response_model=List[BrandOut], summary="Lista brands")
def list_brands(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scope("read"))
):
    """Restituisce tutti i brand dell'organizzazione."""
    return get_user_brands_query(db, current_user).all()

@router.get("/brands/{brand_id}", response_model=BrandOut, summary="Dettaglio brand")
def get_brand(
    brand_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scope("read"))
):
    return verify_brand_access(db, current_user, brand_id)

# ========================
# PROJECTS
# ========================

@router.get("/projects", response_model=List[ProjectOut], summary="Lista progetti")
def list_projects(
    brand_id: Optional[int] = Query(None, description="Filtra per brand"),
    status: Optional[str] = Query(None, description="Filtra per stato: draft, generating, review, approved, published"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scope("read"))
):
    """Restituisce i progetti. Filtrabile per brand e stato."""
    query = db.query(Project).join(Brand).filter(
        Brand.organization_id == current_user.organization_id
    )
    if brand_id:
        query = query.filter(Project.brand_id == brand_id)
    if status:
        query = query.filter(Project.status == status)
    return query.order_by(Project.start_date.desc()).all()

@router.get("/projects/{project_id}", response_model=ProjectOut, summary="Dettaglio progetto")
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scope("read"))
):
    return verify_project_access(db, current_user, project_id)

# ========================
# POSTS (CALENDARIO)
# ========================

@router.get("/posts", response_model=List[PostOut], summary="Lista post del calendario")
def list_posts(
    project_id: Optional[int] = Query(None, description="Filtra per progetto"),
    brand_id: Optional[int] = Query(None, description="Filtra per brand (tutti i progetti)"),
    platform: Optional[str] = Query(None, description="Filtra per piattaforma"),
    date_from: Optional[date] = Query(None, description="Data inizio (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="Data fine (YYYY-MM-DD)"),
    status: Optional[str] = Query(None, description="Filtra per stato"),
    limit: int = Query(50, le=200, description="Max risultati"),
    offset: int = Query(0, description="Offset paginazione"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scope("read"))
):
    """
    Restituisce i post del calendario editoriale.
    Filtrabile per progetto, brand, piattaforma, range date e stato.
    """
    query = db.query(Post).join(Project).join(Brand).filter(
        Brand.organization_id == current_user.organization_id
    )
    if project_id:
        query = query.filter(Post.project_id == project_id)
    if brand_id:
        query = query.filter(Brand.id == brand_id)
    if platform:
        query = query.filter(Post.platform == platform)
    if date_from:
        query = query.filter(Post.scheduled_date >= date_from)
    if date_to:
        query = query.filter(Post.scheduled_date <= date_to)
    if status:
        query = query.filter(Post.status == status)
    
    return query.order_by(Post.scheduled_date.asc()).offset(offset).limit(limit).all()

@router.get("/posts/{post_id}", response_model=PostOut, summary="Dettaglio post")
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scope("read"))
):
    return verify_post_access(db, current_user, post_id)

@router.post("/posts", response_model=PostOut, summary="Crea post nel calendario")
def create_post(
    data: PostCreateInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scope("write"))
):
    """
    Inserisce un nuovo post nel calendario editoriale.
    Il post viene associato al progetto specificato.
    """
    project = verify_project_access(db, current_user, data.project_id)
    
    post = Post(
        project_id=data.project_id,
        platform=data.platform,
        scheduled_date=data.scheduled_date,
        scheduled_time=data.scheduled_time or "09:00",
        title=data.title,
        content=data.content,
        hashtags=data.hashtags or [],
        pillar=data.pillar,
        post_type=data.post_type or "educational",
        content_type=data.content_type or "post",
        visual_suggestion=data.visual_suggestion,
        cta=data.cta,
        call_to_action=data.call_to_action,
        status="draft",
        publication_status="draft"
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post

@router.post("/posts/bulk", summary="Crea post multipli")
def create_posts_bulk(
    data: BulkPostCreateInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scope("write"))
):
    """Inserisce più post nel calendario in una singola chiamata."""
    created = []
    for post_data in data.posts:
        project = verify_project_access(db, current_user, post_data.project_id)
        post = Post(
            project_id=post_data.project_id,
            platform=post_data.platform,
            scheduled_date=post_data.scheduled_date,
            scheduled_time=post_data.scheduled_time or "09:00",
            title=post_data.title,
            content=post_data.content,
            hashtags=post_data.hashtags or [],
            pillar=post_data.pillar,
            post_type=post_data.post_type or "educational",
            content_type=post_data.content_type or "post",
            visual_suggestion=post_data.visual_suggestion,
            cta=post_data.cta,
            call_to_action=post_data.call_to_action,
            status="draft",
            publication_status="draft"
        )
        db.add(post)
        created.append(post)
    
    db.commit()
    for p in created:
        db.refresh(p)
    
    return {"success": True, "created_count": len(created), "post_ids": [p.id for p in created]}

@router.patch("/posts/{post_id}", response_model=PostOut, summary="Aggiorna post")
def update_post(
    post_id: int,
    data: PostUpdateInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scope("write"))
):
    """Aggiorna un post esistente nel calendario."""
    post = verify_post_access(db, current_user, post_id)
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(post, field, value)
    
    db.commit()
    db.refresh(post)
    return post

@router.delete("/posts/{post_id}", summary="Elimina post")
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scope("write"))
):
    """Elimina un post dal calendario."""
    post = verify_post_access(db, current_user, post_id)
    db.delete(post)
    db.commit()
    return {"success": True, "message": f"Post {post_id} eliminato"}

# ========================
# PUBBLICAZIONE
# ========================

@router.post("/posts/{post_id}/schedule", summary="Schedula post per pubblicazione")
async def schedule_post_api(
    post_id: int,
    platforms: Optional[List[str]] = Query(None, description="Piattaforme target"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scope("publish"))
):
    """
    Schedula un post per la pubblicazione automatica.
    Richiede connessioni social attive per il brand.
    """
    from app.models.social_connection import SocialConnection, PostPublication
    
    post = verify_post_access(db, current_user, post_id)
    project = post.project
    brand = db.query(Brand).filter(Brand.id == project.brand_id).first()
    
    target_platforms = platforms or [post.platform]
    scheduled = []
    
    for platform in target_platforms:
        connection = db.query(SocialConnection).filter(
            SocialConnection.brand_id == brand.id,
            SocialConnection.platform == platform,
            SocialConnection.is_active == True
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=400,
                detail=f"Nessuna connessione attiva per {platform} sul brand {brand.name}"
            )
        
        # Crea record pubblicazione
        scheduled_time = datetime.combine(
            post.scheduled_date,
            datetime.strptime(post.scheduled_time or "09:00", "%H:%M").time()
        ).replace(tzinfo=timezone.utc)
        
        publication = PostPublication(
            post_id=post.id,
            social_connection_id=connection.id,
            platform=platform,
            status="scheduled",
            scheduled_for=scheduled_time
        )
        db.add(publication)
        scheduled.append(platform)
    
    post.publication_status = "scheduled"
    db.commit()
    
    return {"success": True, "scheduled_platforms": scheduled}

@router.post("/posts/{post_id}/publish", summary="Pubblica post immediatamente")
async def publish_post_api(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scope("publish"))
):
    """Pubblica un post immediatamente sulle piattaforme connesse."""
    from app.services.publisher_service import PublisherService
    from app.models.social_connection import SocialConnection, PostPublication
    
    post = verify_post_access(db, current_user, post_id)
    project = post.project
    brand = db.query(Brand).filter(Brand.id == project.brand_id).first()
    
    connection = db.query(SocialConnection).filter(
        SocialConnection.brand_id == brand.id,
        SocialConnection.platform == post.platform,
        SocialConnection.is_active == True
    ).first()
    
    if not connection:
        raise HTTPException(status_code=400, detail=f"Nessuna connessione {post.platform} attiva")
    
    publisher = PublisherService()
    result = await publisher.publish_post(post, connection, db)
    
    return result

# ========================
# GENERAZIONE AI
# ========================

@router.post("/generate/calendar/{project_id}", summary="Genera calendario con AI")
def generate_calendar_api(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scope("write"))
):
    """
    Avvia la generazione AI del calendario editoriale per un progetto.
    Il processo è asincrono: il progetto passa in stato 'generating'.
    """
    from app.api.routes.generation import generate_calendar
    project = verify_project_access(db, current_user, project_id)
    
    if project.status == ProjectStatus.generating:
        raise HTTPException(status_code=409, detail="Generazione già in corso")
    
    # Riusa la logica esistente
    return generate_calendar(project_id=project_id, db=db, current_user=current_user)

# ========================
# INFO / HEALTH
# ========================

@router.get("/me", summary="Info utente e organizzazione")
def api_me(
    db: Session = Depends(get_db),
    auth: tuple = Depends(get_api_key_user)
):
    """Restituisce info sull'utente e organizzazione associati alla API key."""
    user, ak = auth
    return {
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "organization_id": user.organization_id,
        "api_key_name": ak.name,
        "scopes": ak.scopes,
        "key_prefix": ak.key_prefix
    }


# ========================
# CONTEXT (risoluzione automatica)
# ========================

@router.get("/context", summary="Contesto utente: brands, progetti attivi")
def get_context(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scope("read"))
):
    """
    Restituisce il contesto completo dell'utente: brands e progetti attivi.
    Utile per capire dove inserire i post senza dover fare chiamate multiple.
    Se c'è un solo brand/progetto, vengono indicati come default.
    """
    brands = db.query(Brand).filter(
        Brand.organization_id == current_user.organization_id
    ).all()
    
    result = []
    for brand in brands:
        projects = db.query(Project).filter(
            Project.brand_id == brand.id,
            Project.status.in_(["review", "approved", "published"])
        ).order_by(Project.start_date.desc()).all()
        
        result.append({
            "brand_id": brand.id,
            "brand_name": brand.name,
            "sector": brand.sector,
            "projects": [{
                "project_id": p.id,
                "name": p.name,
                "start_date": str(p.start_date),
                "end_date": str(p.end_date),
                "platforms": p.platforms,
                "status": p.status.value if hasattr(p.status, 'value') else p.status
            } for p in projects]
        })
    
    # Identifica default se c'è un solo brand/progetto
    default_brand = result[0] if len(result) == 1 else None
    default_project = None
    if default_brand and len(default_brand["projects"]) == 1:
        default_project = default_brand["projects"][0]
    
    return {
        "brands": result,
        "default_brand_id": default_brand["brand_id"] if default_brand else None,
        "default_brand_name": default_brand["brand_name"] if default_brand else None,
        "default_project_id": default_project["project_id"] if default_project else None,
        "default_project_name": default_project["name"] if default_project else None,
        "hint": "Usa default_brand_id e default_project_id per creare post se disponibili"
    }


# ========================
# CREATE POST (parametri espliciti per compatibilità MCP)
# ========================

from fastapi import Body

@router.post("/posts/create", response_model=PostOut, summary="Crea post (parametri espliciti)")
def create_post_explicit(
    project_id: int = Body(..., description="ID del progetto"),
    platform: str = Body(..., description="Piattaforma: instagram, linkedin, facebook, google_business"),
    content: str = Body(..., description="Testo del post"),
    scheduled_date: date = Body(..., description="Data pubblicazione (YYYY-MM-DD)"),
    scheduled_time: str = Body("09:00", description="Ora pubblicazione (HH:MM)"),
    title: Optional[str] = Body(None, description="Titolo del post"),
    hashtags: Optional[List[str]] = Body(None, description="Lista hashtag"),
    pillar: Optional[str] = Body(None, description="Pillar del contenuto"),
    post_type: Optional[str] = Body("educational", description="Tipo: educational, promotional, engagement, storytelling"),
    content_type: Optional[str] = Body("post", description="Formato: post, story, reel"),
    visual_suggestion: Optional[str] = Body(None, description="Suggerimento visivo per immagine"),
    cta: Optional[str] = Body(None, description="Call to action"),
    call_to_action: Optional[str] = Body(None, description="Call to action estesa"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_scope("write"))
):
    """
    Crea un post nel calendario editoriale con parametri espliciti.
    Endpoint ottimizzato per integrazioni MCP.
    """
    project = verify_project_access(db, current_user, project_id)
    
    post = Post(
        project_id=project_id,
        platform=platform,
        scheduled_date=scheduled_date,
        scheduled_time=scheduled_time,
        title=title,
        content=content,
        hashtags=hashtags or [],
        pillar=pillar,
        post_type=post_type or "educational",
        content_type=content_type or "post",
        visual_suggestion=visual_suggestion,
        cta=cta,
        call_to_action=call_to_action,
        status="draft",
        publication_status="draft"
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


# ========================
# OPENAPI SPEC DEDICATA
# ========================

from fastapi.openapi.utils import get_openapi
from fastapi import Request

@router.get("/openapi.json", summary="OpenAPI spec solo Public API", include_in_schema=False)
def public_openapi(request: Request):
    """Restituisce la spec OpenAPI filtrata solo per gli endpoint Public API v1."""
    full_spec = request.app.openapi()
    
    filtered_paths = {}
    for path, methods in full_spec.get("paths", {}).items():
        if path.startswith("/api/v1/") and path != "/api/v1/openapi.json":
            filtered_paths[path] = methods
    
    # Raccogli solo gli schema referenziati
    used_schemas = set()
    spec_str = str(filtered_paths)
    for schema_name in full_spec.get("components", {}).get("schemas", {}).keys():
        if schema_name in spec_str:
            used_schemas.add(schema_name)
    
    filtered_schemas = {k: v for k, v in full_spec.get("components", {}).get("schemas", {}).items() if k in used_schemas}
    
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "Noscite Calendar - Public API",
            "description": "API per integrazioni esterne: gestione calendario editoriale, post, brands e progetti. Autenticazione via header X-API-Key.",
            "version": "1.0.0"
        },
        "paths": filtered_paths,
        "components": {
            "schemas": filtered_schemas,
            "securitySchemes": {
                "APIKeyHeader": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key"
                }
            }
        }
    }
