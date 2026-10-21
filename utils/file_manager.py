"""Filename helpers."""

import re


def safe_filename(name: str) -> str:
    """
    Clean a filename sent by a user.

    "../../etc/passwd.pdf" -> "passwd.pdf", "my paper?.pdf" -> "my paper_.pdf"
    """
    name = re.split(r"[\\/]", name or "")[-1]          # drop any folder parts
    name = re.sub(r"[^A-Za-z0-9._ ()-]", "_", name)   # keep only safe characters
    name = name.strip(" .")

    if not name.lower().endswith(".pdf") or len(name) <= 4:
        raise ValueError("Only .pdf files are allowed.")

    return name[-150:]  # keep names a sane length
