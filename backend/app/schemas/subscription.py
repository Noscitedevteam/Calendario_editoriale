from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

# === PIANI ===

class PlanResponse(BaseModel):
    id: int
    name: str
    display_name: str
    price_monthly: Decimal
    price_yearly: Optional[Decimal] = None
    max_brands: int
    max_users: int
    monthly_calendar_generations: int
    monthly_text_tokens: int
    monthly_images: int
    has_export_excel: bool
    has_activity_log: bool
    has_advanced_roles: bool
    has_api_access: bool
    has_crm_integration: bool
    has_auto_publishing: bool
    has_analytics: bool
    has_ab_testing: bool
    allows_overage: bool
    is_active: bool
    
    class Config:
        from_attributes = True

class PlanUpdate(BaseModel):
    display_name: Optional[str] = None
    price_monthly: Optional[Decimal] = None
    price_yearly: Optional[Decimal] = None
    max_brands: Optional[int] = None
    max_users: Optional[int] = None
    monthly_calendar_generations: Optional[int] = None
    monthly_text_tokens: Optional[int] = None
    monthly_images: Optional[int] = None
    is_active: Optional[bool] = None

# === ORGANIZZAZIONI ESTESE ===

class OrganizationSaaSResponse(BaseModel):
    id: int
    name: str
    slug: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    vat_number: Optional[str] = None
    address: Optional[str] = None
    
    # Subscription info
    plan_id: Optional[int] = None
    plan_name: Optional[str] = None
    plan_display_name: Optional[str] = None
    subscription_status: str = "trial"
    trial_ends_at: Optional[datetime] = None
    subscription_starts_at: Optional[datetime] = None
    subscription_ends_at: Optional[datetime] = None
    
    # Limiti effettivi (considerando custom_limits per Enterprise)
    effective_max_brands: Optional[int] = None
    effective_max_users: Optional[int] = None
    effective_monthly_calendars: Optional[int] = None
    effective_monthly_tokens: Optional[int] = None
    effective_monthly_images: Optional[int] = None
    
    # Conteggi attuali
    brands_count: int = 0
    users_count: int = 0
    
    # Enterprise
    custom_limits: Optional[dict] = None
    notes: Optional[str] = None
    
    is_active: bool = True
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class OrganizationSaaSUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    vat_number: Optional[str] = None
    address: Optional[str] = None
    plan_id: Optional[int] = None
    subscription_status: Optional[str] = None
    trial_ends_at: Optional[datetime] = None
    subscription_starts_at: Optional[datetime] = None
    subscription_ends_at: Optional[datetime] = None
    custom_limits: Optional[dict] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class OrganizationCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    vat_number: Optional[str] = None
    address: Optional[str] = None
    plan_id: int
    custom_limits: Optional[dict] = None  # Per Enterprise
    notes: Optional[str] = None

# === USAGE ===

class UsageResponse(BaseModel):
    organization_id: int
    period_start: date
    period_end: date
    
    # Utilizzo corrente
    calendar_generations_used: int = 0
    text_tokens_used: int = 0
    images_generated: int = 0
    
    # Limiti
    calendar_generations_limit: int = 0
    text_tokens_limit: int = 0
    images_limit: int = 0
    
    # Percentuali
    calendar_percentage: float = 0
    tokens_percentage: float = 0
    images_percentage: float = 0
    
    # Overage
    overage_tokens: int = 0
    overage_images: int = 0
    overage_cost: Decimal = Decimal('0.00')
    
    class Config:
        from_attributes = True

class UsageSummary(BaseModel):
    """Riepilogo usage per dashboard"""
    calendars_used: int
    calendars_limit: int
    calendars_percentage: float
    tokens_used: int
    tokens_limit: int
    tokens_percentage: float
    images_used: int
    images_limit: int
    images_percentage: float
    days_remaining: int
    overage_cost: Decimal = Decimal('0.00')
