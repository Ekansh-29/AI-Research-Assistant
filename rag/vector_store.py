"""Qdrant vector store: chunks for search + a small list of indexed papers.

Two collections (think "tables"):
  research_chunks          one point per chunk: its vector + text, file, page
  research_documents_meta  one point per paper: filename, pages, chunks, date

We never compute embeddings ourselves. We hand Qdrant the raw text inside
models.Document(...) and the client turns it into a vector:
  - cloud mode: Qdrant's servers do it (Cloud Inference), so our server stays tiny
  - local mode: the qdrant-client uses FastEmbed on your laptop
"""

import threading
import uuid
from contextlib import nullcontext
from datetime import datetime
from functools import lru_cache

from langchain_core.documents import Document
from qdrant_client import QdrantClient, models

from config import (
    CHUNKS_COLLECTION,
    DOCUMENTS_COLLECTION,
    EMBEDDING_DIM,
    EMBEDDING_MODEL,
    QDRANT_API_KEY,
    QDRANT_LOCAL_PATH,
    QDRANT_URL,
    USE_CLOUD,
)

UPSERT_BATCH = 64


def _source_filter(filename: str) -> models.Filter:
    return models.Filter(
        must=[models.FieldCondition(key="source", match=models.MatchValue(value=filename))]
    )


def _doc_id(filename: str) -> str:
    """Same filename -> same ID, so we can find/delete a paper's record directly."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, filename))


class VectorStore:
    def __init__(self) -> None:
        if USE_CLOUD:
            self.client = QdrantClient(
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY,
                cloud_inference=True,
                timeout=60,
            )
            self._lock = nullcontext()  # the cloud handles parallel requests
        else:
            QDRANT_LOCAL_PATH.mkdir(parents=True, exist_ok=True)
            self.client = QdrantClient(
                path=str(QDRANT_LOCAL_PATH),
                force_disable_check_same_thread=True,
            )
            self._lock = threading.RLock()  # local file mode: one operation at a time

        self._ensure_collections()

    # ------------------------------------------------------------------ setup
    def _ensure_collections(self) -> None:
        with self._lock:
            if not self.client.collection_exists(CHUNKS_COLLECTION):
                self.client.create_collection(
                    CHUNKS_COLLECTION,
                    vectors_config=models.VectorParams(
                        size=EMBEDDING_DIM, distance=models.Distance.COSINE
                    ),
                )
                # Index on "source" so "delete all chunks of file X" is fast
                self.client.create_payload_index(
                    CHUNKS_COLLECTION, "source", models.PayloadSchemaType.KEYWORD
                )

            if not self.client.collection_exists(DOCUMENTS_COLLECTION):
                # This collection only stores info, so a 1-number dummy vector is enough
                self.client.create_collection(
                    DOCUMENTS_COLLECTION,
                    vectors_config=models.VectorParams(size=1, distance=models.Distance.DOT),
                )

    # ----------------------------------------------------------------- chunks
    def add_chunks(self, chunks: list[Document]) -> None:
        """Embed and store chunks (in batches, to keep requests small)."""
        points = [
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=models.Document(text=chunk.page_content, model=EMBEDDING_MODEL),
                payload={
                    "text": chunk.page_content,
                    "source": chunk.metadata.get("source"),
                    "page": chunk.metadata.get("page"),
                },
            )
            for chunk in chunks
        ]
        with self._lock:
            for start in range(0, len(points), UPSERT_BATCH):
                self.client.upsert(
                    CHUNKS_COLLECTION,
                    points=points[start : start + UPSERT_BATCH],
                    wait=True,
                )

    def search(self, query: str, k: int) -> list[Document]:
        """Return the k chunks closest in meaning to the query."""
        with self._lock:
            result = self.client.query_points(
                CHUNKS_COLLECTION,
                query=models.Document(text=query, model=EMBEDDING_MODEL),
                limit=k,
                with_payload=True,
            )
        return [
            Document(
                page_content=point.payload.get("text", ""),
                metadata={
                    "source": point.payload.get("source"),
                    "page": point.payload.get("page"),
                    "score": point.score,
                },
            )
            for point in result.points
        ]

    def delete_chunks(self, filename: str) -> None:
        with self._lock:
            self.client.delete(
                CHUNKS_COLLECTION,
                points_selector=models.FilterSelector(filter=_source_filter(filename)),
                wait=True,
            )

    # ------------------------------------------------------- paper records
    def list_documents(self) -> list[dict]:
        records, offset = [], None
        with self._lock:
            while True:
                points, offset = self.client.scroll(
                    DOCUMENTS_COLLECTION,
                    limit=256,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False,
                )
                records.extend(p.payload for p in points)
                if offset is None:
                    break
        return sorted(records, key=lambda r: r.get("indexed_at", ""))

    def get_document(self, filename: str) -> dict | None:
        with self._lock:
            found = self.client.retrieve(DOCUMENTS_COLLECTION, ids=[_doc_id(filename)])
        return found[0].payload if found else None

    def save_document(self, filename: str, pages: int, chunks: int) -> None:
        record = {
            "filename": filename,
            "pages": pages,
            "chunks": chunks,
            "indexed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        with self._lock:
            self.client.upsert(
                DOCUMENTS_COLLECTION,
                points=[models.PointStruct(id=_doc_id(filename), vector=[1.0], payload=record)],
                wait=True,
            )

    def delete_document(self, filename: str) -> None:
        with self._lock:
            self.client.delete(
                DOCUMENTS_COLLECTION,
                points_selector=models.PointIdsList(points=[_doc_id(filename)]),
                wait=True,
            )


@lru_cache(maxsize=1)
def get_vector_store() -> VectorStore:
    """One shared connection for the whole app."""
    return VectorStore()
