"""
config.py — Configuración centralizada del proyecto.

NOTA AL MARGEN (para principiantes):
====================================
- Toda configuración (API keys, modelos, rutas) vive aquí, no en el código.
- Usamos `pydantic-settings` para leer del archivo `.env` automáticamente
  y validar tipos. Si una variable falta o es inválida, el programa falla
  *al arrancar*, no después de 30 minutos de uso.
- Esto es un patrón llamado "12-Factor App" (factor #3: Config).

PUNTOS DE CUIDADO:
- Nunca hardcodees claves en el código. Usa siempre variables de entorno.
- En producción, las variables suelen venir de AWS Secrets Manager o
  Parameter Store, NO de un archivo .env (eso es solo para desarrollo).
"""
from functools import lru_cache
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Modelo único con toda la configuración del sistema."""

    # Pydantic-settings lee primero variables de entorno y luego el .env.
    # `extra="ignore"` evita errores si hay variables extra en .env.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # AWS_REGION = aws_region, da igual mayúsculas.
        extra="ignore",
    )

    # ---- General -------------------------------------------------------------
    app_env: Literal["local", "staging", "prod"] = "local"
    log_level: str = "INFO"

    # ---- LLM -----------------------------------------------------------------
    llm_provider: Literal["openai", "anthropic", "bedrock"] = "openai"
    llm_model: str = "gpt-4o-mini"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    # ---- Embeddings ----------------------------------------------------------
    embedding_provider: Literal["openai", "bedrock", "huggingface"] = "openai"
    embedding_model: str = "text-embedding-3-small"

    # ---- AWS -----------------------------------------------------------------
    aws_region: str = "us-west-2"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None  # Las credenciales temporales lo requieren.
    s3_bucket: Optional[str] = None

    # ---- Vector store --------------------------------------------------------
    vector_store: Literal["chroma", "pgvector"] = "chroma"
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection: str = "politicas_fraude"

    # ---- Recuperación --------------------------------------------------------
    retrieval_top_k: int = Field(default=10, ge=1, le=100)
    rerank_top_n: int = Field(default=4, ge=1, le=20)
    hybrid_alpha: float = Field(default=0.5, ge=0.0, le=1.0)

    # ---- Observabilidad ------------------------------------------------------
    langsmith_api_key: Optional[str] = None
    langsmith_project: str = "asistente-financiero"

    # ---- Servicios externos --------------------------------------------------
    fraud_api_url: str = "http://localhost:8000/mock/fraud"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Singleton de configuración.

    NOTA: `@lru_cache` hace que `Settings()` se construya UNA sola vez.
    Las llamadas siguientes reutilizan el mismo objeto. Esto es útil porque:
      1) Validamos el .env solo una vez (rápido).
      2) Inyectable en FastAPI con `Depends(get_settings)`.
    """
    return Settings()
