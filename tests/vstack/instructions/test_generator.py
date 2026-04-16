"""Utilities and tests for test generator."""

from __future__ import annotations

from vstack.instructions.generator import InstructionGenerator


class TestInstructionGenerator:
    """Test cases for InstructionGenerator."""

    def test_generator_uses_instruction_type(self) -> None:
        """Test that generator uses instruction type."""
        gen = InstructionGenerator()
        assert gen.config.type_name == "instruction"
