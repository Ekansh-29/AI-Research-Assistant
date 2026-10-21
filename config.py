"""Central settings for the whole app.

Values come from the .env file on your laptop, or from the
"Environment" settings on Render when deployed. See .env.example.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


# --- Vector database (Qdrant) ---------------------------------------------
# If QDRANT_URL is set  -> use Qdrant Cloud (embeddings made by Qdrant's servers)
# If QDRANT_URL is empty -> use a local Qdrant folder (embeddings made on your laptop)
QDRANT_URL = os.getenv("QDRANT_URL", "").strip()
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "").strip() or None
QDRANT_LOCAL_PATH = Path(os.getenv("QDRANT_LOCAL_PATH", BASE_DIR / "qdrant_data"))
USE_CLOUD = bool(QDRANT_URL)

CHUNKS_COLLECTION = os.getenv("CHUNKS_COLLECTION", "research_chunks")
DOCUMENTS_COLLECTION = os.getenv("DOCUMENTS_COLLECTION", "research_documents_meta")

# --- Embedding model --------------------------------------------------------
# Must be a model your Qdrant cluster offers (Cloud console -> cluster -> Inference tab)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-minilm-l6-v2")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))

# --- LLM --------------------------------------------------------------------
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").strip().lower()  # "groq" or "ollama"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# --- RAG behaviour ----------------------------------------------------------
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
TOP_K = int(os.getenv("TOP_K", "4"))

# --- API / security ---------------------------------------------------------
# If ADMIN_TOKEN is set, uploading and deleting need this password.
# Leave it empty on your laptop; ALWAYS set it on Render.
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "").strip()
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "15"))
ASK_LIMIT_PER_MINUTE = int(os.getenv("ASK_LIMIT_PER_MINUTE", "10"))
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]
FRONTEND_DIR = BASE_DIR / "frontend"
