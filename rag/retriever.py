"""Retriever utilities for querying the vector database."""

from langchain_core.documents import Document

from ingestion.embeddings import EmbeddingManager
from rag.vector_store import VectorStoreManager


class ResearchRetriever:
    """Handles semantic retrieval from ChromaDB."""

    def __init__(self) -> None:
        embeddings = EmbeddingManager().get_embeddings()
        self.vector_store = VectorStoreManager(embeddings)
        self.retriever = self.vector_store.as_retriever(k=4)

    def retrieve(self, query: str) -> list[Document]:
        """Return the most relevant document chunks."""
        return self.retriever.invoke(query)