"""Tests for hook generator behavior."""

from __future__ import annotations

from vstack.hooks.generator import HookGenerator


class TestHookGenerator:
    """Test cases for HookGenerator."""

    def test_generator_uses_hook_type(self) -> None:
        """Test that generator uses hook type."""
        gen = HookGenerator()
        assert gen.config.type_name == "hook"
