"""RAG chain that combines retrieval with generation."""

import re

from rag.llm import get_llm
from rag.models import RAGResponse
from rag.prompts import RAG_PROMPT
from rag.retriever import ResearchRetriever

# qwen3 "thinks out loud" inside <think>...</think>; users shouldn't see that.
_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.DOTALL)

NO_DOCUMENTS_ANSWER = "No documents are indexed yet. Upload a PDF first, then ask your question."


def _format_context(docs) -> str:
    """Join chunks, labelling each with its file and page so the LLM can refer to them."""
    parts = []
    for doc in docs:
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page", "?")
        parts.append(f"[{source}, page {page}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


class ResearchChain:
    """End-to-end Retrieval-Augmented Generation pipeline."""

    def __init__(self) -> None:
        self.retriever = ResearchRetriever()
        self.llm = get_llm()

    def ask(self, question: str) -> RAGResponse:
        """Answer a question using retrieved document context."""
        docs = self.retriever.retrieve(question)

        if not docs:
            return RAGResponse(answer=NO_DOCUMENTS_ANSWER, documents=[])

        prompt = RAG_PROMPT.format(
            context=_format_context(docs),
            question=question,
        )

        response = self.llm.invoke(prompt)
        answer = _THINK_BLOCK.sub("", str(response.content)).strip()

        return RAGResponse(answer=answer, documents=docs)
