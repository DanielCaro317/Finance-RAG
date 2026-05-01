# ☁️ Curso AWS Cloud-Native: Asistente RAG 100% en la nube

> **Propósito**: replicar el proyecto **completamente en AWS**, usando
> servicios gestionados siempre que sea posible. Al terminar serás
> capaz de diseñar, desplegar y operar un sistema RAG corporativo en
> AWS con buenas prácticas Well-Architected.

> **Pre-requisitos**:
> - Haber completado el [CURSO_PASO_A_PASO.md](CURSO_PASO_A_PASO.md) o entender el proyecto local.
> - Cuenta AWS activa (Free Tier sirve para casi todo).
> - Tarjeta de crédito asociada (algunos servicios cobran centavos).
> - AWS CLI v2 instalado.

> **Tiempo estimado**: 8-15 horas. Algunos servicios tardan minutos en aprovisionarse.

> **Costo estimado del curso**: USD 5–30 si destruyes recursos al terminar cada módulo. USD 100+ al mes si dejas todo encendido.

---

## 📑 Tabla de Contenidos

| # | Módulo | Servicio AWS principal |
|---|--------|------------------------|
| C0 | [Setup de cuenta y CLI](#módulo-c0--setup-de-cuenta-y-cli) | IAM, AWS CLI |
| C1 | [Mapeo: local → cloud](#módulo-c1--mapeo-local--cloud) | (Conceptual) |
| C2 | [S3 para documentos crudos](#módulo-c2--s3-para-documentos-crudos) | S3 |
| C3 | [Secretos en Secrets Manager](#módulo-c3--secrets-manager) | Secrets Manager |
| C4 | [Habilitar Bedrock](#módulo-c4--habilitar-bedrock) | Bedrock |
| C5 | [Embeddings con Bedrock Titan](#módulo-c5--embeddings-con-bedrock) | Bedrock |
| C6 | [LLM con Bedrock Claude](#módulo-c6--llm-con-bedrock-claude) | Bedrock |
| C7 | [Vector store: OpenSearch Serverless](#módulo-c7--vector-store-opensearch-serverless) | OpenSearch |
| C8 | [Alternativa: Aurora + pgvector](#módulo-c8--alternativa-aurora-pgvector) | Aurora Serverless v2 |
| C9 | [Bedrock Knowledge Bases (RAG managed)](#módulo-c9--bedrock-knowledge-bases) | Bedrock KB |
| C10 | [Bedrock Agents (agente managed)](#módulo-c10--bedrock-agents) | Bedrock Agents |
| C11 | [Container Registry: ECR](#módulo-c11--ecr) | ECR |
| C12 | [ECS Fargate: correr la API](#módulo-c12--ecs-fargate) | ECS Fargate |
| C13 | [Application Load Balancer + HTTPS](#módulo-c13--alb--https) | ALB, ACM, Route53 |
| C14 | [Auth con Cognito](#módulo-c14--cognito) | Cognito |
| C15 | [Ingesta asíncrona: S3 + Lambda + SQS](#módulo-c15--ingesta-asíncrona) | Lambda, SQS, S3 events |
| C16 | [Pipelines con Step Functions](#módulo-c16--step-functions) | Step Functions |
| C17 | [PDFs complejos con Textract](#módulo-c17--textract) | Textract |
| C18 | [Observabilidad: CloudWatch + X-Ray](#módulo-c18--cloudwatch--x-ray) | CloudWatch, X-Ray |
| C19 | [Evaluación con Bedrock Evaluations](#módulo-c19--bedrock-evaluations) | Bedrock |
| C20 | [Experimentación con SageMaker](#módulo-c20--sagemaker) | SageMaker Studio |
| C21 | [Infraestructura como código (CDK)](#módulo-c21--cdk-infrastructure-as-code) | CDK |
| C22 | [CI/CD con GitHub Actions → ECR](#módulo-c22--cicd) | CodePipeline / GHA |
| C23 | [Optimización de costos](#módulo-c23--optimización-de-costos) | Cost Explorer, Budgets |
| C24 | [Well-Architected Review](#módulo-c24--well-architected-review) | (Conceptual) |
| C25 | [Limpieza: destruir todo](#módulo-c25--limpieza) | Best practice |

---

# Módulo C0 — Setup de cuenta y CLI

## Objetivo
Tener una cuenta AWS funcional, AWS CLI configurado, y un usuario IAM
con los permisos correctos (NO usar la cuenta root).

## Conceptos críticos

### ¿Qué es IAM?
IAM (Identity and Access Management) controla **quién** puede hacer
**qué** en tu cuenta. Tres conceptos:
- **User**: persona o servicio con credenciales.
- **Role**: identidad temporal asumida por un servicio (ej. ECS asume rol para acceder a S3).
- **Policy**: documento JSON que dice qué acciones están permitidas.

### Regla de oro: principio de privilegio mínimo
NUNCA uses la cuenta root para nada operativo. NUNCA des `*:*`. Siempre
permisos específicos.

## Pasos

### C0.1 — Crear cuenta AWS
https://aws.amazon.com → **Create an AWS Account**.

> ⚠️ Inmediatamente al entrar: **activa MFA en la cuenta root** y NO
> uses esa cuenta para trabajo diario.

### C0.2 — Crear usuario IAM administrativo

```bash
# Desde la consola web (más fácil la primera vez):
# IAM → Users → Create user → "rag-admin"
# Adjuntar policy: AdministratorAccess (solo para aprender; en prod sería más estricto)
# Crear access key tipo "CLI"
```

### C0.3 — Instalar AWS CLI v2
- **Windows**: `winget install Amazon.AWSCLI` o instalador oficial.
- **macOS**: `brew install awscli`
- **Linux**: `sudo apt install awscli` o instalador oficial.

```bash
aws --version
# aws-cli/2.x.x
```

### C0.4 — Configurar perfil
```bash
aws configure --profile rag-admin
# AWS Access Key ID: AKIA...
# AWS Secret Access Key: ...
# Default region: us-east-1
# Default output format: json
```

> ⚠️ Las credenciales `ASIA...` (con session token) que tienes en `.env`
> son **temporales**. Para el curso conviene un usuario IAM permanente.

### C0.5 — Verificar
```bash
aws sts get-caller-identity --profile rag-admin
# Devuelve tu UserId, Account, Arn
```

### C0.6 — Configurar `~/.aws/credentials`
Si vas a usar este perfil siempre:
```bash
export AWS_PROFILE=rag-admin            # macOS/Linux
$env:AWS_PROFILE="rag-admin"            # Windows PowerShell
```

### C0.7 — Activar Cost Alerts
**MUY importante** para no llevarte sorpresas:
1. Console → Billing → Budgets → Create budget.
2. Tipo "Cost budget", $10/mes.
3. Notify a tu email cuando supere 80% del presupuesto.

## ✅ Checkpoint
- `aws sts get-caller-identity` funciona.
- Tu cuenta tiene un budget alert configurado.
- MFA activado en root.

## 🧠 Consejo
> Crea un alias en tu shell: `alias awsr="aws --profile rag-admin"`. Te
> ahorra teclear el perfil en cada comando.

---

# Módulo C1 — Mapeo: local → cloud

## Antes de migrar, entiende la equivalencia

| Componente local | Servicio AWS recomendado | Alternativa |
|------------------|--------------------------|-------------|
| `chroma_db/` | **OpenSearch Serverless (vector engine)** | Aurora + pgvector |
| `data/raw/` | **S3** | EFS si necesitas POSIX |
| `.env` | **Secrets Manager** (sensibles) + **Parameter Store** (no sensibles) | — |
| OpenAI API key | **Secrets Manager** | — |
| Embeddings (OpenAI) | **Bedrock Titan / Cohere Embed** | OpenAI (vía VPC endpoint) |
| LLM (OpenAI) | **Bedrock (Claude / Llama)** | OpenAI |
| FastAPI en localhost | **ECS Fargate detrás de ALB** | App Runner / Lambda + API Gateway |
| Reranker | **Bedrock Cohere Rerank** | LLM-as-judge |
| Ingesta sync | **Lambda + S3 event** | Step Functions |
| pypdf | **Textract** (PDFs complejos) | unstructured en Lambda |
| Logs | **CloudWatch Logs** | — |
| Métricas | **CloudWatch Metrics** | — |
| Tracing | **X-Ray** | — |
| TLS / dominio | **ACM + Route53 + ALB** | — |
| Auth | **Cognito** | Auth0 / propio |
| CI/CD | **CodePipeline + CodeBuild** | GitHub Actions |
| Eval | **Bedrock Evaluations** | Ragas en SageMaker |
| Notebooks exploratorios | **SageMaker Studio** | EC2 |
| Knowledge Base | **Bedrock Knowledge Bases** (RAG sin código) | Construir a mano |

## Decisión: ¿"managed RAG" (Bedrock KB) o construido a mano?

AWS ofrece **Bedrock Knowledge Bases**: pones un bucket con docs y
listo, te da un RAG funcional. Pros y contras:

| | Bedrock KB | Construido a mano |
|---|------------|-------------------|
| Tiempo a producción | Horas | Semanas |
| Personalización | Limitada | Total |
| Chunking | Auto (sin control fino) | Tú decides |
| Reranker | Sí (managed) | Tú lo eliges |
| Costo | Por hora de OpenSearch + por embedding + por LLM | Pagas componentes pero más control |
| Vendor lock-in | Alto | Medio |

**Recomendación pedagógica**: hacer el módulo C9 con Bedrock KB para
*conocer* la opción, pero el sistema principal es el construido a mano
para *aprender* y mantener control.

---

# Módulo C2 — S3 para documentos crudos

## Concepto

S3 es el almacén de objetos de AWS. Tres ideas clave:
- **Bucket**: contenedor (nombre globalmente único).
- **Object**: archivo (con key/path interno).
- **Storage class**: Standard, IA, Glacier... costo vs latencia.

## Por qué versioning para datos regulados

Si activas Versioning, cada PUT crea una nueva versión en vez de
sobrescribir. Si alguien borra (incluso accidental), recuperas. Es un
must para banca/regulado.

## Pasos

### C2.1 — Crear bucket
```bash
aws s3api create-bucket \
    --bucket mi-banco-rag-docs \
    --region us-east-1
# Nota: us-east-1 NO necesita LocationConstraint; otras regiones sí:
# --create-bucket-configuration LocationConstraint=us-west-2
```

### C2.2 — Bloquear acceso público
```bash
aws s3api put-public-access-block \
    --bucket mi-banco-rag-docs \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

### C2.3 — Activar cifrado por defecto (SSE-S3)
```bash
aws s3api put-bucket-encryption --bucket mi-banco-rag-docs \
    --server-side-encryption-configuration '{
        "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm":"AES256"}}]
    }'
```

Para datos altamente regulados → **SSE-KMS** con CMK propia.

### C2.4 — Activar Versioning
```bash
aws s3api put-bucket-versioning --bucket mi-banco-rag-docs \
    --versioning-configuration Status=Enabled
```

### C2.5 — Lifecycle policy (mover a Glacier)

Documentos que no se acceden en 90 días → Glacier (10x más barato):
```bash
aws s3api put-bucket-lifecycle-configuration --bucket mi-banco-rag-docs \
    --lifecycle-configuration '{
      "Rules": [{
        "ID": "move-old-to-glacier",
        "Status": "Enabled",
        "Filter": {},
        "Transitions": [{"Days": 90, "StorageClass": "GLACIER"}]
      }]
    }'
```

### C2.6 — Subir un documento
```bash
aws s3 cp data/raw/manual_fraude_v2.md s3://mi-banco-rag-docs/raw/manual_fraude_v2.md
```

### C2.7 — Configurar el proyecto
En `.env`:
```bash
S3_BUCKET=mi-banco-rag-docs
AWS_REGION=us-east-1
```

Tu `app/services/s3_service.py` ya soporta uploads — al ingerir con
`upload_to_s3=True` queda subido.

## Costos S3
- Standard: ~$0.023/GB/mes.
- Glacier Deep Archive: ~$0.001/GB/mes.
- 10GB de docs en Standard ≈ $0.23/mes.

## 🧠 Consejo
> NUNCA pongas el nombre del bucket en el código. Siempre vía Settings.
> Y en producción, usa **bucket policies** restrictivas (solo el rol de
> ECS puede leer/escribir).

---

# Módulo C3 — Secrets Manager

## Concepto

Secrets Manager guarda **secretos cifrados** y los rota automáticamente
si quieres. Caro vs Parameter Store (~$0.40/secreto/mes) pero:
- Rotación automática.
- Historial de versiones.
- Auditoría completa en CloudTrail.

**Parameter Store** (gratis) sirve para no-sensibles (URLs, flags).

## Pasos

### C3.1 — Guardar OPENAI_API_KEY
```bash
aws secretsmanager create-secret \
    --name rag/openai-api-key \
    --description "OpenAI API key for RAG project" \
    --secret-string "sk-..."
```

### C3.2 — Recuperar
```bash
aws secretsmanager get-secret-value --secret-id rag/openai-api-key \
    --query SecretString --output text
```

### C3.3 — Política IAM mínima
La task de ECS solo debe poder leer este secreto, nada más:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["secretsmanager:GetSecretValue"],
    "Resource": "arn:aws:secretsmanager:us-east-1:<ACCT>:secret:rag/*"
  }]
}
```

### C3.4 — Inyección al contenedor (ECS task definition)
```json
"secrets": [
  {
    "name": "OPENAI_API_KEY",
    "valueFrom": "arn:aws:secretsmanager:us-east-1:<ACCT>:secret:rag/openai-api-key"
  }
]
```

ECS lee el secreto al arrancar el contenedor y lo inyecta como variable
de entorno. Tu código sigue leyendo `os.environ["OPENAI_API_KEY"]`.

### C3.5 — Parameter Store (no sensibles)
```bash
aws ssm put-parameter --name /rag/llm-model --value "gpt-4o-mini" --type String
aws ssm put-parameter --name /rag/retrieval-top-k --value "10" --type String
```

## 🧠 Consejo
> Rota los secretos cada 90 días automáticamente. Secrets Manager lo
> hace solo si configuras una Lambda de rotación.

---

# Módulo C4 — Habilitar Bedrock

## Concepto

**AWS Bedrock** es el servicio gestionado de LLMs en AWS. Te da acceso
a modelos de Anthropic (Claude), Meta (Llama), Cohere, AI21, Mistral y
Amazon (Titan). Sin gestionar GPUs.

## Pasos

### C4.1 — Habilitar el servicio
1. Console → Bedrock.
2. **Model access** (panel izquierdo).
3. Click **Manage model access**.
4. Selecciona los modelos que quieres usar:
   - Anthropic Claude 3.5 Sonnet
   - Anthropic Claude 3 Haiku (más barato, rápido)
   - Amazon Titan Embeddings G1 - Text
   - Cohere Embed Multilingual (recomendado para español)
5. **Submit** — algunos modelos requieren aprobación (suele ser inmediata para personal accounts).

> ⚠️ Bedrock está disponible en regiones limitadas. Recomiendo
> **us-east-1**, **us-west-2** o **eu-central-1**.

### C4.2 — Verificar acceso
```bash
aws bedrock list-foundation-models --region us-east-1 \
    --query "modelSummaries[?contains(modelId, 'claude')].modelId"
```

### C4.3 — Test rápido (Python)
```python
import boto3, json
client = boto3.client("bedrock-runtime", region_name="us-east-1")
resp = client.invoke_model(
    modelId="anthropic.claude-3-haiku-20240307-v1:0",
    body=json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 200,
        "messages": [{"role":"user","content":"Hola, ¿qué eres?"}]
    })
)
print(json.loads(resp["body"].read())["content"][0]["text"])
```

## Costos Bedrock (referencia 2024)
| Modelo | Input $/1K tok | Output $/1K tok |
|--------|----------------|-----------------|
| Claude 3 Haiku | $0.00025 | $0.00125 |
| Claude 3.5 Sonnet | $0.003 | $0.015 |
| Titan Embed v2 | $0.00002 | — |
| Cohere Embed Multilingual | $0.0001 | — |

Una conversación RAG corta (≤2K tokens in + 500 out) con Haiku ≈ $0.001.

## 🧠 Consejo
> Empieza con **Claude 3 Haiku** + **Cohere Embed Multilingual**. Es la
> combinación barata-y-buena para español. Sube a Sonnet solo si Haiku
> falla calidad-mente.

---

# Módulo C5 — Embeddings con Bedrock

## En el proyecto

Tu `app/core/embeddings.py` ya tiene la clase `BedrockEmbeddings`. Solo
hay que activarla en `.env`:

```bash
EMBEDDING_PROVIDER=bedrock
EMBEDDING_MODEL=cohere.embed-multilingual-v3
AWS_REGION=us-east-1
```

> ⚠️ Cohere y Titan tienen formatos de body distintos. Mejora el código
> para soportar Cohere (ejercicio del módulo).

## Cohere Embed body
```python
body = json.dumps({
    "texts": [text],
    "input_type": "search_document",  # o "search_query"
    "embedding_types": ["float"],
})
```

## Titan body
```python
body = json.dumps({"inputText": text})
```

## Re-indexación obligatoria

Si cambias de OpenAI a Bedrock, los espacios vectoriales son **distintos**.
Tienes que **borrar y re-indexar todo el corpus**.

```bash
# Borra la colección Chroma local (si estás migrando)
rm -rf chroma_db/

# Re-ingieres
python -m scripts.ingest_documents data/raw/ --domain general
```

## 🧠 Consejo
> Cohere Embed Multilingual se entrenó con español, francés, alemán,
> chino, etc. Para banca latinoamericana, **superior a Titan en ES**.

---

# Módulo C6 — LLM con Bedrock Claude

## Configuración

```bash
LLM_PROVIDER=bedrock
LLM_MODEL=anthropic.claude-3-haiku-20240307-v1:0
```

Tu código `BedrockChatLLM` ya lo soporta. Test:
```bash
curl -X POST http://localhost:8000/chat \
    -H "Content-Type: application/json" \
    -d '{"query":"hola"}'
```

## Inferencia provisionada vs on-demand

- **On-demand** (default): pagas por token. Sin compromiso. Buena para variabilidad.
- **Provisioned throughput**: reservas capacidad mensual. Mejor latencia. Más caro si sub-utilizas.

Empieza on-demand. Sube a provisioned si tienes >1M requests/mes y latencia importa.

## Cross-region inference

Si tu región tiene cuota baja, activa **inference profiles** que
distribuyen carga entre regiones:
```python
modelId="us.anthropic.claude-3-5-sonnet-20241022-v2:0"  # prefijo "us."
```

## 🧠 Consejo
> Bedrock cobra por token IN y OUT. Optimiza el system prompt — cada
> token de prompt × cada llamada × cada usuario = $$$. Manténlo conciso.

---

# Módulo C7 — Vector store: OpenSearch Serverless

## Concepto

**OpenSearch Serverless con motor "vectorsearch"** es el reemplazo
gestionado de ChromaDB en AWS. Soporta:
- KNN vectorial (HNSW).
- Filtros de metadata.
- BM25 nativo (no necesitas gestionar BM25 en memoria como en local).
- Auto-scaling.

## Costos
~$700/mes mínimo (2 OCUs base de 0.5 OCU x 24h x 30d). **Caro para
pruebas**. Para aprender, considera Aurora pgvector (módulo C8) que es
~10x más barato en escalas pequeñas.

## Pasos

### C7.1 — Crear collection (vía CLI)
```bash
# 1) Política de cifrado
aws opensearchserverless create-security-policy \
    --name rag-encryption-policy --type encryption \
    --policy '{
      "Rules":[{"ResourceType":"collection","Resource":["collection/rag-vectors"]}],
      "AWSOwnedKey":true
    }'

# 2) Política de red (público con auth IAM)
aws opensearchserverless create-security-policy \
    --name rag-network-policy --type network \
    --policy '[{
      "Rules":[{"ResourceType":"collection","Resource":["collection/rag-vectors"]}],
      "AllowFromPublic":true
    }]'

# 3) Política de acceso a datos
aws opensearchserverless create-access-policy \
    --name rag-access-policy --type data \
    --policy '[{
      "Rules":[
        {"ResourceType":"collection","Resource":["collection/rag-vectors"],"Permission":["aoss:*"]},
        {"ResourceType":"index","Resource":["index/rag-vectors/*"],"Permission":["aoss:*"]}
      ],
      "Principal":["arn:aws:iam::<ACCT>:user/rag-admin"]
    }'

# 4) Crear la collection
aws opensearchserverless create-collection \
    --name rag-vectors --type VECTORSEARCH
```

Espera ~5-10 min hasta que esté `ACTIVE`:
```bash
aws opensearchserverless list-collections --query "collectionSummaries[*].[name,status]"
```

### C7.2 — Cliente Python (`opensearch-py`)
```bash
pip install opensearch-py requests-aws4auth
```

```python
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3

session = boto3.Session()
credentials = session.get_credentials()
auth = AWS4Auth(
    credentials.access_key, credentials.secret_key,
    "us-east-1", "aoss",
    session_token=credentials.token,
)

client = OpenSearch(
    hosts=[{"host": "<COLLECTION_ID>.us-east-1.aoss.amazonaws.com", "port": 443}],
    http_auth=auth,
    use_ssl=True,
    connection_class=RequestsHttpConnection,
)
```

### C7.3 — Crear índice con campo vectorial
```python
client.indices.create(
    index="rag-vectors",
    body={
        "settings": {"index": {"knn": True}},
        "mappings": {
            "properties": {
                "vector": {
                    "type": "knn_vector",
                    "dimension": 1024,           # Cohere multilingual
                    "method": {"name":"hnsw","engine":"nmslib"},
                },
                "text": {"type": "text"},
                "source": {"type": "keyword"},
                "domain": {"type": "keyword"},
                "jurisdiction": {"type": "keyword"},
                "effective_year": {"type": "integer"},
            }
        }
    }
)
```

### C7.4 — Adapter en tu proyecto

Crea `app/core/vectorstore_opensearch.py` con la misma interfaz que
`VectorStore` (add, query, count, all_documents). En `config.py` añade
`VECTOR_STORE=opensearch_serverless` y un factory que decida.

```python
def get_vector_store():
    s = get_settings()
    if s.vector_store == "chroma":
        return ChromaVectorStore(...)
    if s.vector_store == "opensearch_serverless":
        return OpenSearchVectorStore(...)
```

### C7.5 — Query con filtros de metadata
```python
body = {
    "size": top_k,
    "query": {
        "bool": {
            "must": [{"knn": {"vector": {"vector": q_vec, "k": top_k}}}],
            "filter": [{"term": {"jurisdiction": "CO"}}]
        }
    }
}
client.search(index="rag-vectors", body=body)
```

## 🧠 Consejo
> Si tu volumen es bajo (<1M chunks), **Aurora pgvector** es 10x más
> barato. OpenSearch Serverless brilla con escala alta o necesidad de
> BM25 nativo.

---

# Módulo C8 — Alternativa: Aurora pgvector

## Por qué Aurora Serverless v2

- Costo: ~$50-200/mes en cargas pequeñas vs $700+ de OpenSearch.
- PostgreSQL completo: SQL + vectores + transacciones + JOIN.
- Ya conocido por equipos de backend.

## Pasos

### C8.1 — Crear cluster Aurora Serverless v2 PostgreSQL
```bash
aws rds create-db-cluster \
    --db-cluster-identifier rag-aurora \
    --engine aurora-postgresql --engine-version 15.4 \
    --master-username postgres \
    --master-user-password '<TUP@ssword>' \
    --serverless-v2-scaling-configuration MinCapacity=0.5,MaxCapacity=4 \
    --enable-http-endpoint
```

Crea instancia:
```bash
aws rds create-db-instance \
    --db-instance-identifier rag-aurora-instance-1 \
    --db-cluster-identifier rag-aurora \
    --db-instance-class db.serverless \
    --engine aurora-postgresql
```

### C8.2 — Habilitar pgvector
Conéctate (Cloud9, EC2 bastion, o psql desde tu PC con el cluster
público y security group abierto en 5432):
```sql
CREATE EXTENSION vector;
```

### C8.3 — Esquema
```sql
CREATE TABLE chunks (
    id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    embedding vector(1024),
    source TEXT,
    domain TEXT,
    jurisdiction TEXT,
    effective_year INT,
    version TEXT,
    page INT,
    chunk_index INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON chunks (domain, jurisdiction, effective_year);
```

### C8.4 — Adapter Python
```python
import psycopg

class PgvectorStore:
    def __init__(self, dsn):
        self.dsn = dsn
    def add(self, ids, texts, embeddings, metadatas):
        with psycopg.connect(self.dsn) as conn, conn.cursor() as cur:
            cur.executemany("""
                INSERT INTO chunks (id, text, embedding, source, domain, jurisdiction, effective_year, version)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET embedding=EXCLUDED.embedding
            """, [(i, t, e, m["source"], m["domain"], m.get("jurisdiction"),
                   m.get("effective_year"), m.get("version"))
                  for i, t, e, m in zip(ids, texts, embeddings, metadatas)])
    def query(self, embedding, top_k, where=None):
        clauses = []
        params = [embedding, top_k]
        if where:
            for k, v in where.items():
                clauses.append(f"{k} = %s"); params.insert(-1, v)
        sql = f"""
            SELECT text, source, domain, jurisdiction, effective_year,
                   1 - (embedding <=> %s::vector) AS score
            FROM chunks
            {('WHERE ' + ' AND '.join(clauses)) if clauses else ''}
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        ...
```

## Costos Aurora Serverless v2
- 0.5 ACU × 24h × 30d × $0.12 = ~$43/mes mínimo.
- Storage: $0.10/GB/mes.

## 🧠 Consejo
> El operador `<=>` es distancia coseno en pgvector. `<->` es L2,
> `<#>` es producto interno (negativo). Para texto SIEMPRE coseno.

---

# Módulo C9 — Bedrock Knowledge Bases

## Concepto

Bedrock KB es **RAG-as-a-Service**. Le das:
- Un bucket S3 con documentos.
- Un modelo de embeddings.
- Un vector store (OpenSearch Serverless u otros).

Y te da un endpoint `RetrieveAndGenerate` que ya hace todo: chunking,
embeddings, retrieval, LLM. **Ideal para empezar rápido**, ideal para
casos donde no quieres operar nada.

## Pasos (vía consola, más rápido la primera vez)

### C9.1 — Pre-requisitos
- Bucket S3 con al menos un PDF/TXT/MD.
- Modelos habilitados en Bedrock (Embed + LLM).

### C9.2 — Crear KB
1. Console → Bedrock → **Knowledge bases** → Create.
2. Name: `rag-kb-financiero`.
3. IAM role: dejar que la consola cree uno.
4. **Data source**: S3, apuntar al bucket.
5. **Embeddings**: Cohere Embed Multilingual.
6. **Vector store**: "Quick create" → crea OpenSearch Serverless automáticamente.
7. **Sync**: dispara la primera ingesta.

### C9.3 — Test desde consola
La consola tiene un chat de prueba. Pregunta y mira citas.

### C9.4 — Llamarla desde tu código
```python
import boto3
client = boto3.client("bedrock-agent-runtime", region_name="us-east-1")

resp = client.retrieve_and_generate(
    input={"text": "¿Cuál es el monto máximo de transferencia internacional?"},
    retrieveAndGenerateConfiguration={
        "type": "KNOWLEDGE_BASE",
        "knowledgeBaseConfiguration": {
            "knowledgeBaseId": "<KB_ID>",
            "modelArn": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
        }
    }
)
print(resp["output"]["text"])
print(resp["citations"])
```

### C9.5 — Sync automático (cuando cambias S3)
Configura un **EventBridge rule** que dispare un Lambda que llame
`startIngestionJob` cuando llegue un nuevo objeto a S3.

## Cuándo usar KB vs construido

**Usa KB cuando**:
- Tu equipo no tiene tiempo de construir.
- Documentos relativamente uniformes.
- No necesitas chunking custom o tools complejas.

**Construye a mano cuando**:
- Necesitas agentes con tools de tu negocio.
- Filtros de metadata complejos (RBAC).
- Quieres optimizar costo o tener control total.

## 🧠 Consejo
> Aún si vas a construir a mano, **prueba KB primero** con tus docs y
> compara métricas. A veces la solución managed gana.

---

# Módulo C10 — Bedrock Agents

## Concepto

**Bedrock Agents** = agentes managed con tools (action groups) y
knowledge bases conectadas. Definir un agente:
1. Eliges modelo (Claude).
2. Defines instrucciones (system prompt).
3. Defines action groups (tools) — cada uno apunta a un Lambda.
4. Conectas KBs.

## Pasos

### C10.1 — Crea Lambda para `lookup_fraud_status`
```python
# lambda_fraud.py
import json
def lambda_handler(event, context):
    # Bedrock pasa: event["actionGroup"], event["function"], event["parameters"]
    tx_id = next((p["value"] for p in event["parameters"] if p["name"] == "transaction_id"), None)
    # Tu lógica:
    result = {"transaction_id": tx_id, "status": "ok", "risk_score": 30}
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event["actionGroup"],
            "function": event["function"],
            "functionResponse": {"responseBody": {"TEXT": {"body": json.dumps(result)}}}
        }
    }
```

Despliega:
```bash
zip -r lambda_fraud.zip lambda_fraud.py
aws lambda create-function \
    --function-name rag-fraud-tool \
    --runtime python3.11 \
    --handler lambda_fraud.lambda_handler \
    --role arn:aws:iam::<ACCT>:role/lambda-basic-execution \
    --zip-file fileb://lambda_fraud.zip
```

### C10.2 — OpenAPI schema del action group
```yaml
openapi: 3.0.0
info: {title: Fraud Tools, version: 1.0.0}
paths:
  /lookup_fraud_status:
    post:
      description: Consulta el estado de fraude de una transacción
      parameters:
        - name: transaction_id
          in: query
          required: true
          schema: {type: string}
      responses:
        '200':
          description: ok
```

### C10.3 — Crear el agente (consola)
1. Bedrock → Agents → Create.
2. Modelo: Claude 3.5 Sonnet.
3. Instructions: tu system prompt.
4. Add Action Group → Lambda + OpenAPI schema.
5. Add Knowledge Base → la KB del módulo C9.
6. Prepare → Test.

### C10.4 — Invocar
```python
resp = client.invoke_agent(
    agentId="<AGENT_ID>",
    agentAliasId="TSTALIASID",
    sessionId="user-123-session-1",
    inputText="¿La transacción TX-99 es fraude y qué dice la política?"
)
for ev in resp["completion"]:
    if "chunk" in ev: print(ev["chunk"]["bytes"].decode(), end="")
```

## Pros vs construir agente a mano

| | Bedrock Agents | Hecho en Python |
|---|----------------|-----------------|
| Latencia | Algo mayor (más hops) | Menor |
| Multi-turno con memoria | Built-in | Hay que construirlo |
| Trace de razonamiento | Built-in | LangSmith |
| Personalización | Limitada | Total |
| Costo | + por sesión | Solo tokens |

## 🧠 Consejo
> Bedrock Agents está madurando rápido. Si tu caso es simple, te
> ahorra meses de trabajo.

---

# Módulo C11 — ECR

## Concepto

**Elastic Container Registry** es Docker Hub privado en AWS. Tus
imágenes Docker viven aquí, ECS las descarga al desplegar.

## Pasos

### C11.1 — Crear repositorio
```bash
aws ecr create-repository --repository-name asistente-rag --region us-east-1
```

### C11.2 — Login
```bash
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin \
    <ACCT>.dkr.ecr.us-east-1.amazonaws.com
```

### C11.3 — Build y push
```bash
docker build -t asistente-rag .
docker tag asistente-rag:latest <ACCT>.dkr.ecr.us-east-1.amazonaws.com/asistente-rag:latest
docker push <ACCT>.dkr.ecr.us-east-1.amazonaws.com/asistente-rag:latest
```

### C11.4 — Activar Image Scanning
```bash
aws ecr put-image-scanning-configuration \
    --repository-name asistente-rag \
    --image-scanning-configuration scanOnPush=true
```

Ver vulnerabilidades:
```bash
aws ecr describe-image-scan-findings --repository-name asistente-rag --image-id imageTag=latest
```

### C11.5 — Lifecycle policy (limpiar imágenes viejas)
```bash
aws ecr put-lifecycle-policy --repository-name asistente-rag --lifecycle-policy-text '{
  "rules": [{
    "rulePriority": 1,
    "description": "Mantener solo 10 imágenes",
    "selection": {"tagStatus": "any", "countType": "imageCountMoreThan", "countNumber": 10},
    "action": {"type": "expire"}
  }]
}'
```

## Costos
$0.10/GB/mes de almacenamiento. Una imagen ~500MB = $0.05/mes.

## 🧠 Consejo
> Tagea con SHA del commit (`asistente-rag:abc1234`) además de `latest`.
> Así puedes hacer rollback exacto.

---

# Módulo C12 — ECS Fargate

## Concepto

**ECS Fargate** corre contenedores **sin gestionar servidores**. Defines
CPU/RAM, te da un IP y endpoint. Auto-scaling. Pagas por segundo.

## Pasos

### C12.1 — Crear cluster
```bash
aws ecs create-cluster --cluster-name rag-cluster
```

### C12.2 — Log group para CloudWatch
```bash
aws logs create-log-group --log-group-name /ecs/asistente-rag
```

### C12.3 — Roles IAM
- `ecsTaskExecutionRole`: permite a ECS leer ECR + escribir CloudWatch + leer Secrets Manager.
- `ragTaskRole`: permite al CONTENEDOR llamar a Bedrock/S3/etc.

```bash
# Execution role (ya existe en muchas cuentas, si no, créalo):
aws iam create-role --role-name ecsTaskExecutionRole \
    --assume-role-policy-document '{
      "Version":"2012-10-17",
      "Statement":[{"Effect":"Allow","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Action":"sts:AssumeRole"}]
    }'

aws iam attach-role-policy --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Permitir leer secretos:
aws iam put-role-policy --role-name ecsTaskExecutionRole \
    --policy-name read-rag-secrets \
    --policy-document '{
      "Version":"2012-10-17",
      "Statement":[{"Effect":"Allow","Action":"secretsmanager:GetSecretValue","Resource":"arn:aws:secretsmanager:us-east-1:<ACCT>:secret:rag/*"}]
    }'

# Task role (lo que el CÓDIGO puede hacer):
aws iam create-role --role-name ragTaskRole \
    --assume-role-policy-document '...'  # mismo trust policy

aws iam put-role-policy --role-name ragTaskRole --policy-name rag-runtime-perms \
    --policy-document '{
      "Version":"2012-10-17",
      "Statement":[
        {"Effect":"Allow","Action":["bedrock:InvokeModel"],"Resource":"*"},
        {"Effect":"Allow","Action":["s3:GetObject","s3:PutObject"],"Resource":"arn:aws:s3:::mi-banco-rag-docs/*"},
        {"Effect":"Allow","Action":["aoss:APIAccessAll"],"Resource":"*"}
      ]
    }'
```

### C12.4 — Task definition (`task-def.json`)
```json
{
  "family": "asistente-rag",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024", "memory": "2048",
  "executionRoleArn": "arn:aws:iam::<ACCT>:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::<ACCT>:role/ragTaskRole",
  "containerDefinitions": [{
    "name": "api",
    "image": "<ACCT>.dkr.ecr.us-east-1.amazonaws.com/asistente-rag:latest",
    "portMappings": [{"containerPort": 8000}],
    "environment": [
      {"name": "APP_ENV", "value": "prod"},
      {"name": "LLM_PROVIDER", "value": "bedrock"},
      {"name": "LLM_MODEL", "value": "anthropic.claude-3-haiku-20240307-v1:0"},
      {"name": "EMBEDDING_PROVIDER", "value": "bedrock"},
      {"name": "EMBEDDING_MODEL", "value": "cohere.embed-multilingual-v3"},
      {"name": "VECTOR_STORE", "value": "opensearch_serverless"},
      {"name": "AWS_REGION", "value": "us-east-1"}
    ],
    "secrets": [
      {"name": "OPENAI_API_KEY", "valueFrom": "arn:aws:secretsmanager:us-east-1:<ACCT>:secret:rag/openai-api-key"}
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/asistente-rag",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "ecs"
      }
    }
  }]
}

```

Registrar:
```bash
aws ecs register-task-definition --cli-input-json file://task-def.json
```

### C12.5 — Service (con auto-scaling)
```bash
# Crear servicio (asume que tienes una VPC con subnets públicas + un security group abierto en 8000)
aws ecs create-service \
    --cluster rag-cluster \
    --service-name asistente-rag \
    --task-definition asistente-rag \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

### C12.6 — Verificar
```bash
aws ecs describe-services --cluster rag-cluster --services asistente-rag \
    --query "services[0].deployments"
```

Mira los logs:
```bash
aws logs tail /ecs/asistente-rag --follow
```

## Auto-scaling
```bash
aws application-autoscaling register-scalable-target \
    --service-namespace ecs \
    --resource-id service/rag-cluster/asistente-rag \
    --scalable-dimension ecs:service:DesiredCount \
    --min-capacity 1 --max-capacity 10

aws application-autoscaling put-scaling-policy \
    --service-namespace ecs \
    --resource-id service/rag-cluster/asistente-rag \
    --scalable-dimension ecs:service:DesiredCount \
    --policy-name cpu-target-tracking \
    --policy-type TargetTrackingScaling \
    --target-tracking-scaling-policy-configuration '{
      "TargetValue": 70.0,
      "PredefinedMetricSpecification": {"PredefinedMetricType": "ECSServiceAverageCPUUtilization"}
    }'
```

## Costos
- 1 vCPU + 2GB RAM Fargate × 24h × 30d ≈ $30/mes.
- Egress: $0.09/GB de salida.

## 🧠 Consejo
> Empieza con 1 vCPU / 2GB. Si el LLM no es local (Bedrock), el
> contenedor solo orquesta — no necesitas mucho.

---

# Módulo C13 — ALB + HTTPS

## Concepto

**Application Load Balancer** distribuye tráfico HTTP(S) entre tus tasks
ECS, hace health checks, soporta path-based routing.

**ACM** (Certificate Manager) emite certificados HTTPS gratis para
dominios que tengas en Route53.

## Pasos

### C13.1 — Compra/configura dominio en Route53
Si no tienes dominio: Route53 → Register domain (~$12/año .com).

### C13.2 — Solicita certificado ACM
```bash
aws acm request-certificate \
    --domain-name asistente-rag.midominio.com \
    --validation-method DNS \
    --region us-east-1
```

Sigue las instrucciones para validar añadiendo un registro CNAME en
Route53 (la consola ofrece botón "Create records in Route 53").

### C13.3 — Crea ALB
```bash
# Target group
aws elbv2 create-target-group \
    --name rag-tg --protocol HTTP --port 8000 \
    --vpc-id vpc-xxx --target-type ip \
    --health-check-path /health --health-check-interval-seconds 30

# ALB (en subnets públicas)
aws elbv2 create-load-balancer \
    --name rag-alb --type application \
    --subnets subnet-xxx subnet-yyy \
    --security-groups sg-alb

# Listener HTTPS
aws elbv2 create-listener \
    --load-balancer-arn <ALB_ARN> \
    --protocol HTTPS --port 443 \
    --certificates CertificateArn=<CERT_ARN> \
    --default-actions Type=forward,TargetGroupArn=<TG_ARN>

# Listener HTTP que redirige a HTTPS
aws elbv2 create-listener \
    --load-balancer-arn <ALB_ARN> --protocol HTTP --port 80 \
    --default-actions '[{"Type":"redirect","RedirectConfig":{"Protocol":"HTTPS","Port":"443","StatusCode":"HTTP_301"}}]'
```

### C13.4 — Conectar ECS service al ALB
Recrea el service con `loadBalancers`:
```bash
aws ecs update-service --cluster rag-cluster --service asistente-rag \
    --load-balancers '[{"targetGroupArn":"<TG_ARN>","containerName":"api","containerPort":8000}]'
```

### C13.5 — Apuntar dominio al ALB
Route53 → Hosted zone → Create record → tipo A, alias al ALB.

### C13.6 — Test
```bash
curl https://asistente-rag.midominio.com/health
```

## Costos ALB
$0.0225/hora + $0.008/LCU-hora ≈ $20/mes baseline.

## 🧠 Consejo
> Activa **WAF** (~$5/mes) en producción para protegerte de SQL
> injection, prompt injection patterns conocidos, rate limit por IP.

---

# Módulo C14 — Cognito

## Concepto

**Cognito User Pools** = directorio de usuarios managed con login,
MFA, OAuth, JWT. Tu API valida JWT, listo.

## Pasos

### C14.1 — Crea User Pool
```bash
aws cognito-idp create-user-pool --pool-name rag-users \
    --policies '{"PasswordPolicy":{"MinimumLength":12,"RequireUppercase":true,"RequireNumbers":true,"RequireSymbols":true}}'
```

### C14.2 — App client (sin secret, para web)
```bash
aws cognito-idp create-user-pool-client \
    --user-pool-id us-east-1_XXXXX \
    --client-name rag-web \
    --no-generate-secret \
    --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH
```

### C14.3 — Validar JWT en FastAPI

```python
# app/api/auth.py
import requests
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

POOL_ID = "us-east-1_XXXXX"
REGION = "us-east-1"
JWKS = requests.get(f"https://cognito-idp.{REGION}.amazonaws.com/{POOL_ID}/.well-known/jwks.json").json()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        headers = jwt.get_unverified_header(token)
        key = next(k for k in JWKS["keys"] if k["kid"] == headers["kid"])
        claims = jwt.decode(token, key, algorithms=["RS256"], options={"verify_aud": False})
        return claims
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
```

Aplicarlo a `/chat`:
```python
@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, user: dict = Depends(current_user)) -> ChatResponse:
    ...
```

### C14.4 — RBAC integrado al retrieval

Si Cognito devuelve `cognito:groups` con `["analyst", "fraud_team"]`,
úsalos como filtro:
```python
where = {"allowed_groups": {"$in": user.get("cognito:groups", [])}}
chunks = retriever.retrieve(query, top_k=10, where=where)
```

## 🧠 Consejo
> Para apps internas: configura Cognito con **federación SSO** (SAML)
> contra el AD/Okta de la empresa. Single sign-on real.

---

# Módulo C15 — Ingesta asíncrona (S3 + Lambda + SQS)

## Por qué async

Indexar un PDF de 200 páginas puede tomar minutos. Hacerlo síncrono
bloquea la API. Mejor:
1. Cliente sube archivo a S3.
2. S3 dispara evento → SQS.
3. Worker Lambda procesa cada mensaje.
4. Si falla, SQS reintenta + DLQ.

## Pasos

### C15.1 — Cola SQS
```bash
aws sqs create-queue --queue-name rag-ingest-queue \
    --attributes '{"VisibilityTimeout":"600","MessageRetentionPeriod":"345600"}'

aws sqs create-queue --queue-name rag-ingest-dlq

# Configurar redrive a DLQ tras 3 fallos
aws sqs set-queue-attributes --queue-url <QUEUE_URL> \
    --attributes '{"RedrivePolicy":"{\"deadLetterTargetArn\":\"<DLQ_ARN>\",\"maxReceiveCount\":\"3\"}"}'
```

### C15.2 — Notificación S3 → SQS
```bash
aws s3api put-bucket-notification-configuration \
    --bucket mi-banco-rag-docs \
    --notification-configuration '{
      "QueueConfigurations":[{
        "QueueArn":"<QUEUE_ARN>",
        "Events":["s3:ObjectCreated:*"],
        "Filter":{"Key":{"FilterRules":[{"Name":"prefix","Value":"raw/"}]}}
      }]
    }'
```

### C15.3 — Lambda worker

```python
# lambda_ingest.py
import boto3, json, os, tempfile
from app.services.ingestion import ingest_file  # tu código

s3 = boto3.client("s3")

def handler(event, context):
    for record in event["Records"]:
        body = json.loads(record["body"])
        for s3_event in body.get("Records", []):
            bucket = s3_event["s3"]["bucket"]["name"]
            key = s3_event["s3"]["object"]["key"]
            with tempfile.NamedTemporaryFile(suffix=os.path.splitext(key)[1]) as tmp:
                s3.download_file(bucket, key, tmp.name)
                # Metadata desde el path: raw/{domain}/{archivo}
                domain = key.split("/")[1] if "/" in key else "general"
                ingest_file(tmp.name, domain=domain, upload_to_s3=False)
```

### C15.4 — Empaquetado (Layer + Function)

Las dependencias (chromadb, openai, etc.) son grandes — usa una **Lambda
Layer** o Container image (>250MB).

**Recomendación**: imagen Docker para la Lambda:
```dockerfile
FROM public.ecr.aws/lambda/python:3.11
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app ./app
COPY lambda_ingest.py .
CMD ["lambda_ingest.handler"]
```

Build, push a ECR, crea la Lambda con `--package-type Image`.

### C15.5 — Trigger SQS
```bash
aws lambda create-event-source-mapping \
    --function-name rag-ingest-worker \
    --event-source-arn <QUEUE_ARN> \
    --batch-size 1
```

### C15.6 — Test end-to-end
```bash
aws s3 cp mi_doc.pdf s3://mi-banco-rag-docs/raw/fraude/mi_doc.pdf
# Esperas ~30s, miras logs:
aws logs tail /aws/lambda/rag-ingest-worker --follow
```

## 🧠 Consejo
> Pon `VisibilityTimeout > Lambda timeout`. Si Lambda tarda 5min,
> el visibility timeout debe ser ≥6min. Si no, SQS reintenta antes
> de que termine la primera ejecución → procesas duplicado.

---

# Módulo C16 — Step Functions

## Cuándo usar

Para pipelines con **múltiples pasos**, branching, retry policies por
paso, paralelismo. Ej: "extrae texto → traduce → chunkea → embedea →
indexa → notifica". Si un paso falla, retry, sino DLQ.

## Diseño para nuestro RAG

```
[S3 Event]
    │
    ▼
[Lambda: detect type]──┬──► PDF → [Lambda: Textract] ──┐
                       ├──► MD/TXT → [Lambda: read] ────┤
                       └──► DOCX → [Lambda: docx]──────┤
                                                        ▼
                                          [Lambda: chunk + embed]
                                                        │
                                                        ▼
                                            [Lambda: index OpenSearch]
                                                        │
                                                        ▼
                                          [SNS notify "doc indexed"]
```

## State machine (resumen)
```json
{
  "Comment": "RAG ingestion pipeline",
  "StartAt": "DetectType",
  "States": {
    "DetectType": {
      "Type": "Choice",
      "Choices": [
        {"Variable": "$.ext", "StringEquals": ".pdf", "Next": "Textract"},
        {"Variable": "$.ext", "StringEquals": ".docx", "Next": "ParseDocx"}
      ],
      "Default": "ReadText"
    },
    "Textract": {"Type":"Task","Resource":"arn:...:textract-lambda","Next":"Chunk"},
    "ReadText": {"Type":"Task","Resource":"arn:...:read-lambda","Next":"Chunk"},
    "ParseDocx": {"Type":"Task","Resource":"arn:...:docx-lambda","Next":"Chunk"},
    "Chunk": {"Type":"Task","Resource":"arn:...:chunk-lambda","Next":"Index","Retry":[{"ErrorEquals":["States.ALL"],"MaxAttempts":3}]},
    "Index": {"Type":"Task","Resource":"arn:...:index-lambda","End":true}
  }
}
```

## 🧠 Consejo
> Step Functions Express ($1/M ejecuciones) para pipelines ≤5min. Standard
> para procesos largos (hasta 1 año!) con histórico completo. Para nuestro
> RAG → Express.

---

# Módulo C17 — Textract

## Concepto

**Textract** extrae texto, tablas, formularios y key-values de PDFs e
imágenes. Mucho mejor que `pypdf` para:
- PDFs escaneados (OCR).
- PDFs con tablas complejas.
- Formularios estructurados.

## Modos
- `DetectDocumentText`: solo texto.
- `AnalyzeDocument`: + TABLES, FORMS, QUERIES.
- `StartDocumentAnalysis` (async): para docs grandes >1MB.

## Pasos

### C17.1 — Async para PDFs grandes
```python
import boto3, time
client = boto3.client("textract")

job = client.start_document_analysis(
    DocumentLocation={"S3Object": {"Bucket": "mi-banco-rag-docs", "Name": "raw/manual.pdf"}},
    FeatureTypes=["TABLES", "FORMS"]
)
job_id = job["JobId"]

while True:
    r = client.get_document_analysis(JobId=job_id)
    if r["JobStatus"] in ("SUCCEEDED", "FAILED"): break
    time.sleep(2)

# Reconstruye texto preservando estructura
for block in r["Blocks"]:
    if block["BlockType"] == "LINE":
        print(block["Text"])
```

### C17.2 — QUERIES (extracción dirigida)

Para pedir campos específicos (mejor que regex en muchos casos):
```python
client.start_document_analysis(
    DocumentLocation={...},
    FeatureTypes=["QUERIES"],
    QueriesConfig={"Queries":[
        {"Text":"¿Cuál es el monto máximo?", "Alias":"max_amount"},
        {"Text":"¿Quién aprueba transferencias?", "Alias":"approver"}
    ]}
)
```

### C17.3 — Integrar al pipeline
Reemplaza el lector PDF en `app/services/ingestion.py`:
```python
def _read_pdf_textract(s3_key: str) -> str:
    # ...usa Textract si está habilitado.
```

## Costos
$0.0015/página `DetectDocumentText`, $0.05/página `AnalyzeDocument`. Un
manual de 100 páginas = $0.15-$5 según features.

## 🧠 Consejo
> Para PDFs simples nativos (no escaneados, sin tablas), `pypdf` es
> gratis y rápido. Reserva Textract para los complicados.

---

# Módulo C18 — CloudWatch + X-Ray

## CloudWatch Logs

ECS ya manda logs si configuraste `awslogs` (módulo C12). Para queries
útiles:

### Logs Insights queries
```
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 50
```

```
fields @timestamp, latency_ms, model
| filter status = 200
| stats avg(latency_ms), pct(latency_ms, 95), pct(latency_ms, 99) by model
```

## CloudWatch Metrics + Alarmas

### Métrica custom: tokens consumidos
```python
import boto3
cloudwatch = boto3.client("cloudwatch")
cloudwatch.put_metric_data(
    Namespace="RAG",
    MetricData=[{
        "MetricName": "TokensConsumed",
        "Value": tokens,
        "Unit": "Count",
        "Dimensions": [{"Name": "Model", "Value": "claude-3-haiku"}]
    }]
)
```

### Alarma de presupuesto LLM diario
```bash
aws cloudwatch put-metric-alarm \
    --alarm-name rag-tokens-daily-budget \
    --metric-name TokensConsumed --namespace RAG \
    --period 86400 --statistic Sum \
    --threshold 5000000 --comparison-operator GreaterThanThreshold \
    --evaluation-periods 1 \
    --alarm-actions arn:aws:sns:us-east-1:<ACCT>:rag-alerts
```

## X-Ray (tracing distribuido)

Te muestra: HTTP request → ALB → ECS → Bedrock → OpenSearch → response,
con latencia de cada hop. Inestimable para debug.

### Activar
1. Añade `aws-xray-sdk` a requirements.
2. En `app/main.py`:
```python
from aws_xray_sdk.core import xray_recorder, patch_all
from aws_xray_sdk.ext.fastapi.middleware import XRayMiddleware

xray_recorder.configure(service="asistente-rag")
patch_all()  # parchea boto3, requests, httpx automáticamente

app.add_middleware(XRayMiddleware, recorder=xray_recorder)
```
3. Run xray daemon como sidecar en la task ECS.
4. Ver mapas en Console → X-Ray.

## 🧠 Consejo
> Crea **un dashboard** en CloudWatch con: req/min, p99 latency, errors,
> tokens/día, costo estimado. Lo abres una vez al día como termómetro.

---

# Módulo C19 — Bedrock Evaluations

## Concepto

Bedrock tiene un servicio de **evaluación de modelos** integrado que
hace lo que Ragas hace, pero gestionado:
- Subes un dataset (CSV/JSONL).
- Eliges modelo, métricas, modelo-juez.
- AWS corre evaluación.
- Reporte con puntajes.

## Pasos (consola)

1. Bedrock → Model evaluation → Create.
2. Type: Automatic (LLM-as-judge) o Human.
3. Model: Claude 3 Haiku.
4. Task type: Question and Answer.
5. Dataset: subes JSONL al S3 con `{"prompt":"...","reference":"..."}`.
6. Metrics: Accuracy, Robustness, Toxicity.
7. Run.

Los resultados quedan en S3 con un reporte HTML.

## Cuándo usar Bedrock Eval vs Ragas

| | Bedrock Eval | Ragas |
|---|--------------|-------|
| Setup | Cero código | Pip install + script |
| Métricas RAG-específicas (faithfulness, context recall) | Limitado | ✓ |
| Métricas custom | No | ✓ |
| Costo | Por evaluación | Tokens del juez |

**Combina ambos**: Ragas en CI para iteración rápida, Bedrock Eval para
reportes ejecutivos formales.

---

# Módulo C20 — SageMaker Studio

## Para qué

Notebooks Jupyter en la nube con acceso directo a Bedrock, S3,
OpenSearch — sin instalar nada local. Útil para:
- Exploración de datos.
- Experimentar con chunking strategies.
- Tunear parámetros.
- Análisis de logs.

## Pasos

### C20.1 — Crear Studio domain
Console → SageMaker → Studio → Create domain. (Toma 5-10 min.)

### C20.2 — Lanzar Studio
Click "Launch" → ambiente Jupyter con kernels pre-configurados.

### C20.3 — Notebook ejemplo
```python
# Cell 1: leer corpus desde S3
import boto3, pandas as pd
s3 = boto3.client("s3")
# ...

# Cell 2: experimentar con varios chunk_size
for size in [500, 1000, 1500, 2000]:
    chunks = chunk_text(text, chunk_size=size)
    print(f"size={size}: {len(chunks)} chunks, avg_len={sum(len(c.text) for c in chunks)/len(chunks):.0f}")

# Cell 3: visualizar embeddings con UMAP
import umap
reducer = umap.UMAP()
coords = reducer.fit_transform(embeddings)
plt.scatter(coords[:,0], coords[:,1], c=[colors[d] for d in domains])
```

## Costos
~$1/hora de notebook activo (kernel ml.t3.medium). **Apaga** cuando
termines.

---

# Módulo C21 — CDK (Infrastructure as Code)

## Por qué IaC

Hasta ahora todo se hizo con `aws ... create ...` en CLI. Eso NO es
sostenible: cuando quieres recrear todo en otra región o limpiar
recursos, te toca recordar 50 comandos.

**IaC = define infraestructura en código, versionada en git, idempotente**.

Opciones: **CDK** (TypeScript/Python), **Terraform** (HCL),
**CloudFormation** (YAML), **Pulumi**.

CDK en Python te permite usar el mismo lenguaje que tu app.

## Pasos

### C21.1 — Instalar
```bash
npm install -g aws-cdk
mkdir infra && cd infra
cdk init app --language python
source .venv/bin/activate
pip install aws-cdk-lib constructs
```

### C21.2 — Stack ejemplo
```python
# infra/rag_stack.py
from aws_cdk import (
    Stack, Duration,
    aws_s3 as s3,
    aws_secretsmanager as sm,
    aws_ecs as ecs,
    aws_ecr_assets as ecr_assets,
    aws_ec2 as ec2,
    aws_iam as iam,
)
from constructs import Construct

class RagStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Bucket S3
        bucket = s3.Bucket(
            self, "DocsBucket",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )

        # Secret OpenAI
        openai_secret = sm.Secret(self, "OpenAiKey", secret_name="rag/openai-api-key")

        # VPC mínima
        vpc = ec2.Vpc(self, "Vpc", max_azs=2, nat_gateways=0)

        # Cluster ECS + servicio
        cluster = ecs.Cluster(self, "Cluster", vpc=vpc)
        task = ecs.FargateTaskDefinition(self, "Task", cpu=1024, memory_limit_mib=2048)

        image = ecr_assets.DockerImageAsset(self, "Image", directory="..")
        task.add_container(
            "api",
            image=ecs.ContainerImage.from_docker_image_asset(image),
            port_mappings=[ecs.PortMapping(container_port=8000)],
            environment={"AWS_REGION": "us-east-1", "VECTOR_STORE": "chroma"},
            secrets={"OPENAI_API_KEY": ecs.Secret.from_secrets_manager(openai_secret)},
            logging=ecs.LogDrivers.aws_logs(stream_prefix="api"),
        )

        # Permisos: Bedrock + S3
        task.task_role.add_to_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeModel"], resources=["*"]
        ))
        bucket.grant_read_write(task.task_role)
```

### C21.3 — Deploy
```bash
cdk bootstrap  # solo la primera vez por cuenta/región
cdk synth      # ver el CloudFormation generado
cdk deploy     # aplica
```

### C21.4 — Destroy
```bash
cdk destroy
```

## 🧠 Consejo
> Después del primer deploy, **deja todo en CDK** y nunca más toques
> nada por consola/CLI. Lo que se hace fuera de IaC se llama "drift" y
> te muerde el día menos pensado.

---

# Módulo C22 — CI/CD

## Pipeline objetivo

```
Push a main → GitHub Actions → tests → build Docker → push ECR → cdk deploy → smoke test
```

## GitHub Actions

`.github/workflows/deploy.yml`:
```yaml
name: Deploy
on: {push: {branches: [main]}}
permissions: {id-token: write, contents: read}  # OIDC

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - run: pip install -r requirements.txt
      - run: pytest -q

      # OIDC: GitHub se autentica como rol AWS sin claves estáticas
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::<ACCT>:role/github-deploy
          aws-region: us-east-1

      - uses: aws-actions/amazon-ecr-login@v2

      - name: Build, tag, push
        run: |
          IMAGE=<ACCT>.dkr.ecr.us-east-1.amazonaws.com/asistente-rag
          docker build -t $IMAGE:${{ github.sha }} -t $IMAGE:latest .
          docker push $IMAGE:${{ github.sha }}
          docker push $IMAGE:latest

      - name: Deploy CDK
        run: |
          cd infra
          npm install -g aws-cdk
          pip install -r requirements.txt
          cdk deploy --require-approval never

      - name: Smoke test
        run: |
          sleep 30
          curl -fsS https://asistente-rag.midominio.com/health
```

## OIDC (sin claves AWS estáticas en GitHub)

1. En IAM, crea un Identity Provider tipo OIDC apuntando a `token.actions.githubusercontent.com`.
2. Crea un rol con trust policy que permita a tu repo asumirlo.
3. Adjunta políticas mínimas (push ECR + deploy CDK).

Beneficio: no tienes credenciales en GitHub Secrets. Cero rotación.

## 🧠 Consejo
> Pon **branch protection** en `main`: requiere PR review + CI pasando
> antes de mergear. Tu pipeline se vuelve la única ruta a producción.

---

# Módulo C23 — Optimización de costos

## Servicios "always on" — los caros

| Servicio | Estimado mes | Cómo bajar |
|----------|--------------|------------|
| OpenSearch Serverless | $700+ | Usar Aurora pgvector |
| Aurora Serverless v2 | $43+ | Pause when idle (manual) |
| ECS Fargate (1 task) | $30 | App Runner ($5 mín)? Lambda? |
| ALB | $20 | API Gateway + Lambda en lugar |
| NAT Gateway | $32 | VPC endpoints (S3, Bedrock) |

## Pay-per-use — los baratos

| Servicio | Costo |
|----------|-------|
| Bedrock | Por token |
| Lambda | Por ms |
| S3 | Por GB |
| Textract | Por página |
| SQS | Por request (1M gratis/mes) |

## Tips concretos

1. **Reserved Capacity en Bedrock**: si usas >>$1K/mes, evalúa
   Provisioned Throughput.
2. **Cache de embeddings**: hash los chunks antes de embedear; si ya
   existe, no pagues de nuevo.
3. **Cache de respuestas LLM**: para preguntas idénticas, Redis/ElastiCache.
4. **Modelo más barato**: Haiku vs Sonnet ~12x más barato. Mide calidad antes de subir.
5. **Reduce contexto**: rerank a 3 chunks no 10. Cada chunk extra son tokens.
6. **Spot tasks ECS** si tu carga tolera interrupciones.

## Cost Explorer + Budgets

```bash
# Budget de $50/mes con alerta 80%
aws budgets create-budget --account-id <ACCT> --budget '{
  "BudgetName":"rag-monthly",
  "BudgetLimit":{"Amount":"50","Unit":"USD"},
  "TimeUnit":"MONTHLY",
  "BudgetType":"COST"
}' --notifications-with-subscribers '[{
  "Notification":{"NotificationType":"ACTUAL","ComparisonOperator":"GREATER_THAN","Threshold":80},
  "Subscribers":[{"SubscriptionType":"EMAIL","Address":"tu@email.com"}]
}]'
```

## 🧠 Consejo
> Etiqueta TODOS los recursos con `tag:Project=rag`. Cost Explorer te
> deja filtrar por tag y ver cuánto te cuesta el proyecto al céntimo.

---

# Módulo C24 — Well-Architected Review

AWS Well-Architected Framework: 6 pilares. Aplicado a nuestro RAG:

## 1. Operational Excellence
- ✅ IaC con CDK (todo versionado).
- ✅ Logs centralizados en CloudWatch.
- ✅ Pipeline CI/CD.
- ⚠️ Runbooks: documenta cómo recuperarte de fallos comunes.

## 2. Security
- ✅ Secrets Manager (no claves en código).
- ✅ IAM por privilegio mínimo (task role distinto a execution role).
- ✅ HTTPS forzado, certificado ACM.
- ✅ Cognito + JWT + RBAC.
- ⚠️ WAF para protección de capa 7.
- ⚠️ Auditoría: CloudTrail activo en toda la cuenta.
- ⚠️ Prompt injection: sanitización de inputs.

## 3. Reliability
- ✅ Multi-AZ (subnets en ≥2 AZs).
- ✅ Auto-scaling ECS.
- ✅ Health checks ALB + DLQ en SQS.
- ⚠️ Backup: snapshots Aurora, versioning S3.
- ⚠️ DR plan: ¿qué si us-east-1 cae? Multi-region cold standby.

## 4. Performance Efficiency
- ✅ Fargate Spot para cargas tolerantes.
- ✅ Caché de embeddings (próximo paso).
- ⚠️ Pruebas de carga (k6/locust) antes de prod.
- ⚠️ CDN: CloudFront delante del ALB para activos estáticos.

## 5. Cost Optimization
- ✅ Budget alerts.
- ✅ Tagging.
- ⚠️ Reserved Capacity si volumen es predecible.
- ⚠️ Apagar dev/staging fuera de horario (Lambda + EventBridge).

## 6. Sustainability
- ✅ Fargate (pagas por uso, no idle).
- ⚠️ Region selection: regiones con energía renovable (ej. eu-west-3).

## 🧠 Consejo
> Cada 6 meses, revisa los 6 pilares. Anota dónde estás verde, amarillo,
> rojo. Prioriza los rojos en el siguiente quarter.

---

# Módulo C25 — Limpieza

## Por qué importa

Si dejas todo encendido sin querer, al final de mes tendrás una factura
sorpresa de $500+. **Siempre limpia recursos** que no usas.

## Orden de borrado (respeta dependencias)

```bash
# 1) Servicio ECS → tasks
aws ecs update-service --cluster rag-cluster --service asistente-rag --desired-count 0
aws ecs delete-service --cluster rag-cluster --service asistente-rag --force

# 2) Cluster ECS
aws ecs delete-cluster --cluster rag-cluster

# 3) ALB + Target Group + Listeners
aws elbv2 delete-load-balancer --load-balancer-arn <ALB_ARN>
aws elbv2 delete-target-group --target-group-arn <TG_ARN>

# 4) Aurora cluster
aws rds delete-db-instance --db-instance-identifier rag-aurora-instance-1 --skip-final-snapshot
aws rds delete-db-cluster --db-cluster-identifier rag-aurora --skip-final-snapshot

# 5) OpenSearch Serverless
aws opensearchserverless delete-collection --id <COLLECTION_ID>

# 6) Bedrock KB / Agent (consola es más fácil)

# 7) S3 (vacía primero, luego elimina)
aws s3 rm s3://mi-banco-rag-docs --recursive
aws s3api delete-bucket --bucket mi-banco-rag-docs

# 8) Lambdas
aws lambda delete-function --function-name rag-ingest-worker
aws lambda delete-function --function-name rag-fraud-tool

# 9) SQS
aws sqs delete-queue --queue-url <QUEUE_URL>
aws sqs delete-queue --queue-url <DLQ_URL>

# 10) Secrets Manager (con period delay, o force)
aws secretsmanager delete-secret --secret-id rag/openai-api-key --force-delete-without-recovery

# 11) ECR (vacía y elimina)
aws ecr delete-repository --repository-name asistente-rag --force

# 12) CloudWatch log groups
aws logs delete-log-group --log-group-name /ecs/asistente-rag
aws logs delete-log-group --log-group-name /aws/lambda/rag-ingest-worker

# 13) Cognito User Pool
aws cognito-idp delete-user-pool --user-pool-id us-east-1_XXXXX

# 14) Route53 record (si lo creaste manual)

# 15) ACM cert (si ya nadie lo usa)
aws acm delete-certificate --certificate-arn <CERT_ARN>
```

## Lo más fácil: si todo está en CDK
```bash
cd infra
cdk destroy --all
```

Un comando, todo limpio.

## Verifica que no queda nada
```bash
# Ver costos del último día
aws ce get-cost-and-usage \
    --time-period Start=$(date -u -d "yesterday" +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \
    --granularity DAILY --metrics UnblendedCost
```

Tu factura de mañana debería ser ~$0.

## 🧠 Consejo
> Después de cada sesión de práctica, ejecuta `cdk destroy`. Mañana
> recreas con `cdk deploy` en 5 minutos. **No pagues por aprender mientras duermes.**

---

# 🎓 Examen Final Cloud-Native

## Comprensión

1. ¿Cuándo usar **Bedrock Knowledge Bases** vs construir el RAG a mano?
2. ¿Por qué **Cohere Embed Multilingual** suele ganar a **Titan** para español?
3. ¿Qué diferencia hay entre `executionRoleArn` y `taskRoleArn` en ECS?
4. ¿Por qué **OpenSearch Serverless** es ~10x más caro que **Aurora pgvector**
   en cargas pequeñas?
5. ¿Para qué sirve **OIDC** entre GitHub Actions y AWS?
6. ¿Qué pasa si pones `VisibilityTimeout < Lambda timeout` en SQS+Lambda?
7. ¿Cuándo conviene **Step Functions Standard** vs **Express**?
8. ¿Qué dos servicios usarías para **eliminar NAT Gateway** y bajar $30/mes?
   *(Pista: VPC endpoints).*
9. ¿Por qué cifrado **SSE-KMS** en lugar de **SSE-S3** para datos altamente regulados?
10. ¿Qué falla si tu task role no tiene permisos `bedrock:InvokeModel`?

## Ejercicios prácticos

### EC1 — Migración progresiva
Tu app local usa Chroma + OpenAI. Migra a Bedrock + OpenSearch Serverless
**sin interrumpir el servicio**. (Pista: feature flag + dual-write).

### EC2 — VPC endpoints
Configura VPC endpoints para S3, Bedrock, Secrets Manager. Elimina el
NAT Gateway. Verifica que la app sigue funcionando.

### EC3 — Multi-tenant
Usa Cognito groups como filtro automático en retrieval: cada usuario
solo ve los chunks autorizados a su grupo.

### EC4 — Bedrock Agent
Replica `FinancialAgent` en Bedrock Agents. Compara latencia y calidad
con tu agente Python.

### EC5 — Disaster Recovery
Simula una caída de us-east-1. Documenta cómo recuperarías el servicio
desde us-west-2 en <1 hora. Implementa los pasos.

### EC6 — Cost dashboard
Crea un dashboard CloudWatch con: tokens/día, $ estimado/día por
servicio, p99 latency, error rate.

### EC7 — IaC completo
Migra **todo** lo que hiciste por consola/CLI a un CDK stack. Destruye
manualmente y recréalo con `cdk deploy` en limpio.

### EC8 — CI/CD blue-green
Configura deploys blue-green en ECS: nueva versión arranca al lado de
la vieja, ALB redirige tráfico gradualmente. Rollback en 1 click.

### EC9 — WAF + rate limiting
Pon WAF delante del ALB. Bloquea: SQL injection, IPs con >100 req/min,
geolocalizaciones de alto riesgo.

### EC10 — Observabilidad full
Integra X-Ray, CloudWatch Logs Insights queries guardadas, alarmas
en SNS → email + Slack. Documenta runbooks por alarma.

## ✅ Criterio de aprobación

Si después de este curso:
- Puedes diseñar la arquitectura cloud de un nuevo caso de uso RAG en una pizarra.
- Sabes los costos aproximados de cada componente.
- Puedes argumentar por qué eliges X sobre Y en cada capa.
- Sabes cómo desplegar y limpiar todo con un comando.
- Puedes hablar fluidamente del Well-Architected Framework.

**Eres un AWS RAG Solutions Architect**. Vale como tema de conversación
en entrevistas y como diferencial en propuestas a clientes.

---

## 📚 Recursos AWS oficiales

- **AWS Well-Architected Framework Generative AI Lens**: https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/
- **Bedrock User Guide**: https://docs.aws.amazon.com/bedrock/
- **Bedrock Knowledge Bases**: https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html
- **OpenSearch Serverless**: https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless.html
- **AWS CDK Workshop**: https://cdkworkshop.com/
- **AWS Samples (RAG)**: https://github.com/aws-samples/amazon-bedrock-rag

## 📌 Templates listos para copiar

Todos los archivos de configuración (task-def.json, lifecycle policies,
IAM policies, CDK stacks completos) están como referencia en este
documento. Copia, ajusta a tu cuenta, despliega.

---

## 🎯 Cierre

Has cubierto:
- 25 módulos de servicios AWS aplicados.
- Dos arquitecturas: managed (Bedrock KB) y construida.
- Seguridad, observabilidad, IaC, CI/CD, costos.
- Well-Architected aplicado a Gen AI.

El paso final no está en este documento: **constrúyelo en TU caso real**
con TUS documentos y TUS preguntas. Mide. Itera. Optimiza costos.

> **Recuerda**: la nube no es magia, es **operación**. La diferencia
> entre un sistema que funciona el día 1 y uno que funciona el día 365
> es la disciplina de monitorear, medir y optimizar continuamente.

**Felicidades. Ahora ve a operar.** ☁️🚀
