"""Tests for instruction module constants."""

from __future__ import annotations

from vstack.instructions.constants import (
    INSTRUCTION_OUTPUT_SUBDIR,
    INSTRUCTION_OUTPUT_SUFFIX,
    INSTRUCTION_TEMPLATES_SUBDIR,
)


class TestInstructionConstants:
    """Test cases for instruction constant values."""

    def test_output_suffix_is_instructions_md(self) -> None:
        """Output suffix must end with .instructions.md."""
        assert INSTRUCTION_OUTPUT_SUFFIX == ".instructions.md"

    def test_templates_subdir_is_instructions(self) -> None:
        """Templates subdir must be 'instructions'."""
        assert INSTRUCTION_TEMPLATES_SUBDIR == "instructions"

    def test_output_subdir_is_instructions(self) -> None:
        """Output subdir must be 'instructions'."""
        assert INSTRUCTION_OUTPUT_SUBDIR == "instructions"
