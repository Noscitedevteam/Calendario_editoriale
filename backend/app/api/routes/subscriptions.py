from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from decimal import Decimal
import re

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, Organization
from app.models.subscription import SubscriptionPlan, UsageTracking
from app.models.brand import Brand
from app.schemas.subscription import (
    PlanResponse, PlanUpdate,
    OrganizationSaaSResponse, OrganizationSaaSUpdate, OrganizationCreate,
    UsageResponse, UsageSummary
)

router = APIRouter()

# === HELPERS ===

def require_superuser(current_user: User = Depends(get_current_user)):
    if current_user.role != "superuser":
        raise HTTPException(status_code=403, detail="Superuser access required")
    return current_user

def generate_slug(name: str) -> str:
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    return slug.strip('-')

def get_effective_limits(org: Organization, plan: SubscriptionPlan) -> dict:
    """Calcola limiti effettivi considerando custom_limits per Enterprise"""
    if org.custom_limits:
        return {
            "max_brands": org.custom_limits.get("max_brands", plan.max_brands if plan else 1),
            "max_users": org.custom_limits.get("max_users", plan.max_users if plan else 1),
            "monthly_calendars": org.custom_limits.get("monthly_calendar_generations", plan.monthly_calendar_generations if plan else 3),
            "monthly_tokens": org.custom_limits.get("monthly_text_tokens", plan.monthly_text_tokens if plan else 50000),
            "monthly_images": org.custom_limits.get("monthly_images", plan.monthly_images if plan else 20),
        }
    elif plan:
        return {
            "max_brands": plan.max_brands,
            "max_users": plan.max_users,
            "monthly_calendars": plan.monthly_calendar_generations,
            "monthly_tokens": plan.monthly_text_tokens,
            "monthly_images": plan.monthly_images,
        }
    return {"max_brands": 1, "max_users": 1, "monthly_calendars": 3, "monthly_tokens": 50000, "monthly_images": 20}

def get_current_period() -> tuple:
    """Ritorna (period_start, period_end) del mese corrente"""
    today = date.today()
    period_start = today.replace(day=1)
    next_month = period_start + relativedelta(months=1)
    period_end = next_month - relativedelta(days=1)
    return period_start, period_end

# === PIANI ===

@router.get("/plans", response_model=List[PlanResponse])
def list_plans(
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    """Lista tutti i piani disponibili (pubblico)"""
    query = db.query(SubscriptionPlan)
    if not include_inactive:
        query = query.filter(SubscriptionPlan.is_active == True)
    return query.order_by(SubscriptionPlan.price_monthly).all()

@router.get("/plans/{plan_id}", response_model=PlanResponse)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    """Dettaglio piano"""
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Piano non trovato")
    return plan

@router.put("/plans/{plan_id}", response_model=PlanResponse)
def update_plan(
    plan_id: int,
    plan_data: PlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser)
):
    """Aggiorna piano (solo superuser)"""
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Piano non trovato")
    
    for field, value in plan_data.dict(exclude_none=True).items():
        setattr(plan, field, value)
    
    db.commit()
    db.refresh(plan)
    return plan

# === ORGANIZZAZIONI SaaS ===

@router.get("/organizations", response_model=List[OrganizationSaaSResponse])
def list_organizations_saas(
    search: Optional[str] = None,
    plan_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser)
):
    """Lista organizzazioni con info SaaS (solo superuser)"""
    query = db.query(Organization)
    
    if search:
        query = query.filter(
            Organization.name.ilike(f"%{search}%") | 
            Organization.email.ilike(f"%{search}%")
        )
    if plan_id:
        query = query.filter(Organization.plan_id == plan_id)
    if status:
        query = query.filter(Organization.subscription_status == status)
    
    total = query.count()
    orgs = query.offset((page-1)*per_page).limit(per_page).all()
    
    result = []
    for org in orgs:
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == org.plan_id).first() if org.plan_id else None
        limits = get_effective_limits(org, plan)
        
        brands_count = db.query(Brand).filter(Brand.organization_id == org.id).count()
        users_count = db.query(User).filter(User.organization_id == org.id, User.is_active == True).count()
        
        result.append(OrganizationSaaSResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            email=org.email,
            phone=org.phone,
            vat_number=org.vat_number,
            address=org.address,
            plan_id=org.plan_id,
            plan_name=plan.name if plan else None,
            plan_display_name=plan.display_name if plan else None,
            subscription_status=org.subscription_status or "trial",
            trial_ends_at=org.trial_ends_at,
            subscription_starts_at=org.subscription_starts_at,
            subscription_ends_at=org.subscription_ends_at,
            effective_max_brands=limits["max_brands"],
            effective_max_users=limits["max_users"],
            effective_monthly_calendars=limits["monthly_calendars"],
            effective_monthly_tokens=limits["monthly_tokens"],
            effective_monthly_images=limits["monthly_images"],
            brands_count=brands_count,
            users_count=users_count,
            custom_limits=org.custom_limits,
            notes=org.notes,
            is_active=org.is_active if org.is_active is not None else True,
            created_at=org.created_at
        ))
    
    return result

@router.post("/organizations", response_model=OrganizationSaaSResponse)
def create_organization_saas(
    org_data: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser)
):
    """Crea nuova organizzazione con piano (solo superuser)"""
    # Verifica piano
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == org_data.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Piano non trovato")
    
    # Genera slug unico
    base_slug = generate_slug(org_data.name)
    slug = base_slug
    counter = 1
    while db.query(Organization).filter(Organization.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    org = Organization(
        name=org_data.name,
        slug=slug,
        email=org_data.email,
        phone=org_data.phone,
        vat_number=org_data.vat_number,
        address=org_data.address,
        plan_id=org_data.plan_id,
        subscription_status="trial",
        trial_ends_at=datetime.utcnow() + relativedelta(days=14),
        custom_limits=org_data.custom_limits,
        notes=org_data.notes,
        is_active=True
    )
    
    db.add(org)
    db.commit()
    db.refresh(org)
    
    # Crea record usage per il mese corrente
    period_start, period_end = get_current_period()
    usage = UsageTracking(
        organization_id=org.id,
        period_start=period_start,
        period_end=period_end
    )
    db.add(usage)
    db.commit()
    
    limits = get_effective_limits(org, plan)
    
    return OrganizationSaaSResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        email=org.email,
        phone=org.phone,
        vat_number=org.vat_number,
        address=org.address,
        plan_id=org.plan_id,
        plan_name=plan.name,
        plan_display_name=plan.display_name,
        subscription_status=org.subscription_status,
        trial_ends_at=org.trial_ends_at,
        effective_max_brands=limits["max_brands"],
        effective_max_users=limits["max_users"],
        effective_monthly_calendars=limits["monthly_calendars"],
        effective_monthly_tokens=limits["monthly_tokens"],
        effective_monthly_images=limits["monthly_images"],
        brands_count=0,
        users_count=0,
        custom_limits=org.custom_limits,
        notes=org.notes,
        is_active=True,
        created_at=org.created_at
    )

@router.put("/organizations/{org_id}", response_model=OrganizationSaaSResponse)
def update_organization_saas(
    org_id: int,
    org_data: OrganizationSaaSUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser)
):
    """Aggiorna organizzazione (solo superuser)"""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organizzazione non trovata")
    
    for field, value in org_data.dict(exclude_none=True).items():
        setattr(org, field, value)
    
    db.commit()
    db.refresh(org)
    
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == org.plan_id).first() if org.plan_id else None
    limits = get_effective_limits(org, plan)
    brands_count = db.query(Brand).filter(Brand.organization_id == org.id).count()
    users_count = db.query(User).filter(User.organization_id == org.id, User.is_active == True).count()
    
    return OrganizationSaaSResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        email=org.email,
        phone=org.phone,
        vat_number=org.vat_number,
        address=org.address,
        plan_id=org.plan_id,
        plan_name=plan.name if plan else None,
        plan_display_name=plan.display_name if plan else None,
        subscription_status=org.subscription_status or "trial",
        trial_ends_at=org.trial_ends_at,
        subscription_starts_at=org.subscription_starts_at,
        subscription_ends_at=org.subscription_ends_at,
        effective_max_brands=limits["max_brands"],
        effective_max_users=limits["max_users"],
        effective_monthly_calendars=limits["monthly_calendars"],
        effective_monthly_tokens=limits["monthly_tokens"],
        effective_monthly_images=limits["monthly_images"],
        brands_count=brands_count,
        users_count=users_count,
        custom_limits=org.custom_limits,
        notes=org.notes,
        is_active=org.is_active if org.is_active is not None else True,
        created_at=org.created_at
    )

# === USAGE TRACKING ===

@router.get("/usage/my", response_model=UsageSummary)
def get_my_usage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Usage dell'organizzazione corrente dell'utente"""
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="Utente non associato a un'organizzazione")
    
    org = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == org.plan_id).first() if org and org.plan_id else None
    limits = get_effective_limits(org, plan)
    
    period_start, period_end = get_current_period()
    
    usage = db.query(UsageTracking).filter(
        UsageTracking.organization_id == current_user.organization_id,
        UsageTracking.period_start == period_start
    ).first()
    
    if not usage:
        # Crea record se non esiste
        usage = UsageTracking(
            organization_id=current_user.organization_id,
            period_start=period_start,
            period_end=period_end
        )
        db.add(usage)
        db.commit()
        db.refresh(usage)
    
    # Calcola percentuali (-1 = illimitato)
    def calc_percentage(used, limit):
        if limit == -1:
            return 0
        return min(100, round((used / limit) * 100, 1)) if limit > 0 else 0
    
    days_remaining = (period_end - date.today()).days + 1
    
    return UsageSummary(
        calendars_used=usage.calendar_generations_used,
        calendars_limit=limits["monthly_calendars"],
        calendars_percentage=calc_percentage(usage.calendar_generations_used, limits["monthly_calendars"]),
        tokens_used=usage.text_tokens_used,
        tokens_limit=limits["monthly_tokens"],
        tokens_percentage=calc_percentage(usage.text_tokens_used, limits["monthly_tokens"]),
        images_used=usage.images_generated,
        images_limit=limits["monthly_images"],
        images_percentage=calc_percentage(usage.images_generated, limits["monthly_images"]),
        days_remaining=max(0, days_remaining),
        overage_cost=usage.overage_cost or Decimal('0.00')
    )

@router.get("/usage/{org_id}", response_model=UsageResponse)
def get_organization_usage(
    org_id: int,
    period: Optional[str] = None,  # YYYY-MM
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superuser)
):
    """Usage di un'organizzazione specifica (solo superuser)"""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organizzazione non trovata")
    
    if period:
        try:
            year, month = map(int, period.split('-'))
            period_start = date(year, month, 1)
        except:
            raise HTTPException(status_code=400, detail="Formato periodo non valido. Usa YYYY-MM")
    else:
        period_start, _ = get_current_period()
    
    period_end = (period_start + relativedelta(months=1)) - relativedelta(days=1)
    
    usage = db.query(UsageTracking).filter(
        UsageTracking.organization_id == org_id,
        UsageTracking.period_start == period_start
    ).first()
    
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == org.plan_id).first() if org.plan_id else None
    limits = get_effective_limits(org, plan)
    
    if not usage:
        usage = UsageTracking(
            organization_id=org_id,
            period_start=period_start,
            period_end=period_end
        )
    
    def calc_percentage(used, limit):
        if limit == -1:
            return 0
        return min(100, round((used / limit) * 100, 1)) if limit > 0 else 0
    
    return UsageResponse(
        organization_id=org_id,
        period_start=period_start,
        period_end=period_end,
        calendar_generations_used=usage.calendar_generations_used,
        text_tokens_used=usage.text_tokens_used,
        images_generated=usage.images_generated,
        calendar_generations_limit=limits["monthly_calendars"],
        text_tokens_limit=limits["monthly_tokens"],
        images_limit=limits["monthly_images"],
        calendar_percentage=calc_percentage(usage.calendar_generations_used, limits["monthly_calendars"]),
        tokens_percentage=calc_percentage(usage.text_tokens_used, limits["monthly_tokens"]),
        images_percentage=calc_percentage(usage.images_generated, limits["monthly_images"]),
        overage_tokens=usage.overage_tokens,
        overage_images=usage.overage_images,
        overage_cost=usage.overage_cost or Decimal('0.00')
    )

# === UTILITY PER INCREMENTARE USAGE (usato da altri endpoint) ===

def increment_usage(db: Session, organization_id: int, calendars: int = 0, tokens: int = 0, images: int = 0):
    """Incrementa contatori usage. Chiamato da generation.py, posts.py, ecc."""
    period_start, period_end = get_current_period()
    
    usage = db.query(UsageTracking).filter(
        UsageTracking.organization_id == organization_id,
        UsageTracking.period_start == period_start
    ).first()
    
    if not usage:
        usage = UsageTracking(
            organization_id=organization_id,
            period_start=period_start,
            period_end=period_end
        )
        db.add(usage)
    
    if calendars:
        usage.calendar_generations_used += calendars
    if tokens:
        usage.text_tokens_used += tokens
    if images:
        usage.images_generated += images
    
    db.commit()
    return usage

def check_usage_limit(db: Session, organization_id: int, check_type: str) -> tuple[bool, str]:
    """
    Verifica se l'organizzazione può ancora usare la risorsa.
    Ritorna (allowed: bool, message: str)
    """
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        return False, "Organizzazione non trovata"
    
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == org.plan_id).first() if org.plan_id else None
    limits = get_effective_limits(org, plan)
    
    period_start, _ = get_current_period()
    usage = db.query(UsageTracking).filter(
        UsageTracking.organization_id == organization_id,
        UsageTracking.period_start == period_start
    ).first()
    
    if not usage:
        return True, "OK"
    
    if check_type == "calendar":
        limit = limits["monthly_calendars"]
        used = usage.calendar_generations_used
        name = "generazioni calendario"
    elif check_type == "tokens":
        limit = limits["monthly_tokens"]
        used = usage.text_tokens_used
        name = "token"
    elif check_type == "images":
        limit = limits["monthly_images"]
        used = usage.images_generated
        name = "immagini"
    else:
        return True, "OK"
    
    # -1 = illimitato
    if limit == -1:
        return True, "OK"
    
    if used >= limit:
        # Check se piano permette overage
        if plan and plan.allows_overage:
            return True, f"Limite {name} raggiunto. Verrà applicato costo extra."
        return False, f"Limite mensile di {name} raggiunto ({used}/{limit}). Upgrade del piano richiesto."
    
    return True, "OK"
