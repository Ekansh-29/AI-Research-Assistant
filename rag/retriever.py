"""Retriever utilities for querying the vector database."""

from langchain_core.documents import Document

from config import TOP_K
from rag.vector_store import get_vector_store


class ResearchRetriever:
    """Finds the chunks most similar in meaning to a question."""

    def __init__(self, k: int = TOP_K) -> None:
        self.vector_store = get_vector_store()
        self.retriever = self.vector_store.as_retriever(k=k)

    def retrieve(self, query: str) -> list[Document]:
        return self.retriever.invoke(query)
