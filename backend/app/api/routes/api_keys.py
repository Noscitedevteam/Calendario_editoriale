"""Gestione API Keys per l'utente autenticato (via JWT dal frontend)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.api_key_auth import generate_api_key, hash_api_key
from app.models.user import User
from app.models.api_key import ApiKey

router = APIRouter()

class ApiKeyCreateInput(BaseModel):
    name: str
    scopes: List[str] = ["read", "write"]
    expires_in_days: Optional[int] = None  # None = non scade

class ApiKeyOut(BaseModel):
    id: int
    name: str
    key_prefix: str
    scopes: list
    is_active: bool
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class ApiKeyCreatedOut(ApiKeyOut):
    raw_key: str  # mostrata SOLO alla creazione

@router.get("/", response_model=List[ApiKeyOut])
def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista le API keys dell'utente."""
    return db.query(ApiKey).filter(
        ApiKey.user_id == current_user.id,
        ApiKey.is_active == True
    ).all()

@router.post("/", response_model=ApiKeyCreatedOut)
def create_api_key(
    data: ApiKeyCreateInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crea una nuova API key. 
    ATTENZIONE: la chiave completa viene mostrata SOLO in questa risposta.
    """
    valid_scopes = {"read", "write", "publish", "admin"}
    for s in data.scopes:
        if s not in valid_scopes:
            raise HTTPException(status_code=400, detail=f"Scope non valido: {s}. Validi: {valid_scopes}")
    
    raw_key, key_hash, key_prefix = generate_api_key()
    
    expires_at = None
    if data.expires_in_days:
        from datetime import timedelta
        expires_at = datetime.now(timezone.utc) + timedelta(days=data.expires_in_days)
    
    ak = ApiKey(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        name=data.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        scopes=data.scopes,
        expires_at=expires_at
    )
    db.add(ak)
    db.commit()
    db.refresh(ak)
    
    return ApiKeyCreatedOut(
        id=ak.id,
        name=ak.name,
        key_prefix=ak.key_prefix,
        scopes=ak.scopes,
        is_active=ak.is_active,
        last_used_at=ak.last_used_at,
        expires_at=ak.expires_at,
        created_at=ak.created_at,
        raw_key=raw_key
    )

@router.delete("/{key_id}")
def revoke_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Revoca (disattiva) una API key."""
    ak = db.query(ApiKey).filter(
        ApiKey.id == key_id,
        ApiKey.user_id == current_user.id
    ).first()
    if not ak:
        raise HTTPException(status_code=404, detail="API Key non trovata")
    
    ak.is_active = False
    db.commit()
    return {"success": True, "message": f"API Key '{ak.name}' revocata"}
