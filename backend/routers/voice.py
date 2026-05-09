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
