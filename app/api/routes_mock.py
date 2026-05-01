"""
api/routes_mock.py — Endpoint mock del backend de fraudes.

Este endpoint simula un servicio empresarial real al que el agente
podría llamar. Útil para demostraciones end-to-end sin depender de
infraestructura externa.

Reemplázalo por un cliente real cuando despliegues.
"""
from __future__ import annotations

import hashlib

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/mock", tags=["mock"])


@router.get("/fraud/{transaction_id}")
def fraud(transaction_id: str) -> dict:
    """
    Genera un estado pseudo-determinista basado en el ID de transacción.
    Así diferentes IDs dan respuestas distintas pero estables.
    """
    if not transaction_id.startswith("TX-"):
        raise HTTPException(400, "ID inválido — debe empezar por 'TX-'.")
    h = int(hashlib.md5(transaction_id.encode()).hexdigest(), 16)
    risk = h % 100
    status = "fraud" if risk > 85 else ("review" if risk > 60 else "ok")
    return {
        "transaction_id": transaction_id,
        "status": status,
        "risk_score": risk,
        "amount": (h % 50_000) + 100,
        "currency": "USD",
        "country": ["CO", "MX", "AR", "ES", "US"][h % 5],
    }
