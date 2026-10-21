"""High-level document ingestion service."""

from ingestion.loader import load_pdf_bytes
from ingestion.splitter import split_documents
from rag.vector_store import get_vector_store


class DocumentIngestor:
    """Runs the indexing pipeline: read PDF -> split into chunks -> store in Qdrant."""

    def __init__(self) -> None:
        self.vector_store = get_vector_store()

    def ingest(self, filename: str, content: bytes) -> dict:
        documents, total_pages = load_pdf_bytes(content, filename)
        chunks = split_documents(documents)

        self.vector_store.add_chunks(chunks)

        return {"pages": total_pages, "chunks": len(chunks)}
