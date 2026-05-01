"""
tests/test_smoke.py — Tests de humo (no requieren API keys reales).

Estos tests verifican el "esqueleto" del sistema: que importe, que la
app FastAPI arranque, que /health responda. NO ejecutan llamadas a LLM.

Para correrlos:
    pytest -q
"""
from fastapi.testclient import TestClient


def test_health_endpoint():
    """El endpoint /health responde 200 con el shape esperado."""
    from app.main import app
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "vector_store" in body
    assert "llm_provider" in body


def test_mock_fraud_endpoint():
    """El endpoint mock devuelve un estado válido."""
    from app.main import app
    client = TestClient(app)
    r = client.get("/mock/fraud/TX-12345")
    assert r.status_code == 200
    body = r.json()
    assert body["transaction_id"] == "TX-12345"
    assert body["status"] in {"ok", "review", "fraud"}


def test_chunking_recursive():
    """El chunker recursivo no devuelve listas vacías."""
    from app.core.chunking import chunk_text
    text = "Párrafo uno.\n\nPárrafo dos con más contenido. " * 50
    chunks = chunk_text(text, chunk_size=200, chunk_overlap=50)
    assert len(chunks) > 1
    assert all(c.text for c in chunks)
