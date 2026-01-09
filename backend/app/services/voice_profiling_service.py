"""
Voice Profiling Service
Intervista vocale AI per profilazione brand e generazione piano editoriale
"""
import os
import json
import asyncio
import base64
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum
import websockets
import openai
import aiohttp


class InterviewState(Enum):
    IDLE = "idle"
    CONNECTING = "connecting"
    INTERVIEWING = "interviewing"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class BrandProfile:
    """Profilo brand estratto dall'intervista"""
    company_description: str = ""
    sector: str = ""
    target_audience: str = ""
    tone_of_voice: str = ""
    key_topics: List[str] = field(default_factory=list)
    avoid_topics: List[str] = field(default_factory=list)
    platforms: List[str] = field(default_factory=list)
    posts_per_week: int = 3
    content_pillars: List[str] = field(default_factory=list)
    brand_values: List[str] = field(default_factory=list)
    competitors: List[str] = field(default_factory=list)
    unique_selling_points: List[str] = field(default_factory=list)


class VoiceProfilingService:
    """
    Servizio per interviste vocali di profilazione brand.
    Usa OpenAI Realtime API per conversazione naturale.
    """
    
    OPENAI_REALTIME_URL = "wss://api.openai.com/v1/realtime"
    
    INTERVIEW_QUESTIONS = [
        {
            "id": "intro",
            "question": "Ciao! Sono qui per aiutarti a creare un piano editoriale perfetto per la tua azienda. Iniziamo: puoi descrivermi brevemente cosa fa la tua azienda e in che settore operate?",
            "extracts": ["company_description", "sector"]
        },
        {
            "id": "target",
            "question": "Interessante! E chi sono i vostri clienti ideali? A chi vi rivolgete principalmente?",
            "extracts": ["target_audience"]
        },
        {
            "id": "tone",
            "question": "Come vorresti che le persone percepissero il vostro brand sui social? Professionale, amichevole, innovativo, autorevole...?",
            "extracts": ["tone_of_voice", "brand_values"]
        },
        {
            "id": "topics",
            "question": "Quali sono gli argomenti principali di cui vorreste parlare? E ci sono temi che preferite evitare?",
            "extracts": ["key_topics", "avoid_topics", "content_pillars"]
        },
        {
            "id": "platforms",
            "question": "Su quali piattaforme social siete più attivi o vorreste esserlo? LinkedIn, Facebook, Instagram...?",
            "extracts": ["platforms"]
        },
        {
            "id": "frequency",
            "question": "Quanti post a settimana vorreste pubblicare? Pensate a quanto tempo potete dedicare ai contenuti.",
            "extracts": ["posts_per_week"]
        },
        {
            "id": "differentiators",
            "question": "Ultima domanda: cosa vi rende unici rispetto ai concorrenti? Qual è il vostro punto di forza?",
            "extracts": ["unique_selling_points", "competitors"]
        }
    ]
    
    def __init__(self, api_key: str, elevenlabs_key: str = None):
        self.api_key = api_key
        self.elevenlabs_key = elevenlabs_key
        self.state = InterviewState.IDLE
        self.ws = None
        
        self.brand_profile = BrandProfile()
        self.current_question_idx = 0
        self.conversation_history: List[Dict] = []
        
        self.brand_id: int = 0
        self.brand_name: str = ""
        
    def get_current_question(self) -> Optional[Dict]:
        if 0 <= self.current_question_idx < len(self.INTERVIEW_QUESTIONS):
            return self.INTERVIEW_QUESTIONS[self.current_question_idx]
        return None
    
    def get_progress(self) -> Dict:
        return {
            "state": self.state.value,
            "current_question": self.current_question_idx + 1,
            "total_questions": len(self.INTERVIEW_QUESTIONS),
            "percent_complete": round((self.current_question_idx / len(self.INTERVIEW_QUESTIONS)) * 100),
            "brand_name": self.brand_name
        }
    
    def get_system_prompt(self) -> str:
        current_q = self.get_current_question()
        questions_context = "\n".join([
            f"- {q['question']}" for q in self.INTERVIEW_QUESTIONS
        ])
        
        return f"""Sei un consulente di marketing esperto che sta conducendo un'intervista per creare un piano editoriale social media.

BRAND: {self.brand_name}
DOMANDA CORRENTE: {current_q['question'] if current_q else 'Intervista completata'}

STILE:
- Parla in italiano, tono professionale ma amichevole
- Risposte brevi e naturali (max 2-3 frasi)
- Fai una domanda alla volta
- Se la risposta è vaga, chiedi un chiarimento specifico
- Quando hai abbastanza info, passa alla domanda successiva

DOMANDE DA COPRIRE:
{questions_context}

IMPORTANTE:
- Non ripetere domande già fatte
- Adatta le domande in base alle risposte
- Quando hai tutte le info, concludi ringraziando

CONVERSAZIONE FINORA:
{json.dumps(self.conversation_history[-6:], ensure_ascii=False, indent=2) if self.conversation_history else 'Nessuna'}"""

    async def connect(self) -> bool:
        """Connette a OpenAI Realtime API"""
        try:
            self.state = InterviewState.CONNECTING
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "OpenAI-Beta": "realtime=v1"
            }
            
            self.ws = await websockets.connect(
                f"{self.OPENAI_REALTIME_URL}?model=gpt-4o-realtime-preview-2024-10-01",
                extra_headers=headers,
                ping_interval=30,
                ping_timeout=10
            )
            
            # Configura sessione
            await self._configure_session()
            
            self.state = InterviewState.INTERVIEWING
            return True
            
        except Exception as e:
            print(f"❌ Errore connessione OpenAI: {e}")
            self.state = InterviewState.ERROR
            return False
    
    async def _configure_session(self):
        """Configura la sessione OpenAI"""
        config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": self.get_system_prompt(),
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {"model": "whisper-1"},
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 800
                }
            }
        }
        await self.ws.send(json.dumps(config))
    
    async def start_interview(self) -> None:
        """Avvia l'intervista con la prima domanda"""
        if not self.ws:
            return
        
        first_question = self.INTERVIEW_QUESTIONS[0]["question"]
        
        await self.ws.send(json.dumps({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": f"Inizia l'intervista con questa domanda: {first_question}"}]
            }
        }))
        await self.ws.send(json.dumps({"type": "response.create"}))
    
    async def send_audio(self, audio_data: bytes) -> None:
        """Invia audio a OpenAI"""
        if not self.ws:
            return
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        await self.ws.send(json.dumps({
            "type": "input_audio_buffer.append",
            "audio": audio_base64
        }))
    
    async def commit_audio(self) -> None:
        """Commit del buffer audio"""
        if not self.ws:
            return
        await self.ws.send(json.dumps({"type": "input_audio_buffer.commit"}))
        await self.ws.send(json.dumps({"type": "response.create"}))
    
    async def send_text(self, text: str) -> None:
        """Invia testo come input"""
        if not self.ws:
            return
        
        self.conversation_history.append({"role": "user", "text": text})
        
        await self.ws.send(json.dumps({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": text}]
            }
        }))
        await self.ws.send(json.dumps({"type": "response.create"}))
    
    async def receive_events(self):
        """Generator per eventi da OpenAI"""
        if not self.ws:
            return
        try:
            async for message in self.ws:
                yield json.loads(message)
        except websockets.exceptions.ConnectionClosed:
            self.state = InterviewState.ERROR
            yield {"type": "error", "error": {"message": "Connessione chiusa"}}
    
    async def analyze_response(self, transcript: str) -> Dict:
        """Analizza la risposta e estrae info per il profilo brand"""
        current_q = self.get_current_question()
        if not current_q:
            return {"move_next": True, "extracted": {}}
        
        prompt = f"""Analizza questa risposta dell'utente riguardo alla profilazione del brand.

DOMANDA: {current_q['question']}
RISPOSTA: "{transcript}"

CAMPI DA ESTRARRE: {current_q['extracts']}

ISTRUZIONI:
1. Estrai le informazioni rilevanti dalla risposta
2. Se la risposta è completa, "move_next": true
3. Se servono chiarimenti, "move_next": false e suggerisci follow-up
4. Converti posts_per_week in numero intero

Rispondi SOLO con JSON valido:
{{
    "move_next": true/false,
    "extracted": {{
        "campo1": "valore",
        "campo2": ["lista", "valori"]
    }},
    "follow_up": "domanda di chiarimento se necessaria"
}}"""

        try:
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Sei un analista esperto. Rispondi SOLO con JSON valido."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"❌ Errore analisi: {e}")
            return {"move_next": True, "extracted": {}}
    
    def update_profile(self, extracted: Dict) -> None:
        """Aggiorna il profilo brand con i dati estratti"""
        for key, value in extracted.items():
            if hasattr(self.brand_profile, key):
                current = getattr(self.brand_profile, key)
                if isinstance(current, list) and isinstance(value, list):
                    setattr(self.brand_profile, key, current + value)
                elif isinstance(current, list) and isinstance(value, str):
                    current.append(value)
                else:
                    setattr(self.brand_profile, key, value)
    
    def advance_question(self) -> bool:
        """Passa alla domanda successiva. Ritorna False se finito."""
        self.current_question_idx += 1
        if self.current_question_idx >= len(self.INTERVIEW_QUESTIONS):
            self.state = InterviewState.COMPLETED
            return False
        return True
    
    def get_profile_dict(self) -> Dict:
        """Ritorna il profilo come dizionario"""
        return {
            "company_description": self.brand_profile.company_description,
            "sector": self.brand_profile.sector,
            "target_audience": self.brand_profile.target_audience,
            "tone_of_voice": self.brand_profile.tone_of_voice,
            "key_topics": self.brand_profile.key_topics,
            "avoid_topics": self.brand_profile.avoid_topics,
            "platforms": self.brand_profile.platforms,
            "posts_per_week": self.brand_profile.posts_per_week,
            "content_pillars": self.brand_profile.content_pillars,
            "brand_values": self.brand_profile.brand_values,
            "unique_selling_points": self.brand_profile.unique_selling_points
        }
    
    async def text_to_speech(self, text: str):
        """Genera audio con ElevenLabs (streaming)"""
        if not self.elevenlabs_key:
            return
        
        url = "https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB/stream"
        
        headers = {
            "xi-api-key": self.elevenlabs_key,
            "Content-Type": "application/json",
        }
        
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    async for chunk in response.content.iter_chunked(4096):
                        if chunk:
                            yield chunk
    
    async def disconnect(self) -> None:
        """Disconnette da OpenAI"""
        if self.ws:
            await self.ws.close()
            self.ws = None
        self.state = InterviewState.IDLE


def create_voice_profiling_service() -> VoiceProfilingService:
    api_key = os.getenv("OPENAI_API_KEY")
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY non configurata")
    return VoiceProfilingService(api_key, elevenlabs_key)
