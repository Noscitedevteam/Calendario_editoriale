from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
import httpx
import secrets

router = APIRouter()

# Placeholder per test - restituisce una pagina di conferma
@router.get("/facebook/callback")
async def facebook_callback(
    code: str = None,
    state: str = None,
    error: str = None,
    error_description: str = None
):
    """Callback OAuth Facebook - placeholder per validazione Meta"""
    
    if error:
        return HTMLResponse(f"""
        <html>
        <head><title>Errore OAuth</title></head>
        <body>
            <h1>Errore di autorizzazione</h1>
            <p>{error}: {error_description}</p>
            <a href="https://calendar.noscite.it">Torna alla home</a>
        </body>
        </html>
        """)
    
    # Per ora restituisce una pagina di conferma
    return HTMLResponse(f"""
    <html>
    <head><title>OAuth Callback</title></head>
    <body>
        <h1>✅ Callback OAuth ricevuto</h1>
        <p>Code: {code[:20] if code else 'N/A'}...</p>
        <p>State: {state or 'N/A'}</p>
        <p>Questa pagina conferma che l'endpoint OAuth è attivo.</p>
        <a href="https://calendar.noscite.it">Torna alla home</a>
    </body>
    </html>
    """)

@router.get("/instagram/callback")
async def instagram_callback(
    code: str = None,
    state: str = None,
    error: str = None
):
    """Callback OAuth Instagram"""
    return await facebook_callback(code, state, error, None)

@router.get("/linkedin/callback")
async def linkedin_callback(
    code: str = None,
    state: str = None,
    error: str = None
):
    """Callback OAuth LinkedIn - placeholder"""
    if error:
        return HTMLResponse(f"<h1>Errore: {error}</h1>")
    
    return HTMLResponse(f"""
    <html>
    <head><title>LinkedIn OAuth</title></head>
    <body>
        <h1>✅ LinkedIn Callback ricevuto</h1>
        <p>Code: {code[:20] if code else 'N/A'}...</p>
        <a href="https://calendar.noscite.it">Torna alla home</a>
    </body>
    </html>
    """)

@router.get("/google/callback")
async def google_callback(
    code: str = None,
    state: str = None,
    error: str = None
):
    """Callback OAuth Google Business - placeholder"""
    if error:
        return HTMLResponse(f"<h1>Errore: {error}</h1>")
    
    return HTMLResponse(f"""
    <html>
    <head><title>Google OAuth</title></head>
    <body>
        <h1>✅ Google Callback ricevuto</h1>
        <p>Code: {code[:20] if code else 'N/A'}...</p>
        <a href="https://calendar.noscite.it">Torna alla home</a>
    </body>
    </html>
    """)
