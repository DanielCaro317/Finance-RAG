"""
api/routes_ingest.py — Endpoints de ingesta documental.

EXPONE:
  POST /ingest          : sube un archivo + metadata y lo indexa.
  GET  /ingest/stats    : cuenta documentos indexados.

PUNTOS DE CUIDADO:
  - Limita el tamaño de upload (MAX_UPLOAD_MB) — un PDF de 500MB puede
    tumbar el servicio y disparar el costo de embeddings.
  - Idealmente la ingesta es ASÍNCRONA: encolas en SQS / Celery y un
    worker procesa. Aquí lo hacemos síncrono por simpleza.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.vectorstore import get_vector_store
from app.schemas.models import IngestResponse
from app.services.ingestion import ingest_file

router = APIRouter(prefix="/ingest", tags=["ingest"])

MAX_UPLOAD_MB = 50


@router.post("", response_model=IngestResponse)
async def ingest(
    file: UploadFile = File(..., description="PDF, MD, TXT, DOCX o HTML."),
    domain: str = Form("general"),
    jurisdiction: Optional[str] = Form(None),
    effective_year: Optional[int] = Form(None),
    version: str = Form("v1"),
    upload_to_s3: bool = Form(True),
) -> IngestResponse:
    """Sube un archivo y lo indexa en la base vectorial."""
    # Lee el archivo a un temp local (los lectores trabajan con paths).
    suffix = Path(file.filename or "").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        if len(content) > MAX_UPLOAD_MB * 1024 * 1024:
            raise HTTPException(413, f"Archivo > {MAX_UPLOAD_MB}MB")
        tmp.write(content)
        tmp_path = tmp.name

    try:
        return ingest_file(
            tmp_path,
            domain=domain,
            jurisdiction=jurisdiction,
            effective_year=effective_year,
            version=version,
            upload_to_s3=upload_to_s3,
        )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


@router.get("/stats")
def stats() -> dict:
    return {"n_chunks": get_vector_store().count()}
