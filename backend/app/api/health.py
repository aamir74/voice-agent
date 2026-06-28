"""Health endpoint for readiness checks and ops visibility."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings
from app.core.state import chroma_healthy

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, object]:
    chroma_ok = chroma_healthy()
    livekit_configured = bool(
        settings.livekit_url
        and settings.livekit_api_key
        and settings.livekit_api_secret
    )
    status = "ok" if chroma_ok and livekit_configured else "degraded"
    return {
        "status": status,
        "chroma_ok": chroma_ok,
        "livekit_configured": livekit_configured,
    }
