"""High-level document management service.

Works with plain (filename, bytes) so both the API and Streamlit can use it.
"""

import threading

from ingestion.ingestor import DocumentIngestor
from utils.file_manager import delete_file, safe_filename, save_file
from utils.metadata_manager import MetadataManager


class DocumentExistsError(ValueError):
    """Raised when a file with the same name is already indexed."""


class DocumentNotFoundError(LookupError):
    """Raised when deleting a file that isn't indexed."""


class DocumentManager:
    """Coordinates document upload, indexing, metadata and deletion."""

    def __init__(self) -> None:
        self.metadata = MetadataManager()
        self.ingestor = DocumentIngestor()
        # Index one document at a time (keeps memory use and Chroma writes safe)
        self._lock = threading.Lock()

    def list_documents(self) -> list[dict]:
        return self.metadata.load()

    def is_document_indexed(self, filename: str) -> bool:
        return self.metadata.get(filename) is not None

    def index_document(self, filename: str, content: bytes) -> dict:
        """Save, index and register a new PDF. Returns its stats."""
        filename = safe_filename(filename)

        if not content.startswith(b"%PDF"):
            raise ValueError("That file is not a valid PDF.")

        with self._lock:
            if self.is_document_indexed(filename):
                raise DocumentExistsError(f"{filename} has already been indexed.")

            pdf_path = save_file(filename, content)

            try:
                stats = self.ingestor.ingest(pdf_path)
            except Exception:
                # Undo anything half-done so we don't leave junk behind
                delete_file(filename)
                self.ingestor.vector_store.delete_vectors(filename)
                raise

            self.metadata.add_document(
                filename=filename,
                pages=stats["pages"],
                chunks=stats["chunks"],
            )

        return {"filename": filename, **stats}

    def delete_document(self, filename: str) -> None:
        """Remove the PDF file, its vectors and its metadata entry."""
        if not self.is_document_indexed(filename):
            raise DocumentNotFoundError(f"{filename} is not indexed.")

        with self._lock:
            delete_file(filename)
            self.ingestor.vector_store.delete_vectors(filename)
            self.metadata.remove_document(filename)
