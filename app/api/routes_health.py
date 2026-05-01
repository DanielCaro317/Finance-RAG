"""
api/routes_health.py — Endpoints de salud / status.

Útil para:
  - Liveness/Readiness probes en Kubernetes / ECS.
  - Smoke tests post-deploy.
"""
from fastapi import APIRouter

from app.config import get_settings
from app.core.vectorstore import get_vector_store
from app.schemas.models import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    s = get_settings()
    try:
        n = get_vector_store().count()
    except Exception:
        n = 0
    return HealthResponse(
        status="ok",
        app_env=s.app_env,
        vector_store=s.vector_store,
        llm_provider=s.llm_provider,
        n_documents=n,
    )
