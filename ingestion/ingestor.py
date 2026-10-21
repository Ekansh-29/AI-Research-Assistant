"""High-level document ingestion service."""

from pathlib import Path

from ingestion.loader import load_pdf_documents
from ingestion.splitter import split_documents
from rag.vector_store import get_vector_store


class DocumentIngestor:
    """Runs the full indexing pipeline: load -> split -> embed + store."""

    def __init__(self) -> None:
        self.vector_store = get_vector_store()

    def ingest(self, pdf_path: str | Path) -> dict:
        """Index a PDF into ChromaDB and return simple statistics."""
        documents = load_pdf_documents(pdf_path)
        chunks = split_documents(documents)

        self.vector_store.index_documents(chunks)

        return {
            "pages": documents[0].metadata["total_pages"],
            "chunks": len(chunks),
        }
