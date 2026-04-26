"""Tests for CLI base types: CommandContext and BaseCommand."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

import pytest

from vstack.cli.base import BaseCommand, CommandContext


class _FakeCommand(BaseCommand):
    """Minimal concrete BaseCommand for testing."""

    def __init__(self, exit_code: int = 0) -> None:
        self.exit_code = exit_code

    def run(self, *, context: CommandContext) -> int:
        del context
        return self.exit_code


class TestCommandContext:
    """Test cases for CommandContext."""

    def test_require_install_dir_returns_value(self, tmp_path: Path) -> None:
        """Returns install_dir when it is set."""
        context = CommandContext(args=Namespace(), install_dir=tmp_path, only=None)
        assert context.require_install_dir("install") == tmp_path

    def test_require_install_dir_raises_when_missing(self) -> None:
        """Raises ValueError when the command requires install_dir but none is set."""
        context = CommandContext(args=Namespace(), install_dir=None, only=None)
        with pytest.raises(ValueError, match="requires install_dir"):
            context.require_install_dir("status")


class TestBaseCommand:
    """Test cases for BaseCommand."""

    def test_concrete_subclass_run_returns_exit_code(self) -> None:
        """Concrete subclass run() returns the configured exit code."""
        context = CommandContext(args=Namespace(), install_dir=None, only=None)
        assert _FakeCommand(exit_code=3).run(context=context) == 3
