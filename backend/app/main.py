"""FastAPI application: REST endpoints for tokens, uploads, prompt, and sources.

The real-time voice loop runs in a separate process (app/agent/voice_agent.py).
This app shares state with it through the on-disk Chroma store and the small state
files in app/core/state.py.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, prompt, sources, token, upload
from app.core.config import settings
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


def create_app() -> FastAPI:
    settings.ensure_dirs()
    app = FastAPI(title="Voice Agent Backend", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(token.router)
    app.include_router(upload.router)
    app.include_router(prompt.router)
    app.include_router(sources.router)

    logger.info("app_started", extra={"cors_origins": settings.cors_origin_list})
    return app


app = create_app()
