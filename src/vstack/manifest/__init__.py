"""Manifest domain models and persistence helpers."""

from vstack.manifest.store import (
    CURRENT_HASH_ALGORITHM,
    CURRENT_MANIFEST_VERSION,
    ArtifactEntry,
    Manifest,
    ManifestFile,
    content_hash,
    hash_with_algorithm,
    preserve_existing_entry,
    preserved_manifest_entries,
)

__all__ = [
    "CURRENT_HASH_ALGORITHM",
    "CURRENT_MANIFEST_VERSION",
    "ArtifactEntry",
    "Manifest",
    "ManifestFile",
    "content_hash",
    "hash_with_algorithm",
    "preserve_existing_entry",
    "preserved_manifest_entries",
]
