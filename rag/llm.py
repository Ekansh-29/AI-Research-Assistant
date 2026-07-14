"""LLM configuration."""

from langchain_ollama import ChatOllama

MODEL_NAME = "qwen3:8b"


def get_llm() -> ChatOllama:
    """Return the configured Ollama model."""
    return ChatOllama(
        model=MODEL_NAME,
        temperature=0,
    )