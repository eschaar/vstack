"""Tests for CLI parser behavior."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, cast

import pytest

from vstack.cli import parser as parser_module
from vstack.cli.base import BaseCommand, CommandContext
from vstack.cli.catalog import TopLevelCommandConfig


class TestParserHelpers:
    """Test cases for ParserHelpers."""

    def test_vscode_user_dir_none_when_missing(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test that vscode user dir none when missing."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        assert parser_module.CommandLineParser().vscode_user_dir() is None


class TestResolveTargets:
    """Test cases for ResolveTargets."""

    def test_resolve_targets_default_uses_cwd_dot_github(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test that resolve targets default uses cwd dot github."""
        monkeypatch.chdir(tmp_path)
        args = argparse.Namespace(target=None, use_global=False)
        assert parser_module.CommandLineParser().resolve_targets(args) == tmp_path / ".github"

    def test_resolve_targets_target_existing(self, tmp_path: Path) -> None:
        """Test that resolve targets target existing."""
        target = tmp_path / "workspace"
        target.mkdir()
        args = argparse.Namespace(target=str(target), use_global=False)
        assert parser_module.CommandLineParser().resolve_targets(args) == target / ".github"

    def test_resolve_targets_target_missing_raises_value_error(self, tmp_path: Path) -> None:
        """Test that resolve targets target missing raises ValueError."""
        args = argparse.Namespace(target=str(tmp_path / "missing"), use_global=False)
        with pytest.raises(ValueError, match="target directory does not exist"):
            parser_module.CommandLineParser().resolve_targets(args)

    def test_resolve_targets_global_missing_raises_value_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that resolve targets global missing raises ValueError."""
        monkeypatch.setattr(parser_module.CommandLineParser, "vscode_user_dir", lambda self: None)
        args = argparse.Namespace(target=None, use_global=True)
        with pytest.raises(ValueError, match="Could not detect VS Code user data directory"):
            parser_module.CommandLineParser().resolve_targets(args)

    def test_resolve_targets_global_returns_user_dir(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Test that resolve targets global returns user dir."""
        user_dir = tmp_path / "User"
        user_dir.mkdir(parents=True)
        monkeypatch.setattr(
            parser_module.CommandLineParser, "vscode_user_dir", lambda self: user_dir
        )
        args = argparse.Namespace(target=None, use_global=True)
        assert parser_module.CommandLineParser().resolve_targets(args) == user_dir


class TestBuildParser:
    """Test cases for BuildParser."""

    def test_build_parser_has_expected_commands(self) -> None:
        """Test that build parser has expected commands."""
        parser = parser_module.CommandLineParser().build()
        subcommands_action = next(
            (action for action in parser._actions if hasattr(action, "choices") and action.choices),
            None,
        )
        assert subcommands_action is not None
        subcommands = set(cast(Any, subcommands_action).choices.keys())
        assert subcommands == {"validate", "verify", "status", "manifest", "install", "uninstall"}

    def test_verify_accepts_only_filter(self) -> None:
        """Test that verify command supports --only type filters."""
        parser = parser_module.CommandLineParser().build()
        args = parser.parse_args(["verify", "--only", "agent", "prompt", "--no-source"])
        assert args.command == "verify"
        assert args.only == ["agent", "prompt"]
        assert args.source is False

    def test_install_accepts_force_name(self) -> None:
        """Test that install supports targeted force names."""
        parser = parser_module.CommandLineParser().build()
        args = parser.parse_args(["install", "--force-name", "vision", "--target", "."])
        assert args.command == "install"
        assert args.force_names == ["vision"]

    def test_install_accepts_adopt_name(self) -> None:
        """Test that install supports targeted adopt names."""
        parser = parser_module.CommandLineParser().build()
        args = parser.parse_args(["install", "--adopt-name", "vision", "--target", "."])
        assert args.command == "install"
        assert args.adopt_name == ["vision"]

    def test_status_accepts_only_filter(self) -> None:
        """Test that status supports --only type filters."""
        parser = parser_module.CommandLineParser().build()
        args = parser.parse_args(["status", "--only", "skill", "--target", "."])
        assert args.command == "status"
        assert args.only == ["skill"]

    def test_status_accepts_format_and_readability_flags(self) -> None:
        """Test that status supports format and readability controls."""
        parser = parser_module.CommandLineParser().build()
        args = parser.parse_args(
            ["status", "--format", "json", "--verbose", "--no-color", "--target", "."]
        )
        assert args.command == "status"
        assert args.output_format == "json"
        assert args.verbose is True
        assert args.no_color is True

    def test_uninstall_accepts_force_name(self) -> None:
        """Test that uninstall supports targeted force names."""
        parser = parser_module.CommandLineParser().build()
        args = parser.parse_args(["uninstall", "--force-name", "vision", "--target", "."])
        assert args.command == "uninstall"
        assert args.force_names == ["vision"]

    def test_manifest_upgrade_subcommand_parses(self) -> None:
        """Test that manifest upgrade subcommand parses target arguments."""
        parser = parser_module.CommandLineParser().build()
        args = parser.parse_args(["manifest", "upgrade", "--target", "."])
        assert args.command == "manifest"
        assert args.manifest_action == "upgrade"

    def test_manifest_upgrade_accepts_backfill_flag(self) -> None:
        """Test that manifest upgrade supports optional checksum backfill."""
        parser = parser_module.CommandLineParser().build()
        args = parser.parse_args(["manifest", "upgrade", "--backfill", "--target", "."])
        assert args.command == "manifest"
        assert args.manifest_action == "upgrade"
        assert args.backfill is True

    def test_manifest_status_subcommand_parses(self) -> None:
        """Test that manifest status subcommand parses status formatting flags."""
        parser = parser_module.CommandLineParser().build()
        args = parser.parse_args(
            [
                "manifest",
                "status",
                "--format",
                "json",
                "--verbose",
                "--no-color",
                "--target",
                ".",
            ]
        )
        assert args.command == "manifest"
        assert args.manifest_action == "status"
        assert args.output_format == "json"
        assert args.verbose is True
        assert args.no_color is True

    def test_manifest_verify_subcommand_parses(self) -> None:
        """Test that manifest verify subcommand parses only filter."""
        parser = parser_module.CommandLineParser().build()
        args = parser.parse_args(["manifest", "verify", "--only", "skill", "--target", "."])
        assert args.command == "manifest"
        assert args.manifest_action == "verify"
        assert args.only == ["skill"]

    def test_scoped_command_requires_scope_help(self) -> None:
        """Parser fails fast when scoped command config has missing scope_help."""

        class _FakeCmd(BaseCommand):
            def run(self, *, context: CommandContext) -> int:
                del context
                return 0

        def _dummy_factory(service: object) -> _FakeCmd:
            del service
            return _FakeCmd()

        cli_parser = parser_module.CommandLineParser()
        sub = argparse.ArgumentParser().add_subparsers(dest="command")
        config = TopLevelCommandConfig(
            command_factory=_dummy_factory,
            help_text="x",
            requires_install_dir=False,
            resolve_only_for_scope=False,
            include_scope_group=True,
            include_only_option=False,
            scope_help=None,
            only_help=None,
            include_status_output_options=False,
        )
        with pytest.raises(ValueError, match="scope_help is required"):
            cli_parser._add_scoped_only_command(sub, command_name="x", config=config)

    def test_scoped_command_requires_only_help_when_only_enabled(self) -> None:
        """Parser fails fast when include_only_option is set without only_help."""

        class _FakeCmd(BaseCommand):
            def run(self, *, context: CommandContext) -> int:
                del context
                return 0

        def _dummy_factory(service: object) -> _FakeCmd:
            del service
            return _FakeCmd()

        cli_parser = parser_module.CommandLineParser()
        sub = argparse.ArgumentParser().add_subparsers(dest="command")
        config = TopLevelCommandConfig(
            command_factory=_dummy_factory,
            help_text="x",
            requires_install_dir=False,
            resolve_only_for_scope=False,
            include_scope_group=True,
            include_only_option=True,
            scope_help="help",
            only_help=None,
            include_status_output_options=False,
        )
        with pytest.raises(ValueError, match="only_help is required"):
            cli_parser._add_scoped_only_command(sub, command_name="x", config=config)
