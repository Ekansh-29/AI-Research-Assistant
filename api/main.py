"""FastAPI backend for the AI Research Assistant.

Run from the project root:
    uvicorn api.main:app --reload
Then open http://localhost:8000 (app) or http://localhost:8000/docs (API docs).
"""

import hmac
import logging
import threading
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.schemas import (
    AskRequest,
    AskResponse,
    DocumentInfo,
    InfoResponse,
    MessageResponse,
    Source,
    UploadResponse,
)
from config import (
    ADMIN_TOKEN,
    ALLOWED_ORIGINS,
    ASK_LIMIT_PER_MINUTE,
    FRONTEND_DIR,
    LLM_PROVIDER,
    MAX_UPLOAD_MB,
    USE_CLOUD,
)
from rag.chain import ResearchChain
from services.document_manager import (
    DocumentExistsError,
    DocumentManager,
    DocumentNotFoundError,
)
from utils.citations import format_sources

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("research_assistant")
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once when the server starts."""
    logger.info(
        "Starting: vector DB = %s, LLM = %s, admin password = %s",
        "Qdrant Cloud" if USE_CLOUD else "local Qdrant folder",
        LLM_PROVIDER,
        "ON" if ADMIN_TOKEN else "OFF",
    )
    app.state.manager = DocumentManager()
    app.state.chain = ResearchChain()
    logger.info("Ready.")
    yield


app = FastAPI(
    title="AI Research Assistant API",
    description="Upload research papers and ask questions about them (RAG).",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------------
# Protection
# -------------------------------------------------------------------------

def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    """Upload/delete need the admin password (only if ADMIN_TOKEN is set)."""
    if not ADMIN_TOKEN:
        return
    if not x_admin_token or not hmac.compare_digest(x_admin_token, ADMIN_TOKEN):
        raise HTTPException(401, "Admin password required for this action.")


class RateLimiter:
    """Allows each visitor (IP address) N requests per 60 seconds."""

    def __init__(self, per_minute: int) -> None:
        self.per_minute = per_minute
        self.hits: dict[str, deque] = defaultdict(deque)
        self.lock = threading.Lock()

    def __call__(self, request: Request) -> None:
        if self.per_minute <= 0:
            return
        # Render sits in front of our app, so the real IP is in this header
        forwarded = request.headers.get("x-forwarded-for", "")
        ip = forwarded.split(",")[0].strip() or (request.client.host if request.client else "?")

        now = time.monotonic()
        with self.lock:
            window = self.hits[ip]
            while window and now - window[0] > 60:
                window.popleft()
            if len(window) >= self.per_minute:
                raise HTTPException(429, "Too many questions. Please wait a minute.")
            window.append(now)


ask_limiter = RateLimiter(ASK_LIMIT_PER_MINUTE)
login_limiter = RateLimiter(5)  # slows down anyone guessing the password


# -------------------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------------------

@app.get("/api/health", response_model=MessageResponse)
def health():
    """Quick check that the server is up (Render uses this)."""
    return {"message": "ok"}


@app.get("/api/info", response_model=InfoResponse)
def info():
    """Tells the frontend whether uploads need the admin password."""
    return {"admin_required": bool(ADMIN_TOKEN), "max_upload_mb": MAX_UPLOAD_MB}


@app.post(
    "/api/admin/verify",
    response_model=MessageResponse,
    dependencies=[Depends(login_limiter), Depends(require_admin)],
)
def verify_admin():
    """Lets the frontend check a password before unlocking admin mode."""
    return {"message": "ok"}


@app.get("/api/documents", response_model=list[DocumentInfo])
def list_documents(request: Request):
    return request.app.state.manager.list_documents()


@app.post(
    "/api/documents",
    response_model=UploadResponse,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
def upload_document(request: Request, file: UploadFile = File(...)):
    content = file.file.read(MAX_UPLOAD_BYTES + 1)

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"File is larger than {MAX_UPLOAD_MB} MB.")

    try:
        return request.app.state.manager.index_document(file.filename, content)
    except DocumentExistsError as exc:
        raise HTTPException(409, str(exc))
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        logger.exception("Indexing failed")
        raise HTTPException(502, f"Indexing failed ({type(exc).__name__}). Check the server logs.")


@app.delete(
    "/api/documents/{filename}",
    response_model=MessageResponse,
    dependencies=[Depends(require_admin)],
)
def delete_document(request: Request, filename: str):
    try:
        request.app.state.manager.delete_document(filename)
    except DocumentNotFoundError as exc:
        raise HTTPException(404, str(exc))
    return {"message": f"Deleted {filename}"}


@app.post("/api/ask", response_model=AskResponse, dependencies=[Depends(ask_limiter)])
def ask(request: Request, body: AskRequest):
    question = body.question.strip()
    if not question:
        raise HTTPException(400, "Question cannot be empty.")

    try:
        result = request.app.state.chain.ask(question)
    except Exception as exc:
        logger.exception("Answering failed")
        raise HTTPException(
            503,
            f"The language model is not reachable right now ({type(exc).__name__}). "
            "Try again in a moment.",
        )

    sources = [
        Source(
            source=doc.metadata.get("source") or "Unknown",
            page=doc.metadata.get("page"),
            snippet=doc.page_content[:300],
        )
        for doc in result.documents
    ]

    return AskResponse(
        answer=result.answer,
        sources=sources,
        citations=format_sources(result.documents),
    )


# Serve the website. Mounted LAST so it doesn't hide the /api routes.
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
