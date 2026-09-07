"""Carga documentos fuente (Markdown con frontmatter, JSON o PDF) como
objetos langchain_core.documents.Document con metadatos normalizados:
id, source, category, page.
"""
import json
from pathlib import Path
from typing import List

from langchain_core.documents import Document

from . import config


def _parse_markdown_frontmatter(text: str) -> tuple[dict, str]:
    """Parsea un frontmatter YAML simple delimitado por '---' sin dependencias extra."""
    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    _, raw_frontmatter, body = parts
    metadata = {}
    for line in raw_frontmatter.strip().splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()
    return metadata, body.strip()


def _load_markdown_file(path: Path) -> Document:
    text = path.read_text(encoding="utf-8")
    metadata, body = _parse_markdown_frontmatter(text)
    metadata.setdefault("id", path.stem)
    metadata.setdefault("source", path.name)
    metadata.setdefault("category", "general")
    metadata.setdefault("page", 1)
    return Document(page_content=body, metadata=metadata)


def _load_json_file(path: Path) -> List[Document]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    entries = raw if isinstance(raw, list) else [raw]
    docs = []
    for entry in entries:
        content = entry.pop("content", "") or entry.pop("text", "")
        entry.setdefault("source", path.name)
        entry.setdefault("category", "general")
        entry.setdefault("page", 1)
        docs.append(Document(page_content=content, metadata=entry))
    return docs


def _load_pdf_file(path: Path) -> List[Document]:
    from langchain_community.document_loaders import PyPDFLoader

    loaded = PyPDFLoader(str(path)).load()
    for i, doc in enumerate(loaded):
        doc.metadata.setdefault("id", f"{path.stem}-p{i + 1}")
        doc.metadata.setdefault("source", path.name)
        doc.metadata.setdefault("category", "general")
        doc.metadata["page"] = doc.metadata.get("page", i) + 1
    return loaded


def load_source_documents(documents_dir: Path = config.DOCUMENTS_DIR) -> List[Document]:
    """Recorre data/documents y devuelve todos los Document soportados (.md, .json, .pdf)."""
    documents: List[Document] = []
    for path in sorted(documents_dir.glob("*")):
        if path.suffix.lower() == ".md":
            documents.append(_load_markdown_file(path))
        elif path.suffix.lower() == ".json":
            documents.extend(_load_json_file(path))
        elif path.suffix.lower() == ".pdf":
            documents.extend(_load_pdf_file(path))
    return documents
