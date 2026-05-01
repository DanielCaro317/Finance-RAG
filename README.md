# Asistente Cognitivo Financiero (Advanced Agentic RAG)

API FastAPI con pipeline RAG corporativo, recuperación híbrida (vectorial + BM25),
re-ranking con LLM, agente con herramientas y evaluación con Ragas.

> 📖 **Lee [GUIA_COMPLETA.md](GUIA_COMPLETA.md)** para el paso a paso pedagógico
> de cómo está construido todo (recomendado si es tu primera vez con RAG).

---

## Estructura
```
app/
  api/         endpoints FastAPI (chat, ingest, health, mock)
  core/        chunking, embeddings, vectorstore, retriever, llm, agent
  services/    s3, fraud_api, ingestion
  evaluation/  Ragas + golden set
  schemas/     modelos Pydantic
data/raw/      documentos a indexar
scripts/       CLI: ingest_documents, run_eval
tests/         pytest
```

## Quick start

```bash
# 1) Crear venv e instalar
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# 2) Configurar .env (copia .env.example y edita)
cp .env.example .env

# 3) Ingestar documentos de ejemplo
python -m scripts.ingest_documents data/raw/manual_fraude_v2.md \
    --domain fraude_tecnologico --jurisdiction CO --effective-year 2024 --version v2 --no-s3

# 4) Levantar la API
uvicorn app.main:app --reload --port 8000

# 5) Abrir Swagger
#    http://localhost:8000/docs
```

## Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET    | `/health` | Estado del sistema y nº de chunks indexados. |
| POST   | `/ingest` | Sube un archivo y lo indexa con metadata. |
| POST   | `/chat` | Pregunta al agente RAG. |
| GET    | `/mock/fraud/{tx_id}` | Backend simulado de fraudes. |

## Variables `.env` clave

| Var | Por qué |
|-----|---------|
| `LLM_PROVIDER` | `openai` \| `anthropic` \| `bedrock` |
| `EMBEDDING_PROVIDER` | `openai` \| `bedrock` \| `huggingface` (local, gratis) |
| `HYBRID_ALPHA` | 0=solo BM25, 1=solo vectorial, 0.5=balance |
| `RETRIEVAL_TOP_K` / `RERANK_TOP_N` | tamaño del embudo |

## Docker

```bash
docker compose up --build
```
