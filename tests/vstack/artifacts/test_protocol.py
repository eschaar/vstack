"""Utilities and tests for test protocol."""

from __future__ import annotations

from pathlib import Path

from vstack.artifacts.models import ArtifactResult
from vstack.artifacts.protocol import ArtifactGenerator
from vstack.models import ValidationResult


class _Impl:
    """Represents Impl."""

    def generate(self, output_dir: Path) -> ArtifactResult:
        """Generate."""
        return ArtifactResult([], [], ValidationResult())

    def verify_input(self, expected_names=None) -> ValidationResult:
        """Verify input."""
        return ValidationResult()

    def verify_output(self, output_dir: Path, expected_names=None) -> ValidationResult:
        """Verify output."""
        return ValidationResult()


class TestArtifactGeneratorProtocol:
    """Test cases for ArtifactGeneratorProtocol."""

    def test_protocol_compatible_impl(self, tmp_path: Path) -> None:
        """Test that protocol compatible impl."""
        gen: ArtifactGenerator = _Impl()
        assert gen.verify_input().ok
        assert gen.verify_output(tmp_path).ok
        assert gen.generate(tmp_path).ok
