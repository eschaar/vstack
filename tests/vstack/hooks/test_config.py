"""Tests for hook artifact type configuration."""

from __future__ import annotations

from vstack.hooks.config import HOOK_TYPE


class TestHookType:
    """Test cases for HOOK_TYPE artifact configuration."""

    def test_type_name_is_hook(self) -> None:
        """type_name must be 'hook'."""
        assert HOOK_TYPE.type_name == "hook"

    def test_output_subdir_is_hooks(self) -> None:
        """Output artifacts go under the hooks subdirectory."""
        assert HOOK_TYPE.output_subdir == "hooks"

    def test_artifact_is_not_dir(self) -> None:
        """Hooks produce single-file artifacts, not directories."""
        assert HOOK_TYPE.artifact_is_dir is False

    def test_add_frontmatter_is_false(self) -> None:
        """Hook artifacts must not include frontmatter."""
        assert HOOK_TYPE.add_frontmatter is False

    def test_auto_gen_footer_is_false(self) -> None:
        """Hook artifacts must not include the auto-gen footer."""
        assert HOOK_TYPE.auto_gen_footer is False

    def test_template_filename_is_hook_yaml(self) -> None:
        """Hook artifacts render from hook.yaml template files."""
        assert HOOK_TYPE.template_filename == "hook.yaml"
