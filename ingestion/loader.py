"""PDF loading utilities.

Reads the PDF straight from memory (bytes), so nothing is saved to disk.
"""

import pymupdf  # PyMuPDF
from langchain_core.documents import Document


def load_pdf_bytes(content: bytes, filename: str) -> tuple[list[Document], int]:
    """
    Turn a PDF into LangChain Documents, one per page that has text.

    Returns:
        (documents, total_page_count)

    Raises:
        ValueError: If the PDF is corrupted, password-protected or has no text.
    """
    try:
        pdf = pymupdf.open(stream=content, filetype="pdf")
    except Exception as exc:
        raise ValueError(f"Invalid or corrupted PDF: {filename}") from exc

    documents: list[Document] = []

    with pdf:
        if pdf.needs_pass:
            raise ValueError(f"{filename} is password-protected.")

        total_pages = pdf.page_count

        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text().strip()
            if text:
                documents.append(
                    Document(
                        page_content=text,
                        metadata={"source": filename, "page": page_number},
                    )
                )

    if not documents:
        raise ValueError(
            f"No readable text found in {filename}. "
            "It may be a scanned (image-only) PDF."
        )

    return documents, total_pages
