"""Tests for CLI parser behavior."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from vstack.cli import parser as parser_module


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

    def test_resolve_targets_target_missing_exits(self, tmp_path: Path) -> None:
        """Test that resolve targets target missing exits."""
        args = argparse.Namespace(target=str(tmp_path / "missing"), use_global=False)
        with pytest.raises(SystemExit) as exc:
            parser_module.CommandLineParser().resolve_targets(args)
        assert exc.value.code == 1

    def test_resolve_targets_global_missing_exits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that resolve targets global missing exits."""
        monkeypatch.setattr(parser_module.CommandLineParser, "vscode_user_dir", lambda self: None)
        args = argparse.Namespace(target=None, use_global=True)
        with pytest.raises(SystemExit) as exc:
            parser_module.CommandLineParser().resolve_targets(args)
        assert exc.value.code == 1

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
        actions = [a for a in parser._actions if isinstance(a, argparse._SubParsersAction)]
        subcommands = set(actions[0].choices.keys())
        assert subcommands == {"validate", "verify", "install", "uninstall"}

    def test_verify_accepts_only_filter(self) -> None:
        """Test that verify command supports --only type filters."""
        parser = parser_module.CommandLineParser().build()
        args = parser.parse_args(["verify", "--only", "agent", "prompt", "--no-source"])
        assert args.command == "verify"
        assert args.only == ["agent", "prompt"]
        assert args.source is False
