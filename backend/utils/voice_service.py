import os
import httpx
import logging
from typing import Optional
from backend.config import ELEVENLABS_API_KEY, GROQ_API_KEY

logger = logging.getLogger(__name__)

class VoiceService:
    """
    Speech-to-Text service supporting ElevenLabs and Groq Whisper.
    """

    @staticmethod
    async def transcribe(audio_content: bytes, filename: str = "audio.wav") -> dict:
        """
        Transcribes audio content to text.
        Priority: ElevenLabs -> Groq Whisper
        """
        
        # 1. Try ElevenLabs if API key is present
        if ELEVENLABS_API_KEY:
            try:
                logger.info("Attempting transcription via ElevenLabs...")
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://api.elevenlabs.io/v1/speech-to-text",
                        headers={"xi-api-key": ELEVENLABS_API_KEY},
                        files={"file": (filename, audio_content, "audio/wav")},
                        data={"model_id": "scribe_v1"},
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        return {"text": data.get("text"), "provider": "ElevenLabs"}
                    else:
                        logger.warning(f"ElevenLabs error: {response.text}")
            except Exception as e:
                logger.error(f"ElevenLabs transcription failed: {e}")

        # 2. Fallback to Groq Whisper (Cheapest and Fastest)
        if GROQ_API_KEY:
            try:
                logger.info("Falling back to Groq Whisper (Cheapest option)...")
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://api.groq.com/openai/v1/audio/transcriptions",
                        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                        files={"file": (filename, audio_content, "audio/wav")},
                        data={
                            "model": "whisper-large-v3",
                            "response_format": "json"
                        },
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        return {"text": data.get("text"), "provider": "Groq Whisper"}
                    else:
                        logger.warning(f"Groq Whisper error: {response.text}")
            except Exception as e:
                logger.error(f"Groq Whisper transcription failed: {e}")

        return {"text": None, "provider": None}

    @staticmethod
    async def speak(text: str) -> Optional[bytes]:
        """
        Converts text to speech using ElevenLabs.
        """
        if not ELEVENLABS_API_KEY:
            logger.warning("ELEVENLABS_API_KEY not set, TTS disabled")
            return None

        try:
            logger.info("Attempting TTS via ElevenLabs...")
            async with httpx.AsyncClient() as client:
                # Using 'Rachel' voice ID as default (or you can pick another)
                voice_id = "21m00Tcm4TlvDq8ikWAM" 
                response = await client.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                    headers={"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"},
                    json={
                        "text": text,
                        "model_id": "eleven_monolingual_v1",
                        "voice_settings": {
                            "stability": 0.5,
                            "similarity_boost": 0.5
                        }
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return response.content
                else:
                    logger.warning(f"ElevenLabs TTS error: {response.text}")
                    return None
        except Exception as e:
            logger.error(f"ElevenLabs TTS failed: {e}")
            return None

voice_service = VoiceService()
