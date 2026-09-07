"""Verifica si el índice Serverless de Pinecone existe y lo crea si hace falta.

Uso:
    python -m src.setup_pinecone
"""
import time

from pinecone import Pinecone, ServerlessSpec

from . import config


def get_pinecone_client() -> Pinecone:
    config.require_api_keys()
    return Pinecone(api_key=config.PINECONE_API_KEY)


def ensure_index_exists() -> None:
    pc = get_pinecone_client()
    existing_names = {idx["name"] for idx in pc.list_indexes()}

    if config.INDEX_NAME in existing_names:
        print(f"El índice '{config.INDEX_NAME}' ya existe. No se crea de nuevo.")
        return

    print(
        f"Creando índice Serverless '{config.INDEX_NAME}' "
        f"(dim={config.EMBEDDING_DIMENSION}, cloud={config.PINECONE_CLOUD}, "
        f"region={config.PINECONE_REGION})..."
    )
    pc.create_index(
        name=config.INDEX_NAME,
        dimension=config.EMBEDDING_DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(cloud=config.PINECONE_CLOUD, region=config.PINECONE_REGION),
    )

    while not pc.describe_index(config.INDEX_NAME).status["ready"]:
        print("Esperando a que el índice quede listo...")
        time.sleep(2)

    print(f"Índice '{config.INDEX_NAME}' creado y listo.")


if __name__ == "__main__":
    ensure_index_exists()
