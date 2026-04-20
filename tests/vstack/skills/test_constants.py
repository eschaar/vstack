"""Tests for skill constants."""

from __future__ import annotations

from vstack.skills.constants import (
    SKILL_OUTPUT_SUBDIR,
    SKILL_TEMPLATES_SUBDIR,
    SKILLS_PARTIALS_DIR,
    SKILLS_TEMPLATES_DIR,
)


class TestSkillConstants:
    """Test cases for SkillConstants."""

    def test_skill_subdir_values(self) -> None:
        """Test that skill subdir values."""
        assert SKILL_TEMPLATES_SUBDIR == "skills"
        assert SKILL_OUTPUT_SUBDIR == "skills"

    def test_template_and_partials_dirs_exist(self) -> None:
        """Test that template and partials dirs exist."""
        assert SKILLS_TEMPLATES_DIR.exists()
        assert SKILLS_PARTIALS_DIR.exists()
