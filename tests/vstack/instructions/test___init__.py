"""Tests for vstack.instructions package public API."""

from __future__ import annotations

from vstack.instructions import InstructionGenerator


class TestInstructionsInit:
    """Test cases for vstack.instructions package exports."""

    def test_exports_instruction_generator(self) -> None:
        """Package exports InstructionGenerator at the top level."""
        assert InstructionGenerator is not None

    def test_all_contains_instruction_generator(self) -> None:
        """__all__ declares InstructionGenerator."""
        import vstack.instructions as mod

        assert "InstructionGenerator" in mod.__all__
