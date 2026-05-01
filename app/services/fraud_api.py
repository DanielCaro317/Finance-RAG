"""
services/fraud_api.py — Cliente del backend interno de fraudes.

NOTA AL MARGEN:
====================
Aquí simulamos un servicio externo. En la realidad, una organización
tendría microservicios internos accesibles por HTTP. La idea es que el
agente RAG pueda combinar:
  - Conocimiento estático (políticas en docs)
  - Conocimiento dinámico (estado actual de una transacción)

PUNTOS DE CUIDADO:
  - Timeout corto (5s) — el LLM espera bloqueado.
  - Manejo de errores: si la API cae, el agente debe responder con
    fallback claro ("No pude consultar el sistema de fraudes").
  - NUNCA expongas PII al LLM si no es necesario (ofusca CCs/cédulas).
"""
from __future__ import annotations

from typing import Any

import httpx
from loguru import logger

from app.config import get_settings


def lookup_fraud_status(transaction_id: str) -> dict[str, Any]:
    """Consulta el estado de fraude de una transacción."""
    s = get_settings()
    url = f"{s.fraud_api_url}/{transaction_id}"
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(url)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        logger.warning(f"fraud_api error: {e}")
        return {"transaction_id": transaction_id, "status": "unknown", "error": str(e)}
