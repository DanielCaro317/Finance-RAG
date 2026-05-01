"""
schemas/models.py — Contratos de datos (Pydantic).

NOTA AL MARGEN:
====================
Pydantic define "modelos" que validan datos automáticamente. Cuando un
cliente HTTP envía JSON a la API, FastAPI usa estos modelos para:
  1) Validar tipos (rechaza si falta un campo o tiene tipo incorrecto).
  2) Convertir tipos (ej. "5" -> 5).
  3) Generar la documentación OpenAPI en /docs.

Los "schemas" son el contrato público de la API. Pensar bien estos
modelos al inicio evita refactors dolorosos después.
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Modelos de dominio (chunks de documentos)
# =============================================================================
class DocumentMetadata(BaseModel):
    """
    Metadata de un fragmento (chunk) indexado.

    PUNTOS DE CUIDADO (caso LexisNexis citado en la propuesta):
      - Sin metadatos como `jurisdiction` y `effective_year`, el RAG
        puede mezclar reglas de jurisdicciones distintas — desastre legal.
      - SIEMPRE incluye al menos: source, dominio, fecha de vigencia,
        versión del documento.
    """
    source: str = Field(..., description="Nombre o ruta del documento origen.")
    domain: str = Field(..., description="Dominio: 'tributario'|'penal'|'fraude_tecnologico'|...")
    jurisdiction: Optional[str] = Field(None, description="Ej: 'CO', 'MX', 'global'.")
    effective_year: Optional[int] = Field(None, description="Año desde el que aplica la regla.")
    version: Optional[str] = Field(None, description="v1, v2... (control de versiones).")
    page: Optional[int] = None
    chunk_index: Optional[int] = None
    extra: dict[str, Any] = Field(default_factory=dict)


class RetrievedChunk(BaseModel):
    """Un fragmento devuelto por el retriever (con su score)."""
    text: str
    metadata: DocumentMetadata
    score: float
    source_retriever: str = Field(..., description="'vector' | 'bm25' | 'hybrid' | 'rerank'.")


# =============================================================================
# API: Chat
# =============================================================================
class ChatRequest(BaseModel):
    """Petición que llega a /chat."""
    query: str = Field(..., min_length=1, description="La pregunta del usuario.")
    # Filtros de metadata opcionales (ej. {"domain": "fraude_tecnologico"}).
    filters: Optional[dict[str, Any]] = None
    use_agent: bool = Field(default=True, description="Si True, el LLM puede invocar tools.")


class Citation(BaseModel):
    """Referencia a un chunk usado en la respuesta (para auditoría)."""
    source: str
    page: Optional[int] = None
    snippet: str


class ChatResponse(BaseModel):
    """Respuesta de /chat."""
    answer: str
    citations: list[Citation]
    retrieved_chunks: list[RetrievedChunk]
    used_tools: list[str] = []
    latency_ms: int
    model: str


# =============================================================================
# API: Ingest
# =============================================================================
class IngestResponse(BaseModel):
    document_id: str
    n_chunks: int
    s3_uri: Optional[str] = None
    indexed_at: datetime


# =============================================================================
# API: Health
# =============================================================================
class HealthResponse(BaseModel):
    status: str
    app_env: str
    vector_store: str
    llm_provider: str
    n_documents: int
