"""Shared runtime state: system prompt, Chroma collection, and last RAG sources.

This is process-local state. The FastAPI app and the LiveKit agent worker run as
separate processes, but both persist through the same on-disk Chroma directory, so
an uploaded document is retrievable by the agent. The editable system prompt is held
in memory and persisted to a small JSON file so it survives restarts and is shared
via disk (each process reads the latest value before using it).
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_lock = threading.Lock()
_chroma_client: chromadb.ClientAPI | None = None
_collection: Collection | None = None

# Last retrieval result, exposed via GET /api/sources for the bonus RAG panel.
_last_sources: list[dict[str, Any]] = []

_PROMPT_FILE = Path(settings.data_dir) / "system_prompt.txt"


# --------------------------------------------------------------------------- #
# Chroma collection (lazy singleton)
# --------------------------------------------------------------------------- #
def get_collection() -> Collection:
    """Return the shared persistent Chroma collection, creating it if needed."""
    global _chroma_client, _collection
    with _lock:
        if _collection is None:
            settings.ensure_dirs()
            _chroma_client = chromadb.PersistentClient(path=settings.chroma_dir)
            # We supply our own embeddings, so disable Chroma's default embedder.
            _collection = _chroma_client.get_or_create_collection(
                name=settings.collection_name,
                embedding_function=None,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("chroma_ready", extra={"collection": settings.collection_name})
        return _collection


def chroma_healthy() -> bool:
    """Return True if the Chroma collection can be reached."""
    try:
        get_collection().count()
        return True
    except Exception:  # noqa: BLE001 - health check must never raise
        logger.exception("chroma_unhealthy")
        return False


# --------------------------------------------------------------------------- #
# Editable system prompt (persisted to disk so both processes share it)
# --------------------------------------------------------------------------- #
def get_system_prompt() -> str:
    """Return the current system prompt, falling back to the configured default."""
    try:
        if _PROMPT_FILE.exists():
            text = _PROMPT_FILE.read_text(encoding="utf-8").strip()
            if text:
                return text
    except OSError:
        logger.exception("prompt_read_failed")
    return settings.default_system_prompt


def set_system_prompt(prompt: str) -> str:
    """Persist a new system prompt and return the stored value."""
    cleaned = prompt.strip() or settings.default_system_prompt
    with _lock:
        settings.ensure_dirs()
        _PROMPT_FILE.write_text(cleaned, encoding="utf-8")
    logger.info("prompt_updated", extra={"length": len(cleaned)})
    return cleaned


# --------------------------------------------------------------------------- #
# Last RAG sources (for the UI panel)
# --------------------------------------------------------------------------- #
def set_last_sources(sources: list[dict[str, Any]]) -> None:
    global _last_sources
    _last_sources = sources
    _persist_sources(sources)


def get_last_sources() -> list[dict[str, Any]]:
    # Prefer the in-memory value; fall back to disk (agent and API are separate procs).
    if _last_sources:
        return _last_sources
    return _read_sources()


# Sources are written by the agent process and read by the API process, so they
# round-trip through a small JSON file as well.
_SOURCES_FILE = Path(settings.data_dir) / "last_sources.json"


def _persist_sources(sources: list[dict[str, Any]]) -> None:
    try:
        settings.ensure_dirs()
        _SOURCES_FILE.write_text(json.dumps(sources), encoding="utf-8")
    except OSError:
        logger.exception("sources_write_failed")


def _read_sources() -> list[dict[str, Any]]:
    try:
        if _SOURCES_FILE.exists():
            return json.loads(_SOURCES_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.exception("sources_read_failed")
    return []
