"""Tests for prompt module constants."""

from __future__ import annotations

from vstack.prompts.constants import (
    PROMPT_OUTPUT_SUBDIR,
    PROMPT_OUTPUT_SUFFIX,
    PROMPT_TEMPLATES_SUBDIR,
)


class TestPromptConstants:
    """Test cases for prompt constant values."""

    def test_output_suffix_is_prompt_md(self) -> None:
        """Output suffix must end with .prompt.md."""
        assert PROMPT_OUTPUT_SUFFIX == ".prompt.md"

    def test_templates_subdir_is_prompts(self) -> None:
        """Templates subdir must be 'prompts'."""
        assert PROMPT_TEMPLATES_SUBDIR == "prompts"

    def test_output_subdir_is_prompts(self) -> None:
        """Output subdir must be 'prompts'."""
        assert PROMPT_OUTPUT_SUBDIR == "prompts"
