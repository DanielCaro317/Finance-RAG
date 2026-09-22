# Asistente Cognitivo Financiero

Agente RAG corporativo sobre documentación normativa de fraude financiero: API en FastAPI, recuperación híbrida, re-ranking, tool calling y evaluación automatizada con Ragas.

## El problema

Un asistente sobre normativa financiera tiene un margen de error muy estrecho. Citar el plazo de reclamación equivocado, o mezclar la política de 2022 con la de 2024, no es un fallo cosmético: es una respuesta con consecuencias regulatorias. Tres decisiones de diseño responden a eso.

**La búsqueda vectorial sola no basta.** Captura significado, pero falla justo donde la normativa es más precisa: códigos de artículo, identificadores, acrónimos de dominio. BM25 acierta exactamente ahí. El sistema combina ambas con un peso configurable (`HYBRID_ALPHA`) y normaliza las puntuaciones antes de mezclarlas.

**El orden de los resultados importa tanto como el conjunto.** Tras recuperar los candidatos, un segundo paso los re-puntúa mirando pregunta y fragmento juntos —más preciso y más caro, por eso solo se aplica al top-k reducido—. Sin re-ranking, el fragmento correcto aparece recuperado pero enterrado, y el modelo responde con el segundo mejor.

**El conocimiento estático no alcanza.** Una pregunta como *"¿qué pasó con la transacción 7891?"* no se responde con documentos: requiere consultar un sistema vivo. Por eso es un agente con herramientas y no un RAG lineal —decide si buscar, con qué filtros de metadata, o si llamar a una API externa— implementado como un ciclo ReAct explícito, con límite de iteraciones y validación de argumentos, en lugar de delegarlo a un framework.

## Arquitectura

```
Documentos ──► chunking ──► embeddings ──► vector store
 (Markdown)   (recursivo /
               por headers)
                                 ┌──► Recuperación híbrida ──► Re-ranking ──┐
Pregunta ──► Agente (tool calling)     (vectorial + BM25)                   ├──► LLM ──► Respuesta + citas
                                 └──► API de fraudes (conocimiento dinámico)┘

Evaluación · Ragas sobre golden set: faithfulness · answer relevancy · context precision · context recall
```

Los proveedores de LLM y de embeddings son intercambiables por configuración: OpenAI, Anthropic o AWS Bedrock para generación; OpenAI, Bedrock o HuggingFace local para embeddings.

## Estructura

```
app/
  api/         endpoints FastAPI (chat, ingest, health, mock)
  core/        chunking, embeddings, vectorstore, retriever, llm, agent
  services/    S3, API de fraudes, ingesta
  evaluation/  Ragas + golden set
  schemas/     modelos Pydantic
data/raw/      documentos a indexar
scripts/       CLI: ingest_documents, run_eval
tests/         pytest
docs/          arquitectura y despliegue en AWS
```

## Puesta en marcha

```bash
python -m venv .venv && source .venv/bin/activate   # .venv\Scripts\activate en Windows
pip install -r requirements.txt
cp .env.example .env                                # configurar proveedores y claves

# Indexar un documento con su metadata
python -m scripts.ingest_documents data/raw/manual_fraude_v2.md \
    --domain fraude_tecnologico --jurisdiction CO --effective-year 2024 --version v2 --no-s3

uvicorn app.main:app --reload --port 8000           # Swagger en /docs
```

O con Docker:

```bash
docker compose up --build
```

## API

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/health` | Estado del sistema y nº de chunks indexados |
| `POST` | `/ingest` | Sube un archivo y lo indexa con metadata |
| `POST` | `/chat` | Pregunta al agente RAG |
| `GET` | `/mock/fraud/{tx_id}` | Backend simulado de fraudes |

## Evaluación

```bash
python -m scripts.run_eval
```

Ejecuta el golden set contra el pipeline completo y reporta las cuatro métricas de Ragas. La evaluación está integrada desde el inicio, no añadida al final: cada cambio de modelo, de estrategia de chunking o de parámetros de recuperación se contrasta contra la misma línea base.

## Configuración

| Variable | Efecto |
|----------|--------|
| `LLM_PROVIDER` | `openai` · `anthropic` · `bedrock` |
| `EMBEDDING_PROVIDER` | `openai` · `bedrock` · `huggingface` (local) |
| `HYBRID_ALPHA` | 0 = solo BM25 · 1 = solo vectorial · 0.5 = balance |
| `RETRIEVAL_TOP_K` / `RERANK_TOP_N` | Tamaño del embudo de recuperación |

## Documentación

- **[docs/arquitectura.md](docs/arquitectura.md)** — cada capa del sistema, la razón técnica detrás de cada decisión, las alternativas descartadas, y cómo ejecutarlo, probarlo y evaluarlo.
- **[docs/despliegue-aws.md](docs/despliegue-aws.md)** — replicación completa en AWS con servicios gestionados: mapeo componente a componente, decisiones de arquitectura por capa, costos y desmontaje.
