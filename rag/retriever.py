"""Retriever: finds the chunks most similar in meaning to a question."""

from langchain_core.documents import Document

from config import TOP_K
from rag.vector_store import get_vector_store


class ResearchRetriever:
    def __init__(self, k: int = TOP_K) -> None:
        self.vector_store = get_vector_store()
        self.k = k

    def retrieve(self, query: str) -> list[Document]:
        return self.vector_store.search(query, self.k)
