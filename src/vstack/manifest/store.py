"""vstack manifest model and file persistence."""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from vstack.constants import MANIFEST_FILENAME

CURRENT_MANIFEST_VERSION = 2
CURRENT_HASH_ALGORITHM = "sha256"
_META_COMMENT_RE = re.compile(r"<!--\s*VSTACK-META:\s*(\{.*?\})\s*-->")


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


@dataclass
class ArtifactEntry:
    """Represent a single installed artifact entry in ``vstack.json``."""

    name: str
    file: str
    version: str | None = None
    checksum: str | None = None
    checksum_algorithm: str | None = None


@dataclass
class Manifest:
    """Represent the parsed install manifest stored in ``vstack.json``."""

    vstack_version: str
    installed_at: str
    manifest_version: int = CURRENT_MANIFEST_VERSION
    hash_algorithm: str = CURRENT_HASH_ALGORITHM
    artifacts: dict[str, list[ArtifactEntry]] = field(default_factory=lambda: {})

    def entries_for(self, type_name: str) -> list[ArtifactEntry]:
        """Return manifest entries for a single artifact type key."""
        return self.artifacts.get(type_name, [])

    def names_for(self, type_name: str) -> list[str]:
        """Return artifact names for a single manifest type key."""
        return [e.name for e in self.entries_for(type_name)]

    def files_for(self, type_name: str) -> list[str]:
        """Return relative output file paths for a manifest type key."""
        return [e.file for e in self.entries_for(type_name)]

    def to_dict(self) -> dict:
        """Serialize the manifest into JSON-compatible primitives."""
        return {
            "manifest_version": self.manifest_version,
            "hash_algorithm": self.hash_algorithm,
            "vstack_version": self.vstack_version,
            "installed_at": self.installed_at,
            "artifacts": {
                type_name: [
                    {
                        "name": e.name,
                        "file": e.file,
                        **({} if e.version is None else {"version": e.version}),
                        **({} if e.checksum is None else {"checksum": e.checksum}),
                        **(
                            {}
                            if e.checksum is None or e.checksum_algorithm is None
                            else {"checksum_algorithm": e.checksum_algorithm}
                        ),
                    }
                    for e in entries
                ]
                for type_name, entries in self.artifacts.items()
            },
        }

    @staticmethod
    def _infer_algorithm(
        *,
        entry: dict,
        fallback_algorithm: str,
        manifest_version: int,
    ) -> str | None:
        """Infer checksum algorithm for entries missing explicit metadata."""
        explicit = entry.get("checksum_algorithm") or entry.get("hash_algorithm")
        if explicit:
            return str(explicit)

        checksum = entry.get("checksum") or entry.get("content_hash")
        if not checksum:
            return None

        if isinstance(checksum, str):
            if len(checksum) == 64:
                return CURRENT_HASH_ALGORITHM
        if (
            manifest_version >= CURRENT_MANIFEST_VERSION
            and fallback_algorithm == CURRENT_HASH_ALGORITHM
        ):
            return CURRENT_HASH_ALGORITHM
        return None

    def needs_upgrade(self) -> bool:
        """Return ``True`` when this manifest should be normalized to current schema."""
        return self.manifest_version < CURRENT_MANIFEST_VERSION

    @staticmethod
    def _infer_algorithm_for_legacy_entry(checksum: str, fallback_algorithm: str) -> str | None:
        """Infer the checksum algorithm for a legacy entry that has no explicit algorithm field.

        Uses the same heuristics as :meth:`_infer_algorithm` but with ``manifest_version=0``
        to signal the pre-schema-v2 legacy path explicitly, avoiding a magic-constant call site.
        """
        return Manifest._infer_algorithm(
            entry={"checksum": checksum},
            fallback_algorithm=fallback_algorithm,
            manifest_version=0,
        )

    def upgraded(self) -> Manifest:
        """Return an upgraded copy of this manifest in current schema format."""
        upgraded_artifacts: dict[str, list[ArtifactEntry]] = {}
        for type_name, entries in self.artifacts.items():
            upgraded_artifacts[type_name] = []
            for entry in entries:
                checksum_algorithm = entry.checksum_algorithm
                if entry.checksum and checksum_algorithm is None:
                    checksum_algorithm = self._infer_algorithm_for_legacy_entry(
                        checksum=entry.checksum,
                        fallback_algorithm=str(self.hash_algorithm).lower(),
                    )

                upgraded_artifacts[type_name].append(
                    ArtifactEntry(
                        name=entry.name,
                        file=entry.file,
                        version=entry.version,
                        checksum=entry.checksum,
                        checksum_algorithm=checksum_algorithm,
                    )
                )

        return Manifest(
            vstack_version=self.vstack_version,
            installed_at=self.installed_at,
            manifest_version=CURRENT_MANIFEST_VERSION,
            hash_algorithm=CURRENT_HASH_ALGORITHM,
            artifacts=upgraded_artifacts,
        )

    @staticmethod
    def _has_vstack_meta_footer(content: str) -> bool:
        """Return ``True`` when content includes a VSTACK-META footer block."""
        return bool(_META_COMMENT_RE.search(content))

    def with_backfilled_checksums(
        self,
        *,
        install_dir: Path,
    ) -> tuple[Manifest, list[str], list[str]]:
        """Return a copy with checksums backfilled for footer-tagged legacy entries.

        Legacy entries are eligible only when:
        - entry has no ``checksum`` yet
        - file exists on disk under ``install_dir``
        - file still includes a ``VSTACK-META`` footer
        """
        normalized_algorithm = str(self.hash_algorithm or CURRENT_HASH_ALGORITHM).lower()
        if normalized_algorithm not in {"sha256", "md5"}:
            normalized_algorithm = CURRENT_HASH_ALGORITHM

        backfilled: list[str] = []
        skipped: list[str] = []
        updated_artifacts: dict[str, list[ArtifactEntry]] = {}

        for type_name, entries in self.artifacts.items():
            updated_artifacts[type_name] = []
            for entry in entries:
                if entry.checksum is not None:
                    updated_artifacts[type_name].append(entry)
                    continue

                out_file = install_dir / entry.file
                display_name = f"{type_name}:{entry.name}"

                if not out_file.exists():
                    skipped.append(f"{display_name} (missing file)")
                    updated_artifacts[type_name].append(entry)
                    continue

                try:
                    content = out_file.read_text(encoding="utf-8")
                except OSError:
                    skipped.append(f"{display_name} (unreadable file)")
                    updated_artifacts[type_name].append(entry)
                    continue

                if not self._has_vstack_meta_footer(content):
                    skipped.append(f"{display_name} (missing VSTACK-META footer)")
                    updated_artifacts[type_name].append(entry)
                    continue

                checksum = hash_with_algorithm(content, normalized_algorithm)
                updated_artifacts[type_name].append(
                    ArtifactEntry(
                        name=entry.name,
                        file=entry.file,
                        version=entry.version,
                        checksum=checksum,
                        checksum_algorithm=normalized_algorithm,
                    )
                )
                backfilled.append(display_name)

        return (
            Manifest(
                vstack_version=self.vstack_version,
                installed_at=self.installed_at,
                manifest_version=self.manifest_version,
                hash_algorithm=self.hash_algorithm,
                artifacts=updated_artifacts,
            ),
            backfilled,
            skipped,
        )

    @classmethod
    def from_dict(cls, data: dict) -> Manifest:
        """Create a :class:`Manifest` from parsed JSON data."""
        try:
            manifest_version = int(data.get("manifest_version", 1))
        except (TypeError, ValueError) as error:
            raise ValueError("Invalid manifest_version in vstack.json") from error
        manifest_hash_algorithm = str(data.get("hash_algorithm") or CURRENT_HASH_ALGORITHM)

        artifacts: dict[str, list[ArtifactEntry]] = {}
        raw_artifacts = data.get("artifacts", {})
        if not isinstance(raw_artifacts, dict):
            raw_artifacts = {}

        for type_name, entries in raw_artifacts.items():
            if not isinstance(entries, list):
                continue
            artifacts[type_name] = [
                ArtifactEntry(
                    name=e["name"],
                    file=e["file"],
                    version=e.get("version"),
                    checksum=e.get("checksum") or e.get("content_hash"),
                    checksum_algorithm=cls._infer_algorithm(
                        entry=e,
                        fallback_algorithm=manifest_hash_algorithm,
                        manifest_version=manifest_version,
                    ),
                )
                for e in entries
                if isinstance(e, dict) and "name" in e and "file" in e
            ]
        return cls(
            manifest_version=manifest_version,
            hash_algorithm=manifest_hash_algorithm,
            vstack_version=data.get("vstack_version", ""),
            installed_at=data.get("installed_at", ""),
            artifacts=artifacts,
        )


def preserved_manifest_entries(
    existing_manifest: Manifest | None,
    selected_manifest_keys: set[str],
) -> dict[str, list[ArtifactEntry]]:
    """Preserve artifact families not selected for the current operation."""
    if existing_manifest is None:
        return {}

    preserved: dict[str, list[ArtifactEntry]] = {}
    for manifest_key, entries in existing_manifest.artifacts.items():
        if manifest_key not in selected_manifest_keys:
            preserved[manifest_key] = list(entries)
    return preserved


def preserve_existing_entry(
    *,
    new_entries: dict[str, list[ArtifactEntry]],
    manifest_key: str,
    existing_entry: ArtifactEntry,
) -> None:
    """Carry forward one unchanged manifest entry for a manifest key."""
    new_entries.setdefault(manifest_key, []).append(existing_entry)


class ManifestFile:
    """Read and write the ``vstack.json`` manifest inside an install root."""

    def __init__(self, parent_dir: Path) -> None:
        self.path = parent_dir / MANIFEST_FILENAME
        self.read_error: str | None = None

    def exists(self) -> bool:
        """Return ``True`` when the manifest file exists on disk."""
        return self.path.exists()

    def read(self, *, allow_legacy: bool = False) -> Manifest | None:
        """Parse the manifest file from disk."""
        if not self.path.exists():
            self.read_error = None
            return None
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            manifest = Manifest.from_dict(data)
            if manifest.needs_upgrade() and not allow_legacy:
                self.read_error = (
                    "Legacy manifest schema detected in vstack.json. "
                    "Run: vstack manifest upgrade --target <project-root>."
                )
                return None

            self.read_error = None
            return manifest
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            self.read_error = "Invalid manifest format in vstack.json"
            return None

    def write(self, manifest: Manifest) -> None:
        """Write a manifest to disk in stable, human-readable JSON format.

        The write is atomic: content is first written to a sibling temporary file
        and then replaced with an ``os.replace`` call so a crash or keyboard
        interrupt cannot leave ``vstack.json`` in a partially-written state.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_name(self.path.name + ".tmp")
        tmp_path.write_text(
            json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(tmp_path, self.path)
