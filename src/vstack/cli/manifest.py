"""vstack manifest — reads and writes ``vstack.json``.

The manifest tracks every artifact installed by ``vstack install`` so that
``vstack uninstall`` can remove exactly those files without touching anything
the user placed there manually.

Format::

    {
      "vstack_version": "…",
      "installed_at":   "…",
      "artifacts": {
        "skills": [{"name": "vision", "version": "1.0.1", "file": "skills/vision/SKILL.md"}],
                "agents": [{"name": "engineer", "file": "agents/engineer.agent.md"}],
                "instructions": [{"name": "python", "file": "instructions/python.instructions.md"}],
                "prompts": [{"name": "code-review", "file": "prompts/code-review.prompt.md"}]
      }
    }
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from vstack.constants import MANIFEST_FILENAME


@dataclass
class ArtifactEntry:
    """Represent a single installed artifact entry in ``vstack.json``."""

    name: str
    file: str
    version: str | None = None


@dataclass
class Manifest:
    """Represent the parsed install manifest stored in ``vstack.json``."""

    vstack_version: str
    installed_at: str
    artifacts: dict[str, list[ArtifactEntry]] = field(default_factory=dict)

    # ── Accessors ─────────────────────────────────────────────────────────────

    def entries_for(self, type_name: str) -> list[ArtifactEntry]:
        """Return manifest entries for a single artifact type key.

        Args:
            type_name: Manifest artifact key such as ``"skills"``.
        """
        return self.artifacts.get(type_name, [])

    def names_for(self, type_name: str) -> list[str]:
        """Return artifact names for a single manifest type key.

        Args:
            type_name: Manifest artifact key such as ``"skills"``.
        """
        return [e.name for e in self.entries_for(type_name)]

    def files_for(self, type_name: str) -> list[str]:
        """Return relative output file paths for a manifest type key.

        Args:
            type_name: Manifest artifact key such as ``"skills"``.
        """
        return [e.file for e in self.entries_for(type_name)]

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Serialize the manifest into JSON-compatible primitives.

        Returns:
            A nested dictionary structure suitable for ``json.dumps``.
        """
        return {
            "vstack_version": self.vstack_version,
            "installed_at": self.installed_at,
            "artifacts": {
                type_name: [
                    {
                        "name": e.name,
                        "file": e.file,
                        **({} if e.version is None else {"version": e.version}),
                    }
                    for e in entries
                ]
                for type_name, entries in self.artifacts.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> Manifest:
        """Create a :class:`Manifest` from parsed JSON data.

        Args:
            data: Parsed JSON object read from ``vstack.json``.

        Returns:
            A normalized in-memory manifest representation.
        """
        artifacts: dict[str, list[ArtifactEntry]] = {}
        for type_name, entries in data.get("artifacts", {}).items():
            artifacts[type_name] = [
                ArtifactEntry(
                    name=e["name"],
                    file=e["file"],
                    version=e.get("version"),
                )
                for e in entries
                if isinstance(e, dict) and "name" in e
            ]
        return cls(
            vstack_version=data.get("vstack_version", ""),
            installed_at=data.get("installed_at", ""),
            artifacts=artifacts,
        )


class ManifestFile:
    """Read and write the ``vstack.json`` manifest inside an install root."""

    def __init__(self, parent_dir: Path) -> None:
        """Create a manifest accessor rooted at the provided install directory.

        Args:
            parent_dir: Install root that contains or will contain
                ``vstack.json``.
        """
        self.path = parent_dir / MANIFEST_FILENAME

    def exists(self) -> bool:
        """Return ``True`` when the manifest file exists on disk."""
        return self.path.exists()

    def read(self) -> Manifest | None:
        """Parse the manifest file from disk.

        Returns:
            The parsed manifest, or ``None`` when the file is missing or
            cannot be decoded safely.
        """
        if not self.path.exists():
            return None
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return Manifest.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return None

    def write(self, manifest: Manifest) -> None:
        """Write a manifest to disk in stable, human-readable JSON format.

        Args:
            manifest: Manifest data to persist.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
