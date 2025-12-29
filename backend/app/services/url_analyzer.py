"""
URL Analyzer Service
Scarica e analizza contenuti da URL per estrarre brand context
"""
import httpx
from bs4 import BeautifulSoup
from anthropic import Anthropic
from app.core.config import settings
import re
import json
from typing import List, Optional
from urllib.parse import urlparse

client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

# User agent per evitare blocchi
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def fetch_url_content(url: str, max_chars: int = 15000) -> Optional[str]:
    """Scarica il contenuto testuale da un URL"""
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers=HEADERS)
            response.raise_for_status()
            
            content_type = response.headers.get("content-type", "")
            
            # Se è un PDF, estrai testo base
            if "pdf" in content_type.lower():
                return f"[PDF Document from {url}]"
            
            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Rimuovi script, style, nav, footer
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
                tag.decompose()
            
            # Estrai testo
            text = soup.get_text(separator="\n", strip=True)
            
            # Pulisci spazi multipli
            text = re.sub(r'\n\s*\n', '\n\n', text)
            text = re.sub(r' +', ' ', text)
            
            # Limita lunghezza
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            
            return text
            
    except Exception as e:
        print(f"[URL_ANALYZER] Error fetching {url}: {e}")
        return None


async def fetch_multiple_urls(urls: List[str]) -> str:
    """Scarica contenuti da multiple URL e li combina"""
    contents = []
    
    for url in urls[:5]:  # Max 5 URL per evitare timeout
        content = await fetch_url_content(url)
        if content:
            domain = urlparse(url).netloc
            contents.append(f"--- FONTE: {domain} ---\n{content}\n")
    
    return "\n\n".join(contents)


def analyze_brand_from_content(content: str, brand_name: str = "") -> dict:
    """Usa Claude per analizzare il contenuto e estrarre brand profile"""
    
    if not content or len(content) < 100:
        return {}
    
    prompt = f"""Analizza questo contenuto e estrai un profilo brand dettagliato.

CONTENUTO DA ANALIZZARE:
{content[:20000]}

ISTRUZIONI:
Estrai e sintetizza le seguenti informazioni dal contenuto:

1. BRAND VOICE: Come comunica il brand? (formale/informale, tecnico/accessibile, etc.)
2. VALORI CHIAVE: Quali sono i valori fondamentali espressi?
3. TEMI PRINCIPALI: Quali argomenti/temi tratta principalmente?
4. TARGET AUDIENCE: A chi si rivolge?
5. MESSAGGI CHIAVE: Quali sono i messaggi/concetti ricorrenti?
6. STILE CONTENUTI: Come sono strutturati i contenuti? Che formato usano?
7. PAROLE CHIAVE: Termini e espressioni distintive del brand
8. TONO: Qual è il tono emotivo? (ispiratore, educativo, provocatorio, etc.)

Rispondi SOLO con un JSON valido:
{{
    "brand_voice": "descrizione dello stile comunicativo",
    "core_values": ["valore1", "valore2", "valore3"],
    "main_themes": ["tema1", "tema2", "tema3"],
    "target_audience": "descrizione del target",
    "key_messages": ["messaggio1", "messaggio2"],
    "content_style": "descrizione dello stile contenuti",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "tone": "descrizione del tono",
    "summary": "breve sintesi del brand in 2-3 frasi"
}}
"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text
        
        # Parse JSON
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            return json.loads(json_match.group())
            
    except Exception as e:
        print(f"[URL_ANALYZER] Analysis error: {e}")
    
    return {}


def create_brand_context_prompt(analysis: dict, brand_name: str = "") -> str:
    """Crea un prompt contestuale dal brand analysis per la generazione contenuti"""
    
    if not analysis:
        return ""
    
    context = f"""
=== PROFILO BRAND ESTRATTO DAI CONTENUTI DI RIFERIMENTO ===

BRAND: {brand_name}

VOICE & TONE:
{analysis.get('brand_voice', 'Non specificato')}
Tono: {analysis.get('tone', 'Non specificato')}

VALORI FONDAMENTALI:
{', '.join(analysis.get('core_values', []))}

TEMI PRINCIPALI DA TRATTARE:
{', '.join(analysis.get('main_themes', []))}

TARGET AUDIENCE:
{analysis.get('target_audience', 'Non specificato')}

MESSAGGI CHIAVE DA VEICOLARE:
{chr(10).join('- ' + m for m in analysis.get('key_messages', []))}

STILE DEI CONTENUTI:
{analysis.get('content_style', 'Non specificato')}

PAROLE CHIAVE E ESPRESSIONI DEL BRAND:
{', '.join(analysis.get('keywords', []))}

SINTESI:
{analysis.get('summary', '')}

=== ISTRUZIONI ===
Genera contenuti che rispecchino fedelmente questo profilo brand.
Usa lo stesso tono, le stesse espressioni e mantieni coerenza con i valori espressi.
"""
    
    return context


async def get_brand_context_from_urls(urls: List[str], brand_name: str = "") -> str:
    """Pipeline completa: scarica URL, analizza, genera context"""
    
    if not urls:
        return ""
    
    print(f"[URL_ANALYZER] Fetching {len(urls)} URLs...")
    
    # Scarica contenuti
    content = await fetch_multiple_urls(urls)
    
    if not content:
        print("[URL_ANALYZER] No content fetched")
        return ""
    
    print(f"[URL_ANALYZER] Fetched {len(content)} chars, analyzing...")
    
    # Analizza con Claude
    analysis = analyze_brand_from_content(content, brand_name)
    
    if not analysis:
        print("[URL_ANALYZER] Analysis failed")
        return ""
    
    print(f"[URL_ANALYZER] Analysis complete: {list(analysis.keys())}")
    
    # Genera context prompt
    context = create_brand_context_prompt(analysis, brand_name)
    
    return context
