"""RAG chain that combines retrieval with generation."""

from rag.llm import get_llm
from rag.prompts import RAG_PROMPT
from rag.retriever import ResearchRetriever

from rag.models import RAGResponse

class ResearchChain:
    """End-to-end Retrieval-Augmented Generation pipeline."""

    def __init__(self) -> None:
        self.retriever = ResearchRetriever()
        self.llm = get_llm()

    def ask(self, question: str) -> RAGResponse:
        """Answer a question using retrieved document context."""

        docs = self.retriever.retrieve(question)

        context = "\n\n".join(doc.page_content for doc in docs)

        prompt = RAG_PROMPT.format(
            context=context,
            question=question,
        )

        response = self.llm.invoke(prompt)

        return RAGResponse(
            answer=response.content,
            documents=docs,
        )