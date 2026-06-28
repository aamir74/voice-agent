"""LLM via Google Gemini (OpenAI-compatible endpoint).

Gemini exposes an OpenAI-compatible chat completions API, so we reuse the LiveKit
OpenAI plugin pointed at Gemini's base URL. RAG context and the editable system
prompt are injected at the agent layer (see app/agent/voice_agent.py) so this stays
a thin, swappable factory.
"""

from __future__ import annotations

from livekit.plugins import openai

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_llm() -> openai.LLM:
    """Return a configured Gemini LLM instance."""
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    logger.info("llm_init", extra={"model": settings.llm_model})
    return openai.LLM(
        model=settings.llm_model,
        api_key=settings.gemini_api_key,
        base_url=settings.gemini_base_url,
    )
