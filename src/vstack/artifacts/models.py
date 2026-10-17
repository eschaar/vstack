"""Shared models for generated skills, agents, instructions, and hooks."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from vstack.models import ValidationResult


@dataclass
class RenderedArtifact:
    """Represent a rendered artifact ready to write to disk.

    Attributes:
        name:        Logical identifier (directory name or stem without suffix).
        content:     Full file content, ready to write.
        source_path: Origin template or source file.
        frontmatter: Parsed YAML front matter dict, or ``None`` when the
                     artifact type does not use front matter.
        unresolved:  Template tokens that were not resolved during rendering.
                     Always empty for artifact types that are not templated.
    """

    name: str
    content: str
    source_path: Path
    frontmatter: dict | None = None
    unresolved: list[str] = field(default_factory=list)


@dataclass
class ArtifactResult:
    """Result of generating a set of artifacts to an output directory.

    Attributes:
        artifacts:            The rendered artifacts that were written.
        unresolved_warnings:  Human-readable warnings for any unresolved tokens.
        verification:         Output verification result run after writing.
    """

    artifacts: list[RenderedArtifact]
    unresolved_warnings: list[str]
    verification: ValidationResult

    @property
    def ok(self) -> bool:
        """``True`` when there are no unresolved warnings and verification passed."""
        return not self.unresolved_warnings and self.verification.ok
