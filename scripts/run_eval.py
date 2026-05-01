"""scripts/run_eval.py — Ejecuta la evaluación Ragas y muestra el resumen."""
from __future__ import annotations

import json

from app.evaluation.ragas_eval import run_evaluation


if __name__ == "__main__":
    out = run_evaluation()
    print(json.dumps(out.get("summary", out), indent=2, ensure_ascii=False))
