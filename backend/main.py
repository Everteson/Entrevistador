"""
AI Interviewer - FastAPI Backend
Main application with all endpoints for the interview system.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from modules.stt import STTService
from modules.tts import TTSService
from modules.llm import LLMService
from modules.profiles import get_profile, get_all_profiles, get_system_prompt
from modules.context_manager import ContextManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="AI Interviewer",
    description="Sistema de entrevistas técnicas com IA",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load configuration
config_path = Path(__file__).parent / "config.json"
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# Initialize services
stt_service = STTService(
    model_size=config["stt"]["model_size"],
    device=config["stt"]["device"],
    compute_type=config["stt"]["compute_type"]
)

# Get API keys from environment or config
elevenlabs_key = os.getenv("ELEVENLABS_API_KEY") or config["api_keys"]["elevenlabs"]
openrouter_key = os.getenv("OPENROUTER_API_KEY") or config["api_keys"]["openrouter"]
voice_id = os.getenv("ELEVENLABS_VOICE_ID") or config["tts"]["voice_id"]

tts_service = TTSService(
    api_key=elevenlabs_key,
    voice_id=voice_id,
    model_id=config["tts"]["model_id"],
    stability=config["tts"]["stability"],
    similarity_boost=config["tts"]["similarity_boost"],
    style=config["tts"]["style"],
    use_speaker_boost=config["tts"]["use_speaker_boost"]
)

llm_service = LLMService(
    api_key=openrouter_key,
    model=config["llm"]["model"],
    temperature=config["llm"]["temperature"],
    max_tokens=config["llm"]["max_tokens"]
)

# Session management
sessions: Dict[str, Dict] = {}

# Pydantic models
class InterviewRequest(BaseModel):
    session_id: Optional[str] = None
    profile: str = "pleno"
    stack: str = "backend"

class MessageRequest(BaseModel):
    session_id: str
    text: str
    is_code: bool = False

class EvaluationRequest(BaseModel):
    session_id: str


# ============= ENDPOINTS =============

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "AI Interviewer",
        "version": "1.0.0"
    }

@app.get("/api/profiles")
async def get_profiles():
    """Get all available interviewer profiles."""
    return {
        "profiles": get_all_profiles()
    }

@app.post("/api/interview/start")
async def start_interview(request: InterviewRequest):
    """Start a new interview session."""
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        # Create new session
        sessions[session_id] = {
            "profile": request.profile,
            "stack": request.stack,
            "context": ContextManager(max_exchanges=config["llm"]["context_window"]),
            "created_at": datetime.now().isoformat(),
            "messages": []
        }
        
        # Generate initial greeting
        system_prompt = get_system_prompt(request.profile, request.stack)
        initial_message = "Olá! Estou pronto para começar a entrevista."
        
        response = llm_service.generate_response(
            system_prompt=system_prompt,
            messages=[],
            user_message=initial_message
        )
        
        falar_content, codigo_content = llm_service.parse_response(response)
        
        # Add to context
        sessions[session_id]["context"].add_exchange(initial_message, response)
        sessions[session_id]["messages"].append({
            "role": "assistant",
            "falar": falar_content,
            "codigo": codigo_content,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"Started interview session: {session_id} ({request.profile}/{request.stack})")
        
        return {
            "session_id": session_id,
            "profile": request.profile,
            "stack": request.stack,
            "falar": falar_content,
            "codigo": codigo_content
        }
    
    except Exception as e:
        logger.error(f"Error starting interview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/transcribe")
async def transcribe_audio(
    session_id: str = Form(...),
    audio: UploadFile = File(...)
):
    """Transcribe audio to text using Fast Whisper."""
    try:
        # Save uploaded audio temporarily
        temp_path = f"temp_{session_id}_{datetime.now().timestamp()}.wav"
        
        with open(temp_path, "wb") as f:
            content = await audio.read()
            f.write(content)
        
        # Transcribe
        transcription = stt_service.transcribe(
            temp_path,
            language=config["stt"]["language"]
        )
        
        # Clean up
        os.remove(temp_path)
        
        logger.info(f"Transcribed audio for session {session_id}: {transcription[:50]}...")
        
        return {
            "transcription": transcription,
            "session_id": session_id
        }
    
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/interview/message")
async def send_message(request: MessageRequest):
    """Send a message (transcribed or typed) and get LLM response."""
    try:
        if request.session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = sessions[request.session_id]
        
        # Get system prompt
        system_prompt = get_system_prompt(session["profile"], session["stack"])
        
        # Get context messages
        context_messages = session["context"].get_messages()
        
        # Generate response
        response = llm_service.generate_response(
            system_prompt=system_prompt,
            messages=context_messages,
            user_message=request.text
        )
        
        # Parse response
        falar_content, codigo_content = llm_service.parse_response(response)
        
        # Update context
        session["context"].add_exchange(request.text, response)
        
        # Store messages
        session["messages"].append({
            "role": "user",
            "text": request.text,
            "is_code": request.is_code,
            "timestamp": datetime.now().isoformat()
        })
        
        session["messages"].append({
            "role": "assistant",
            "falar": falar_content,
            "codigo": codigo_content,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"Processed message for session {request.session_id}")
        
        return {
            "falar": falar_content,
            "codigo": codigo_content,
            "context_size": session["context"].get_exchange_count()
        }
    
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/synthesize")
async def synthesize_speech(request: MessageRequest):
    """Convert text to speech using ElevenLabs."""
    try:
        # Generate audio
        audio_bytes = tts_service.synthesize(request.text)
        
        logger.info(f"Synthesized speech: {len(audio_bytes)} bytes")
        
        return StreamingResponse(
            iter([audio_bytes]),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=speech.mp3"
            }
        )
    
    except Exception as e:
        logger.error(f"Error synthesizing speech: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/interview/evaluate")
async def evaluate_interview(request: EvaluationRequest):
    """Generate final interview evaluation."""
    try:
        if request.session_id not in sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = sessions[request.session_id]
        
        # Get all messages for evaluation
        system_prompt = get_system_prompt(session["profile"], session["stack"])
        all_messages = [{"role": "system", "content": system_prompt}]
        all_messages.extend(session["context"].get_messages())
        
        # Generate evaluation
        evaluation = llm_service.generate_evaluation(
            messages=all_messages,
            profile=session["profile"],
            stack=session["stack"]
        )
        
        logger.info(f"Generated evaluation for session {request.session_id}")
        
        return evaluation
    
    except Exception as e:
        logger.error(f"Error generating evaluation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Get session information."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    
    return {
        "session_id": session_id,
        "profile": session["profile"],
        "stack": session["stack"],
        "created_at": session["created_at"],
        "message_count": len(session["messages"]),
        "context_size": session["context"].get_exchange_count()
    }

@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del sessions[session_id]
    logger.info(f"Deleted session: {session_id}")
    
    return {"status": "deleted", "session_id": session_id}

@app.get("/api/config")
async def get_config():
    """Get current configuration (without API keys)."""
    safe_config = {
        "stt": config["stt"],
        "llm": {
            "model": config["llm"]["model"],
            "temperature": config["llm"]["temperature"],
            "max_tokens": config["llm"]["max_tokens"],
            "context_window": config["llm"]["context_window"]
        },
        "interviewer": config["interviewer"]
    }
    return safe_config


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
