"""Tests for CLI interface dispatch orchestration."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, cast

import pytest

from vstack.cli.base import CommandContext
from vstack.cli.interface import CommandLineInterface


class _BuiltParser:
    """Parser-like object exposing parse_args."""

    def __init__(self, args: argparse.Namespace) -> None:
        self._args = args

    def parse_args(self) -> argparse.Namespace:
        """Return the configured parsed args."""
        return self._args


class _Parser:
    """Parser factory test double with configurable args and targets."""

    def __init__(self, args: argparse.Namespace, resolved_target=None) -> None:
        self._args = args
        self._resolved_target = resolved_target

    def build(self) -> _BuiltParser:
        """Return a parser-like object exposing parse_args."""
        return _BuiltParser(self._args)

    def resolve_targets(self, _args, *, command_name: str = "command") -> object:
        """Return the configured install target."""
        del command_name
        return self._resolved_target


class _Command:
    """Command test double that records invocation context."""

    def __init__(self, exit_code: int = 0) -> None:
        self.exit_code = exit_code
        self.calls: list[CommandContext] = []

    def run(self, *, context: CommandContext):
        """Record the call and return the configured exit code."""
        self.calls.append(context)
        return self.exit_code


class _Service:
    """Service construction test double."""

    def __init__(self, *, templates_root) -> None:
        self.templates_root = templates_root


class TestCommandLineInterface:
    """Test cases for interface-level parser and command dispatch."""

    def test_run_dispatches_validate_without_resolving_target(self, monkeypatch, tmp_path) -> None:
        """Test that validate passes through only-filter and no install_dir."""
        args = argparse.Namespace(command="validate", only=["skill"], use_global=False)
        parser = _Parser(args=args)
        command = _Command(exit_code=5)

        monkeypatch.setattr(
            "vstack.cli.interface.build_command_registry",
            lambda service: {"validate": command},
        )

        interface = CommandLineInterface(
            parser_cls=cast(Any, lambda: parser),
            service_cls=cast(Any, _Service),
            templates_root=tmp_path,
        )

        assert interface.run() == 5
        assert len(command.calls) == 1
        assert command.calls[0].args is args
        assert command.calls[0].install_dir is None
        assert command.calls[0].only == ["skill"]

    def test_run_dispatches_install_with_global_default_types(self, monkeypatch, tmp_path) -> None:
        """Test that install resolves targets and applies default global type filters."""
        args = argparse.Namespace(command="install", only=None, use_global=True)
        parser = _Parser(args=args, resolved_target=tmp_path / ".github")
        command = _Command(exit_code=9)

        monkeypatch.setattr(
            "vstack.cli.interface.build_command_registry",
            lambda service: {"install": command},
        )

        interface = CommandLineInterface(
            parser_cls=cast(Any, lambda: parser),
            service_cls=cast(Any, _Service),
            templates_root=tmp_path,
        )

        assert interface.run() == 9
        assert len(command.calls) == 1
        assert command.calls[0].args is args
        assert command.calls[0].install_dir == tmp_path / ".github"
        assert command.calls[0].only == ["agent", "instruction", "prompt", "skill"]

    def test_resolve_only_for_scope_rejects_disallowed_global_types(self) -> None:
        """Global mode rejects unsupported type filters with a helpful message."""
        args = argparse.Namespace(use_global=True, only=["skill", "workflow"])
        with pytest.raises(ValueError, match=r"Unsupported type\(s\): workflow"):
            CommandLineInterface.resolve_only_for_scope(args)

    def test_resolve_install_dir_returns_none_when_not_required(self, tmp_path: Path) -> None:
        """Commands that do not need an install dir skip target resolution."""

        class _Parser:
            def resolve_targets(
                self, args: argparse.Namespace, *, command_name: str = "command"
            ) -> Path:
                del args, command_name
                raise AssertionError("resolve_targets must not be called")

        cli = CommandLineInterface(templates_root=tmp_path)
        resolved = cli._resolve_install_dir(
            cli_parser=cast(Any, _Parser()),
            args=argparse.Namespace(command="validate"),
            requires_install_dir=False,
        )
        assert resolved is None

    def test_resolve_only_filter_passthrough_when_scope_resolution_disabled(
        self, tmp_path: Path
    ) -> None:
        """When scope resolution is off, interface passes through args.only as-is."""
        cli = CommandLineInterface(templates_root=tmp_path)
        args = argparse.Namespace(only=["skill"])
        assert cli._resolve_only_filter(args=args, resolve_only_for_scope=False) == ["skill"]

    def test_resolve_only_for_scope_passthrough_when_not_global(self) -> None:
        """Non-global calls return requested --only unchanged."""
        args = argparse.Namespace(use_global=False, only=["skill"])
        assert CommandLineInterface.resolve_only_for_scope(args) == ["skill"]

    def test_resolve_only_for_scope_accepts_allowed_global_types(self) -> None:
        """Global mode accepts allowed types unchanged."""
        args = argparse.Namespace(use_global=True, only=["skill", "agent"])
        assert CommandLineInterface.resolve_only_for_scope(args) == ["skill", "agent"]
