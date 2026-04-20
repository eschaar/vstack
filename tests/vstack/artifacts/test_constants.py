"""Tests for artifact constants."""

from __future__ import annotations

from vstack.artifacts.constants import AUTO_GEN_FOOTER


class TestArtifactConstants:
    """Test cases for ArtifactConstants."""

    def test_auto_gen_footer_contains_marker(self) -> None:
        """Test that auto gen footer contains marker."""
        assert "AUTO-GENERATED" in AUTO_GEN_FOOTER
