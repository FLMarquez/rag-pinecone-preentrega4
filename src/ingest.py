"""Pipeline de ingesta: carga documentos, los divide en chunks, genera
embeddings y los sube a Pinecone incluyendo el texto original en la metadata
(evita consultas adicionales a una base relacional para recuperar el contenido).

Uso:
    python -m src.ingest
"""
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

from . import config
from .document_loader import load_source_documents
from .setup_pinecone import ensure_index_exists, get_pinecone_client


def build_chunks():
    source_docs = load_source_documents()
    if not source_docs:
        raise RuntimeError(
            f"No se encontraron documentos en {config.DOCUMENTS_DIR}. "
            "Agregá archivos .md, .json o .pdf antes de ejecutar la ingesta."
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        length_function=len,
    )

    chunks = []
    for doc in source_docs:
        parts = splitter.split_text(doc.page_content)
        for i, part in enumerate(parts):
            metadata = dict(doc.metadata)
            base_id = metadata.get("id", "doc")
            metadata["id"] = base_id if len(parts) == 1 else f"{base_id}-chunk{i}"
            metadata["parent_id"] = base_id
            metadata["chunk_index"] = i
            # Guardamos el texto original en la metadata para no depender
            # de una base relacional adicional al momento de recuperar.
            metadata["text"] = part
            chunks.append({"content": part, "metadata": metadata})

    print(f"{len(source_docs)} documentos fuente -> {len(chunks)} chunks generados.")
    return chunks


def run_ingestion() -> None:
    config.require_api_keys()
    ensure_index_exists()

    chunks = build_chunks()
    embeddings = OpenAIEmbeddings(
        model=config.EMBEDDING_MODEL,
        openai_api_key=config.OPENAI_API_KEY,
    )

    index = get_pinecone_client().Index(config.INDEX_NAME)
    vectorstore = PineconeVectorStore(index=index, embedding=embeddings, text_key="text")

    ids = [chunk["metadata"]["id"] for chunk in chunks]
    texts = [chunk["content"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]

    vectorstore.add_texts(
        texts=texts,
        metadatas=metadatas,
        ids=ids,
        namespace=config.NAMESPACE,
    )

    print(
        f"Ingesta completa: {len(chunks)} chunks subidos al índice "
        f"'{config.INDEX_NAME}' (namespace='{config.NAMESPACE}')."
    )


if __name__ == "__main__":
    run_ingestion()
