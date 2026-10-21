"""LLM configuration.

LLM_PROVIDER in .env picks the model:
  groq   -> Groq's free hosted API (used when deployed)
  ollama -> Ollama running on your laptop
"""

from langchain_core.language_models import BaseChatModel

from config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    LLM_PROVIDER,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
)


def get_llm() -> BaseChatModel:
    if LLM_PROVIDER == "groq":
        if not GROQ_API_KEY:
            raise RuntimeError("LLM_PROVIDER is 'groq' but GROQ_API_KEY is not set.")

        from langchain_groq import ChatGroq  # imported only when needed

        return ChatGroq(model=GROQ_MODEL, api_key=GROQ_API_KEY, temperature=0)

    if LLM_PROVIDER == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)

    raise RuntimeError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER!r} (use 'groq' or 'ollama').")
