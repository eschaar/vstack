"""Tests for CLI package exports."""

from __future__ import annotations

import vstack.cli


class TestCliInit:
    """Test cases for CliInit."""

    def test_cli_package_importable(self) -> None:
        """Test that cli package importable."""
        assert vstack.cli is not None
