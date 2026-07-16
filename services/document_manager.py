"""High-level document management service."""

from pathlib import Path
from utils.metadata_manager import MetadataManager
from ingestion.ingestor import DocumentIngestor
from utils.file_manager import save_uploaded_file


class DocumentManager:
    """Coordinates document upload, indexing and metadata."""

    def __init__(self):

        self.metadata = MetadataManager()

        self.ingestor = DocumentIngestor()

    def list_documents(self):

        return self.metadata.load()

    def is_document_indexed(self, filename: str):

        docs = self.metadata.load()

        return any(
            doc["filename"] == filename
            for doc in docs
        )

    def index_document(self, uploaded_file):
        """
        Save, index and register a new document.

        Returns
        -------
        dict
            Indexing statistics.
        """

        if self.is_document_indexed(uploaded_file.name):
            raise ValueError(
                f"{uploaded_file.name} has already been indexed."
            )

        # Save uploaded PDF
        pdf_path = save_uploaded_file(uploaded_file)

        # Index into Chroma
        stats = self.ingestor.ingest(pdf_path)

        # Save metadata
        self.metadata.add_document(
            filename=uploaded_file.name,
            pages=stats["pages"],
            chunks=stats["chunks"],
        )

        return stats

    def delete_document(self, filename: str):
        """
        Delete a document from the application.

        Removes:
        - uploaded PDF
        - vector embeddings
        - metadata
        """

        pdf_path = Path("uploads") / filename

        if pdf_path.exists():
            pdf_path.unlink()

        self.ingestor.vector_store.delete_vectors(filename)

        self.metadata.remove_document(filename)