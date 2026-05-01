"""
evaluation/dataset.py — Dataset de evaluación "Golden Set".

¿QUÉ ES UN GOLDEN SET?
======================
Es una lista curada de pares (pregunta, respuesta_esperada, contextos_correctos).
Sirve como "verdad de referencia" contra la cual medir el RAG cada
vez que cambias chunking, modelo, prompts, etc.

REGLA DE ORO: empieza con 20-50 ejemplos REALES (preguntas que harán
los usuarios de verdad), no inventados al aire.

PUNTOS DE CUIDADO:
  - Versiona el dataset (git). Cada cambio en el corpus puede invalidarlo.
  - Incluye ejemplos "trampa" — preguntas SIN respuesta en el corpus,
    para verificar que el modelo dice "no sé" en vez de alucinar.
"""
from __future__ import annotations

GOLDEN_SET: list[dict] = [
    {
        "question": "¿Cuál es el monto máximo permitido para una transferencia internacional sin aprobación adicional?",
        "ground_truth": "El monto máximo permitido es USD 10,000 sin aprobación adicional según la política de fraude tecnológico v2.",
    },
    {
        "question": "¿Qué señales indican fraude en transacciones con tarjeta?",
        "ground_truth": "Velocidad anormal de transacciones, geolocalización inusual y montos atípicos comparados con el patrón del cliente.",
    },
    {
        "question": "¿Cuál es la temperatura del sol?",
        "ground_truth": "No encontré información suficiente en las políticas.",
    },
]
