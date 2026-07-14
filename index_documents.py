from ingestion.ingestor import DocumentIngestor


def main():

    ingestor = DocumentIngestor()

    chunks = ingestor.ingest("data/attention.pdf")

    print(f"Indexed {chunks} chunks successfully.")


if __name__ == "__main__":
    main()