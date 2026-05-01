"""
core/vectorstore.py — Capa de persistencia vectorial.

¿QUÉ HACE UNA "VECTOR DATABASE"?
================================
Guarda pares (vector, metadata, texto) y permite buscar los K vectores
más cercanos a una "consulta" (también un vector). La cercanía se mide
con similitud coseno (típicamente).

ELECCIONES:
  - ChromaDB: simple, persistente en disco, ideal para empezar y prototipos.
  - FAISS:    bibliotca de Facebook, súper rápida, sin metadatos nativos.
  - PGVector: extensión de PostgreSQL — ideal en producción si ya usas
              Postgres (transacciones, joins con tablas SQL, backups).

PUNTOS DE CUIDADO:
  - "namespaces" o "collections" SEPARAN dominios (ej. fraude vs tributario).
    Mejor varias collections enfocadas que una gigante con todo mezclado.
  - El control de versiones de un documento se hace via metadata `version`
    + filtro en la consulta (no borrando vectores viejos: pierdes histórico).
"""
from __future__ import annotations

from typing import Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger

from app.config import get_settings
from app.schemas.models import DocumentMetadata, RetrievedChunk


class VectorStore:
    """Wrapper sobre ChromaDB con la API mínima que necesitamos."""

    def __init__(self, persist_dir: str, collection_name: str):
        # PersistentClient guarda en disco — sobrevive a reinicios.
        # Para desarrollo en memoria usaríamos chromadb.Client() (sin persistencia).
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        # get_or_create: idempotente. metadata={"hnsw:space": "cosine"} fija
        # la métrica (alternativas: "l2", "ip"). Cosine es estándar para texto.
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"Chroma collection '{collection_name}' lista.")

    # -------------------------------------------------------------------------
    def add(
        self,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Inserta o actualiza chunks (upsert)."""
        # Chroma no acepta valores None en metadata: limpiamos.
        cleaned = [{k: v for k, v in m.items() if v is not None} for m in metadatas]
        self.collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=cleaned,
        )

    # -------------------------------------------------------------------------
    def query(
        self,
        embedding: list[float],
        top_k: int = 10,
        where: Optional[dict[str, Any]] = None,
    ) -> list[RetrievedChunk]:
        """Búsqueda vectorial con filtro opcional de metadata."""
        # `where` permite filtrar por metadata en SQL-like dict.
        # Ej: {"domain": "fraude_tecnologico", "effective_year": {"$gte": 2023}}
        res = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=where or None,
            include=["documents", "metadatas", "distances"],
        )
        out: list[RetrievedChunk] = []
        # Chroma devuelve listas de listas (1 lista por query — aquí 1).
        docs = res["documents"][0]
        metas = res["metadatas"][0]
        dists = res["distances"][0]
        for text, meta, dist in zip(docs, metas, dists):
            # distancia coseno -> similitud = 1 - dist (Chroma usa distancia).
            score = max(0.0, 1.0 - float(dist))
            out.append(
                RetrievedChunk(
                    text=text,
                    metadata=DocumentMetadata(**_safe_meta(meta)),
                    score=score,
                    source_retriever="vector",
                )
            )
        return out

    # -------------------------------------------------------------------------
    def all_documents(self) -> tuple[list[str], list[dict[str, Any]], list[str]]:
        """Devuelve TODO el corpus (para el índice BM25 en memoria)."""
        # PUNTO DE CUIDADO: para corpus grandes esto NO escala. En producción
        # usa ElasticSearch/OpenSearch (BM25 nativo) o tantivy.
        res = self.collection.get(include=["documents", "metadatas"])
        return res["ids"], res["metadatas"], res["documents"]

    # -------------------------------------------------------------------------
    def count(self) -> int:
        return self.collection.count()


def _safe_meta(m: dict[str, Any]) -> dict[str, Any]:
    """Garantiza los campos requeridos por DocumentMetadata."""
    return {
        "source": m.get("source", "unknown"),
        "domain": m.get("domain", "general"),
        "jurisdiction": m.get("jurisdiction"),
        "effective_year": m.get("effective_year"),
        "version": m.get("version"),
        "page": m.get("page"),
        "chunk_index": m.get("chunk_index"),
        "extra": {k: v for k, v in m.items() if k not in {
            "source", "domain", "jurisdiction", "effective_year",
            "version", "page", "chunk_index"
        }},
    }


# ---- Singleton -------------------------------------------------------------
_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Singleton perezoso para reutilizar la conexión."""
    global _store
    if _store is None:
        s = get_settings()
        _store = VectorStore(s.chroma_persist_dir, s.chroma_collection)
    return _store
