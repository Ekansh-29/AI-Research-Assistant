"""High-level document ingestion service."""

from pathlib import Path
from ingestion.loader import load_pdf_documents
from ingestion.splitter import split_documents
from ingestion.loader import extract_text_from_pdf
from ingestion.splitter import split_text
from ingestion.embeddings import EmbeddingManager
from rag.vector_store import VectorStoreManager


class DocumentIngestor:
    """Handles the complete indexing pipeline."""

    def __init__(self):

        embeddings = EmbeddingManager().get_embeddings()

        self.vector_store = VectorStoreManager(embeddings)

    def ingest(self, pdf_path: str | Path) -> dict:
        """
        Index a PDF into ChromaDB.

        Returns:
            Dictionary containing indexing statistics.
        """

        documents = load_pdf_documents(pdf_path)

        chunks = split_documents(documents)

        self.vector_store.index_documents(chunks)

        return {
            "pages": len(documents),
            "chunks": len(chunks),
        }