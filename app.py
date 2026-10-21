"""Streamlit interface for the AI Research Assistant."""

from pathlib import Path

import streamlit as st

from rag.chain import ResearchChain
from utils.citations import format_sources
from services.document_manager import DocumentManager
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
# Constants
# -------------------------------------------------------

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# -------------------------------------------------------
# Session State
# -------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------------------------------------------
# Cached Resources
# -------------------------------------------------------

@st.cache_resource
def load_chain():
    return ResearchChain()


chain = load_chain()
manager = DocumentManager()

# -------------------------------------------------------
# Sidebar
# -------------------------------------------------------

st.sidebar.title("📚 Indexed Papers")

documents = manager.list_documents()

if documents:

    for doc in documents:

        st.sidebar.markdown(f"### 📄 {doc['filename']}")
        st.sidebar.write(f"📑 Pages: {doc['pages']}")
        st.sidebar.write(f"✂️ Chunks: {doc['chunks']}")
        st.sidebar.caption(f"Indexed: {doc['indexed_at']}")

        if st.sidebar.button(
             "🗑 Delete",
             key=doc["filename"],
        ): 
            manager.delete_document(doc["filename"])
            st.rerun()
        st.sidebar.divider()

else:
    st.sidebar.info("No papers indexed yet.")

# -------------------------------------------------------
# Upload Section
# -------------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload a research paper",
    type=["pdf"],
)

if uploaded_file:

    if st.button("Index Document"):

        with st.spinner("Indexing document..."):

            try:
                stats = manager.index_document(uploaded_file.name, uploaded_file.getvalue())

                st.success(
                    f"✅ Indexed {stats['chunks']} chunks from {stats['pages']} pages."
                )

                st.rerun()

            except ValueError as e:
                st.warning(str(e))

# -------------------------------------------------------
# Previous Chat Messages
# -------------------------------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

        if (
            message["role"] == "assistant"
            and message.get("sources")
        ):

            st.divider()
            st.caption("📚 Sources")

            for citation in format_sources(message["sources"]):
                st.markdown(citation)

# -------------------------------------------------------
# Chat Input
# -------------------------------------------------------

question = st.chat_input(
    "Ask a question about your research papers..."
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

    # Generate answer
    with st.chat_message("assistant"):

        placeholder = st.empty()

        with st.spinner("Thinking..."):

            response = chain.ask(question)

        placeholder.markdown(response.answer)

        if response.documents:

            st.divider()
            st.caption("📚 Sources")

            for citation in format_sources(response.documents):
                st.markdown(citation)

    # Save assistant response
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response.answer,
            "sources": response.documents,
        }
    )