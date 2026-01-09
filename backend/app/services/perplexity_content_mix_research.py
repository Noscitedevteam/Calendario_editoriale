"""
Perplexity Content Mix Research Service
Ricerca dinamica del mix ottimale di formati contenuto (post/story/reel)
basata su settore, piattaforma, buyer persona e obiettivi.
"""
import asyncio
import httpx
import json
import logging
from datetime import datetime
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

# Cache semplice in memoria
_content_mix_cache = {}
CACHE_DURATION_DAYS = 30


async def research_optimal_content_mix(
    business_type: str,  # "B2B" o "B2C"
    sector: str,  # es. "manifatturiero", "tech", "food", "fashion"
    platform: str,  # "instagram", "linkedin", "facebook", etc.
    buyer_persona: str,  # es. "manager 40-50 anni", "giovane imprenditore"
    country: str = "Italia",
    objective: str = "engagement"  # "engagement", "lead_generation", "brand_awareness"
) -> dict:
    """
    Ricerca con Perplexity il mix ottimale di formati contenuto per una piattaforma.
    """
    
    # Genera cache key
    cache_key = f"mix_{business_type}_{sector}_{platform}_{buyer_persona}_{country}_{objective}".lower().replace(" ", "_")
    
    # Controlla cache
    if cache_key in _content_mix_cache:
        cached = _content_mix_cache[cache_key]
        cached_date = datetime.fromisoformat(cached["last_updated"])
        if (datetime.now() - cached_date).days < CACHE_DURATION_DAYS:
            logger.info(f"[PERPLEXITY-MIX] Cache hit for {cache_key}")
            return cached
    
    if not settings.PERPLEXITY_API_KEY:
        logger.warning("[PERPLEXITY-MIX] API key not configured, using defaults")
        return _get_default_content_mix(platform)
    
    # Costruisci query per Perplexity
    query = f"""
Ricerca le statistiche e best practices più recenti ({datetime.now().year}) per la distribuzione ottimale dei formati di contenuto su {platform}.

Contesto:
- Tipo azienda: {business_type}
- Settore: {sector}
- Target/Buyer Persona: {buyer_persona}
- Paese: {country}
- Obiettivo principale: {objective}

Devo sapere:
1. Quale percentuale di POST classici (immagine + testo lungo) pubblicare settimanalmente
2. Quale percentuale di STORIES (contenuti effimeri 24h) pubblicare
3. Quale percentuale di REELS/video brevi pubblicare
4. Quanti contenuti totali a settimana sono raccomandati per questa piattaforma
5. Quali tipi di contenuto funzionano meglio per ogni formato nel settore {sector}

Rispondi SOLO con un JSON valido in questo formato esatto:
{{
    "platform": "{platform}",
    "supports_stories": true,
    "supports_reels": true,
    "recommended_weekly_total": 7,
    "format_mix": {{
        "post_percentage": 50,
        "story_percentage": 30,
        "reel_percentage": 20
    }},
    "format_weekly_count": {{
        "posts": 4,
        "stories": 2,
        "reels": 1
    }},
    "best_content_ideas": {{
        "posts": ["case study", "infografiche", "annunci"],
        "stories": ["behind the scenes", "sondaggi", "Q&A"],
        "reels": ["tutorial veloci", "trend", "tips"]
    }},
    "sector_specific_tips": "Consigli specifici per il settore",
    "confidence": "high",
    "sources_summary": "Breve riassunto delle fonti consultate"
}}

IMPORTANTE:
- Se la piattaforma NON supporta un formato, metti percentage a 0 e supports_* a false
- LinkedIn NON supporta stories né reels nativi
- Google Business NON supporta stories né reels
- TikTok è SOLO reels (100%)
- Le percentuali devono sommare a 100
- Rispondi SOLO con il JSON, niente altro testo
"""

    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
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
                                "content": "Sei un esperto di social media marketing e content strategy. Rispondi sempre e solo con JSON valido, senza markdown o altro testo. Basa le tue risposte su dati e statistiche recenti."
                            },
                            {
                                "role": "user", 
                                "content": query
                            }
                        ],
                        "temperature": 0.1
                    },
                    timeout=60
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
                    _content_mix_cache[cache_key] = result
                    
                    logger.info(f"[PERPLEXITY-MIX] Successfully researched content mix for {platform}/{sector}")
                    return result
                else:
                    logger.warning(f"[PERPLEXITY-MIX] API error (attempt {attempt+1}/{max_retries}): {response.status_code}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay * (attempt + 1))
                        continue
                    raise Exception(f"API error after {max_retries} attempts: {response.status_code}")
                        
        except json.JSONDecodeError as e:
            logger.warning(f"[PERPLEXITY-MIX] JSON parse error (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (attempt + 1))
                continue
            raise
        except httpx.TimeoutException as e:
            logger.warning(f"[PERPLEXITY-MIX] Timeout (attempt {attempt+1}/{max_retries})")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (attempt + 1))
                continue
            raise
        except Exception as e:
            logger.warning(f"[PERPLEXITY-MIX] Error (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (attempt + 1))
                continue
            raise
    
    # Se arriviamo qui dopo tutti i retry falliti, solleva eccezione
    raise Exception(f"[PERPLEXITY-MIX] All {max_retries} attempts failed for {platform}")


async def research_all_platforms_content_mix(
    business_type: str,
    sector: str,
    buyer_persona: str,
    platforms: list,
    country: str = "Italia",
    objective: str = "engagement"
) -> dict:
    """Ricerca mix contenuti per tutte le piattaforme specificate."""
    results = {}
    
    for platform in platforms:
        results[platform] = await research_optimal_content_mix(
            business_type=business_type,
            sector=sector,
            platform=platform,
            buyer_persona=buyer_persona,
            country=country,
            objective=objective
        )
    
    return results


def format_content_mix_for_prompt(content_mix_data: dict) -> str:
    """
    Formatta i dati del mix contenuti per includerli nel prompt di Claude.
    """
    if not content_mix_data:
        return "Nessuna ricerca disponibile - usa mix standard"
    
    lines = ["## MIX CONTENUTI RACCOMANDATO (basato su ricerca Perplexity)\n"]
    
    for platform, data in content_mix_data.items():
        platform_upper = platform.upper()
        
        if data.get("source") == "perplexity":
            confidence = data.get("confidence", "medium")
            lines.append(f"### {platform_upper} (confidence: {confidence})")
        else:
            lines.append(f"### {platform_upper} (default)")
        
        # Supporto formati
        supports_stories = data.get("supports_stories", False)
        supports_reels = data.get("supports_reels", False)
        
        # Mix percentuali
        mix = data.get("format_mix", {})
        weekly = data.get("format_weekly_count", {})
        total = data.get("recommended_weekly_total", 5)
        
        lines.append(f"- Contenuti settimanali totali: {total}")
        lines.append(f"- POST: {mix.get('post_percentage', 100)}% ({weekly.get('posts', total)} a settimana)")
        
        if supports_stories:
            lines.append(f"- STORIES: {mix.get('story_percentage', 0)}% ({weekly.get('stories', 0)} a settimana)")
        else:
            lines.append(f"- STORIES: Non supportate su {platform}")
        
        if supports_reels:
            lines.append(f"- REELS: {mix.get('reel_percentage', 0)}% ({weekly.get('reels', 0)} a settimana)")
        else:
            lines.append(f"- REELS: Non supportati su {platform}")
        
        # Idee contenuto
        ideas = data.get("best_content_ideas", {})
        if ideas.get("posts"):
            lines.append(f"- Idee POST: {', '.join(ideas['posts'][:3])}")
        if ideas.get("stories") and supports_stories:
            lines.append(f"- Idee STORIES: {', '.join(ideas['stories'][:3])}")
        if ideas.get("reels") and supports_reels:
            lines.append(f"- Idee REELS: {', '.join(ideas['reels'][:3])}")
        
        # Tips settoriali
        tips = data.get("sector_specific_tips")
        if tips:
            lines.append(f"- Tips settore: {tips[:200]}")
        
        lines.append("")
    
    return "\n".join(lines)


def _get_default_content_mix(platform: str) -> dict:
    """Mix contenuti di fallback se Perplexity non è disponibile"""
    
    defaults = {
        "instagram": {
            "platform": "instagram",
            "supports_stories": True,
            "supports_reels": True,
            "recommended_weekly_total": 7,
            "format_mix": {
                "post_percentage": 45,
                "story_percentage": 35,
                "reel_percentage": 20
            },
            "format_weekly_count": {
                "posts": 3,
                "stories": 3,
                "reels": 1
            },
            "best_content_ideas": {
                "posts": ["educational", "case study", "infografiche"],
                "stories": ["behind the scenes", "sondaggi", "daily updates"],
                "reels": ["tips veloci", "tutorial", "trend"]
            },
            "confidence": "medium",
            "sector_specific_tips": "Instagram premia la costanza e la varietà di formati"
        },
        "linkedin": {
            "platform": "linkedin",
            "supports_stories": False,
            "supports_reels": False,
            "recommended_weekly_total": 4,
            "format_mix": {
                "post_percentage": 100,
                "story_percentage": 0,
                "reel_percentage": 0
            },
            "format_weekly_count": {
                "posts": 4,
                "stories": 0,
                "reels": 0
            },
            "best_content_ideas": {
                "posts": ["thought leadership", "industry insights", "case study", "team updates"],
                "stories": [],
                "reels": []
            },
            "confidence": "high",
            "sector_specific_tips": "LinkedIn preferisce contenuti professionali, articoli e carousel"
        },
        "facebook": {
            "platform": "facebook",
            "supports_stories": True,
            "supports_reels": True,
            "recommended_weekly_total": 5,
            "format_mix": {
                "post_percentage": 60,
                "story_percentage": 20,
                "reel_percentage": 20
            },
            "format_weekly_count": {
                "posts": 3,
                "stories": 1,
                "reels": 1
            },
            "best_content_ideas": {
                "posts": ["engagement posts", "eventi", "promozioni"],
                "stories": ["countdown", "behind the scenes"],
                "reels": ["video informativi", "trend"]
            },
            "confidence": "medium",
            "sector_specific_tips": "Facebook favorisce i video e i contenuti che generano discussione"
        },
        "tiktok": {
            "platform": "tiktok",
            "supports_stories": False,
            "supports_reels": True,
            "recommended_weekly_total": 5,
            "format_mix": {
                "post_percentage": 0,
                "story_percentage": 0,
                "reel_percentage": 100
            },
            "format_weekly_count": {
                "posts": 0,
                "stories": 0,
                "reels": 5
            },
            "best_content_ideas": {
                "posts": [],
                "stories": [],
                "reels": ["trend", "tutorial", "POV", "duetti", "challenges"]
            },
            "confidence": "high",
            "sector_specific_tips": "TikTok premia autenticità e trend attuali"
        },
        "google_business": {
            "platform": "google_business",
            "supports_stories": False,
            "supports_reels": False,
            "recommended_weekly_total": 2,
            "format_mix": {
                "post_percentage": 100,
                "story_percentage": 0,
                "reel_percentage": 0
            },
            "format_weekly_count": {
                "posts": 2,
                "stories": 0,
                "reels": 0
            },
            "best_content_ideas": {
                "posts": ["offerte", "novità", "eventi", "prodotti"],
                "stories": [],
                "reels": []
            },
            "confidence": "high",
            "sector_specific_tips": "Google Business serve per SEO locale e informazioni pratiche"
        }
    }
    
    default = defaults.get(platform.lower(), {
        "platform": platform,
        "supports_stories": False,
        "supports_reels": False,
        "recommended_weekly_total": 3,
        "format_mix": {
            "post_percentage": 100,
            "story_percentage": 0,
            "reel_percentage": 0
        },
        "format_weekly_count": {
            "posts": 3,
            "stories": 0,
            "reels": 0
        },
        "best_content_ideas": {
            "posts": ["contenuti generici"],
            "stories": [],
            "reels": []
        },
        "confidence": "low",
        "sector_specific_tips": "Default generico"
    })
    
    default["source"] = "default_fallback"
    default["last_updated"] = datetime.now().isoformat()
    
    return default


def clear_cache():
    """Svuota la cache dei mix"""
    global _content_mix_cache
    _content_mix_cache = {}
    logger.info("[PERPLEXITY-MIX] Cache cleared")


def get_cache_stats() -> dict:
    """Statistiche sulla cache"""
    return {
        "entries": len(_content_mix_cache),
        "keys": list(_content_mix_cache.keys())
    }
