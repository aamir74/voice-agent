"""Gemini embeddings used by both ingestion and retrieval.

Kept in its own module so ingestion and RAG share one implementation (DRY) and the
document/query task types stay consistent.
"""

from __future__ import annotations

from google import genai
from google.genai import types

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def _embed(texts: list[str], task_type: str) -> list[list[float]]:
    if not texts:
        return []
    client = _get_client()
    result = client.models.embed_content(
        model=settings.embedding_model,
        contents=texts,
        config=types.EmbedContentConfig(task_type=task_type),
    )
    return [list(e.values) for e in result.embeddings]


def embed_documents(texts: list[str]) -> list[list[float]]:
    """Embed document chunks for storage."""
    return _embed(texts, task_type="RETRIEVAL_DOCUMENT")


def embed_query(text: str) -> list[float]:
    """Embed a single user query for retrieval."""
    vectors = _embed([text], task_type="RETRIEVAL_QUERY")
    return vectors[0] if vectors else []
