"""LLM configuration.

This is the ONLY file that knows which LLM we use. When we deploy,
we swap Ollama for a hosted API here and nothing else changes.
"""

from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama

from config import OLLAMA_BASE_URL, OLLAMA_MODEL


def get_llm() -> BaseChatModel:
    """Return the configured chat model."""
    return ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0,
    )
