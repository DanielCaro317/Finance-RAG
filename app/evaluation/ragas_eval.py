"""
evaluation/ragas_eval.py — Evaluación con Ragas ("LLM as a Judge").

MÉTRICAS QUE CALCULA:
=====================
  - faithfulness:        ¿la respuesta está respaldada por los chunks?
                         Penaliza alucinaciones.
  - answer_relevancy:    ¿la respuesta aborda directamente la pregunta?
  - context_precision:   ¿los chunks recuperados son relevantes y bien
                         ordenados (los relevantes en posiciones altas)?
  - context_recall:      ¿se recuperaron los chunks necesarios para
                         contestar bien? Requiere ground_truth.

PUNTOS DE CUIDADO:
  - Ragas usa el LLM como juez — el costo de una evaluación de 50
    preguntas puede ser de USD 0.20–1.00 (dependiendo del modelo).
  - Idealmente, ejecuta esto en CI tras cada cambio significativo
    (nuevo modelo, nuevo chunking) y guarda los scores históricos.
"""
from __future__ import annotations

from typing import Any

from loguru import logger

from app.core.agent import answer_with_rag
from app.evaluation.dataset import GOLDEN_SET


def run_evaluation() -> dict[str, Any]:
    """
    Ejecuta el pipeline contra el GOLDEN_SET y calcula métricas Ragas.

    NOTA: Esta función importa ragas localmente porque algunas instalaciones
    fallan en Windows; así no rompemos el resto del sistema si falta.
    """
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import (
            answer_relevancy,
            context_precision,
            context_recall,
            faithfulness,
        )
    except ImportError as e:
        logger.error(f"Ragas no disponible: {e}")
        return {"error": str(e)}

    rows: list[dict[str, Any]] = []
    for ex in GOLDEN_SET:
        result = answer_with_rag(ex["question"], use_agent=False)
        rows.append({
            "question": ex["question"],
            "answer": result["answer"],
            "contexts": [c.text for c in result["chunks"]],
            "ground_truth": ex["ground_truth"],
        })

    ds = Dataset.from_list(rows)
    scores = evaluate(
        ds,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
    )
    return {"summary": scores.to_pandas().mean(numeric_only=True).to_dict(),
            "rows": rows}
