"""
api/routes_chat.py — Endpoint principal de conversación.

EXPONE:
  POST /chat   : recibe pregunta, devuelve respuesta + citas + chunks.

NOTA AL MARGEN:
====================
Este es el endpoint que las herramientas de orquestación (n8n, Make)
invocarán por webhook. Por eso devolvemos un JSON rico con metadata
suficiente para auditoría posterior.
"""
from __future__ import annotations

import time

from fastapi import APIRouter

from app.config import get_settings
from app.core.agent import answer_with_rag, build_citations
from app.schemas.models import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    s = get_settings()
    t0 = time.perf_counter()
    result = answer_with_rag(req.query, use_agent=req.use_agent)
    elapsed = int((time.perf_counter() - t0) * 1000)
    return ChatResponse(
        answer=result["answer"],
        citations=build_citations(result["chunks"]),
        retrieved_chunks=result["chunks"],
        used_tools=result.get("tools", []),
        latency_ms=elapsed,
        model=s.llm_model,
    )
