"""Shared internal helpers for CLI command handlers."""

from __future__ import annotations


def normalize_targeted_names(names: list[str] | None) -> set[str]:
    """Normalize targeted artifact names for force/adopt operations."""
    return {name.strip() for name in names or [] if name.strip()}
