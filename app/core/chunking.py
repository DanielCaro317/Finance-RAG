"""
core/chunking.py — Estrategias de fragmentación (chunking).

¿QUÉ ES "CHUNKING" Y POR QUÉ IMPORTA TANTO? (lección clave del Masterclass)
==========================================================================
Los LLMs tienen ventana de contexto limitada y los embeddings funcionan mejor
sobre fragmentos cortos y semánticamente cohesivos. Por eso PARTIMOS los
documentos en "chunks". Pero NO sirve cualquier corte:

  ❌ Fixed-size (cortar cada N caracteres):
       "Tarjeta de crédito |se considera fraude| cuando..."
       El significado se rompe a la mitad. El embedding pierde sentido.

  ✅ Recursive / semántico:
       Respeta separadores naturales (\\n\\n párrafo > \\n línea > . frase).
       Mantiene unidades de significado intactas.

PARÁMETROS CLAVE:
  - chunk_size:   Tamaño objetivo (en caracteres o tokens). 500–1500 típicamente.
  - chunk_overlap: Solapamiento entre chunks consecutivos (10–20% del size).
                   Evita perder contexto en bordes.

PUNTOS DE CUIDADO:
  - Solapamiento excesivo => duplicación, infla la base, costo y ruido.
  - Solapamiento nulo => pierdes contexto al borde y bajas faithfulness.
  - Para Markdown/HTML conviene un splitter que respete encabezados.
"""
from __future__ import annotations

from dataclasses import dataclass

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)


@dataclass
class Chunk:
    """Estructura simple para un fragmento generado."""
    text: str
    index: int
    extra_metadata: dict[str, str]


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
) -> list[Chunk]:
    """
    Splitter recursivo: la opción "general purpose" más segura.

    NOTA: Internamente intenta cortar primero por '\\n\\n', luego '\\n',
    luego ' ', y por último carácter. Así respeta el lenguaje natural
    cuando puede.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        # length_function=len cuenta caracteres. Para contar tokens reales
        # podrías usar tiktoken (más preciso para presupuesto LLM).
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    pieces = splitter.split_text(text)
    return [Chunk(text=p, index=i, extra_metadata={}) for i, p in enumerate(pieces)]


def chunk_markdown(text: str) -> list[Chunk]:
    """
    Splitter consciente de encabezados Markdown.

    VENTAJA: Cada chunk hereda como metadata el título de su sección
    (H1, H2, H3). Esto mejora muchísimo la recuperación porque el LLM
    "sabe" de qué política es cada fragmento.

    VARIACIÓN POSIBLE:
      - Combina con RecursiveCharacterTextSplitter para sub-dividir
        secciones que sean demasiado largas tras el split por encabezado.
    """
    headers_to_split_on = [
        ("#", "h1"),
        ("##", "h2"),
        ("###", "h3"),
    ]
    md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    docs = md_splitter.split_text(text)

    # Tras dividir por encabezados, sub-dividimos secciones largas.
    sub = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)

    chunks: list[Chunk] = []
    idx = 0
    for d in docs:
        for piece in sub.split_text(d.page_content):
            chunks.append(Chunk(text=piece, index=idx, extra_metadata=dict(d.metadata)))
            idx += 1
    return chunks
