"""Expose the chunks retrieved for the most recent answer (bonus RAG panel)."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.state import get_last_sources

router = APIRouter(prefix="/api", tags=["sources"])


class Source(BaseModel):
    text: str
    source: str
    score: float


class SourcesResponse(BaseModel):
    sources: list[Source]


@router.get("/sources", response_model=SourcesResponse)
def read_sources() -> SourcesResponse:
    return SourcesResponse(sources=get_last_sources())
