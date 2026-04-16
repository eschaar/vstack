"""Utilities and tests for test init."""

from __future__ import annotations

import vstack.frontmatter


class TestFrontmatterInit:
    """Test cases for FrontmatterInit."""

    def test_reexports_parser_builder_schema(self) -> None:
        """Test that reexports parser builder schema."""
        assert vstack.frontmatter.FrontmatterParser is not None
        assert vstack.frontmatter.build_output is not None
