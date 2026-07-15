"""Utilities for formatting document citations."""

from collections import defaultdict


def format_sources(documents):
    """
    Group retrieved documents by source file and page number.

    Returns:
        List of formatted citation strings.
    """

    grouped = defaultdict(set)

    for doc in documents:

        source = doc.metadata.get("source", "Unknown")

        page = doc.metadata.get("page", "?")

        grouped[source].add(page)

    citations = []

    for source, pages in grouped.items():

        page_list = ", ".join(str(p) for p in sorted(pages))

        citations.append(f"📄 {source} — Pages {page_list}")

    return citations