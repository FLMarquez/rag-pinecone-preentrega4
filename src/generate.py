"""Genera una respuesta en lenguaje natural a partir de los documentos
recuperados por RAGSystem, usando la API REST de Gemini.

Se llama a la API REST directamente con `requests` en vez de usar el SDK
`google-genai` / `langchain_google_genai`: en este entorno el SDK resultó
lento e inestable (llegaba a colgarse) para generación de texto, mientras
que la misma petición vía REST responde en segundos de forma consistente.

Uso:
    python -m src.generate "¿Cómo configuro un timeout en requests?"
"""
import sys

import requests
from langchain_core.documents import Document

from . import config
from .hybrid_retriever import RAGSystem

GEMINI_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/{model}:generateContent"

PROMPT_TEMPLATE = """Respondé la pregunta del usuario basándote únicamente en el \
siguiente contexto. Si el contexto no alcanza para responder, decilo explícitamente \
en vez de inventar información. Citá las fuentes usando su id entre corchetes, por \
ejemplo [{example_id}].

Contexto:
{context}

Pregunta: {question}

Respuesta:"""


def build_context(docs: list[Document]) -> str:
    partes = []
    for doc in docs:
        doc_id = doc.metadata.get("parent_id", doc.metadata.get("id", "desconocido"))
        partes.append(f"[{doc_id}]\n{doc.page_content}")
    return "\n\n".join(partes)


def call_gemini(prompt: str, model: str = None, timeout: int = 60, retries: int = 2) -> str:
    model = model or config.GENERATION_MODEL
    model_path = model if model.startswith("models/") else f"models/{model}"
    url = GEMINI_URL_TEMPLATE.format(model=model_path)

    # La API de Gemini a veces responde con latencia muy variable en redes
    # inestables; reintentamos ante timeouts en vez de fallar directamente.
    last_error = None
    for attempt in range(retries + 1):
        try:
            response = requests.post(
                url,
                params={"key": config.GOOGLE_API_KEY},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=timeout,
            )
            response.raise_for_status()
            data = response.json()
            parts = data["candidates"][0]["content"]["parts"]
            return "".join(part.get("text", "") for part in parts)
        except requests.exceptions.Timeout as e:
            last_error = e
            print(f"  (timeout en intento {attempt + 1}/{retries + 1}, reintentando...)")

    raise last_error


def answer(question: str, k: int = None) -> str:
    config.require_api_keys()
    rag = RAGSystem(top_k=k or config.TOP_K)
    docs = rag.query(question, k=k)

    if not docs:
        return "No encontré documentos relevantes para responder esa pregunta."

    example_id = docs[0].metadata.get("parent_id", docs[0].metadata.get("id", "doc1"))
    prompt = PROMPT_TEMPLATE.format(
        context=build_context(docs),
        question=question,
        example_id=example_id,
    )

    return call_gemini(prompt)


if __name__ == "__main__":
    pregunta = " ".join(sys.argv[1:]) or "¿Cómo configuro un timeout en requests?"
    print(f"Pregunta: {pregunta}\n")
    print(answer(pregunta))
