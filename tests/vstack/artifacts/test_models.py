"""Utilities and tests for test models."""

from __future__ import annotations

from pathlib import Path

from vstack.artifacts.models import ArtifactResult, RenderedArtifact
from vstack.models import ValidationResult


class TestRenderedArtifact:
    """Test cases for RenderedArtifact."""

    def test_defaults(self) -> None:
        """Test that defaults."""
        artifact = RenderedArtifact(name="x", content="body", source_path=Path("a"))
        assert artifact.frontmatter is None
        assert artifact.unresolved == []


class TestArtifactResult:
    """Test cases for ArtifactResult."""

    def test_ok_true_when_clean(self) -> None:
        """Test that ok true when clean."""
        result = ArtifactResult(
            artifacts=[], unresolved_warnings=[], verification=ValidationResult()
        )
        assert result.ok

    def test_ok_false_when_warnings(self) -> None:
        """Test that ok false when warnings."""
        result = ArtifactResult(
            artifacts=[],
            unresolved_warnings=["warn"],
            verification=ValidationResult(),
        )
        assert not result.ok
