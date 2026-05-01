"""
scripts/ingest_documents.py — Ingesta masiva por línea de comandos.

USO:
    python -m scripts.ingest_documents data/raw/manual.pdf --domain fraude_tecnologico
    python -m scripts.ingest_documents data/raw/  --domain general   # carpeta entera
"""
from __future__ import annotations

import argparse
from pathlib import Path

from loguru import logger

from app.services.ingestion import ingest_file


def main():
    p = argparse.ArgumentParser()
    p.add_argument("path", help="Archivo o carpeta a ingerir.")
    p.add_argument("--domain", default="general")
    p.add_argument("--jurisdiction", default=None)
    p.add_argument("--effective-year", type=int, default=None)
    p.add_argument("--version", default="v1")
    p.add_argument("--no-s3", action="store_true", help="No subir a S3.")
    args = p.parse_args()

    path = Path(args.path)
    files = [path] if path.is_file() else list(path.rglob("*.*"))
    logger.info(f"Ingiriendo {len(files)} archivo(s)...")

    for f in files:
        if f.suffix.lower() not in {".pdf", ".md", ".txt", ".docx", ".html"}:
            continue
        try:
            r = ingest_file(
                str(f),
                domain=args.domain,
                jurisdiction=args.jurisdiction,
                effective_year=args.effective_year,
                version=args.version,
                upload_to_s3=not args.no_s3,
            )
            logger.success(f"  ✓ {f.name} -> {r.n_chunks} chunks (id={r.document_id})")
        except Exception as e:
            logger.error(f"  ✗ {f.name}: {e}")


if __name__ == "__main__":
    main()
