"""High-level document management service.

Upload  = clean name -> check it's new -> index chunks -> save paper record
Delete  = remove chunks -> remove paper record
The PDF itself is never stored; only its chunks live in Qdrant.
"""

import threading

from ingestion.ingestor import DocumentIngestor
from utils.file_manager import safe_filename


class DocumentExistsError(ValueError):
    """Raised when a file with the same name is already indexed."""


class DocumentNotFoundError(LookupError):
    """Raised when deleting a file that isn't indexed."""


class DocumentManager:
    def __init__(self) -> None:
        self.ingestor = DocumentIngestor()
        self.store = self.ingestor.vector_store
        # Index one document at a time (keeps memory low on the free server)
        self._lock = threading.Lock()

    def list_documents(self) -> list[dict]:
        return self.store.list_documents()

    def is_document_indexed(self, filename: str) -> bool:
        return self.store.get_document(filename) is not None

    def index_document(self, filename: str, content: bytes) -> dict:
        filename = safe_filename(filename)

        if not content.startswith(b"%PDF"):
            raise ValueError("That file is not a valid PDF.")

        with self._lock:
            if self.is_document_indexed(filename):
                raise DocumentExistsError(f"{filename} has already been indexed.")

            try:
                stats = self.ingestor.ingest(filename, content)
            except Exception:
                # Undo a half-finished upload so no orphan chunks are left
                self.store.delete_chunks(filename)
                raise

            self.store.save_document(filename, stats["pages"], stats["chunks"])

        return {"filename": filename, **stats}

    def delete_document(self, filename: str) -> None:
        if not self.is_document_indexed(filename):
            raise DocumentNotFoundError(f"{filename} is not indexed.")

        with self._lock:
            self.store.delete_chunks(filename)
            self.store.delete_document(filename)
