"""PDF ingestion: extract text -> chunk -> embed -> store in Chroma.

Called by the upload API. Keeps the pipeline small and explicit (KISS): PyMuPDF for
extraction, a simple overlapping character splitter for chunking, Gemini for
embeddings, and Chroma for storage.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

import fitz  # PyMuPDF

from app.core.config import settings
from app.core.logging import get_logger
from app.core.state import get_collection
from app.services.embeddings import embed_documents

logger = get_logger(__name__)


@dataclass
class IngestResult:
    filename: str
    chunk_count: int


def extract_text(pdf_path: str) -> str:
    """Extract all text from a PDF, one page after another."""
    parts: list[str] = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            parts.append(page.get_text("text"))
    return "\n".join(parts)


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into overlapping windows on word boundaries.

    Sizes are measured in characters (a good-enough proxy for tokens here — KISS).
    Overlap preserves context across chunk boundaries for better retrieval.
    """
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for word in words:
        current.append(word)
        current_len += len(word) + 1
        if current_len >= chunk_size:
            chunks.append(" ".join(current))
            # Re-seed the next chunk with the tail words for overlap.
            overlap_words: list[str] = []
            overlap_len = 0
            for w in reversed(current):
                overlap_len += len(w) + 1
                overlap_words.insert(0, w)
                if overlap_len >= overlap:
                    break
            current = overlap_words
            current_len = sum(len(w) + 1 for w in current)
    if current:
        chunks.append(" ".join(current))
    return chunks


def ingest_pdf(pdf_path: str, filename: str) -> IngestResult:
    """Extract, chunk, embed, and store a PDF in the Chroma collection."""
    logger.info("ingest_start", extra={"filename": filename})

    text = extract_text(pdf_path)
    chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
    if not chunks:
        logger.warning("ingest_no_text", extra={"filename": filename})
        return IngestResult(filename=filename, chunk_count=0)

    embeddings = embed_documents(chunks)

    collection = get_collection()
    ids = [f"{filename}::{uuid.uuid4().hex}" for _ in chunks]
    metadatas = [
        {"source": filename, "chunk_index": i, "text": chunk}
        for i, chunk in enumerate(chunks)
    ]
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )

    logger.info(
        "ingest_done", extra={"filename": filename, "chunk_count": len(chunks)}
    )
    return IngestResult(filename=filename, chunk_count=len(chunks))
