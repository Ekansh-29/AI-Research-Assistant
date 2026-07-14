"""PDF text extraction utilities."""

from pathlib import Path

import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_path: str | Path) -> str:
    """
    Extract and concatenate text from all pages of a PDF file.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        All page text joined into a single string (pages separated by newlines).

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the path is not a valid PDF or the file cannot be read.
    """
    path = Path(pdf_path)

    # Validate path before opening the document
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a .pdf file, got: {path.suffix!r}")

    try:
        with fitz.open(path) as doc:
            # Collect plain text from every page
            page_texts = [page.get_text() for page in doc]
            return "\n".join(page_texts)

    except fitz.FileDataError as exc:
        raise ValueError(f"Invalid or corrupted PDF: {path}") from exc

    except RuntimeError as exc:
        # Covers password-protected or otherwise unreadable PDFs
        raise ValueError(f"Could not read PDF: {path}") from exc


from langchain_core.documents import Document


def load_pdf_documents(pdf_path: str | Path) -> list[Document]:
    """
    Load a PDF as a list of LangChain Documents,
    one Document per page.
    """

    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    documents = []

    with fitz.open(path) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text()

            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": path.name,
                        "page": page_number,
                    },
                )
            )

    return documents
