"""
core/retriever.py — Recuperación híbrida + Re-ranking.

¿POR QUÉ NO BASTA CON BÚSQUEDA VECTORIAL "PURA"?
================================================
La búsqueda vectorial captura SIGNIFICADO, pero a veces falla con:
  - Códigos exactos ("artículo 234-A", "ID-7891")
  - Acrónimos raros, nombres propios poco comunes
  - Términos muy específicos del dominio

La búsqueda LÉXICA (BM25, basada en frecuencias de palabras) brilla
exactamente donde la vectorial flaquea. Combinarlas (HÍBRIDA) suele dar
una mejora sustancial en recall sobre corpus de dominio.

EL RERANKER:
  Tras recuperar TOP-K candidatos, un segundo modelo (cross-encoder o LLM)
  los re-puntúa mirando query y candidato JUNTOS — más preciso, más caro,
  por eso solo se aplica al TOP-K reducido.

PUNTOS DE CUIDADO:
  - El reranker LLM puede ser lento. Si la latencia importa, usa
    cross-encoders pequeños (ej. BAAI/bge-reranker-base) o Cohere Rerank.
  - HYBRID_ALPHA en .env permite tunear el peso vectorial vs léxico.
"""
from __future__ import annotations

from typing import Any, Optional

from loguru import logger
from rank_bm25 import BM25Okapi

from app.config import get_settings
from app.core.embeddings import EmbeddingProvider
from app.core.vectorstore import VectorStore, _safe_meta
from app.schemas.models import DocumentMetadata, RetrievedChunk


def _tokenize(text: str) -> list[str]:
    """Tokenizador simple para BM25. En producción usa uno con stemming."""
    # NOTA: Para español conviene quitar acentos y stopwords (nltk/spacy).
    return [t.lower() for t in text.split() if t.strip()]


class HybridRetriever:
    """
    Une búsqueda vectorial (semántica) con BM25 (léxica) y opcionalmente
    aplica un reranker LLM al final.

    Score final = alpha * score_vec + (1-alpha) * score_bm25
    (ambos normalizados a [0,1] antes de combinar).
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedder: EmbeddingProvider,
        alpha: float = 0.5,
    ):
        self.vector_store = vector_store
        self.embedder = embedder
        self.alpha = alpha
        self._bm25_dirty = True
        self._bm25: Optional[BM25Okapi] = None
        self._bm25_corpus_ids: list[str] = []
        self._bm25_corpus_meta: list[dict[str, Any]] = []
        self._bm25_corpus_text: list[str] = []

    # -------------------------------------------------------------------------
    def invalidate(self) -> None:
        """Llamar tras una nueva ingesta para reconstruir el índice BM25."""
        self._bm25_dirty = True

    def _build_bm25(self) -> None:
        ids, metas, docs = self.vector_store.all_documents()
        self._bm25_corpus_ids = ids
        self._bm25_corpus_meta = metas
        self._bm25_corpus_text = docs
        if docs:
            self._bm25 = BM25Okapi([_tokenize(d) for d in docs])
        else:
            self._bm25 = None
        self._bm25_dirty = False
        logger.info(f"BM25 reconstruido sobre {len(docs)} chunks.")

    # -------------------------------------------------------------------------
    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        where: Optional[dict[str, Any]] = None,
    ) -> list[RetrievedChunk]:
        """Devuelve TOP-K candidatos combinando vector + BM25."""
        # 1) Vectorial.
        q_vec = self.embedder.embed([query])[0]
        vec_results = self.vector_store.query(q_vec, top_k=top_k, where=where)

        # 2) BM25 (sobre todo el corpus, sin filtrado de metadata por simpleza).
        if self._bm25_dirty:
            self._build_bm25()

        bm25_results: list[RetrievedChunk] = []
        if self._bm25 is not None:
            scores = self._bm25.get_scores(_tokenize(query))
            # Top-K índices.
            ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
            max_score = max((s for _, s in ranked), default=1.0) or 1.0
            for idx, sc in ranked:
                if sc <= 0:
                    continue
                bm25_results.append(
                    RetrievedChunk(
                        text=self._bm25_corpus_text[idx],
                        metadata=DocumentMetadata(**_safe_meta(self._bm25_corpus_meta[idx])),
                        score=float(sc) / max_score,
                        source_retriever="bm25",
                    )
                )

        # 3) Fusión: dedup por texto, suma ponderada.
        merged: dict[str, RetrievedChunk] = {}
        for r in vec_results:
            key = r.text[:200]
            merged[key] = RetrievedChunk(
                text=r.text,
                metadata=r.metadata,
                score=self.alpha * r.score,
                source_retriever="hybrid",
            )
        for r in bm25_results:
            key = r.text[:200]
            if key in merged:
                merged[key].score += (1 - self.alpha) * r.score
            else:
                merged[key] = RetrievedChunk(
                    text=r.text,
                    metadata=r.metadata,
                    score=(1 - self.alpha) * r.score,
                    source_retriever="hybrid",
                )

        ranked_final = sorted(merged.values(), key=lambda c: c.score, reverse=True)
        return ranked_final[:top_k]


# =============================================================================
# Re-ranker basado en LLM ("LLM as a re-ranker")
# =============================================================================
def llm_rerank(
    query: str,
    candidates: list[RetrievedChunk],
    top_n: int,
    llm_call,  # callable: (system, user) -> str
) -> list[RetrievedChunk]:
    """
    Pide al LLM que re-puntúe y devuelva los más relevantes.

    NOTA: Es la forma más simple de reranker. En prod, considera
    cross-encoders (bge-reranker, Cohere) — más rápidos y baratos.
    """
    if not candidates:
        return []

    enumerated = "\n\n".join(
        f"[{i}] {c.text[:600]}" for i, c in enumerate(candidates)
    )
    system = (
        "Eres un evaluador estricto. Dado una pregunta y una lista de pasajes, "
        "devuelve los índices de los pasajes MÁS relevantes para responderla, "
        f"separados por coma, máximo {top_n}. Solo los índices, sin explicación."
    )
    user = f"PREGUNTA:\n{query}\n\nPASAJES:\n{enumerated}\n\nRESPUESTA:"
    raw = llm_call(system, user).strip()

    # Parseo defensivo: extrae enteros.
    import re
    indices = [int(x) for x in re.findall(r"\d+", raw)][:top_n]
    seen = set()
    out: list[RetrievedChunk] = []
    for i in indices:
        if 0 <= i < len(candidates) and i not in seen:
            seen.add(i)
            c = candidates[i]
            out.append(
                RetrievedChunk(
                    text=c.text, metadata=c.metadata,
                    score=c.score, source_retriever="rerank",
                )
            )
    return out or candidates[:top_n]  # fallback si el parseo falla.


# ---- Singleton -------------------------------------------------------------
_retriever: Optional[HybridRetriever] = None


def get_retriever() -> HybridRetriever:
    global _retriever
    if _retriever is None:
        from app.core.embeddings import build_embedding_provider
        s = get_settings()
        _retriever = HybridRetriever(
            vector_store=__import__("app.core.vectorstore", fromlist=["get_vector_store"]).get_vector_store(),
            embedder=build_embedding_provider(),
            alpha=s.hybrid_alpha,
        )
    return _retriever
