"""Recuperador híbrido: combina búsqueda vectorial (Pinecone) con búsqueda
léxica (BM25) mediante un EnsembleRetriever de LangChain.
"""
from typing import List

from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

try:
    # langchain >= 1.0
    from langchain_classic.retrievers import EnsembleRetriever
except ImportError:
    # langchain 0.x
    from langchain.retrievers import EnsembleRetriever

from . import config
from .document_loader import load_source_documents
from .ingest import build_chunks
from .setup_pinecone import get_pinecone_client


class RAGSystem:
    """Encapsula un EnsembleRetriever (BM25 + Pinecone) y expone una API
    simple de consulta que devuelve el top-k combinando resultados léxicos
    y semánticos.
    """

    def __init__(
        self,
        top_k: int = config.TOP_K,
        bm25_weight: float = 0.4,
        vector_weight: float = 0.6,
        namespace: str = config.NAMESPACE,
    ):
        config.require_api_keys()
        self.top_k = top_k
        self.namespace = namespace

        self._bm25_retriever = self._build_bm25_retriever(top_k)
        self._vector_retriever = self._build_vector_retriever(top_k, namespace)

        self.ensemble_retriever = EnsembleRetriever(
            retrievers=[self._bm25_retriever, self._vector_retriever],
            weights=[bm25_weight, vector_weight],
        )

    @staticmethod
    def _build_bm25_retriever(top_k: int) -> BM25Retriever:
        # BM25 necesita el corpus completo en memoria: reconstruimos los mismos
        # chunks usados en la ingesta para que los índices léxico y vectorial
        # trabajen sobre el mismo universo de documentos.
        chunks = build_chunks()
        docs = [
            Document(page_content=chunk["content"], metadata=chunk["metadata"])
            for chunk in chunks
        ]
        retriever = BM25Retriever.from_documents(docs)
        retriever.k = top_k
        return retriever

    @staticmethod
    def _build_vector_retriever(top_k: int, namespace: str):
        embeddings = OpenAIEmbeddings(
            model=config.EMBEDDING_MODEL,
            openai_api_key=config.OPENAI_API_KEY,
        )
        index = get_pinecone_client().Index(config.INDEX_NAME)
        vectorstore = PineconeVectorStore(index=index, embedding=embeddings, text_key="text")
        return vectorstore.as_retriever(
            search_kwargs={"k": top_k, "namespace": namespace},
        )

    def query(self, question: str, k: int = None) -> List[Document]:
        """Ejecuta la consulta contra el EnsembleRetriever y devuelve el top-k
        documentos combinando resultados léxicos (BM25) y semánticos (Pinecone).
        """
        k = k or self.top_k
        results = self.ensemble_retriever.invoke(question)
        return results[:k]


if __name__ == "__main__":
    rag = RAGSystem()
    pregunta = "¿Cómo configuro un timeout en requests?"
    for doc in rag.query(pregunta):
        print(f"- [{doc.metadata.get('parent_id', doc.metadata.get('id'))}] "
              f"{doc.page_content[:80]}...")
