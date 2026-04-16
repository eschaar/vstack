"""Utilities and tests for test init."""

from __future__ import annotations

import vstack


class TestInit:
    """Test cases for Init."""

    def test_main_exported(self) -> None:
        """Test that main exported."""
        assert "main" in vstack.__all__
        assert callable(vstack.main)
