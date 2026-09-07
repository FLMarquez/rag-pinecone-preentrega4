"""Configuración centralizada leída desde variables de entorno (.env)."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = PROJECT_ROOT / "data" / "documents"
GOLDEN_SET_PATH = PROJECT_ROOT / "data" / "golden_set.json"

PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

INDEX_NAME = os.environ.get("INDEX_NAME", "rag-preentrega4")
NAMESPACE = os.environ.get("PINECONE_NAMESPACE", "requests-docs")

PINECONE_CLOUD = os.environ.get("PINECONE_CLOUD", "aws")
PINECONE_REGION = os.environ.get("PINECONE_REGION", "us-east-1")

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSION = int(os.environ.get("EMBEDDING_DIMENSION", "1536"))

CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "100"))

TOP_K = int(os.environ.get("TOP_K", "5"))


def require_api_keys() -> None:
    missing = [
        name
        for name, value in [
            ("PINECONE_API_KEY", PINECONE_API_KEY),
            ("OPENAI_API_KEY", OPENAI_API_KEY),
        ]
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Faltan variables de entorno requeridas: "
            + ", ".join(missing)
            + ". Copiá .env.example a .env y completá los valores."
        )
