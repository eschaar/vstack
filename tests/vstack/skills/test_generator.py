"""Utilities and tests for test generator."""

from __future__ import annotations

from vstack.skills.generator import SkillGenerator


class TestSkillGenerator:
    """Test cases for SkillGenerator."""

    def test_generator_uses_skill_type(self) -> None:
        """Test that generator uses skill type."""
        gen = SkillGenerator()
        assert gen.config.type_name == "skill"
