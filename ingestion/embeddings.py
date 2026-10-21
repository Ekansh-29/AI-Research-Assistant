"""Embedding model utilities for vector store integration."""

from functools import lru_cache

from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings

from config import EMBEDDING_MODEL


class EmbeddingManager:
    """Wraps a HuggingFace embedding model (turns text into vectors)."""

    def __init__(self, model_name: str = EMBEDDING_MODEL) -> None:
        # BGE models work best with normalized vectors
        self._embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            encode_kwargs={"normalize_embeddings": True},
        )

    def get_embeddings(self) -> Embeddings:
        return self._embeddings


@lru_cache(maxsize=1)
def get_shared_embeddings() -> Embeddings:
    """
    Load the embedding model ONCE per process and reuse it everywhere.

    lru_cache remembers the result, so the second call returns the same
    object instead of loading the model again.
    """
    return EmbeddingManager().get_embeddings()
