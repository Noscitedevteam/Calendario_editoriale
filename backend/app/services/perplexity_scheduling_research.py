"""
Perplexity Scheduling Research Service
Ricerca dinamica degli orari migliori per pubblicazione social
basata su tipo azienda, canale, buyer persona, settore e paese.
"""
import httpx
import json
import logging
from datetime import datetime
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# Cache semplice in memoria (in produzione usa Redis)
_scheduling_cache = {}
CACHE_DURATION_DAYS = 30


async def research_optimal_schedule(
    business_type: str,  # "B2B" o "B2C"
    sector: str,  # es. "tech", "food", "fashion", "consulenza"
    platform: str,  # "instagram", "linkedin", "facebook", etc.
    buyer_persona: str,  # es. "manager 40-50 anni", "studente universitario"
    country: str = "Italia",
    objective: str = "engagement"  # "engagement", "lead_generation", "brand_awareness"
) -> dict:
    """
    Ricerca con Perplexity gli orari migliori per pubblicare.
    """
    
    # Genera cache key
    cache_key = f"{business_type}_{sector}_{platform}_{buyer_persona}_{country}_{objective}".lower().replace(" ", "_")
    
    # Controlla cache
    if cache_key in _scheduling_cache:
        cached = _scheduling_cache[cache_key]
        cached_date = datetime.fromisoformat(cached["last_updated"])
        if (datetime.now() - cached_date).days < CACHE_DURATION_DAYS:
            logger.info(f"[PERPLEXITY] Cache hit for {cache_key}")
            return cached
    
    if not settings.PERPLEXITY_API_KEY:
        logger.warning("[PERPLEXITY] API key not configured, using defaults")
        return _get_default_schedule(platform)
    
    # Costruisci query per Perplexity
    query = f"""
Ricerca gli orari migliori per pubblicare su {platform} nel {datetime.now().year} per:

- Tipo azienda: {business_type}
- Settore: {sector}
- Target/Buyer Persona: {buyer_persona}
- Paese: {country}
- Obiettivo: {objective}

Basati su studi recenti, statistiche e best practices aggiornate.

Rispondi SOLO con un JSON valido in questo formato esatto:
{{
    "best_days": ["martedì", "giovedì"],
    "best_days_numbers": [1, 3],
    "best_times": ["08:30", "12:30"],
    "avoid_days": ["domenica"],
    "avoid_times": ["dopo le 22:00"],
    "confidence": "high",
    "notes": "Spiegazione breve del perché questi orari"
}}

IMPORTANTE: 
- best_days_numbers usa 0=lunedì, 1=martedì, ..., 6=domenica
- best_times in formato HH:MM
- confidence può essere "high", "medium", "low"
- Rispondi SOLO con il JSON, niente altro testo
"""

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "sonar",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Sei un esperto di social media marketing. Rispondi sempre e solo con JSON valido, senza markdown o altro testo."
                        },
                        {
                            "role": "user", 
                            "content": query
                        }
                    ],
                    "temperature": 0.1
                },
                timeout=45
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data['choices'][0]['message']['content']
                
                # Pulisci eventuale markdown
                content = content.strip()
                if content.startswith("```"):
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                content = content.strip()
                
                result = json.loads(content)
                
                # Aggiungi metadata
                result["source"] = "perplexity"
                result["last_updated"] = datetime.now().isoformat()
                result["query_params"] = {
                    "business_type": business_type,
                    "sector": sector,
                    "platform": platform,
                    "buyer_persona": buyer_persona,
                    "country": country,
                    "objective": objective
                }
                
                # Salva in cache
                _scheduling_cache[cache_key] = result
                
                logger.info(f"[PERPLEXITY] Successfully researched schedule for {platform}/{business_type}/{sector}")
                return result
            else:
                logger.error(f"[PERPLEXITY] API error: {response.status_code} - {response.text}")
                return _get_default_schedule(platform)
                
    except json.JSONDecodeError as e:
        logger.error(f"[PERPLEXITY] JSON parse error: {e}")
        return _get_default_schedule(platform)
    except Exception as e:
        logger.error(f"[PERPLEXITY] Error: {e}")
        return _get_default_schedule(platform)


async def research_all_platforms_schedule(
    business_type: str,
    sector: str,
    buyer_persona: str,
    platforms: list,
    country: str = "Italia",
    objective: str = "engagement"
) -> dict:
    """Ricerca orari per tutte le piattaforme specificate."""
    results = {}
    
    for platform in platforms:
        results[platform] = await research_optimal_schedule(
            business_type=business_type,
            sector=sector,
            platform=platform,
            buyer_persona=buyer_persona,
            country=country,
            objective=objective
        )
    
    return results


def _get_default_schedule(platform: str) -> dict:
    """Schedule di fallback se Perplexity non è disponibile"""
    
    defaults = {
        "instagram": {
            "best_days": ["martedì", "giovedì", "sabato"],
            "best_days_numbers": [1, 3, 5],
            "best_times": ["12:00", "19:00", "21:00"],
            "avoid_days": ["lunedì mattina"],
            "avoid_times": ["03:00-06:00"],
            "confidence": "medium",
            "notes": "Default basato su statistiche generali Italia"
        },
        "linkedin": {
            "best_days": ["martedì", "mercoledì", "giovedì"],
            "best_days_numbers": [1, 2, 3],
            "best_times": ["07:30", "08:30", "12:30"],
            "avoid_days": ["weekend"],
            "avoid_times": ["sera", "notte"],
            "confidence": "medium",
            "notes": "Default B2B Italia"
        },
        "facebook": {
            "best_days": ["mercoledì", "venerdì", "sabato"],
            "best_days_numbers": [2, 4, 5],
            "best_times": ["13:00", "16:00", "20:00"],
            "avoid_days": ["lunedì"],
            "avoid_times": ["mattina presto"],
            "confidence": "medium",
            "notes": "Default engagement Italia"
        },
        "google_business": {
            "best_days": ["lunedì", "giovedì"],
            "best_days_numbers": [0, 3],
            "best_times": ["10:00", "14:00"],
            "avoid_days": ["domenica"],
            "avoid_times": ["sera"],
            "confidence": "medium",
            "notes": "Default local business"
        },
        "twitter": {
            "best_days": ["martedì", "mercoledì", "giovedì"],
            "best_days_numbers": [1, 2, 3],
            "best_times": ["08:00", "12:00", "17:00"],
            "avoid_days": ["weekend"],
            "avoid_times": ["notte"],
            "confidence": "medium",
            "notes": "Default engagement"
        }
    }
    
    default = defaults.get(platform.lower(), {
        "best_days": ["martedì", "giovedì"],
        "best_days_numbers": [1, 3],
        "best_times": ["10:00", "14:00"],
        "avoid_days": [],
        "avoid_times": [],
        "confidence": "low",
        "notes": "Default generico"
    })
    
    default["source"] = "default_fallback"
    default["last_updated"] = datetime.now().isoformat()
    
    return default


def clear_cache():
    """Svuota la cache degli schedule"""
    global _scheduling_cache
    _scheduling_cache = {}
    logger.info("[PERPLEXITY] Cache cleared")


def get_cache_stats() -> dict:
    """Statistiche sulla cache"""
    return {
        "entries": len(_scheduling_cache),
        "keys": list(_scheduling_cache.keys())
    }
