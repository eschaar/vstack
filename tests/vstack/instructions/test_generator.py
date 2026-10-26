"""Tests for instruction generator behavior."""

from __future__ import annotations

from pathlib import Path

from vstack.instructions.generator import InstructionGenerator


class TestInstructionGenerator:
    """Test cases for InstructionGenerator."""

    def test_generator_uses_instruction_type(self) -> None:
        """Test that generator uses instruction type."""
        gen = InstructionGenerator()
        assert gen.config.type_name == "instruction"

    def test_rendered_testing_policy_links_acceptance_without_workflow(
        self, installed_target: Path
    ) -> None:
        """Always-on policy covers observable boundaries without adding ceremony."""
        text = (installed_target / ".github/instructions/testing.instructions.md").read_text(
            encoding="utf-8"
        )
        assert "observable acceptance" in text
        assert "failure, compatibility, and data/operational boundaries" in text
        assert "Code coverage and task checkboxes do not prove acceptance" in text
        assert "required failed or unrun checks are not passes" in text
        assert "BUILD" not in text
        assert "docs/changes/" not in text
