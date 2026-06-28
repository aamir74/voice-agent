"""Speech-to-text via Groq Whisper (OpenAI-compatible endpoint).

Groq exposes an OpenAI-compatible transcription API, so we reuse the LiveKit OpenAI
plugin and simply point it at Groq's base URL with the whisper-large-v3 model.
"""

from __future__ import annotations

from livekit.plugins import openai

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_stt() -> openai.STT:
    """Return a configured Groq Whisper STT instance."""
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not set")
    logger.info("stt_init", extra={"model": settings.stt_model})
    return openai.STT(
        model=settings.stt_model,
        api_key=settings.groq_api_key,
        base_url=settings.groq_base_url,
    )
