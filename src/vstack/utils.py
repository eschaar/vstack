"""Generic utility functions for vstack."""

from __future__ import annotations

import hashlib


def content_hash(content: str) -> str:
    """Return a stable SHA-256 checksum for rendered artifact content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def hash_with_algorithm(content: str, algorithm: str) -> str:
    """Return a checksum for *content* using the requested algorithm."""
    normalized = algorithm.lower()
    if normalized == "sha256":
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
    if normalized == "md5":
        return hashlib.md5(content.encode("utf-8"), usedforsecurity=False).hexdigest()
    raise ValueError(f"Unsupported checksum algorithm: {algorithm}")
