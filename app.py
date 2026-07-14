"""Streamlit interface for the AI Research Assistant."""

import streamlit as st

from rag.chain import ResearchChain



from ingestion.ingestor import DocumentIngestor
from utils.file_manager import save_uploaded_file

st.set_page_config(
    page_title="AI Research Assistant",
    page_icon="📚",
    layout="wide",
)

st.title("📚 AI Research Assistant")
st.write("Ask questions about your indexed research papers.")

uploaded_file = st.file_uploader(
    "Upload a research paper",
    type=["pdf"]
)

if uploaded_file:

    if st.button("Index Document"):

        with st.spinner("Indexing..."):

            pdf_path = save_uploaded_file(uploaded_file)

            ingestor = DocumentIngestor()

            chunks = ingestor.ingest(pdf_path)

        st.success(f"Indexed {chunks} chunks!")

from pathlib import Path

st.sidebar.title("📚 Indexed Papers")

upload_dir = Path("uploads")

pdfs = sorted(upload_dir.glob("*.pdf"))

if pdfs:
    for pdf in pdfs:
        st.sidebar.write(f"📄 {pdf.name}")
else:
    st.sidebar.info("No papers indexed yet.")

# Load the chain once
@st.cache_resource
def load_chain():
    return ResearchChain()

chain = load_chain()

question = st.text_input(
    "Ask a question",
    placeholder="What is self-attention?",
)

if st.button("Ask"):

    if question.strip():

        with st.spinner("Thinking..."):

            response = chain.ask(question)

        st.markdown("## Answer")

        st.write(response.answer)
        st.markdown("---")
        st.subheader("Retrieved Context")

        for i, doc in enumerate(response.documents, start=1):
          with st.expander(f"Chunk {i}"):
               st.write(doc.page_content)