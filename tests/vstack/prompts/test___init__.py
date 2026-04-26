"""Tests for vstack.prompts package public API."""

from __future__ import annotations

from vstack.prompts import PromptGenerator


class TestPromptsInit:
    """Test cases for vstack.prompts package exports."""

    def test_exports_prompt_generator(self) -> None:
        """Package exports PromptGenerator at the top level."""
        assert PromptGenerator is not None

    def test_all_contains_prompt_generator(self) -> None:
        """__all__ declares PromptGenerator."""
        import vstack.prompts as mod

        assert "PromptGenerator" in mod.__all__
