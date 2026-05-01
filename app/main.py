"""
main.py — Punto de entrada de la aplicación FastAPI.

Para arrancar localmente:
    uvicorn app.main:app --reload --port 8000

Documentación interactiva (Swagger UI) automática en:
    http://localhost:8000/docs
"""
from __future__ import annotations

import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api import routes_chat, routes_health, routes_ingest, routes_mock
from app.config import get_settings


# -----------------------------------------------------------------------------
def _configure_logging(level: str) -> None:
    logger.remove()
    logger.add(
        sys.stdout,
        level=level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <7}</level> | "
               "<cyan>{name}:{line}</cyan> - {message}",
    )


def create_app() -> FastAPI:
    s = get_settings()
    _configure_logging(s.log_level)

    app = FastAPI(
        title="Asistente Cognitivo Financiero",
        description=(
            "API RAG corporativa: ingesta documental, recuperación híbrida, "
            "agente con tools y endpoint de chat con citaciones."
        ),
        version="0.1.0",
    )

    # CORS abierto en dev; CIÉRRALO en producción a tu dominio.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if s.app_env == "local" else [],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(routes_health.router)
    app.include_router(routes_chat.router)
    app.include_router(routes_ingest.router)
    app.include_router(routes_mock.router)

    @app.get("/", include_in_schema=False)
    def root() -> dict:
        return {"app": "asistente_cognitivo_financiero", "docs": "/docs"}

    logger.info(f"App arriba — env={s.app_env}, llm={s.llm_provider}/{s.llm_model}")
    return app


app = create_app()
