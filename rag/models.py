"""Shared data models for the RAG pipeline."""

from dataclasses import dataclass

from langchain_core.documents import Document


@dataclass
class RAGResponse:
    """Response returned by the research chain."""

    answer: str
    documents: list[Document]