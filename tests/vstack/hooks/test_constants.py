"""Tests for hook module constants."""

from __future__ import annotations

from vstack.hooks.constants import (
    HOOK_OUTPUT_SUBDIR,
    HOOK_OUTPUT_SUFFIX,
    HOOK_TEMPLATE_FILENAME,
    HOOK_TEMPLATES_SUBDIR,
)


class TestHookConstants:
    """Test cases for hook constant values."""

    def test_output_suffix_is_json(self) -> None:
        """Output suffix must end with .json."""
        assert HOOK_OUTPUT_SUFFIX == ".json"

    def test_templates_subdir_is_hooks(self) -> None:
        """Templates subdir must be 'hooks'."""
        assert HOOK_TEMPLATES_SUBDIR == "hooks"

    def test_output_subdir_is_hooks(self) -> None:
        """Output subdir must be 'hooks'."""
        assert HOOK_OUTPUT_SUBDIR == "hooks"

    def test_template_filename_is_hook_json(self) -> None:
        """Template filename must be hook.json."""
        assert HOOK_TEMPLATE_FILENAME == "hook.json"
