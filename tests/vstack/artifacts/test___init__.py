"""Utilities and tests for test init."""

from __future__ import annotations

import vstack.artifacts


class TestArtifactsInit:
    """Test cases for ArtifactsInit."""

    def test_reexports_key_types(self) -> None:
        """Test that reexports key types."""
        assert vstack.artifacts.ArtifactTypeConfig is not None
        assert vstack.artifacts.GenericArtifactGenerator is not None
