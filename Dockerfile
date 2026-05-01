# =============================================================================
# Dockerfile — empaqueta la app FastAPI en un contenedor reproducible.
# =============================================================================
# NOTA AL MARGEN:
#   Un Dockerfile es la "receta" para construir una imagen Docker. La imagen
#   contiene Python + tu código + dependencias y corre IGUAL en tu laptop,
#   en ECS Fargate, o en Kubernetes.
#
# BUENAS PRÁCTICAS APLICADAS:
#   1. Imagen "slim" para reducir tamaño.
#   2. Multi-stage NO es necesario aquí (no compilamos nada).
#   3. Usuario no-root para mejorar seguridad.
#   4. Cache de pip se aprovecha si no cambias requirements.txt.
# =============================================================================
FROM python:3.11-slim

# Variables de entorno para Python.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencias del sistema necesarias para algunas libs (pypdf, etc).
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiamos primero requirements para aprovechar cache de capas.
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copiamos el resto del código.
COPY app ./app
COPY scripts ./scripts

# Usuario no-root.
RUN useradd -u 1000 -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

# Comando por defecto: arranca uvicorn.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
