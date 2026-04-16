"""vstack manifest — reads and writes ``vstack.json``.

The manifest tracks every artifact installed by ``vstack install`` so that
``vstack uninstall`` can remove exactly those files without touching anything
the user placed there manually.

Format::

    {
      "vstack_version": "…",
      "installed_at":   "…",
      "artifacts": {
        "skills": [{"name": "vision", "version": "1.0.0", "file": "skills/vision/SKILL.md"}],
        "agents": [{"name": "engineer", "file": "agents/engineer.agent.md"}]
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
    """A single artifact tracked in the manifest."""

    name: str
    file: str
    version: str | None = None


@dataclass
class Manifest:
    """In-memory representation of ``vstack.json``."""

    vstack_version: str
    installed_at: str
    artifacts: dict[str, list[ArtifactEntry]] = field(default_factory=dict)

    # ── Accessors ─────────────────────────────────────────────────────────────

    def entries_for(self, type_name: str) -> list[ArtifactEntry]:
        """Entries for."""
        return self.artifacts.get(type_name, [])

    def names_for(self, type_name: str) -> list[str]:
        """Names for."""
        return [e.name for e in self.entries_for(type_name)]

    def files_for(self, type_name: str) -> list[str]:
        """Files for."""
        return [e.file for e in self.entries_for(type_name)]

    # ── Serialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """To dict."""
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
        """From dict."""
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
    """Reads and writes the ``vstack.json`` manifest inside *parent_dir*."""

    def __init__(self, parent_dir: Path) -> None:
        """Initialize instance state."""
        self.path = parent_dir / MANIFEST_FILENAME

    def exists(self) -> bool:
        """Exists."""
        return self.path.exists()

    def read(self) -> Manifest | None:
        """Parse the manifest.  Returns ``None`` when missing or corrupt."""
        if not self.path.exists():
            return None
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return Manifest.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return None

    def write(self, manifest: Manifest) -> None:
        """Write."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
