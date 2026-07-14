from ingestion.loader import load_pdf_documents
from ingestion.splitter import split_documents

docs = load_pdf_documents("data/attention.pdf")

print(f"Pages loaded: {len(docs)}")

for i, doc in enumerate(docs[:3], start=1):
    print(f"Page {i}: {len(doc.page_content)} characters")

chunks = split_documents(docs)

print(f"\nTotal chunks: {len(chunks)}")

for i, chunk in enumerate(chunks[:5], start=1):
    print(f"Chunk {i}")
    print(chunk.metadata)
    print(len(chunk.page_content))
    print("-" * 40)