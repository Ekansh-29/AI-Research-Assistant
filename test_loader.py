"""Quick smoke test for PDF text extraction."""

import sys
from pathlib import Path

from ingestion.loader import extract_text_from_pdf

# Ensure Unicode PDF text prints correctly on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PDF_PATH = Path(__file__).resolve().parent / "data" / "attention.pdf"


def main() -> None:
    text = extract_text_from_pdf(PDF_PATH)

    print(text[:1000])
    print(f"\nTotal characters extracted: {len(text)}")


if __name__ == "__main__":
    main()
