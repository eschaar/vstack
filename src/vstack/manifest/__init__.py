"""Manifest domain models and persistence helpers."""

import warnings

from vstack.manifest.store import (
    CURRENT_HASH_ALGORITHM,
    CURRENT_MANIFEST_VERSION,
    ArtifactEntry,
    Manifest,
    ManifestFile,
)
from vstack.utils import content_hash, hash_with_algorithm

__all__ = [
    "CURRENT_HASH_ALGORITHM",
    "CURRENT_MANIFEST_VERSION",
    "ArtifactEntry",
    "Manifest",
    "ManifestFile",
    "content_hash",
    "hash_with_algorithm",
    # Deprecated shims — removed from store.py in this release.  Will be
    # dropped in the next minor release.  Use Manifest.preserved_entries()
    # and Manifest.preserve_existing_entry() instead.
    "preserve_existing_entry",
    "preserved_manifest_entries",
]


def preserved_manifest_entries(
    existing_manifest: "Manifest | None",
    selected_manifest_keys: "set[str]",
) -> "dict[str, list[ArtifactEntry]]":
    """Return artifact families not in *selected_manifest_keys*.

    .. deprecated::
        Use :meth:`Manifest.preserved_entries` instead.  This module-level
        wrapper will be removed in the next minor release.
    """
    warnings.warn(
        "preserved_manifest_entries() is deprecated; use Manifest.preserved_entries() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    if existing_manifest is None:
        return {}
    return existing_manifest.preserved_entries(selected_manifest_keys)


def preserve_existing_entry(
    *,
    new_entries: "dict[str, list[ArtifactEntry]]",
    manifest_key: str,
    existing_entry: "ArtifactEntry",
) -> None:
    """Carry forward one unchanged manifest entry into *new_entries*.

    .. deprecated::
        Use :meth:`Manifest.preserve_existing_entry` instead.  This
        module-level wrapper will be removed in the next minor release.
    """
    warnings.warn(
        "preserve_existing_entry() is deprecated; use Manifest.preserve_existing_entry() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    Manifest.preserve_existing_entry(
        new_entries=new_entries,
        manifest_key=manifest_key,
        existing_entry=existing_entry,
    )
