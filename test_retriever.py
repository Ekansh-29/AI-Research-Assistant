from rag.retriever import ResearchRetriever

retriever = ResearchRetriever()

docs = retriever.retrieve("What is self attention?")

print(f"Retrieved {len(docs)} chunks\n")

for i, doc in enumerate(docs, start=1):
    print("=" * 60)
    print(f"Chunk {i}\n")
    print(doc.page_content[:400])
    print()