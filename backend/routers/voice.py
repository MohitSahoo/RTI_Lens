from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.utils.voice_service import voice_service
import logging

router = APIRouter(prefix="/api/voice", tags=["voice"])
logger = logging.getLogger(__name__)

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribes uploaded audio file to text.
    """
    try:
        content = await file.read()
        result = await voice_service.transcribe(content, file.filename)
        
        if not result.get("text"):
            raise HTTPException(status_code=500, detail="Transcription failed. Please check API keys.")
            
        return result
    except Exception as e:
        logger.error(f"Voice endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/speak")
async def text_to_speech(payload: dict):
    """
    Converts text to speech and returns audio content.
    """
    text = payload.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
        
    audio_content = await voice_service.speak(text)
    if not audio_content:
        raise HTTPException(status_code=500, detail="TTS generation failed")
        
    from fastapi.responses import Response
    return Response(content=audio_content, media_type="audio/mpeg")
