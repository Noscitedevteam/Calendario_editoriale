"""
Voice Profiling Router
WebSocket endpoint per interviste vocali di profilazione brand
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
import json
import asyncio
import base64
import os
import logging

from app.core.database import get_db
from app.models.brand import Brand
from app.services.voice_profiling_service import (
    VoiceProfilingService,
    InterviewState,
    create_voice_profiling_service
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice-profiling", tags=["voice-profiling"])

# Store sessioni attive
active_sessions: dict[int, VoiceProfilingService] = {}


async def safe_send(websocket: WebSocket, data: dict) -> bool:
    """Invia solo se WebSocket è aperto"""
    try:
        await websocket.send_json(data)
        return True
    except Exception:
        return False


@router.get("/check")
async def check_service():
    """Health check"""
    return {
        "status": "ok",
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "elevenlabs_configured": bool(os.getenv("ELEVENLABS_API_KEY")),
        "active_sessions": len(active_sessions)
    }


@router.post("/brand/{brand_id}/init")
async def init_profiling(brand_id: int, db: Session = Depends(get_db)):
    """Inizializza sessione di profilazione per un brand"""
    
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand non trovato")
    
    try:
        service = create_voice_profiling_service()
        service.brand_id = brand_id
        service.brand_name = brand.name
        
        active_sessions[brand_id] = service
        
        return {
            "status": "ready",
            "brand_id": brand_id,
            "brand_name": brand.name,
            "total_questions": len(service.INTERVIEW_QUESTIONS),
            "websocket_path": f"/api/voice-profiling/ws/{brand_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/{brand_id}")
async def websocket_profiling(websocket: WebSocket, brand_id: int):
    """
    WebSocket per intervista vocale di profilazione.
    
    MESSAGGI CLIENT -> SERVER:
    - {"type": "start"} - Avvia intervista
    - {"type": "audio", "data": "base64..."} - Audio dal microfono
    - {"type": "audio_end"} - Fine parlato
    - {"type": "text", "text": "..."} - Input testuale
    - {"type": "skip"} - Salta domanda corrente
    - {"type": "end"} - Termina intervista
    
    MESSAGGI SERVER -> CLIENT:
    - {"type": "connected", "progress": {...}}
    - {"type": "audio", "data": "base64..."} - Audio risposta
    - {"type": "audio_done"}
    - {"type": "transcript", "role": "user|assistant", "text": "..."}
    - {"type": "progress", "data": {...}}
    - {"type": "profile_updated", "field": "...", "value": "..."}
    - {"type": "completed", "profile": {...}}
    - {"type": "error", "message": "..."}
    """
    
    await websocket.accept()
    
    service = active_sessions.get(brand_id)
    if not service:
        await safe_send(websocket, {
            "type": "error",
            "message": "Sessione non inizializzata. Chiama POST /init prima."
        })
        await websocket.close()
        return
    
    try:
        # Connetti a OpenAI
        connected = await service.connect()
        if not connected:
            await safe_send(websocket, {
                "type": "error",
                "message": "Impossibile connettersi a OpenAI"
            })
            await websocket.close()
            return
        
        await safe_send(websocket, {
            "type": "connected",
            "progress": service.get_progress()
        })
        
        # Task per ricevere eventi da OpenAI
        async def handle_openai_events():
            current_response_text = ""
            
            async for event in service.receive_events():
                event_type = event.get("type", "")
                
                if event_type == "response.audio.delta":
                    # Audio in streaming
                    audio_b64 = event.get("delta", "")
                    if audio_b64:
                        await safe_send(websocket, {
                            "type": "audio",
                            "data": audio_b64
                        })
                
                elif event_type == "response.audio.done":
                    await safe_send(websocket, {"type": "audio_done"})
                
                elif event_type == "response.audio_transcript.delta":
                    # Trascrizione risposta AI
                    current_response_text += event.get("delta", "")
                
                elif event_type == "response.audio_transcript.done":
                    # Risposta AI completata
                    full_text = event.get("transcript", current_response_text)
                    current_response_text = ""
                    
                    service.conversation_history.append({
                        "role": "assistant",
                        "text": full_text
                    })
                    
                    await safe_send(websocket, {
                        "type": "transcript",
                        "role": "assistant",
                        "text": full_text
                    })
                
                elif event_type == "conversation.item.input_audio_transcription.completed":
                    # Trascrizione input utente
                    user_text = event.get("transcript", "")
                    if user_text:
                        service.conversation_history.append({
                            "role": "user",
                            "text": user_text
                        })
                        
                        await safe_send(websocket, {
                            "type": "transcript",
                            "role": "user",
                            "text": user_text
                        })
                        
                        # Analizza risposta
                        analysis = await service.analyze_response(user_text)
                        
                        if analysis.get("extracted"):
                            service.update_profile(analysis["extracted"])
                            await safe_send(websocket, {
                                "type": "profile_updated",
                                "extracted": analysis["extracted"]
                            })
                        
                        if analysis.get("move_next"):
                            if not service.advance_question():
                                # Intervista completata
                                await safe_send(websocket, {
                                    "type": "completed",
                                    "profile": service.get_profile_dict()
                                })
                                return
                        
                        await safe_send(websocket, {
                            "type": "progress",
                            "data": service.get_progress()
                        })
                
                elif event_type == "error":
                    error_msg = event.get("error", {}).get("message", "Errore sconosciuto")
                    await safe_send(websocket, {
                        "type": "error",
                        "message": error_msg
                    })
        
        # Task per ricevere messaggi dal client
        async def handle_client_messages():
            try:
                while True:
                    data = await websocket.receive_json()
                    msg_type = data.get("type")
                    
                    if msg_type == "start":
                        await service.start_interview()
                    
                    elif msg_type == "audio":
                        audio_b64 = data.get("data", "")
                        if audio_b64:
                            audio_bytes = base64.b64decode(audio_b64)
                            await service.send_audio(audio_bytes)
                    
                    elif msg_type == "audio_end":
                        await service.commit_audio()
                    
                    elif msg_type == "text":
                        text = data.get("text", "")
                        if text:
                            await service.send_text(text)
                            await safe_send(websocket, {
                                "type": "transcript",
                                "role": "user",
                                "text": text
                            })
                    
                    elif msg_type == "skip":
                        if not service.advance_question():
                            await safe_send(websocket, {
                                "type": "completed",
                                "profile": service.get_profile_dict()
                            })
                            return
                        await safe_send(websocket, {
                            "type": "progress",
                            "data": service.get_progress()
                        })
                        # Chiedi prossima domanda
                        next_q = service.get_current_question()
                        if next_q:
                            await service.send_text(f"Passa alla prossima domanda: {next_q['question']}")
                    
                    elif msg_type == "end":
                        await safe_send(websocket, {
                            "type": "completed",
                            "profile": service.get_profile_dict()
                        })
                        return
                        
            except WebSocketDisconnect:
                pass
        
        # Esegui entrambi i task
        await asyncio.gather(
            handle_openai_events(),
            handle_client_messages(),
            return_exceptions=True
        )
        
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await safe_send(websocket, {
            "type": "error",
            "message": str(e)
        })
    finally:
        await service.disconnect()
        active_sessions.pop(brand_id, None)


@router.get("/brand/{brand_id}/profile")
async def get_profile(brand_id: int):
    """Ottiene il profilo estratto dall'intervista"""
    service = active_sessions.get(brand_id)
    if not service:
        raise HTTPException(status_code=404, detail="Nessuna sessione attiva")
    
    return {
        "brand_id": brand_id,
        "brand_name": service.brand_name,
        "state": service.state.value,
        "profile": service.get_profile_dict(),
        "progress": service.get_progress()
    }


@router.post("/brand/{brand_id}/save")
async def save_profile(brand_id: int, db: Session = Depends(get_db)):
    """Salva il profilo nel brand"""
    service = active_sessions.get(brand_id)
    if not service:
        raise HTTPException(status_code=404, detail="Nessuna sessione attiva")
    
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand non trovato")
    
    profile = service.get_profile_dict()
    
    # Aggiorna brand con info estratte
    if profile.get("company_description"):
        brand.description = profile["company_description"]
    if profile.get("sector"):
        brand.sector = profile["sector"]
    if profile.get("target_audience"):
        brand.target_audience = profile["target_audience"]
    if profile.get("tone_of_voice"):
        brand.tone_of_voice = profile["tone_of_voice"]
    
    # Salva profilo completo come JSON
    brand.ai_profile = json.dumps(profile, ensure_ascii=False)
    
    db.commit()
    
    # Cleanup
    await service.disconnect()
    active_sessions.pop(brand_id, None)
    
    return {
        "status": "saved",
        "brand_id": brand_id,
        "profile": profile
    }
