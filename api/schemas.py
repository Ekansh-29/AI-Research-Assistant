"""Shapes of the JSON that goes in and out of the API.

FastAPI uses these to check incoming data and to build the /docs page.
"""

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class Source(BaseModel):
    source: str
    page: int | None = None
    snippet: str


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    citations: list[str]


class DocumentInfo(BaseModel):
    filename: str
    pages: int
    chunks: int
    indexed_at: str


class UploadResponse(BaseModel):
    filename: str
    pages: int
    chunks: int


class MessageResponse(BaseModel):
    message: str


class InfoResponse(BaseModel):
    admin_required: bool
    max_upload_mb: int
