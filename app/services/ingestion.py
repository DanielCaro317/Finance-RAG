"""
services/ingestion.py — Pipeline de ingesta documental.

PIPELINE COMPLETO:
==================
  1. Cargar archivo crudo (PDF/MD/TXT/DOCX).
  2. Extraer texto plano.
  3. Chunking (estructurado o semántico).
  4. Generar embeddings.
  5. Guardar (id, vector, metadata, texto) en la vector DB.
  6. (Opcional) Subir el original a S3 para auditoría.
  7. Invalidar el índice BM25 para que se reconstruya.

PUNTOS DE CUIDADO:
  - Asigna metadatos RICOS desde la ingesta. Después es muy difícil
    re-categorizar.
  - Si un documento reemplaza a otro, sube la versión nueva con
    metadata.version='v2' y filtra por v2 en consultas.
  - Para PDFs con tablas/imágenes complejas, usa "unstructured" o
    AWS Textract en vez de pypdf.
"""
from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from app.core.chunking import chunk_markdown, chunk_text
from app.core.embeddings import build_embedding_provider
from app.core.retriever import get_retriever
from app.core.vectorstore import get_vector_store
from app.schemas.models import IngestResponse
from app.services.s3_service import upload_file


# =============================================================================
# Lectores por extensión
# =============================================================================
def _read_pdf(path: Path) -> str:
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    parts = []
    for i, page in enumerate(reader.pages):
        parts.append(f"\n[PÁGINA {i+1}]\n" + (page.extract_text() or ""))
    return "\n".join(parts)


def _read_docx(path: Path) -> str:
    from docx import Document
    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


READERS = {
    ".pdf": _read_pdf,
    ".docx": _read_docx,
    ".md": _read_text,
    ".txt": _read_text,
    ".html": _read_text,
}


# =============================================================================
# Función principal de ingesta
# =============================================================================
def ingest_file(
    local_path: str,
    domain: str = "general",
    jurisdiction: Optional[str] = None,
    effective_year: Optional[int] = None,
    version: str = "v1",
    upload_to_s3: bool = True,
) -> IngestResponse:
    """
    Ingesta un archivo: lee, fragmenta, embebe, indexa, opcionalmente sube a S3.

    EJEMPLO DE USO:
        ingest_file("data/raw/manual_fraude.pdf",
                    domain="fraude_tecnologico",
                    jurisdiction="CO",
                    effective_year=2024,
                    version="v2")
    """
    p = Path(local_path)
    if not p.exists():
        raise FileNotFoundError(local_path)

    ext = p.suffix.lower()
    if ext not in READERS:
        raise ValueError(f"Extensión no soportada: {ext}")

    logger.info(f"Leyendo {p.name} ({ext})...")
    raw_text = READERS[ext](p)

    # 2) Chunking — usamos splitter de markdown si lo es; si no, recursivo.
    if ext == ".md":
        chunks = chunk_markdown(raw_text)
    else:
        chunks = chunk_text(raw_text, chunk_size=1000, chunk_overlap=150)

    if not chunks:
        raise ValueError("Sin chunks tras fragmentación.")
    logger.info(f"Generados {len(chunks)} chunks.")

    # 3) Embeddings (en lote — más rápido y barato).
    embedder = build_embedding_provider()
    vectors = embedder.embed([c.text for c in chunks])

    # 4) Construcción de IDs y metadata.
    document_id = hashlib.md5(f"{p.name}:{version}".encode()).hexdigest()[:12]

    ids: list[str] = []
    metadatas: list[dict[str, Any]] = []
    texts: list[str] = []
    for c in chunks:
        cid = f"{document_id}_c{c.index}"
        ids.append(cid)
        # Extraemos número de página si nuestro lector PDF lo marcó.
        page = None
        if "[PÁGINA " in c.text[:30]:
            try:
                page = int(c.text.split("[PÁGINA ")[1].split("]")[0])
            except Exception:
                page = None
        meta: dict[str, Any] = {
            "source": p.name,
            "domain": domain,
            "jurisdiction": jurisdiction,
            "effective_year": effective_year,
            "version": version,
            "chunk_index": c.index,
            "page": page,
            **c.extra_metadata,
        }
        metadatas.append(meta)
        texts.append(c.text)

    # 5) Indexación.
    store = get_vector_store()
    store.add(ids=ids, texts=texts, embeddings=vectors, metadatas=metadatas)
    logger.info(f"Indexados {len(ids)} chunks en colección.")

    # 6) S3 (opcional).
    s3_uri = None
    if upload_to_s3:
        key = f"raw/{document_id}/{p.name}"
        s3_uri = upload_file(local_path, key)

    # 7) Invalidar BM25 para que se reconstruya en la siguiente query.
    get_retriever().invalidate()

    return IngestResponse(
        document_id=document_id,
        n_chunks=len(ids),
        s3_uri=s3_uri,
        indexed_at=datetime.now(timezone.utc),
    )
