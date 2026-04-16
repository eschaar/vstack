"""Utilities and tests for test models."""

from __future__ import annotations

from vstack.skills.models import GenerateResult, RenderedSkill


class TestSkillModelAliases:
    """Test cases for SkillModelAliases."""

    def test_aliases_exposed(self) -> None:
        """Test that aliases exposed."""
        assert GenerateResult is not None
        assert RenderedSkill is not None
