"""Upload a PDF to the knowledge base and ingest it into the vector store."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import get_logger
from app.services.ingestion import ingest_pdf

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["documents"])


class UploadResponse(BaseModel):
    filename: str
    chunk_count: int


@router.post("/documents", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    settings.ensure_dirs()
    # Store under a unique name to avoid collisions; keep the original for metadata.
    safe_name = Path(file.filename).name
    dest = settings.uploads_dir / f"{uuid.uuid4().hex}_{safe_name}"

    try:
        with dest.open("wb") as out:
            shutil.copyfileobj(file.file, out)
    finally:
        await file.close()

    try:
        result = ingest_pdf(str(dest), safe_name)
    except Exception as exc:  # noqa: BLE001 - surface a clean error to the client
        logger.exception("upload_ingest_failed", extra={"filename": safe_name})
        raise HTTPException(
            status_code=500, detail=f"Failed to ingest document: {exc}"
        ) from exc

    if result.chunk_count == 0:
        raise HTTPException(
            status_code=422,
            detail="No extractable text found in the PDF.",
        )

    return UploadResponse(
        filename=result.filename, chunk_count=result.chunk_count
    )
