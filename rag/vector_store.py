"""Chroma vector store utilities for document retrieval."""

from functools import lru_cache
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStoreRetriever

from config import CHROMA_DIR, COLLECTION_NAME
from ingestion.embeddings import get_shared_embeddings


class VectorStoreManager:
    """Manages a persisted Chroma collection used for indexing and search."""

    def __init__(
        self,
        embeddings: Embeddings,
        persist_directory: str | Path = CHROMA_DIR,
        collection_name: str = COLLECTION_NAME,
    ) -> None:
        self._persist_directory = Path(persist_directory)
        self._persist_directory.mkdir(parents=True, exist_ok=True)

        # Reconnects to the existing collection if chroma_db already exists
        self._store = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=str(self._persist_directory),
        )

    def index_documents(self, documents: list[Document]) -> list[str]:
        """Embed and store chunks. Returns the IDs Chroma assigned."""
        if not documents:
            return []
        return self._store.add_documents(documents)

    def as_retriever(self, k: int = 4) -> VectorStoreRetriever:
        """Return a retriever that fetches the k most similar chunks."""
        return self._store.as_retriever(search_kwargs={"k": k})

    def delete_vectors(self, filename: str) -> None:
        """Delete every chunk that came from this file."""
        self._store.delete(where={"source": filename})


@lru_cache(maxsize=1)
def get_vector_store() -> VectorStoreManager:
    """One shared vector store for the whole app (uploads and questions)."""
    return VectorStoreManager(get_shared_embeddings())
