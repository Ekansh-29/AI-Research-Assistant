"""Manage metadata for indexed research papers."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


class MetadataManager:
    def __init__(self, metadata_file: str = "metadata.json"):
        self.path = Path(metadata_file)

        if not self.path.exists():
            self.path.write_text("[]")

    def load(self):
        return json.loads(self.path.read_text())

    def save(self, data):
        self.path.write_text(json.dumps(data, indent=4))

    def add_document(
        self,
        filename: str,
        pages: int,
        chunks: int,
    ):
        docs = self.load()
         # Remove existing entry with the same filename
        docs = [
            doc
            for doc in docs
            if doc["filename"] != filename
        ]
        #Adding the latest metadata
        docs.append(
            {
                "filename": filename,
                "pages": pages,
                "chunks": chunks,
                "indexed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
        )

        self.save(docs)

    def remove_document(self, filename: str):
        docs = self.load()

        docs = [
            d for d in docs
            if d["filename"] != filename
        ]

        self.save(docs)