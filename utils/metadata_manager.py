"""Manage metadata (name, pages, chunks, date) for indexed papers."""

from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path

from config import METADATA_FILE


class MetadataManager:
    # The API can handle several requests at once; this lock stops two of
    # them from writing metadata.json at the same moment.
    _lock = threading.Lock()

    def __init__(self, metadata_file: str | Path = METADATA_FILE):
        self.path = Path(metadata_file)
        if not self.path.exists():
            self.path.write_text("[]")

    def load(self) -> list[dict]:
        return json.loads(self.path.read_text())

    def save(self, data: list[dict]) -> None:
        self.path.write_text(json.dumps(data, indent=4))

    def get(self, filename: str) -> dict | None:
        return next((d for d in self.load() if d["filename"] == filename), None)

    def add_document(self, filename: str, pages: int, chunks: int) -> None:
        with self._lock:
            docs = [d for d in self.load() if d["filename"] != filename]
            docs.append(
                {
                    "filename": filename,
                    "pages": pages,
                    "chunks": chunks,
                    "indexed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
            )
            self.save(docs)

    def remove_document(self, filename: str) -> None:
        with self._lock:
            docs = [d for d in self.load() if d["filename"] != filename]
            self.save(docs)
