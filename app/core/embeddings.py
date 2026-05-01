"""
core/embeddings.py — Generación de embeddings.

¿QUÉ ES UN EMBEDDING?
=====================
Un "embedding" es un vector de números (ej. 1536 dimensiones) que
representa el SIGNIFICADO de un texto. Textos con significado parecido
quedan cerca en ese espacio vectorial. Es la magia que permite buscar
"trasferencias sospechosas" y encontrar un párrafo que dice
"transacciones inusuales" aunque no compartan palabras.

PROVEEDORES SOPORTADOS:
  - openai      : text-embedding-3-small (1536d, $0.02 / 1M tokens) — default.
  - bedrock     : amazon.titan-embed-text-v2:0 (1024d).
  - huggingface : sentence-transformers/all-MiniLM-L6-v2 (384d, GRATIS, local).

PUNTOS DE CUIDADO:
  - SIEMPRE el mismo modelo para indexar y consultar. Si los mezclas, los
    espacios vectoriales son distintos y la búsqueda devuelve basura.
  - Modelos multilingües si tu corpus está en español (text-embedding-3-*
    funcionan bien con español; MiniLM-L6 es solo en inglés).
  - Considera "multimodal embeddings" (Titan Multimodal) si necesitas
    indexar imágenes/gráficos junto con texto.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from loguru import logger

from app.config import get_settings


class EmbeddingProvider(ABC):
    """Interfaz común — facilita cambiar de proveedor sin tocar el resto."""

    dimension: int

    @abstractmethod
    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Devuelve un vector por texto, en el mismo orden."""


class OpenAIEmbeddings(EmbeddingProvider):
    """Embeddings vía API OpenAI."""

    # Mapeo de dimensiones por modelo (referencia, no se valida).
    _DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(self, model: str, api_key: str):
        from openai import OpenAI  # Importación perezosa para no obligar a tener todos los SDKs.
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.dimension = self._DIMENSIONS.get(model, 1536)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        # OpenAI acepta hasta 2048 inputs por llamada — batch para eficiencia.
        # NOTA: si vas a indexar millones de chunks, paraleliza y maneja
        #       rate limits (429) con backoff exponencial.
        resp = self.client.embeddings.create(model=self.model, input=list(texts))
        return [d.embedding for d in resp.data]


class BedrockEmbeddings(EmbeddingProvider):
    """Embeddings vía AWS Bedrock (Titan)."""

    def __init__(self, model: str, region: str):
        import boto3
        import json
        self._json = json
        self.client = boto3.client("bedrock-runtime", region_name=region)
        self.model = model
        self.dimension = 1024  # Titan v2 default.

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        # Bedrock NO tiene endpoint batch para Titan-embed: invocamos N veces.
        out = []
        for t in texts:
            body = self._json.dumps({"inputText": t})
            resp = self.client.invoke_model(modelId=self.model, body=body)
            data = self._json.loads(resp["body"].read())
            out.append(data["embedding"])
        return out


class HuggingFaceEmbeddings(EmbeddingProvider):
    """Embeddings locales (sentence-transformers). Gratis, sin API."""

    def __init__(self, model: str):
        # sentence-transformers se descarga el modelo la primera vez (~80MB).
        from sentence_transformers import SentenceTransformer  # type: ignore
        self.encoder = SentenceTransformer(model)
        self.dimension = self.encoder.get_sentence_embedding_dimension()

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        vecs = self.encoder.encode(list(texts), normalize_embeddings=True)
        return [v.tolist() for v in vecs]


def build_embedding_provider() -> EmbeddingProvider:
    """Factory: construye el provider según la configuración."""
    s = get_settings()
    logger.info(f"Embeddings: provider={s.embedding_provider} model={s.embedding_model}")

    if s.embedding_provider == "openai":
        if not s.openai_api_key:
            raise RuntimeError("Falta OPENAI_API_KEY en .env")
        return OpenAIEmbeddings(model=s.embedding_model, api_key=s.openai_api_key)

    if s.embedding_provider == "bedrock":
        return BedrockEmbeddings(model=s.embedding_model, region=s.aws_region)

    if s.embedding_provider == "huggingface":
        return HuggingFaceEmbeddings(model=s.embedding_model)

    raise ValueError(f"Provider desconocido: {s.embedding_provider}")
