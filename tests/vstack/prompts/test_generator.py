"""Tests for prompt generator behavior."""

from __future__ import annotations

from vstack.prompts.generator import PromptGenerator


class TestPromptGenerator:
    """Test cases for PromptGenerator."""

    def test_generator_uses_prompt_type(self) -> None:
        """Test that generator uses prompt type."""
        gen = PromptGenerator()
        assert gen.config.type_name == "prompt"
