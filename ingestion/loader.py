"""PDF loading utilities."""

from pathlib import Path

import pymupdf  # PyMuPDF (new import name for "fitz")
from langchain_core.documents import Document


def load_pdf_documents(pdf_path: str | Path) -> list[Document]:
    """
    Load a PDF as LangChain Documents, one Document per page.

    Pages with no text (blank or image-only) are skipped.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the PDF is corrupted, password-protected or has no text.
    """
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    try:
        pdf = pymupdf.open(path)
    except Exception as exc:
        raise ValueError(f"Invalid or corrupted PDF: {path.name}") from exc

    documents: list[Document] = []

    with pdf:
        if pdf.needs_pass:
            raise ValueError(f"{path.name} is password-protected.")

        total_pages = pdf.page_count

        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text().strip()

            if not text:
                continue

            documents.append(
                Document(
                    page_content=text,
                    metadata={"source": path.name, "page": page_number},
                )
            )

    if not documents:
        raise ValueError(
            f"No readable text found in {path.name}. "
            "It may be a scanned (image-only) PDF."
        )

    # Remember the real page count (including skipped blank pages)
    for doc in documents:
        doc.metadata["total_pages"] = total_pages

    return documents
