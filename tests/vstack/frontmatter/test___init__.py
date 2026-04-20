"""Tests for frontmatter package exports."""

from __future__ import annotations

import vstack.frontmatter


class TestFrontmatterInit:
    """Test cases for FrontmatterInit."""

    def test_reexports_parser_serializer_schema(self) -> None:
        """Test that reexports parser serializer schema."""
        assert vstack.frontmatter.FrontmatterParser is not None
        assert vstack.frontmatter.FrontmatterSerializer is not None
