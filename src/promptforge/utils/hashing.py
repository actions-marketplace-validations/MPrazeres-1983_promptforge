"""SHA-256 content hashing for prompts and datasets."""

from __future__ import annotations

import hashlib


def hash_content(content: str) -> str:
    """Return SHA-256 hex digest of a string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def hash_file(path: str) -> str:
    """Return SHA-256 hex digest of a file's contents."""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()