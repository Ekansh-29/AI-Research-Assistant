"""Utilities for handling uploaded files."""

from pathlib import Path

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def save_uploaded_file(uploaded_file) -> Path:
    """
    Save a Streamlit UploadedFile to disk.

    Returns
    -------
    Path
        Saved file path.
    """

    destination = UPLOAD_DIR / uploaded_file.name

    with open(destination, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return destination