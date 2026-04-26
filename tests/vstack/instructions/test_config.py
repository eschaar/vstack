"""Tests for instruction artifact type configuration."""

from __future__ import annotations

from vstack.instructions.config import INSTRUCTION_TYPE


class TestInstructionType:
    """Test cases for INSTRUCTION_TYPE artifact configuration."""

    def test_type_name_is_instruction(self) -> None:
        """type_name must be 'instruction'."""
        assert INSTRUCTION_TYPE.type_name == "instruction"

    def test_output_subdir_is_instructions(self) -> None:
        """Output artifacts go under the instructions subdirectory."""
        assert INSTRUCTION_TYPE.output_subdir == "instructions"

    def test_artifact_is_not_dir(self) -> None:
        """Instructions produce single-file artifacts, not directories."""
        assert INSTRUCTION_TYPE.artifact_is_dir is False

    def test_add_frontmatter_is_true(self) -> None:
        """Instruction artifacts include frontmatter."""
        assert INSTRUCTION_TYPE.add_frontmatter is True

    def test_auto_gen_footer_is_true(self) -> None:
        """Instruction artifacts include the auto-gen footer."""
        assert INSTRUCTION_TYPE.auto_gen_footer is True
