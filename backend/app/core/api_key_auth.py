import hashlib
import secrets
from datetime import datetime, timezone
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.api_key import ApiKey
from app.models.user import User

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()

def generate_api_key() -> tuple[str, str, str]:
    """Genera API key. Ritorna (raw_key, key_hash, key_prefix)"""
    raw_key = f"nsc_{secrets.token_urlsafe(32)}"
    key_hash = hash_api_key(raw_key)
    key_prefix = raw_key[:12]
    return raw_key, key_hash, key_prefix

def get_api_key_user(
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
) -> tuple[User, ApiKey]:
    """Autentica via API Key e ritorna (user, api_key_record)"""
    if not api_key:
        raise HTTPException(status_code=401, detail="API Key richiesta. Usa header X-API-Key")
    
    key_hash = hash_api_key(api_key)
    ak = db.query(ApiKey).filter(
        ApiKey.key_hash == key_hash,
        ApiKey.is_active == True
    ).first()
    
    if not ak:
        raise HTTPException(status_code=401, detail="API Key non valida")
    
    # Controlla scadenza
    if ak.expires_at and ak.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="API Key scaduta")
    
    # Aggiorna last_used
    ak.last_used_at = datetime.now(timezone.utc)
    db.commit()
    
    user = db.query(User).filter(User.id == ak.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Utente associato non trovato")
    
    return user, ak

def require_scope(required_scope: str):
    """Dependency factory per verificare scope"""
    def checker(auth: tuple = Depends(get_api_key_user)):
        user, ak = auth
        if "admin" in (ak.scopes or []):
            return user  # admin ha accesso a tutto
        if required_scope not in (ak.scopes or []):
            raise HTTPException(
                status_code=403, 
                detail=f"Scope '{required_scope}' richiesto. La tua API key ha: {ak.scopes}"
            )
        return user
    return checker
