"""Utilities for handling uploaded files."""

import re
from pathlib import Path

from config import UPLOAD_DIR


def safe_filename(name: str) -> str:
    """
    Clean a filename sent by a user so it can't escape the uploads folder.

    "../../etc/passwd.pdf" -> "passwd.pdf", "my paper?.pdf" -> "my paper_.pdf"
    """
    name = re.split(r"[\\/]", name or "")[-1]          # drop any folder parts
    name = re.sub(r"[^A-Za-z0-9._ ()-]", "_", name)   # keep only safe characters
    name = name.strip(" .")

    if not name.lower().endswith(".pdf") or len(name) <= 4:
        raise ValueError("Only .pdf files are allowed.")

    return name[-150:]  # keep names a sane length


def save_file(filename: str, content: bytes) -> Path:
    """Save raw bytes into the uploads folder and return the path."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    destination = UPLOAD_DIR / filename
    destination.write_bytes(content)
    return destination


def delete_file(filename: str) -> None:
    (UPLOAD_DIR / filename).unlink(missing_ok=True)
