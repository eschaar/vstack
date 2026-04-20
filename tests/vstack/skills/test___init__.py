"""Tests for skill package exports."""

from __future__ import annotations

import vstack.skills


class TestSkillsInit:
    """Test cases for SkillsInit."""

    def test_exports_skill_generator(self) -> None:
        """Test that exports skill generator."""
        assert "SkillGenerator" in vstack.skills.__all__
