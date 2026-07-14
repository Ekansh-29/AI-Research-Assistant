from pathlib import Path

from ingestion.loader import extract_text_from_pdf
from ingestion.splitter import split_text

pdf_path = Path("data/attention.pdf")

text = extract_text_from_pdf(pdf_path)

chunks = split_text(text)

print(f"Total chunks: {len(chunks)}")

print("\nFirst chunk:\n")
print(chunks[0])

print("\nSecond chunk:\n")
print(chunks[1])