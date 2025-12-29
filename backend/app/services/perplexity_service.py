import httpx
from app.core.config import settings

async def search_trends(sector: str, brand_name: str = "") -> str:
    """Cerca trend del settore con Perplexity"""
    
    if not settings.PERPLEXITY_API_KEY:
        return ""
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-sonar-large-128k-online",
                "messages": [{
                    "role": "user",
                    "content": f"Quali sono i trend attuali nel settore {sector}? Focus su temi per content marketing B2B. Rispondi in italiano, max 500 parole."
                }]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
    
    return ""

async def fetch_url_content(url: str) -> str:
    """Estrae contenuto da URL"""
    
    if not settings.PERPLEXITY_API_KEY:
        return ""
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-sonar-large-128k-online",
                "messages": [{
                    "role": "user",
                    "content": f"Analizza questa pagina e estrai i contenuti principali, tone of voice e messaggi chiave: {url}. Rispondi in italiano."
                }]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
    
    return ""

async def analyze_competitor(url: str) -> str:
    """Analizza competitor"""
    
    if not settings.PERPLEXITY_API_KEY:
        return ""
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-sonar-large-128k-online",
                "messages": [{
                    "role": "user",
                    "content": f"Analizza la strategia social/content di questo competitor: {url}. Identifica: temi principali, frequenza, tone of voice, punti di forza. In italiano."
                }]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
    
    return ""
