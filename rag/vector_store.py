"""Chroma vector store utilities for document retrieval."""

from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_core.documents import Document

DEFAULT_PERSIST_DIR = "chroma_db"
DEFAULT_COLLECTION_NAME = "research_documents"


class VectorStoreManager:
    """
    Manages a persisted Chroma vector store for the RAG pipeline.

    Instantiate with an Embeddings object (e.g. from EmbeddingManager) and reuse
    the same instance for ingestion and retrieval.
    """

    def __init__(
        self,
        embeddings: Embeddings,
        persist_directory: str | Path = DEFAULT_PERSIST_DIR,
        collection_name: str = DEFAULT_COLLECTION_NAME,
    ) -> None:
        """
        Open or create a persisted Chroma collection.

        Args:
            embeddings: LangChain embeddings used for indexing and query encoding.
            persist_directory: Folder where Chroma persists its database files.
            collection_name: Chroma collection identifier for document storage.
        """
        self._persist_directory = Path(persist_directory)
        self._persist_directory.mkdir(parents=True, exist_ok=True)

        # Reconnects to an existing collection when chroma_db already exists
        self._store = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=str(self._persist_directory),
        )

    def index_documents(self, documents: list[Document]) -> list[str]:
        """
        Index LangChain Documents into Chroma while preserving metadata.

        Args:
            documents: List of LangChain Documents to index.

        Returns:
            List of document IDs assigned by Chroma.
        """

        if not documents:
          return []

        return self._store.add_documents(documents)

    def as_retriever(self, k: int = 4) -> VectorStoreRetriever:
        """
        Return a LangChain retriever backed by this vector store.

        Args:
            k: Number of nearest neighbors to retrieve per query.

        Returns:
            Configured retriever for use in RAG chains.
        """
        return self._store.as_retriever(search_kwargs={"k": k})

    def delete_vectors(self, filename: str) -> None:
        """
        Delete all vectorss belonging to a document.

        Args:
            filename: PDF filename stored in metadata["source"].
        """

        self._store.delete(
            where={
                "source": filename
            }
        )
