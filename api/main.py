"""FastAPI backend for the AI Research Assistant.

Run from the project root:
    uvicorn api.main:app --reload
Then open http://localhost:8000 (app) or http://localhost:8000/docs (API docs).
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.schemas import (
    AskRequest,
    AskResponse,
    DocumentInfo,
    MessageResponse,
    Source,
    UploadResponse,
)
from config import ALLOWED_ORIGINS, FRONTEND_DIR, MAX_UPLOAD_MB
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
    """Runs once when the server starts: load the models a single time."""
    logger.info("Loading embedding model and vector store...")
    app.state.manager = DocumentManager()
    app.state.chain = ResearchChain()
    logger.info("Ready.")
    yield


app = FastAPI(
    title="AI Research Assistant API",
    description="Upload research papers and ask questions about them (RAG).",
    version="1.0.0",
    lifespan=lifespan,
)

# Lets a frontend hosted on a different website call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------------
# Endpoints ("doors")
# -------------------------------------------------------------------------

@app.get("/api/health", response_model=MessageResponse)
def health():
    """Quick check that the server is up."""
    return {"message": "ok"}


@app.get("/api/documents", response_model=list[DocumentInfo])
def list_documents(request: Request):
    """List every indexed paper."""
    return request.app.state.manager.list_documents()


@app.post("/api/documents", response_model=UploadResponse, status_code=201)
def upload_document(request: Request, file: UploadFile = File(...)):
    """Upload a PDF and index it."""
    content = file.file.read(MAX_UPLOAD_BYTES + 1)

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"File is larger than {MAX_UPLOAD_MB} MB.")

    try:
        return request.app.state.manager.index_document(file.filename, content)
    except DocumentExistsError as exc:
        raise HTTPException(409, str(exc))
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@app.delete("/api/documents/{filename}", response_model=MessageResponse)
def delete_document(request: Request, filename: str):
    """Delete a paper, its chunks and its metadata."""
    try:
        request.app.state.manager.delete_document(filename)
    except DocumentNotFoundError as exc:
        raise HTTPException(404, str(exc))
    return {"message": f"Deleted {filename}"}


@app.post("/api/ask", response_model=AskResponse)
def ask(request: Request, body: AskRequest):
    """Answer a question using the indexed papers."""
    question = body.question.strip()
    if not question:
        raise HTTPException(400, "Question cannot be empty.")

    try:
        result = request.app.state.chain.ask(question)
    except Exception as exc:  # usually: Ollama not running / model missing
        logger.exception("LLM call failed")
        raise HTTPException(
            503,
            "The language model is not reachable. Is Ollama running "
            f"and is the model pulled? ({type(exc).__name__})",
        )

    sources = [
        Source(
            source=doc.metadata.get("source", "Unknown"),
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


# -------------------------------------------------------------------------
# Frontend: serve the files in /frontend at the site root.
# Mounted LAST so it doesn't hide the /api routes above.
# -------------------------------------------------------------------------
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
