"""Tests for prompt artifact type configuration."""

from __future__ import annotations

from vstack.prompts.config import PROMPT_TYPE


class TestPromptType:
    """Test cases for PROMPT_TYPE artifact configuration."""

    def test_type_name_is_prompt(self) -> None:
        """type_name must be 'prompt'."""
        assert PROMPT_TYPE.type_name == "prompt"

    def test_output_subdir_is_prompts(self) -> None:
        """Output artifacts go under the prompts subdirectory."""
        assert PROMPT_TYPE.output_subdir == "prompts"

    def test_artifact_is_not_dir(self) -> None:
        """Prompts produce single-file artifacts, not directories."""
        assert PROMPT_TYPE.artifact_is_dir is False

    def test_add_frontmatter_is_true(self) -> None:
        """Prompt artifacts include frontmatter."""
        assert PROMPT_TYPE.add_frontmatter is True

    def test_auto_gen_footer_is_true(self) -> None:
        """Prompt artifacts include the auto-gen footer."""
        assert PROMPT_TYPE.auto_gen_footer is True
