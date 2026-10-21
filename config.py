"""Central settings for the whole app.

Every value can be overridden in a .env file (or in the server's
environment variables when we deploy), so nothing is hard-coded.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Folder that contains this file = project root.
# Using absolute paths means the app works no matter where you start it from.
BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

# --- Storage -------------------------------------------------------------
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads"))
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", BASE_DIR / "chroma_db"))
METADATA_FILE = Path(os.getenv("METADATA_FILE", BASE_DIR / "metadata.json"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "research_documents")

# --- Models --------------------------------------------------------------
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# --- RAG behaviour -------------------------------------------------------
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
TOP_K = int(os.getenv("TOP_K", "4"))

# --- API -----------------------------------------------------------------
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "20"))
# Comma-separated list of websites allowed to call the API ("*" = anyone).
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]
FRONTEND_DIR = BASE_DIR / "frontend"
