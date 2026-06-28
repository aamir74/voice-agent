"""Retrieval: embed a query, search Chroma, return the top chunks with sources.

The retrieved chunks are also stashed in shared state so the frontend's RAG sources
panel can display what grounded the most recent answer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from app.core.config import settings
from app.core.logging import get_logger
from app.core.state import get_collection, set_last_sources
from app.services.embeddings import embed_query

logger = get_logger(__name__)


@dataclass
class RetrievedChunk:
    text: str
    source: str
    score: float


def retrieve(query: str, top_k: int | None = None) -> list[RetrievedChunk]:
    """Return the top_k most relevant chunks for a query (cosine distance)."""
    k = top_k or settings.retrieval_top_k
    collection = get_collection()
    if collection.count() == 0:
        logger.info("retrieve_empty_kb")
        set_last_sources([])
        return []

    query_embedding = embed_query(query)
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["metadatas", "documents", "distances"],
    )

    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    chunks: list[RetrievedChunk] = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        chunks.append(
            RetrievedChunk(
                text=doc,
                source=str((meta or {}).get("source", "unknown")),
                # cosine distance -> similarity score in [0, 1]
                score=round(1.0 - float(dist), 4),
            )
        )

    set_last_sources([asdict(c) for c in chunks])
    logger.info(
        "retrieve_done", extra={"query_len": len(query), "hits": len(chunks)}
    )
    return chunks


def build_context_block(chunks: list[RetrievedChunk]) -> str:
    """Format retrieved chunks into a context string for the LLM prompt."""
    if not chunks:
        return ""
    blocks = [
        f"[Source: {c.source}]\n{c.text}" for c in chunks
    ]
    return "\n\n---\n\n".join(blocks)
