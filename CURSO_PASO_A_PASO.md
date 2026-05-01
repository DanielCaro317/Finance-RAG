# 🎓 Curso Práctico: Construye tu Asistente Cognitivo Financiero (RAG) desde Cero

> **Propósito**: al terminar este curso serás capaz de **construir, depurar y
> defender** un sistema RAG corporativo end-to-end, escribiendo cada línea
> de código con tus propias manos y entendiendo el porqué de cada decisión.

> **Pre-requisitos**: saber qué es Python básico (variables, funciones, clases),
> haber instalado pip alguna vez. NO necesitas saber LLMs, vectores ni APIs.

> **Tiempo estimado**: 6–10 horas distribuidas. Ve a tu ritmo.

---

## 📑 Tabla de Contenidos

| # | Lección | Concepto principal |
|---|---------|--------------------|
| 0 | [Preparación del entorno](#módulo-0--preparación-del-entorno) | venv, pip, .env |
| 1 | [El problema y la solución (RAG conceptual)](#módulo-1--el-problema-que-resolvemos) | Por qué RAG existe |
| 2 | [Crear la estructura del proyecto](#módulo-2--estructura-del-proyecto) | Layout, paquetes Python |
| 3 | [Configuración y secretos](#módulo-3--configuración-y-secretos) | pydantic-settings, 12-factor |
| 4 | [Modelos de datos (Pydantic)](#módulo-4--modelos-de-datos) | Contratos, validación |
| 5 | [Chunking: el arte de cortar bien](#módulo-5--chunking-el-arte-de-cortar) | Splitters, overlap |
| 6 | [Embeddings: convertir texto a vectores](#módulo-6--embeddings) | Espacios vectoriales |
| 7 | [Vector Store: base de datos para vectores](#módulo-7--vector-store) | ChromaDB, similitud coseno |
| 8 | [Tu primer RAG mínimo (¡milestone!)](#módulo-8--milestone-1--rag-mínimo-funcional) | Pipeline end-to-end |
| 9 | [Recuperación híbrida (BM25 + vectorial)](#módulo-9--recuperación-híbrida) | Léxico vs semántico |
| 10 | [Re-ranking](#módulo-10--re-ranking) | LLM-as-a-judge interno |
| 11 | [LLM abstracto multi-proveedor](#módulo-11--capa-llm-abstracta) | Patrón Adapter |
| 12 | [Agente con tools (función calling)](#módulo-12--agente-con-tools) | ReAct, tool schemas |
| 13 | [Servicios externos (mock fraud + S3)](#módulo-13--servicios-externos) | httpx, boto3 |
| 14 | [Pipeline de ingesta](#módulo-14--pipeline-de-ingesta) | PDF/Markdown loaders |
| 15 | [API FastAPI completa](#módulo-15--api-fastapi-completa) | Routers, OpenAPI |
| 16 | [Evaluación con Ragas](#módulo-16--evaluación-con-ragas) | Métricas LLM-as-judge |
| 17 | [Docker y empaquetado](#módulo-17--docker) | Imágenes reproducibles |
| 18 | [Tests](#módulo-18--tests) | pytest, FastAPI TestClient |
| 19 | [Despliegue en AWS](#módulo-19--despliegue-en-aws) | ECR, ECS Fargate, S3 |
| 20 | [Hardening: seguridad, observabilidad, costos](#módulo-20--hardening) | Producción real |
| 21 | [Examen final + ejercicios extra](#módulo-21--examen-final) | Consolidación |

---

# Módulo 0 — Preparación del entorno

## Objetivo
Tener Python 3.11, un entorno virtual aislado, y un editor de código listo.

## Concepto: ¿qué es un entorno virtual y por qué?

Cuando instalas paquetes con `pip install`, se instalan **globalmente** en tu
máquina por defecto. Si trabajas en 5 proyectos a la vez, cada uno con
versiones distintas de las librerías, **se rompen entre sí**. Un *entorno
virtual* (`venv`) es una carpeta aislada con su propio Python y sus propios
paquetes.

**Regla de oro**: 1 proyecto = 1 venv. Siempre.

## Pasos

### 0.1 — Verifica Python
```bash
python --version
# Debe decir Python 3.10 o superior. Ideal 3.11.
```

Si no tienes Python:
- **Windows**: descarga desde https://www.python.org/downloads/ — marca *"Add Python to PATH"*.
- **macOS**: `brew install python@3.11`
- **Linux**: `sudo apt install python3.11 python3.11-venv`

### 0.2 — Crea la carpeta del proyecto
```bash
mkdir asistente_cognitivo_financiero
cd asistente_cognitivo_financiero
```

### 0.3 — Crea y activa el venv
```bash
# Windows:
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux:
python3.11 -m venv .venv
source .venv/bin/activate
```

Notarás que tu prompt cambia a `(.venv)`. Eso significa que estás dentro.

### 0.4 — Editor recomendado
- **VS Code** con la extensión "Python" oficial.
- Abre la carpeta: `code .`
- Selecciona el intérprete: `Ctrl+Shift+P` → "Python: Select Interpreter" → elige el de `.venv`.

## ✅ Checkpoint
- `python --version` → 3.10+
- Tu prompt empieza con `(.venv)`
- VS Code tiene seleccionado el intérprete del venv

## 🧠 Consejo
> Si en algún momento pip te pide instalar algo "globalmente" (sin venv activo),
> **detente**. Activa el venv primero. Esto te ahorrará semanas de pelea con
> versiones incompatibles.

---

# Módulo 1 — El problema que resolvemos

## La historia

Imagina que trabajas en un banco. Tienes:
- 200 manuales internos de prevención de fraude.
- 50 normativas regulatorias.
- Un equipo de analistas que cada día responde 100 preguntas: *"¿se puede
  aprobar esta transferencia?"*, *"¿qué dice la política sobre tarjetas
  prepago?"*, *"¿cómo bloqueo a este usuario?"*.

¿Y si cada analista pudiera **preguntarle a una IA** que responde citando
el manual exacto?

## Por qué NO sirve ChatGPT puro

Pídele a ChatGPT *"¿cuál es el monto máximo de transferencia internacional
sin aprobación según mi banco?"* — te inventará un número plausible. Eso
en banca = demanda multimillonaria.

Razones técnicas:
1. **No conoce tus datos privados** (no se entrenó con ellos).
2. **No puede auditarse**: ¿de dónde sacó esa cifra?
3. **Alucinaciones**: cuando no sabe, **inventa** con seguridad.

## La idea de RAG

**RAG = Retrieval-Augmented Generation**

```
Pregunta → BUSCAR fragmentos relevantes en TUS docs → INYECTARLOS al prompt → LLM responde
```

El LLM ya no inventa: **lee** los fragmentos y **resume** lo que dicen.
Si no encuentra nada relevante, debe decir "no sé".

## Por qué un AGENTE RAG

Un RAG simple **siempre busca**. Un agente decide:
- *"Esto es una pregunta de política → busco en docs."*
- *"Esto pregunta por una transacción específica → llamo a la API de fraudes."*
- *"Esto es saludo → respondo directo."*

Tener tools = poder integrar **conocimiento estático** (docs) + **conocimiento
dinámico** (APIs en tiempo real).

## ✅ Checkpoint mental
Antes de seguir, asegúrate de poder explicar **en voz alta**:
- Qué es RAG (3 letras, 3 fases).
- Por qué un LLM solo no basta para tu banco.
- Diferencia entre RAG simple y agente RAG.

---

# Módulo 2 — Estructura del proyecto

## Concepto: ¿por qué dividir en carpetas?

Un proyecto serio **no** es un solo archivo `main.py` de 5000 líneas. Lo
dividimos en módulos por responsabilidad. Esto no es burocracia — es lo
que hace que mañana puedas:
- Cambiar de OpenAI a Claude tocando 1 archivo.
- Probar `chunking.py` sin levantar la API entera.
- Que un compañero entienda en 5 min dónde añadir su feature.

## Layout estándar para apps RAG

```
asistente_cognitivo_financiero/
├── .env                  # Secretos (NO va a git)
├── .env.example          # Plantilla pública
├── .gitignore
├── requirements.txt      # Dependencias
├── README.md
├── app/                  # Tu código
│   ├── __init__.py
│   ├── main.py           # Punto de entrada FastAPI
│   ├── config.py         # Settings
│   ├── api/              # Endpoints HTTP
│   ├── core/             # Lógica RAG (chunking, embeddings, retriever, llm)
│   ├── services/         # Integraciones externas (S3, APIs)
│   ├── schemas/          # Modelos Pydantic
│   └── evaluation/       # Métricas
├── data/raw/             # Documentos a indexar
├── scripts/              # CLI tools
├── tests/                # Pytest
└── chroma_db/            # (Auto-generado) base vectorial
```

## Pasos

### 2.1 — Crea las carpetas
```bash
mkdir -p app/api app/core app/services app/schemas app/evaluation
mkdir -p data/raw data/processed scripts tests notebooks chroma_db
```

### 2.2 — Convierte cada subcarpeta de `app/` en paquete Python
Crea un archivo vacío `__init__.py` dentro de cada una:
```bash
# Crea archivos vacíos. En Windows usa: type nul > app/__init__.py
touch app/__init__.py app/api/__init__.py app/core/__init__.py
touch app/services/__init__.py app/schemas/__init__.py app/evaluation/__init__.py
touch tests/__init__.py
```

> **¿Qué hace `__init__.py`?** Le dice a Python "esta carpeta es un paquete".
> Sin él, no puedes hacer `from app.core import chunking`.

### 2.3 — Crea `.gitignore`
```gitignore
.env
__pycache__/
*.pyc
.venv/
chroma_db/
data/processed/
*.log
.vscode/
.idea/
.DS_Store
.pytest_cache/
```

### 2.4 — Crea `requirements.txt` mínimo
Por ahora solo lo esencial. Iremos añadiendo:
```
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic==2.9.2
pydantic-settings==2.6.1
python-dotenv==1.0.1
loguru==0.7.2
```

Instala:
```bash
pip install -r requirements.txt
```

## ✅ Checkpoint
```bash
python -c "import app; print('OK')"
# Debe imprimir: OK
```

## 🧠 Consejo
> Cuando crees un nuevo módulo, **antes** de codificarlo:
> 1. Pregúntate: ¿pertenece a `core/` (lógica del dominio) o `services/`
>    (integración externa) o `api/` (transporte HTTP)?
> 2. Si dudas, probablemente es `core/`.

---

# Módulo 3 — Configuración y secretos

## Concepto: 12-Factor App, Factor #3

Filosofía: **el código es el mismo en local, staging y prod**. Lo único
que cambia es la *configuración* (URLs, claves, flags). Por eso:

- Toda config viene de **variables de entorno**, no del código.
- En desarrollo se cargan desde un archivo `.env`.
- En producción vienen del entorno (ECS, K8s, Secrets Manager).

**Anti-patrón**: tener `if env == "prod": api_key = "abc"` en el código.
Si lo haces, te van a hackear.

## Por qué `pydantic-settings`

- **Validación de tipos**: si pones `RETRIEVAL_TOP_K=abc`, falla al
  arrancar (no después de 30 minutos en producción).
- **Centralización**: un solo objeto `Settings()` con todo.
- **IDE-friendly**: autocompletado.

## Pasos

### 3.1 — Crea `app/config.py`

Implementación detallada está en el archivo del proyecto. Lo importante:

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Literal, Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    llm_provider: Literal["openai", "anthropic", "bedrock"] = "openai"
    openai_api_key: Optional[str] = None
    retrieval_top_k: int = Field(default=10, ge=1, le=100)
    # ... etc

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
```

### 3.2 — Crea `.env.example`
Documenta TODAS las variables, con valores placeholders. Este archivo SÍ
va a git (es la plantilla).

### 3.3 — Crea `.env` (LOCAL ÚNICAMENTE)
Tu copia con valores reales.

> **Test mental**: ¿qué pasa si tu PC se infecta y exponen tu `.env`?
> Cualquier atacante tiene tus claves. Por eso:
> 1. Nunca subas `.env` a git.
> 2. Usa keys con scopes mínimos.
> 3. En prod usa Secrets Manager.

### 3.4 — Carga lazy con `@lru_cache`
`@lru_cache(maxsize=1)` hace que `Settings()` se construya **una sola vez**.
Las llamadas siguientes devuelven el mismo objeto. Es más eficiente y
también permite mockear en tests.

## 🧪 Ejercicio
Añade una variable nueva `MAX_UPLOAD_MB` con default 50, validada como
entero entre 1 y 500. Verifica que `Settings(MAX_UPLOAD_MB="abc")` falla.

## 🧠 Consejo
> Nunca leas `os.environ["X"]` esparcido por el código. Siempre pasa por
> `get_settings()`. Te ahorrará dolor el día que migres a Vault o
> Secrets Manager.

---

# Módulo 4 — Modelos de datos

## Concepto: contratos públicos

Pydantic define "schemas" — los **contratos** entre tu API y sus
consumidores. Si cambias un campo, **toda integración rompe**. Por eso
los modelos son tan importantes que merecen un módulo propio.

## La lección del caso LexisNexis

Mencionado en la masterclass: una empresa indexó documentos legales sin
metadata de **jurisdicción**. Cuando alguien de Texas preguntó sobre
herencias, el RAG le mezcló reglas de California. Resultado:
recomendaciones legalmente erróneas, y la empresa fue demandada.

**Lección**: los metadatos NO son opcionales. Diseña el schema antes de
indexar el primer documento.

## Pasos

### 4.1 — Crea `app/schemas/models.py`
Define al menos:

```python
class DocumentMetadata(BaseModel):
    source: str
    domain: str  # 'fraude_tecnologico' | 'tributario' | 'penal' | 'general'
    jurisdiction: Optional[str] = None
    effective_year: Optional[int] = None
    version: Optional[str] = None
    page: Optional[int] = None
    chunk_index: Optional[int] = None
```

### 4.2 — Modelos para los endpoints
```python
class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1)
    filters: Optional[dict] = None
    use_agent: bool = True

class Citation(BaseModel):
    source: str
    page: Optional[int]
    snippet: str

class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    latency_ms: int
```

### 4.3 — Validaciones útiles
- `Field(..., min_length=1)`: la `query` no puede ser vacía.
- `Field(default=10, ge=1, le=100)`: rango.
- `Literal["a", "b"]`: enum simple.

## 🧪 Ejercicio
Define un campo `confidence: float` con rango [0.0, 1.0]. Verifica que
`Citation(source="x", confidence=1.5)` falla.

## 🧠 Consejo
> Antes de codificar el endpoint, **dibuja el JSON** de request y
> response en papel. El schema en código sale solo después.

---

# Módulo 5 — Chunking: el arte de cortar

## Concepto

Los LLMs tienen ventana de contexto limitada (8K–200K tokens) y los
embeddings funcionan **mucho mejor** sobre fragmentos cortos y
cohesivos. El **chunking** divide tus documentos en pedazos digestibles.

## Estrategias

| Estrategia | Cómo corta | Cuándo usar |
|------------|-----------|-------------|
| **Fixed-size** | Cada N caracteres | ❌ Casi nunca |
| **Recursive** | Por separadores naturales (`\n\n`, `\n`, `. `, ` `) | ✅ Default |
| **Markdown-aware** | Por encabezados (#, ##, ###) | ✅ Para .md/HTML |
| **Semantic** | Por embeddings: corta donde el significado cambia | Documentos largos sin estructura |
| **Per-table / per-figure** | Una tabla = un chunk | Reportes financieros |

## Por qué fixed-size es trampa

```
Texto: "El monto máximo permitido para transferencias es de USD 10,000."
Cortado a 30 caracteres:
  Chunk 1: "El monto máximo permitido para"
  Chunk 2: " transferencias es de USD 10,0"
  Chunk 3: "00."
```

Los embeddings de esos chunks son **basura**. La semántica se rompió.

## Recursive (la opción segura)

Intenta cortar primero por `\n\n` (párrafo), luego `\n`, luego `. `,
luego ` `, y finalmente carácter. Así respeta el lenguaje natural
cuando puede.

## Parámetros clave

- **chunk_size**: 500–1500 caracteres típico. Más grande = más contexto
  por chunk pero menos precisión en búsqueda.
- **chunk_overlap**: 10–20% del size. Evita perder contexto en bordes.

```
Chunk 1: [................1000 chars................]
Chunk 2:                              [..150 overlap..|..1000 chars..]
```

## Pasos

### 5.1 — Añade dependencia
En `requirements.txt`:
```
langchain-text-splitters==0.3.2
```
`pip install -r requirements.txt`.

### 5.2 — Crea `app/core/chunking.py`
Usa `RecursiveCharacterTextSplitter` y `MarkdownHeaderTextSplitter` de
langchain (la lib es estable y bien probada).

### 5.3 — Test rápido en consola
```python
from app.core.chunking import chunk_text
chunks = chunk_text("Párrafo 1.\n\nPárrafo 2." * 50, chunk_size=200)
print(len(chunks))   # Debería ser > 1
print(chunks[0].text)
```

## 🧪 Ejercicio
Toma un PDF tuyo. Pruébalo con chunk_size=200 vs 1500. Lee 3 chunks de
cada caso. ¿Cuáles preservan mejor el sentido?

## 🧠 Consejo
> El chunking malo se manifiesta en respuestas tipo "no sé" cuando la
> info SÍ está en el corpus. Si tu RAG falla mucho, **revisa chunking
> antes que el modelo**.

---

# Módulo 6 — Embeddings

## Concepto

Un **embedding** es un vector de N dimensiones (típicamente 384–3072)
que representa el "significado" de un texto. Textos parecidos quedan
cerca en ese espacio vectorial. Es magia matemática, pero se entiende
con un ejemplo:

```
"transferencia bancaria" → [0.21, -0.05, 0.87, ...]
"giro de dinero"          → [0.20, -0.03, 0.85, ...]   ← muy cerca
"receta de pizza"         → [-0.91, 0.12, 0.08, ...]   ← lejos
```

La **similitud coseno** entre vectores mide qué tan parecidos son
(1.0 = idénticos, 0.0 = ortogonales).

## ¿Por qué no usar TF-IDF / búsqueda por palabras?

TF-IDF compara **palabras exactas**. Si la pregunta dice "transferencia"
y el doc dice "giro", TF-IDF los considera distintos. Los embeddings
los unifican porque comparten significado.

## Proveedores

| Proveedor | Modelo | Dim | $/1M tokens | Multilingüe |
|-----------|--------|-----|-------------|-------------|
| OpenAI | `text-embedding-3-small` | 1536 | $0.02 | ✓ |
| OpenAI | `text-embedding-3-large` | 3072 | $0.13 | ✓ |
| AWS Bedrock | `amazon.titan-embed-text-v2:0` | 1024 | barato | ✓ |
| HuggingFace local | `all-MiniLM-L6-v2` | 384 | GRATIS | ✗ (solo EN) |
| HuggingFace local | `multilingual-e5-large` | 1024 | GRATIS | ✓ |

**Para empezar**: `text-embedding-3-small`. Bueno, barato, multilingüe.

## REGLA CRÍTICA

> **Mismo modelo para indexar y consultar.** Si indexaste con
> `embedding-3-small` y consultas con `embedding-3-large`, los vectores
> viven en espacios distintos y la búsqueda devuelve **ruido**.
> Si cambias el modelo, **re-indexas todo**.

## Pasos

### 6.1 — Añade dependencias
```
openai==1.54.0
boto3==1.35.55
```

### 6.2 — Patrón Adapter para multi-proveedor

Crea una clase abstracta `EmbeddingProvider` con método `embed(texts)`.
Tres implementaciones: `OpenAIEmbeddings`, `BedrockEmbeddings`,
`HuggingFaceEmbeddings`. Una factory `build_embedding_provider()` que
lee de settings y devuelve la correcta.

**Por qué**: cuando cambies de proveedor, **no tocas el resto del
código**. Solo el `.env`.

### 6.3 — Test
```python
from app.core.embeddings import build_embedding_provider
emb = build_embedding_provider()
vecs = emb.embed(["hola mundo", "ciao mondo"])
print(len(vecs))           # 2
print(len(vecs[0]))        # 1536 (si openai-small)
```

## 🧪 Ejercicio
Calcula la similitud coseno entre embeddings de:
- "Cuál es el monto máximo de transferencia"
- "¿Hasta cuánto puedo enviar al exterior?"
- "Receta de pizza"

```python
import numpy as np
def cosine(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
```
Verifica que las dos primeras tienen similitud ~0.7+ y la tercera <0.3.

## 🧠 Consejo
> Antes de gastar dinero en embeddings caros (`-large`), prueba con
> `-small` y mide. La diferencia de calidad rara vez vale 6.5x el costo.

---

# Módulo 7 — Vector Store

## Concepto

Una **vector database** guarda tuplas `(id, vector, metadata, texto)` y
permite consultas tipo: "dame los K vectores más cercanos a este vector
de consulta, opcionalmente con filtro de metadata".

## Opciones

| DB | Persistencia | Filtros metadata | Servidor | Cuando |
|----|--------------|-------------------|----------|--------|
| **ChromaDB** | Sí (disco) | ✓ | No | Empezar / single-node |
| **FAISS** | Manual | Limitado | No | Velocidad pura |
| **PGVector** | Sí (Postgres) | ✓ JOIN SQL | Sí | Producción si ya hay Postgres |
| **OpenSearch** | Sí | ✓ + BM25 nativo | Sí | Empresa AWS |
| **Pinecone / Qdrant** | Cloud SaaS | ✓ | Cloud | No quieres operar |

**Empezamos con ChromaDB** porque cero setup.

## Métricas de distancia

- **Coseno** (`cosine`): default para texto. Compara dirección, ignora magnitud.
- **L2** (euclidiana): distancia geométrica.
- **IP** (inner product): producto punto. Equivalente a coseno si los
  vectores están normalizados.

## Pasos

### 7.1 — Añade dependencia
```
chromadb==0.5.20
```

### 7.2 — Crea `app/core/vectorstore.py`

Clase `VectorStore` con métodos:
- `add(ids, texts, embeddings, metadatas)`
- `query(embedding, top_k, where=None) → list[RetrievedChunk]`
- `count()`
- `all_documents()` (para BM25)

Usa `chromadb.PersistentClient(path=...)` para que sobreviva reinicios.

### 7.3 — Filtros con `where`

ChromaDB acepta filtros tipo MongoDB:
```python
store.query(emb, top_k=10, where={"domain": "fraude_tecnologico"})
store.query(emb, top_k=10, where={"effective_year": {"$gte": 2023}})
```

Esto es **clave** para el problema LexisNexis: cuando el usuario
pregunta sobre fraude en CO, filtras por `jurisdiction == "CO"`.

### 7.4 — Test
```python
from app.core.vectorstore import get_vector_store
from app.core.embeddings import build_embedding_provider

store = get_vector_store()
emb = build_embedding_provider()

texts = ["transferencia bancaria internacional", "receta de pizza"]
vectors = emb.embed(texts)
store.add(
    ids=["t1", "t2"],
    texts=texts,
    embeddings=vectors,
    metadatas=[{"source":"test","domain":"finanzas"},{"source":"test","domain":"comida"}]
)

q = emb.embed(["envío de dinero al exterior"])[0]
results = store.query(q, top_k=2)
print(results[0].text)  # Debería ser la transferencia, no la pizza
```

## 🧠 Consejo
> Una collection grande con todo mezclado se vuelve ruidosa. Mejor
> varias collections enfocadas (una por dominio) o una collection con
> filtros de metadata bien usados.

---

# Módulo 8 — Milestone 1: RAG mínimo funcional

## Objetivo

¡Tu primer RAG end-to-end! Aún sin agente, sin reranker, sin API.
Solo: pregunta → busca → contesta.

## Script de prueba

Crea `scripts/demo_rag_minimo.py`:

```python
from app.core.embeddings import build_embedding_provider
from app.core.vectorstore import get_vector_store
from openai import OpenAI

# 1) Indexa un texto de ejemplo
store = get_vector_store()
emb = build_embedding_provider()

texts = [
    "El monto máximo de transferencia internacional sin aprobación es USD 10,000.",
    "Las tarjetas prepago tienen un límite mensual de recarga de USD 5,000.",
    "La política de bloqueo se activa cuando el score de riesgo supera 85.",
]
vecs = emb.embed(texts)
store.add(
    ids=[f"d{i}" for i in range(3)],
    texts=texts,
    embeddings=vecs,
    metadatas=[{"source":"manual","domain":"fraude"}]*3,
)

# 2) Consulta
query = "¿Cuál es el monto máximo de transferencia?"
q_vec = emb.embed([query])[0]
results = store.query(q_vec, top_k=2)

contexto = "\n".join(r.text for r in results)

# 3) LLM redacta
client = OpenAI()  # toma la API key del .env / os.environ
prompt = f"Contexto:\n{contexto}\n\nPregunta: {query}\nResponde solo con base en el contexto."
resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role":"user","content":prompt}],
    temperature=0.0,
)
print(resp.choices[0].message.content)
```

Ejecuta:
```bash
python -m scripts.demo_rag_minimo
```

Si responde "USD 10,000" citando el contexto: **🎉 acabas de hacer tu
primer RAG**. Todo lo demás es mejora.

## ✅ Checkpoint
- Entiendes las 3 fases (embed → store/query → LLM con contexto).
- Ejecutaste el script y funcionó.

## 🧠 Consejo
> Cada vez que añadas una capa nueva (reranker, agente, etc.), antes
> verifica que el RAG mínimo sigue funcionando. Es tu safety net.

---

# Módulo 9 — Recuperación híbrida

## El problema

La búsqueda vectorial es brillante con sinónimos pero **falla** con:
- IDs exactos: `"TX-12345"`, `"artículo 234-A"`.
- Acrónimos raros: `"UAFI"`, `"NQTC"`.
- Términos hiper-específicos del dominio.

¿Por qué? Porque esos tokens raros tienen embeddings poco discriminantes.

## La solución: BM25 + vectorial = híbrida

**BM25** es búsqueda por palabras (algoritmo clásico, robusto). Brilla
exactamente donde la vectorial flaquea.

**Score híbrido**:
```
score = α * score_vectorial + (1 - α) * score_bm25
```
con α ∈ [0, 1] configurable. Default 0.5 = balanceado.

## Por qué normalizar

Los scores vectoriales están en [0, 1]; los de BM25 son arbitrarios.
**Normaliza antes de combinar** (divide por el máximo), si no, BM25
domina sin querer.

## Pasos

### 9.1 — Dependencia
```
rank-bm25==0.2.2
```

### 9.2 — Crea `app/core/retriever.py`

Clase `HybridRetriever`:
- En el constructor toma `vector_store`, `embedder`, `alpha`.
- Método `retrieve(query, top_k, where=None)`:
  1. Embedea query.
  2. Ejecuta búsqueda vectorial → top_k candidatos.
  3. Ejecuta BM25 sobre todo el corpus → top_k candidatos.
  4. Normaliza ambos scores.
  5. Combina (suma ponderada). Dedup por texto.
  6. Devuelve top_k del merge.

### 9.3 — BM25 en memoria

Cargas todo el corpus de Chroma a memoria y construyes el índice BM25.
Esto **no escala** a millones de chunks. Para eso usa OpenSearch.

### 9.4 — Test comparativo

Crea documentos con códigos exactos. Pregunta por uno. Compara:
- Solo vectorial: ¿lo encuentra?
- Solo BM25: ¿lo encuentra?
- Híbrida: ¿lo encuentra mejor?

## 🧪 Ejercicio
Cambia `HYBRID_ALPHA` de 0.5 a 0.0 (puro BM25), 1.0 (puro vectorial),
0.7. ¿Cómo cambia la calidad para distintas preguntas?

## 🧠 Consejo
> En la práctica, α=0.5–0.7 funciona bien. Si tu corpus es muy técnico
> con muchos códigos, baja a 0.3 (más BM25). Si es prosa libre, sube a 0.7.

---

# Módulo 10 — Re-ranking

## Por qué

El retriever te trae los top-K (digamos 10). De esos, quizás solo 3-4
son **realmente** relevantes; los otros son ruido. Mandar los 10 al
LLM = más tokens (más caro) y posible confusión.

**Reranking**: un segundo modelo, más preciso pero más caro, evalúa
**query + candidato juntos** y reordena. De ahí pasamos solo los top-N
(3-4) al LLM final.

## Tipos de reranker

| Tipo | Ejemplo | Costo | Velocidad |
|------|---------|-------|-----------|
| **Cross-encoder** | `BAAI/bge-reranker-base` | Local, gratis | Rápido |
| **Cohere Rerank API** | `rerank-multilingual-v3.0` | $/llamada | Muy rápido |
| **LLM-as-reranker** | GPT-4o califica candidatos | Caro | Lento |

Para empezar, usaremos **LLM-as-reranker** (didáctico, sin dependencias
extra). En producción cambia a cross-encoder.

## Pasos

### 10.1 — Función `llm_rerank(query, candidates, top_n, llm_call)`

Construye un prompt:
```
PREGUNTA: ...
PASAJES:
[0] ...
[1] ...
[2] ...

Devuelve los índices de los top {top_n} más relevantes, separados por coma.
```

Parsea la respuesta con regex `\d+`. **Sé defensivo** — si el LLM
devuelve algo raro, fallback a `candidates[:top_n]`.

### 10.2 — Integración con HybridRetriever

```python
candidates = retriever.retrieve(query, top_k=10)
top4 = llm_rerank(query, candidates, top_n=4, llm_call=...)
```

## 🧠 Consejo
> Si la latencia te importa (>500ms te molesta), salta directamente a
> cross-encoder. El LLM-reranker es genial para entender el concepto
> pero añade ~1-3 segundos.

---

# Módulo 11 — Capa LLM abstracta

## Concepto: patrón Adapter

OpenAI, Anthropic y Bedrock tienen APIs **distintas**:
- Mensajes: `{role:..., content:...}` vs `system="..."` separado.
- Tools: schema diferente cada uno.
- Streaming: distinto formato.

Si llenas tu código de `if provider == "openai"`, te ahogas. Solución:
**una clase abstracta** `LLMProvider` con la misma interfaz, y N
implementaciones que **traducen** internamente.

## Diseño

```python
class LLMProvider(ABC):
    @abstractmethod
    def chat(self, system: str, user: str,
             tools: Optional[list]=None,
             temperature: float=0.1) -> dict:
        """Devuelve {'content': str, 'tool_calls': list}"""
```

## Por qué temperatura baja en RAG

Temperatura controla la aleatoriedad:
- **0.0**: determinista. Mismo input → mismo output.
- **1.0+**: muy creativo. Cada respuesta distinta.

En RAG quieres **fidelidad**, no creatividad. Default `0.1`. Si quieres
respuestas idénticas para mismo input → `0.0`.

## Pasos

### 11.1 — Crea `app/core/llm.py`

Implementa:
- `OpenAIChatLLM`
- `AnthropicChatLLM`
- `BedrockChatLLM`

Cada uno traduce el formato `tools` (que estandarizamos al estilo OpenAI)
al formato de su API. La conversión es lineal:

```python
# OpenAI: {"function": {"name", "description", "parameters"}}
# Anthropic: {"name", "description", "input_schema"}
# Bedrock-Claude: igual a Anthropic + anthropic_version
```

### 11.2 — Factory `build_llm_provider()`

Lee settings y devuelve el correcto. Mismo patrón que embeddings.

## 🧠 Consejo
> Mantén la interfaz `chat()` lo más mínima posible. Cada feature
> exótica de un proveedor que añadas a la interfaz, te obliga a
> implementarla en TODOS los proveedores.

---

# Módulo 12 — Agente con tools

## Concepto: ReAct (Reason + Act)

Un agente sigue este loop:

```
1. LLM recibe: pregunta + tools disponibles.
2. LLM decide:
   a) Responder texto → fin.
   b) Llamar tool X con args Y → ejecuta tool → resultado va al contexto → vuelve a 1.
3. Cota: máximo N iteraciones (evita loops).
```

## ¿Cómo el LLM "decide" llamar tools?

Le pasas a la API una lista de funciones disponibles con sus schemas:
```json
[{
  "type": "function",
  "function": {
    "name": "search_policies",
    "description": "Busca en políticas internas...",
    "parameters": {
      "type": "object",
      "properties": {"query": {"type":"string"}},
      "required": ["query"]
    }
  }
}]
```

El LLM, entrenado en función calling, devuelve `tool_calls=[{name, arguments}]`
en vez de texto cuando decide invocar. Tú ejecutas la función y le pasas
el resultado en una segunda llamada.

## Diseño de tools

Para nuestro asistente:
1. `search_policies(query, domain?, min_year?)` — busca en KB.
2. `lookup_fraud_status(transaction_id)` — consulta API en tiempo real.

**Reglas para diseñar tools**:
- **Nombre claro y verbo**: `get_X`, `search_X`, `create_X`.
- **Description** detallada: el LLM la lee para decidir cuándo usarla.
- **Parámetros tipados** con descriptions.
- **Required** explícito.

## El SYSTEM_PROMPT

Es la "constitución" del agente. **Ejemplo bueno**:
```
Eres un asistente financiero corporativo.

REGLAS:
1. Responde SOLO con base en información recuperada por las herramientas.
2. Si no tienes evidencia, di "No encontré información suficiente".
3. Cita fuentes con [source:page].
4. Si la pregunta es sobre transacción específica → usa lookup_fraud_status.
5. Si es sobre políticas → usa search_policies.
6. NO inventes números, fechas, ni nombres de regulaciones.
```

## Pasos

### 12.1 — Crea `app/core/agent.py`

Clase `FinancialAgent`:
- `__init__(llm, retriever)`
- `_execute_tool(name, args)`: dispatcher.
- `_tool_search(args)`: integra retriever + reranker.
- `_tool_fraud(args)`: llama al servicio.
- `run(query) → {answer, chunks, tools}`: orquesta.

### 12.2 — Loop simplificado (didáctico)

Por simpleza implementamos:
1. Llamada 1: LLM con tools.
2. Si pidió tools → ejecutamos todas.
3. Llamada 2: LLM con resultados → respuesta final.

Para producción serio, considera **LangGraph** (DAGs con estado).

### 12.3 — Función helper `answer_with_rag(query, use_agent=True)`

Si `use_agent=False`: RAG simple (siempre busca).
Si `use_agent=True`: deja al LLM decidir.

## 🧪 Ejercicio
Añade una tool `compute_fx(amount, from, to)` que convierte monedas.
Pregunta al agente "¿cuánto son 5000 USD en COP?" y observa.

## 🧠 Consejo
> Más tools NO siempre es mejor. Si tienes 20 tools, el LLM se confunde.
> Mantén ≤ 8 tools y describe BIEN cuándo usar cada una.

---

# Módulo 13 — Servicios externos

## El servicio de fraudes (mock)

En vez de pelear con un backend real para aprender, **simulamos** uno
con un endpoint que genera respuestas deterministas pseudo-aleatorias
basadas en hash del ID.

`/mock/fraud/{tx_id}` → `{status, risk_score, amount, currency, country}`.

Cuando despliegues real, reemplazas la URL en `.env` por la del backend
real. **Sin tocar el agente**.

## S3 con boto3

Para guardar los originales (PDFs, etc.):
```python
import boto3
s3 = boto3.client("s3", region_name=..., aws_access_key_id=..., ...)
s3.upload_file(local_path, bucket, key)
```

**Buenas prácticas**:
- Bucket privado, nunca público.
- SSE-S3 (cifrado en reposo) activado.
- Versioning si los datos son regulados.
- IAM roles en prod, no claves estáticas.

## Pasos

### 13.1 — `app/services/fraud_api.py`
Cliente httpx con timeout 5s. Manejo de errores.

### 13.2 — `app/services/s3_service.py`
Función `upload_file(local_path, key)` que devuelve URI o None si falla.
**Que falle "suave"**: si S3 cae, la ingesta sigue en local.

### 13.3 — `app/api/routes_mock.py`
Endpoint mock que vive en la misma app, así no necesitas levantar otro servicio.

## 🧠 Consejo
> Servicios externos = puntos de fallo. SIEMPRE timeout, SIEMPRE
> manejo de excepciones, SIEMPRE plan B (mensaje de error útil).

---

# Módulo 14 — Pipeline de ingesta

## Las 7 fases

```
1. Cargar archivo (PDF/MD/DOCX/TXT)
2. Extraer texto plano
3. Chunking según tipo
4. Generar embeddings (batch)
5. Guardar en vector DB con metadata rica
6. Subir original a S3 (auditoría)
7. Invalidar índice BM25
```

## Lectores por tipo

| Extensión | Librería |
|-----------|----------|
| `.pdf` | `pypdf` (texto) o `unstructured` (tablas) |
| `.docx` | `python-docx` |
| `.md`, `.txt` | open() |
| `.html` | `BeautifulSoup` |

Para PDFs complejos (escaneados, tablas): **AWS Textract**, **LlamaParse**,
o **unstructured** con OCR.

## Idempotencia

Si re-ingieres el mismo archivo, **NO** debe duplicar chunks. Solución:
- ID determinista: `md5(filename + version)[:12]`.
- Usa `upsert` en vez de `insert`.

## Versionado de documentos

Cuando un manual se actualiza:
- ❌ NO borres la versión vieja.
- ✅ Ingiere la nueva con `version="v2"`.
- ✅ En consulta, filtra `version == "v2"`.
- Beneficios: auditoría histórica, capacidad de "diff" entre versiones.

## Pasos

### 14.1 — Dependencias
```
pypdf==5.1.0
python-docx==1.1.2
beautifulsoup4==4.12.3
```

### 14.2 — Crea `app/services/ingestion.py`

Función `ingest_file(path, domain, jurisdiction, effective_year, version, upload_to_s3)`.
Implementa las 7 fases.

### 14.3 — CLI `scripts/ingest_documents.py`

```python
python -m scripts.ingest_documents data/raw/manual.pdf --domain fraude --version v2
python -m scripts.ingest_documents data/raw/  # carpeta entera
```

## 🧪 Ejercicio
Ingesta el mismo archivo 2 veces. Verifica con `/health` que el conteo
NO se duplica.

## 🧠 Consejo
> Loggea siempre nombre, n° chunks y latencia de cada ingesta. Cuando
> algo falla en producción, esto te salva la vida.

---

# Módulo 15 — API FastAPI completa

## Por qué FastAPI

- Tipado fuerte → menos bugs.
- Documentación OpenAPI automática (`/docs`).
- Async nativo → alta concurrencia.
- Pydantic integrado.

## Estructura de routers

Un router por dominio:
- `routes_health.py` → `/health`
- `routes_chat.py` → `/chat`
- `routes_ingest.py` → `/ingest`, `/ingest/stats`
- `routes_mock.py` → `/mock/fraud/{id}`

## Pasos

### 15.1 — Dependencias
```
fastapi==0.115.0
uvicorn[standard]==0.32.0
python-multipart==0.0.12   # Para uploads
httpx==0.27.2
```

### 15.2 — Crea cada `routes_*.py`

Patrón:
```python
from fastapi import APIRouter
router = APIRouter(tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    ...
```

### 15.3 — Crea `app/main.py`

```python
def create_app() -> FastAPI:
    app = FastAPI(title="...", version="0.1.0")
    app.add_middleware(CORSMiddleware, ...)
    app.include_router(routes_health.router)
    app.include_router(routes_chat.router)
    ...
    return app

app = create_app()
```

### 15.4 — Levanta

```bash
uvicorn app.main:app --reload --port 8000
```

Abre http://localhost:8000/docs — verás Swagger con todos los endpoints
documentados automáticamente.

## CORS — punto de cuidado

CORS abierto (`allow_origins=["*"]`) está bien en local. **NUNCA en
producción** — solo permite tus dominios reales.

## 🧠 Consejo
> Antes de añadir un nuevo endpoint, **piensa si es un nuevo router**.
> Más de 3 endpoints relacionados ya merecen archivo propio.

---

# Módulo 16 — Evaluación con Ragas

## Por qué evaluar

Sin métricas, no sabes si tu cambio "mejoró" o "empeoró". El LLM siempre
suena confiado. Necesitas datos.

## Las 4 métricas Ragas

| Métrica | Qué mide | Penaliza |
|---------|----------|----------|
| **faithfulness** | ¿La respuesta está respaldada por los chunks? | Alucinaciones |
| **answer_relevancy** | ¿Aborda la pregunta? | Divagaciones |
| **context_precision** | ¿Los chunks relevantes están primero? | Ruido en top |
| **context_recall** | ¿Se recuperaron los chunks necesarios? | Retriever malo |

Las primeras 3 NO necesitan ground truth (LLM-as-judge). La cuarta sí.

## Golden set

Lista curada de `(pregunta, respuesta_esperada)`. **Empieza con 20-50
preguntas REALES** de usuarios. Versionarla en git.

**Incluye preguntas trampa**: temas que NO están en tu corpus. Si tu
RAG no dice "no sé", está alucinando.

## Pasos

### 16.1 — Dependencias
```
ragas==0.2.6
datasets==3.1.0
```

### 16.2 — `app/evaluation/dataset.py`
```python
GOLDEN_SET = [
    {"question": "...", "ground_truth": "..."},
    ...
]
```

### 16.3 — `app/evaluation/ragas_eval.py`
Carga golden set, ejecuta RAG en cada uno, construye `Dataset` de Hugging
Face, llama a `ragas.evaluate(...)`.

### 16.4 — Script CLI

```bash
python -m scripts.run_eval
```

## Cómo interpretar

| Métrica | Bueno | Mediocre | Malo |
|---------|-------|----------|------|
| faithfulness | >0.90 | 0.80-0.90 | <0.80 |
| answer_relevancy | >0.85 | 0.75-0.85 | <0.75 |
| context_precision | >0.80 | 0.65-0.80 | <0.65 |
| context_recall | >0.80 | 0.65-0.80 | <0.65 |

Si `faithfulness < 0.80` → baja temperatura, refuerza system prompt,
mejora chunks.

Si `context_recall < 0.65` → retriever falla. Aumenta `top_k`, ajusta
`alpha`, revisa chunking.

## 🧠 Consejo
> Ejecuta evaluación **antes** de cualquier cambio mayor (modelo,
> chunking, prompt). Compara antes/después con números, no opiniones.

---

# Módulo 17 — Docker

## Por qué

Un Dockerfile garantiza que tu app corre **igual** en tu laptop, en
ECS, en el server de un compañero. "Funciona en mi máquina" deja de
ser excusa.

## El Dockerfile mínimo

```dockerfile
FROM python:3.11-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Cache layer: copiamos requirements ANTES del código
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY scripts ./scripts

# Usuario no-root
RUN useradd -u 1000 -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Por qué slim, no full

`python:3.11-slim` ≈ 130 MB. `python:3.11` ≈ 1 GB. La diferencia
multiplica costo de almacenamiento y tiempo de despliegue.

## Por qué usuario no-root

Si la app tiene un RCE (remote code execution), el atacante hereda los
privilegios del proceso. Root → game over. UID 1000 → daño contenido.

## docker-compose para dev

```yaml
services:
  api:
    build: .
    ports: ["8000:8000"]
    env_file: [.env]
    volumes:
      - ./chroma_db:/app/chroma_db   # persistencia local
      - ./data:/app/data
```

## Pasos

### 17.1 — Crea `Dockerfile`
### 17.2 — Crea `docker-compose.yml`
### 17.3 — Construye y corre
```bash
docker compose up --build
```

### 17.4 — Verifica
```bash
curl http://localhost:8000/health
```

## 🧠 Consejo
> Multi-stage builds (otra capa para compilar, otra para correr) son
> útiles cuando tienes builds grandes (ej. C extensions). En Python
> puro, slim solo basta.

---

# Módulo 18 — Tests

## Pirámide de tests

```
       /\        (1) Smoke: ¿la app arranca?
      /  \       (2) Unit: cada función aislada
     /----\      (3) Integration: piezas juntas (con mocks)
    /------\     (4) E2E: producción real (caro, lento)
```

Para RAG, prioriza:
- Smoke tests rápidos (no llaman LLM).
- Unit tests de chunking, parsing, transforms.
- Integration tests del retriever (con embeddings mockeados).
- E2E ocasionales (caros: cada uno = $).

## Pasos

### 18.1 — Dependencia
```
pytest==8.3.3
httpx==0.27.2
```

### 18.2 — `tests/test_smoke.py`

```python
from fastapi.testclient import TestClient

def test_health():
    from app.main import app
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
```

### 18.3 — Test de chunking
```python
def test_chunking_recursive():
    from app.core.chunking import chunk_text
    text = "Frase uno.\n\nFrase dos." * 30
    chunks = chunk_text(text, chunk_size=200, chunk_overlap=50)
    assert len(chunks) > 1
```

### 18.4 — Ejecuta
```bash
pytest -q
```

## 🧠 Consejo
> Si un test depende del LLM real, **márcalo** (`@pytest.mark.slow`) y
> ejecútalo solo en CI nocturno. Tus tests rápidos deben correr en <10s.

---

# Módulo 19 — Despliegue en AWS

## Arquitectura objetivo

```
Internet → Route53 → CloudFront → ALB (HTTPS) → ECS Fargate Service
                                                   │
                                                   ├── ECR (imagen)
                                                   ├── Secrets Manager (API keys)
                                                   ├── CloudWatch Logs
                                                   ├── S3 (originales)
                                                   └── RDS Postgres + pgvector (opcional)
```

## Pasos clave (resumen — cada uno tiene su sub-curso)

### 19.1 — Empuja imagen a ECR
```bash
aws ecr create-repository --repository-name asistente-rag --region us-east-1
$(aws ecr get-login-password --region us-east-1 | docker login \
    --username AWS --password-stdin <ID>.dkr.ecr.us-east-1.amazonaws.com)
docker build -t asistente-rag .
docker tag asistente-rag:latest <ID>.dkr.ecr.us-east-1.amazonaws.com/asistente-rag:latest
docker push <ID>.dkr.ecr.us-east-1.amazonaws.com/asistente-rag:latest
```

### 19.2 — Crea bucket S3
```bash
aws s3 mb s3://mi-banco-rag-prod --region us-east-1
aws s3api put-bucket-encryption --bucket mi-banco-rag-prod \
    --server-side-encryption-configuration '...'
aws s3api put-bucket-versioning --bucket mi-banco-rag-prod \
    --versioning-configuration Status=Enabled
```

### 19.3 — Guarda secretos en Secrets Manager
```bash
aws secretsmanager create-secret --name openai/api-key --secret-string "sk-..."
```

En la task definition de ECS, referenciás:
```json
"secrets": [{"name": "OPENAI_API_KEY", "valueFrom": "arn:aws:secretsmanager:..."}]
```

### 19.4 — Task definition + Service ECS

CPU 1 vCPU, RAM 2GB para empezar. Auto-scaling en CPU > 70% o requests/min.

### 19.5 — ALB con HTTPS

Certificado en ACM (gratis), apunta dominio en Route53, HTTPS forzado.

### 19.6 — Logs y alarmas en CloudWatch

- Log group `/ecs/asistente-rag`.
- Alarmas: 5xx > 1% en 5 min, latencia P99 > 3s, **costo LLM diario > $X**.

## 🧠 Consejo
> Antes de pasar a prod, corre **load tests** (k6 / locust) con tráfico
> realista. Mide latencia, costo por request, fallos.

---

# Módulo 20 — Hardening

## Seguridad

| Riesgo | Mitigación |
|--------|------------|
| **Prompt injection** | Sanitiza input, usa system prompts robustos, considera GuardrailsAI |
| **PII leak en logs** | Redacta antes de loggear (regex de cédulas, tarjetas) |
| **API keys filtradas** | Secrets Manager, nunca en código, rota periódicamente |
| **DoS** | Rate limiting (slowapi), timeouts, presupuesto LLM por usuario |
| **Acceso no autorizado** | Auth (JWT), RBAC en filtros de retrieval |

## Observabilidad

- **Logs estructurados** (JSON), no print().
- **Métricas**: latencia p50/p95/p99, requests/min, errors/min, tokens consumidos.
- **Tracing**: OpenTelemetry o LangSmith — ver TODA la cadena de un request.

```python
import langsmith
# Auto-instrumenta llamadas a OpenAI/Anthropic.
```

## Costos

Top sources de costo:
1. **Embeddings** en ingesta masiva.
2. **LLM en /chat** (especialmente con reranker LLM).
3. **Bedrock** si lo usas a tope.

Optimizaciones:
- **Caché de embeddings**: hash el texto, no re-embedees lo mismo.
- **Caché de respuestas**: queries idénticas repetidas → Redis.
- **Modelo más barato**: gpt-4o-mini suele bastar.
- **Reduce chunks al LLM**: rerank a top 3-4, no 10.

## Resilencia

- **Retries con backoff** para 429/5xx.
- **Circuit breaker** para servicios externos (no martilles uno caído).
- **Health checks** profundos: ¿LLM responde? ¿VectorDB responde?

## 🧠 Consejo
> El día que tu app entra a producción, programa una "post-mortem
> review" 1 mes después. Mira métricas reales, no proyecciones.

---

# Módulo 21 — Examen final

## Preguntas de comprensión

Responde **sin** mirar la guía:

1. ¿Por qué chunking malo es la causa #1 de RAGs malos?
2. ¿Por qué BÚSQUEDA HÍBRIDA supera a la pura vectorial?
3. ¿Qué metadata es **mínima** indispensable para evitar el caso LexisNexis?
4. ¿Qué métrica Ragas detecta alucinaciones? ¿Cómo se calcula?
5. ¿Por qué `temperature=0.1` en RAG? ¿Y `0.0`?
6. ¿Qué hace `@lru_cache(maxsize=1)` en `get_settings()`?
7. ¿Por qué un agente puede ser MEJOR o PEOR que RAG simple?
8. ¿Qué puede salir mal si tu reranker es LLM-based y tienes alta latencia?
9. ¿Cuál es la diferencia entre **upsert** e **insert** y por qué importa en ingesta?
10. ¿Por qué corremos el contenedor con usuario no-root?

## Ejercicios prácticos

### E1 — Multi-jurisdicción
Indexa el mismo manual con dos versiones (CO 2022 y MX 2024). Pregunta
en español: el agente debe responder con la versión CO si filtras por
jurisdicción CO.

### E2 — Tool nueva
Añade una tool `compute_risk_score(transaction)` que toma un dict con
amount/country/hour y devuelve un score 0-100. Integra al agente.

### E3 — Cambio de proveedor
Cambia `LLM_PROVIDER=anthropic` y ejecuta sin tocar código. Verifica
que todo sigue funcionando. Repite con `bedrock`.

### E4 — Cross-encoder reranker
Reemplaza `llm_rerank()` por uno que use `sentence-transformers/cross-encoder`.
Mide diferencia de latencia y calidad (Ragas).

### E5 — Streaming
Modifica `/chat` para devolver Server-Sent Events token a token. El
cliente debe ver la respuesta "escribiéndose".

### E6 — Caché semántico
Antes de llamar al LLM, busca si una pregunta MUY parecida (sim > 0.95)
ya tiene respuesta en Redis. Si sí, devuélvela directamente.

### E7 — Rate limiting
Con `slowapi`, limita `/chat` a 10 requests/min por IP. Verifica que el
request 11 recibe 429.

### E8 — RBAC en retrieval
Añade un campo `allowed_roles: list[str]` en metadata. En `/chat`,
recibe `X-User-Role` header. Filtra chunks donde el rol esté permitido.

### E9 — Métricas Prometheus
Expone `/metrics` con conteo de requests, latencia (histograma) y
tokens consumidos.

### E10 — Despliegue real
Sube tu imagen a ECR, crea task ECS, expón con ALB, prueba `/health`
desde tu navegador.

## Si haces los 10 ejercicios:
**Eres oficialmente competente en RAG corporativo**. Felicidades 🎉.

---

## Cierre

RAG no es magia. Es:
1. Buen **chunking** + buenos **embeddings** + búsqueda **híbrida**.
2. Un **system prompt** disciplinado y **citas** obligatorias.
3. Métricas (**Ragas**) desde el día 1.
4. **Iterar** con datos reales, no opiniones.

Cada decisión de este curso tiene una razón. Cuando tu jefe pregunte
"¿por qué hiciste X?", sabrás defenderlo con argumentos.

**El siguiente paso**: implementa lo aprendido en TU caso de uso real.
Empieza pequeño (1 documento, 10 preguntas), mide, itera.

---

## 📌 Recursos para seguir aprendiendo

- **Ragas docs**: https://docs.ragas.io
- **LangChain text splitters**: https://python.langchain.com/docs/how_to/recursive_text_splitter/
- **OpenAI cookbook**: https://cookbook.openai.com
- **Anthropic prompt engineering**: https://docs.anthropic.com/claude/docs/intro-to-prompting
- **Pinecone learn (gratis, excelente)**: https://www.pinecone.io/learn/

---

## 🛟 Cuando algo falla — checklist de debug

| Síntoma | Primera cosa a revisar |
|---------|------------------------|
| `ImportError` | ¿venv activo? ¿`pip install -r requirements.txt`? |
| Respuestas vacías | ¿Hay docs ingeridos? `curl /health` muestra n_documents > 0? |
| "OPENAI_API_KEY missing" | ¿Existe `.env`? ¿Empieza por `sk-...`? Reinicia el venv. |
| Embedding dim mismatch | Cambiaste el modelo. **Re-indexa**. |
| Respuestas en idioma erróneo | Modelo de embeddings no multilingüe. |
| Latencia > 10s | Reranker LLM lento. Cambia a cross-encoder. |
| AWS UnauthorizedOperation | Session token expirado (los `ASIA...` duran horas). |
| Docker build lento | ¿Estás copiando `node_modules` o algo grande? Revisa `.dockerignore`. |
| Tests fallan al correr aislados | Probable estado compartido (singleton vector store). Limpia entre tests. |

---

**Fin del curso. Ahora ve a construir.**
