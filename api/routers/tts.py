"""
Text-to-Speech Router
=====================
Endpoint for generating audio from translated text using gTTS.
"""

import io
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ml_engine.language_config import get_gtts_code

logger = logging.getLogger(__name__)

router = APIRouter()


class TTSRequest(BaseModel):
    text: str
    lang: str


@router.post("/generate-tts")
async def generate_tts(body: TTSRequest):
    """
    Generate text-to-speech audio for the given text and language.
    Returns an MP3 audio stream.
    """
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    gtts_code = get_gtts_code(body.lang.lower())
    if not gtts_code:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language for TTS: {body.lang}",
        )

    try:
        from gtts import gTTS

        tts = gTTS(text=text, lang=gtts_code, slow=False)

        # Write to in-memory buffer
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)

        return StreamingResponse(
            audio_buffer,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f'attachment; filename="tts_{body.lang}.mp3"',
            },
        )

    except ImportError:
        logger.error("gTTS not installed.")
        raise HTTPException(
            status_code=503,
            detail="TTS service unavailable. gTTS not installed.",
        )
    except (ConnectionError, TimeoutError) as e:
        logger.warning(f"TTS network unreachable: {e}")
        raise HTTPException(
            status_code=503,
            detail="TTS upstream service temporarily unreachable.",
        )
    except Exception as e:
        logger.error(f"TTS generation failed: {e}", exc_info=True)
        if "connect" in str(e).lower() or "connection" in str(e).lower() or "socket" in str(e).lower():
            raise HTTPException(
                status_code=503,
                detail="TTS upstream service temporarily unreachable.",
            )
        raise HTTPException(
            status_code=500,
            detail="Failed to generate audio. Please try again.",
        )
