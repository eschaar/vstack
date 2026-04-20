"""Tests for skill artifact configuration."""

from __future__ import annotations

from vstack.skills.config import SKILL_SCHEMA, SKILL_TYPE


class TestSkillSchema:
    """Test cases for SkillSchema."""

    def test_required_fields_enforced(self) -> None:
        """Test that required fields enforced."""
        errors = SKILL_SCHEMA.validate_meta({"name": "foo"})
        assert any("description" in e for e in errors)

    def test_name_constraints_enforced(self) -> None:
        """Test that name constraints enforced."""
        errors = SKILL_SCHEMA.validate_meta(
            {
                "name": "Invalid Name",
                "description": "valid description",
            }
        )
        assert any("pattern" in e for e in errors)

    def test_progressive_disclosure_optional_fields_supported(self) -> None:
        """Test that progressive disclosure optional fields supported."""
        errors = SKILL_SCHEMA.validate_meta(
            {
                "name": "code-review",
                "description": "Review code and flag production risks.",
                "license": "Apache-2.0",
                "compatibility": "Requires git, docker, jq, and internet access.",
                "metadata": "  author: vstack\n  track: internal",
            }
        )
        assert errors == []

    def test_compatibility_max_length_enforced(self) -> None:
        """Test that compatibility max length enforced."""
        errors = SKILL_SCHEMA.validate_meta(
            {
                "name": "code-review",
                "description": "valid description",
                "compatibility": "x" * 501,
            }
        )
        assert any("compatibility" in e and "max length" in e for e in errors)


class TestSkillType:
    """Test cases for SkillType."""

    def test_type_config_shape(self) -> None:
        """Test that type config shape."""
        assert SKILL_TYPE.type_name == "skill"
        assert SKILL_TYPE.output_pattern == "{name}/SKILL.md"
        assert SKILL_TYPE.auto_gen_footer is True
        assert SKILL_TYPE.placeholders == {
            "SKILL_CONTEXT": "skill-context.md",
            "BASE_BRANCH": "base-branch.md",
            "RUN_TESTS": "run-tests.md",
            "OBSERVABILITY_CHECKLIST": "observability-checklist.md",
        }
