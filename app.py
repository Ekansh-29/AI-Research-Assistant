"""Streamlit interface for the AI Research Assistant."""

from pathlib import Path

import streamlit as st
from utils.citations import format_sources

from ingestion.ingestor import DocumentIngestor
from rag.chain import ResearchChain
from utils.file_manager import save_uploaded_file

# -------------------------------------------------------
# Page Configuration
# -------------------------------------------------------

st.set_page_config(
    page_title="AI Research Assistant",
    page_icon="📚",
    layout="wide",
)

st.title("📚 AI Research Assistant")
st.write("Ask questions about your indexed research papers.")

# -------------------------------------------------------
# Session State
# -------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------------------------------------------
# Sidebar
# -------------------------------------------------------

st.sidebar.title("📚 Indexed Papers")

upload_dir = Path("uploads")
upload_dir.mkdir(exist_ok=True)

pdfs = sorted(upload_dir.glob("*.pdf"))

if pdfs:
    for pdf in pdfs:
        st.sidebar.write(f"📄 {pdf.name}")
else:
    st.sidebar.info("No papers indexed yet.")

# -------------------------------------------------------
# PDF Upload
# -------------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload a research paper",
    type=["pdf"],
)

if uploaded_file:

    destination = upload_dir / uploaded_file.name

    if st.button("Index Document"):

        if destination.exists():
            st.warning("This document has already been uploaded.")

        else:
            with st.spinner("Indexing document..."):

                pdf_path = save_uploaded_file(uploaded_file)

                ingestor = DocumentIngestor()

                chunks = ingestor.ingest(pdf_path)

            st.success(f"✅ Indexed {chunks} chunks successfully!")

# -------------------------------------------------------
# Load RAG Chain
# -------------------------------------------------------

@st.cache_resource
def load_chain():
    return ResearchChain()


chain = load_chain()

# -------------------------------------------------------
# Display Previous Messages
# -------------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

        if (
            message["role"] == "assistant"
            and "sources" in message
            and message["sources"]
        ):
            st.divider()
            st.caption("📚 Sources")

            for citation in format_sources(message["sources"]):
                st.markdown(citation)

# -------------------------------------------------------
# Chat Input
# -------------------------------------------------------

question = st.chat_input(
    "Ask a question...",
)

if question:

    # Save user message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    # Display user message
    with st.chat_message("user"):
        st.markdown(question)

    # Generate assistant response
    with st.chat_message("assistant"):

        placeholder = st.empty()

        with st.spinner("Thinking..."):
            response = chain.ask(question)

        placeholder.markdown(response.answer)

        st.divider()
        st.caption("📚 Sources");

        for citation in format_sources(response.documents):
            st.markdown(citation)

    # Save assistant response
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response.answer,
            "sources": response.documents
        }
    )