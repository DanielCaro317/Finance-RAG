"""
core/agent.py — Agente RAG con herramientas (tool calling).

¿QUÉ ES UN "AGENTE"?
====================
Un agente es un LLM que decide DINÁMICAMENTE qué herramientas (tools)
invocar antes de responder. La diferencia con un RAG simple:

  RAG simple:    siempre busca en la BD vectorial -> contesta.
  Agente RAG:    decide si buscar, qué filtros usar, si llamar a una API
                 externa (ej. consultar resultado de fraude por ID), si
                 responder directamente, etc.

CICLO BÁSICO ("ReAct" simplificado):
  1. LLM recibe pregunta + lista de tools disponibles.
  2. LLM decide:
       a) Responder texto -> termina.
       b) Llamar a una tool con argumentos -> ejecuta y vuelve a 1
          con el resultado anexado al contexto.

PUNTOS DE CUIDADO:
  - Limita el número de iteraciones (evita loops infinitos).
  - Valida los argumentos de las tools (los LLMs alucinan parámetros).
  - Para producción serio considera frameworks (LangGraph, smolagents)
    pero entender la mecánica "a mano" como aquí es invaluable.
"""
from __future__ import annotations

import json
from typing import Any

from loguru import logger

from app.config import get_settings
from app.core.llm import LLMProvider, get_llm
from app.core.retriever import HybridRetriever, get_retriever, llm_rerank
from app.schemas.models import Citation, RetrievedChunk
from app.services.fraud_api import lookup_fraud_status


# =============================================================================
# Definición de las herramientas disponibles para el agente
# =============================================================================
# Formato estilo OpenAI; AnthropicChatLLM/BedrockChatLLM lo convierten
# internamente. Cada tool debe ser:
#   { "type": "function",
#     "function": { "name", "description", "parameters": JSONSchema } }
# =============================================================================
TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_policies",
            "description": (
                "Busca en la base de conocimiento corporativa (manuales de "
                "fraude, normativas, políticas) usando recuperación híbrida. "
                "Úsala SIEMPRE que la pregunta sea sobre políticas, reglas o "
                "procedimientos internos."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "La consulta semántica."},
                    "domain": {
                        "type": "string",
                        "enum": ["fraude_tecnologico", "tributario", "penal", "general"],
                        "description": "Dominio para filtrar resultados (opcional).",
                    },
                    "min_year": {
                        "type": "integer",
                        "description": "Año mínimo de vigencia (opcional).",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_fraud_status",
            "description": (
                "Consulta en tiempo real el estado de fraude de una "
                "transacción específica por su ID. Úsala cuando el usuario "
                "pregunte por una transacción concreta."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "string",
                        "description": "ID único de la transacción (ej. 'TX-12345').",
                    }
                },
                "required": ["transaction_id"],
            },
        },
    },
]


SYSTEM_PROMPT = """Eres un Asistente Cognitivo Financiero corporativo.

REGLAS ESTRICTAS:
1. Responde SOLO con base en la información recuperada por las herramientas
   o por el contexto provisto. Si no tienes evidencia suficiente, di
   explícitamente "No encontré información suficiente en las políticas".
2. Cita SIEMPRE la fuente al final usando el formato [source:page].
3. Si la pregunta es sobre una transacción específica, usa lookup_fraud_status.
4. Si la pregunta es sobre políticas o procedimientos, usa search_policies.
5. NO inventes números, fechas, ni nombres de regulaciones.
6. Sé conciso y profesional. Responde en el idioma del usuario.
"""


class FinancialAgent:
    """Agente con razonamiento + herramientas."""

    MAX_ITERATIONS = 4  # Cota de seguridad: evita ciclos largos.

    def __init__(self, llm: LLMProvider, retriever: HybridRetriever):
        self.llm = llm
        self.retriever = retriever
        # Memoria de los chunks usados, para citarlos en la respuesta final.
        self._used_chunks: list[RetrievedChunk] = []
        self._used_tools: list[str] = []

    # -------------------------------------------------------------------------
    def _execute_tool(self, name: str, args: dict[str, Any]) -> str:
        """Despachador de tools — agrega aquí las que vayas creando."""
        self._used_tools.append(name)
        if name == "search_policies":
            return self._tool_search(args)
        if name == "lookup_fraud_status":
            return self._tool_fraud(args)
        return f"ERROR: tool '{name}' no existe."

    def _tool_search(self, args: dict[str, Any]) -> str:
        s = get_settings()
        # Filtros de metadata: traducimos los argumentos del LLM.
        where: dict[str, Any] = {}
        if "domain" in args and args["domain"]:
            where["domain"] = args["domain"]
        if "min_year" in args and args["min_year"]:
            where["effective_year"] = {"$gte": int(args["min_year"])}

        candidates = self.retriever.retrieve(
            query=args["query"],
            top_k=s.retrieval_top_k,
            where=where or None,
        )

        # Reranking: filtramos al top_n más relevante.
        def _llm_call(system: str, user: str) -> str:
            return self.llm.chat(system=system, user=user, temperature=0.0)["content"]

        reranked = llm_rerank(args["query"], candidates, s.rerank_top_n, _llm_call)
        self._used_chunks.extend(reranked)

        # Devolvemos al LLM un texto plano con los pasajes relevantes.
        return "\n\n---\n\n".join(
            f"[{c.metadata.source}:p{c.metadata.page or '-'}] {c.text}"
            for c in reranked
        ) or "Sin resultados."

    def _tool_fraud(self, args: dict[str, Any]) -> str:
        result = lookup_fraud_status(args["transaction_id"])
        return json.dumps(result, ensure_ascii=False)

    # -------------------------------------------------------------------------
    def run(self, query: str) -> dict[str, Any]:
        """Bucle principal del agente."""
        self._used_chunks = []
        self._used_tools = []

        # En esta versión simplificada, ejecutamos UNA llamada con tools.
        # Si el modelo decide usar tools, las ejecutamos y hacemos UNA
        # segunda llamada con los resultados anexados al contexto.
        # (Implementación didáctica; producción usaría loop completo).
        first = self.llm.chat(
            system=SYSTEM_PROMPT,
            user=query,
            tools=TOOLS,
        )

        if not first["tool_calls"]:
            # Respondió directamente, sin usar tools.
            logger.warning("El agente no invocó tools — puede ser respuesta sin contexto.")
            return {
                "answer": first["content"],
                "chunks": self._used_chunks,
                "tools": self._used_tools,
            }

        # Ejecuta cada tool y construye un "tool_results" para el LLM.
        tool_outputs = []
        for tc in first["tool_calls"]:
            result = self._execute_tool(tc["name"], tc.get("arguments", {}))
            tool_outputs.append(f"[{tc['name']}] -> {result}")

        # Segunda pasada: el LLM ya tiene los resultados, redacta respuesta final.
        followup_user = (
            f"PREGUNTA ORIGINAL:\n{query}\n\n"
            f"RESULTADOS DE HERRAMIENTAS:\n" + "\n\n".join(tool_outputs) + "\n\n"
            "Redacta la respuesta final cumpliendo TODAS las reglas del system prompt. "
            "Cita las fuentes."
        )
        final = self.llm.chat(system=SYSTEM_PROMPT, user=followup_user)
        return {
            "answer": final["content"],
            "chunks": self._used_chunks,
            "tools": self._used_tools,
        }


# -----------------------------------------------------------------------------
def answer_with_rag(query: str, use_agent: bool = True) -> dict[str, Any]:
    """
    Punto de entrada de alto nivel.

    Si use_agent=False, hace un RAG "directo" (siempre busca y contesta).
    Si use_agent=True, deja al LLM decidir las tools.
    """
    llm = get_llm()
    retriever = get_retriever()

    if use_agent:
        return FinancialAgent(llm, retriever).run(query)

    # ---- RAG directo (sin agente) ------------------------------------------
    s = get_settings()
    cands = retriever.retrieve(query, top_k=s.retrieval_top_k)
    reranked = llm_rerank(
        query, cands, s.rerank_top_n,
        lambda sy, us: llm.chat(sy, us, temperature=0.0)["content"],
    )
    context = "\n\n---\n\n".join(
        f"[{c.metadata.source}:p{c.metadata.page or '-'}] {c.text}" for c in reranked
    )
    user_msg = (
        f"CONTEXTO:\n{context}\n\n"
        f"PREGUNTA: {query}\n\n"
        "Responde con base SOLO en el contexto. Cita [source:page]."
    )
    out = llm.chat(SYSTEM_PROMPT, user_msg)
    return {"answer": out["content"], "chunks": reranked, "tools": []}


def build_citations(chunks: list[RetrievedChunk], n: int = 4) -> list[Citation]:
    """Convierte chunks usados en objetos Citation para la respuesta."""
    out: list[Citation] = []
    for c in chunks[:n]:
        out.append(Citation(
            source=c.metadata.source,
            page=c.metadata.page,
            snippet=c.text[:240] + ("…" if len(c.text) > 240 else ""),
        ))
    return out
