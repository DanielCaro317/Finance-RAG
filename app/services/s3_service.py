"""
services/s3_service.py — Persistencia de documentos crudos en Amazon S3.

¿POR QUÉ S3?
============
Los documentos originales (PDFs, imágenes, DOCX) son la "fuente de verdad".
La base vectorial guarda solo embeddings + texto procesado. Si algún día
quieres re-indexar con un modelo nuevo, necesitas el original. S3 es:
  - Barato ($0.023/GB/mes en Standard)
  - Durable (11 nueves)
  - Versionable (activa Versioning para auditoría regulatoria)

PUNTOS DE CUIDADO:
  - Activa cifrado SSE-S3 o SSE-KMS al crear el bucket.
  - Aplica políticas de bucket privadas (NUNCA público) y bloquea ACLs.
  - Para datos regulados: activa Object Lock + Versioning.
"""
from __future__ import annotations

from typing import Optional

from loguru import logger

from app.config import get_settings


def _client():
    """Crea un cliente S3 con las credenciales del .env."""
    import boto3
    s = get_settings()
    return boto3.client(
        "s3",
        region_name=s.aws_region,
        aws_access_key_id=s.aws_access_key_id,
        aws_secret_access_key=s.aws_secret_access_key,
        aws_session_token=s.aws_session_token,
    )


def upload_file(local_path: str, key: str) -> Optional[str]:
    """
    Sube un archivo a S3. Devuelve s3:// URI o None si S3 no está configurado.

    NOTA: Si no hay bucket configurado, la función retorna None silenciosamente
    (el sistema sigue funcionando solo con almacenamiento local — útil en dev).
    """
    s = get_settings()
    if not s.s3_bucket:
        logger.info("S3_BUCKET no configurado — saltando upload.")
        return None
    try:
        _client().upload_file(local_path, s.s3_bucket, key)
        uri = f"s3://{s.s3_bucket}/{key}"
        logger.info(f"Subido a {uri}")
        return uri
    except Exception as e:
        # No detenemos la ingesta por un error de S3; lo loggeamos.
        logger.error(f"Error subiendo a S3: {e}")
        return None
