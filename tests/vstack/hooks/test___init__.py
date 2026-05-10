"""Tests for vstack.hooks package public API."""

from __future__ import annotations

from vstack.hooks import HookGenerator


class TestHooksInit:
    """Test cases for vstack.hooks package exports."""

    def test_exports_hook_generator(self) -> None:
        """Package exports HookGenerator at the top level."""
        assert HookGenerator is not None

    def test_all_contains_hook_generator(self) -> None:
        """__all__ declares HookGenerator."""
        import vstack.hooks as mod

        assert "HookGenerator" in mod.__all__
