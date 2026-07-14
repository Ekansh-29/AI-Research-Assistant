"""Embedding model utilities for vector store integration."""

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings

# Compact English retrieval model; 384-dim vectors, Chroma-compatible
DEFAULT_MODEL_NAME = "BAAI/bge-small-en-v1.5"


class EmbeddingManager:
    """
    Manages a HuggingFace embedding model for reuse across the ingestion pipeline.

    Instantiate once per process and pass the returned embeddings object to
    LangChain vector stores such as ChromaDB.
    """

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME) -> None:
        """
        Load and cache the embedding model.

        Args:
            model_name: HuggingFace model identifier.
        """
        # BGE models perform best with L2-normalized vectors for similarity search
        self._embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            encode_kwargs={"normalize_embeddings": True},
        )

    def get_embeddings(self) -> Embeddings:
        """
        Return the LangChain embeddings object for use with ChromaDB.

        Returns:
            Configured HuggingFaceEmbeddings instance.
        """
        return self._embeddings
