"""
core/llm.py — Abstracción del Gran Modelo de Lenguaje (LLM).

¿POR QUÉ UN ABSTRACTO?
======================
Hoy quizá uses GPT-4o, mañana Claude 3.5, pasado Gemini. Cambiar de
proveedor SIN tocar el resto del código solo se logra con una interfaz
común. Aquí la llamamos `LLMProvider`.

PUNTOS DE CUIDADO:
  - Cada proveedor tiene su propio formato de "tool calling". Aquí
    implementamos un patrón sencillo (texto + tool calling JSON).
  - Las temperaturas bajas (0–0.2) son MEJORES para RAG: minimizan
    creatividad innecesaria que genera alucinaciones.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from loguru import logger

from app.config import get_settings


class LLMProvider(ABC):
    name: str
    model: str

    @abstractmethod
    def chat(
        self,
        system: str,
        user: str,
        tools: Optional[list[dict[str, Any]]] = None,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        """
        Devuelve dict con:
          - 'content': str respuesta final (puede ser vacío si hay tool_calls).
          - 'tool_calls': lista de {name, arguments} (puede estar vacía).
        """


class OpenAIChatLLM(LLMProvider):
    name = "openai"

    def __init__(self, model: str, api_key: str):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def chat(self, system, user, tools=None, temperature=0.1):
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        resp = self.client.chat.completions.create(**kwargs)
        msg = resp.choices[0].message
        out: dict[str, Any] = {"content": msg.content or "", "tool_calls": []}
        if msg.tool_calls:
            import json
            for tc in msg.tool_calls:
                out["tool_calls"].append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments or "{}"),
                })
        return out


class AnthropicChatLLM(LLMProvider):
    name = "anthropic"

    def __init__(self, model: str, api_key: str):
        from anthropic import Anthropic
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def chat(self, system, user, tools=None, temperature=0.1):
        # Anthropic usa schema distinto para tools.
        # Convertimos del formato "OpenAI tools" al "Anthropic tools".
        anth_tools = []
        if tools:
            for t in tools:
                fn = t.get("function", t)
                anth_tools.append({
                    "name": fn["name"],
                    "description": fn.get("description", ""),
                    "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
                })

        kwargs: dict[str, Any] = {
            "model": self.model,
            "system": system,
            "messages": [{"role": "user", "content": user}],
            "temperature": temperature,
            "max_tokens": 1024,
        }
        if anth_tools:
            kwargs["tools"] = anth_tools

        resp = self.client.messages.create(**kwargs)
        out: dict[str, Any] = {"content": "", "tool_calls": []}
        for block in resp.content:
            if block.type == "text":
                out["content"] += block.text
            elif block.type == "tool_use":
                out["tool_calls"].append({
                    "id": block.id, "name": block.name, "arguments": block.input,
                })
        return out


class BedrockChatLLM(LLMProvider):
    """LLM vía AWS Bedrock (Claude alojado en AWS, no necesita API key extra)."""
    name = "bedrock"

    def __init__(self, model: str, region: str):
        import boto3
        import json
        self._json = json
        self.client = boto3.client("bedrock-runtime", region_name=region)
        self.model = model

    def chat(self, system, user, tools=None, temperature=0.1):
        # Asumimos modelo Claude en Bedrock (Anthropic schema).
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "system": system,
            "temperature": temperature,
            "messages": [{"role": "user", "content": user}],
        }
        if tools:
            body["tools"] = [
                {
                    "name": t["function"]["name"],
                    "description": t["function"].get("description", ""),
                    "input_schema": t["function"].get("parameters", {}),
                }
                for t in tools
            ]
        resp = self.client.invoke_model(
            modelId=self.model, body=self._json.dumps(body)
        )
        data = self._json.loads(resp["body"].read())
        out: dict[str, Any] = {"content": "", "tool_calls": []}
        for block in data.get("content", []):
            if block.get("type") == "text":
                out["content"] += block.get("text", "")
            elif block.get("type") == "tool_use":
                out["tool_calls"].append({
                    "id": block["id"], "name": block["name"],
                    "arguments": block.get("input", {}),
                })
        return out


def build_llm_provider() -> LLMProvider:
    s = get_settings()
    logger.info(f"LLM: provider={s.llm_provider} model={s.llm_model}")
    if s.llm_provider == "openai":
        if not s.openai_api_key:
            raise RuntimeError("Falta OPENAI_API_KEY en .env")
        return OpenAIChatLLM(model=s.llm_model, api_key=s.openai_api_key)
    if s.llm_provider == "anthropic":
        if not s.anthropic_api_key:
            raise RuntimeError("Falta ANTHROPIC_API_KEY en .env")
        return AnthropicChatLLM(model=s.llm_model, api_key=s.anthropic_api_key)
    if s.llm_provider == "bedrock":
        return BedrockChatLLM(model=s.llm_model, region=s.aws_region)
    raise ValueError(f"Provider desconocido: {s.llm_provider}")


_llm: Optional[LLMProvider] = None


def get_llm() -> LLMProvider:
    global _llm
    if _llm is None:
        _llm = build_llm_provider()
    return _llm
