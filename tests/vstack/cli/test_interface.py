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

    def __init__(self, *, templates_root, artifacts_root: str = "docs") -> None:
        self.templates_root = templates_root
        self.artifacts_root = artifacts_root


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


class TestReadArtifactsRoot:
    """Tests for CommandLineInterface._read_artifacts_root."""

    def test_returns_default_when_install_dir_is_none(self) -> None:
        """Returns ARTIFACTS_DOCS_ROOT when no install dir is provided."""
        from vstack.constants import ARTIFACTS_DOCS_ROOT

        assert CommandLineInterface._read_artifacts_root(None) == ARTIFACTS_DOCS_ROOT

    def test_returns_default_when_config_file_absent(self, tmp_path: Path) -> None:
        """Returns ARTIFACTS_DOCS_ROOT when .vstack/config.yaml does not exist."""
        from vstack.constants import ARTIFACTS_DOCS_ROOT

        install_dir = tmp_path / ".github"
        assert CommandLineInterface._read_artifacts_root(install_dir) == ARTIFACTS_DOCS_ROOT

    def test_returns_value_from_config(self, tmp_path: Path) -> None:
        """Returns the artifacts.root value from .vstack/config.yaml."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "artifacts:\n  root: documentation\n", encoding="utf-8"
        )

        install_dir = tmp_path / ".github"
        assert CommandLineInterface._read_artifacts_root(install_dir) == "documentation"

    def test_returns_default_when_value_is_blank(self, tmp_path: Path) -> None:
        """Returns ARTIFACTS_DOCS_ROOT when artifacts.root is present but blank."""
        from vstack.constants import ARTIFACTS_DOCS_ROOT

        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text("artifacts:\n  root:\n", encoding="utf-8")

        install_dir = tmp_path / ".github"
        assert CommandLineInterface._read_artifacts_root(install_dir) == ARTIFACTS_DOCS_ROOT

    def test_returns_default_when_key_absent_in_config(self, tmp_path: Path) -> None:
        """Returns ARTIFACTS_DOCS_ROOT when config.yaml exists but has no artifacts.root key."""
        from vstack.constants import ARTIFACTS_DOCS_ROOT

        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text("exclude:\n  prompts: all\n", encoding="utf-8")

        install_dir = tmp_path / ".github"
        assert CommandLineInterface._read_artifacts_root(install_dir) == ARTIFACTS_DOCS_ROOT

    def test_run_passes_artifacts_root_from_config_to_service(
        self, monkeypatch, tmp_path: Path
    ) -> None:
        """run() reads artifacts.root from .vstack/config.yaml and passes it to the service."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text("artifacts:\n  root: custom\n", encoding="utf-8")

        install_dir = tmp_path / ".github"
        args = argparse.Namespace(command="install", only=None, use_global=False)
        parser = _Parser(args=args, resolved_target=install_dir)
        command = _Command(exit_code=0)
        captured: list[str] = []

        class _CapturingService:
            def __init__(self, *, templates_root, artifacts_root: str = "docs") -> None:
                captured.append(artifacts_root)

        monkeypatch.setattr(
            "vstack.cli.interface.build_command_registry",
            lambda service: {"install": command},
        )

        interface = CommandLineInterface(
            parser_cls=cast(Any, lambda: parser),
            service_cls=cast(Any, _CapturingService),
            templates_root=tmp_path,
        )
        interface.run()

        assert captured == ["custom"]


class TestReadExclude:
    """Tests for CommandLineInterface._read_exclude."""

    def test_returns_empty_when_install_dir_is_none(self) -> None:
        """Returns empty sets when no install dir is provided."""
        excluded_types, excluded_names = CommandLineInterface._read_exclude(None)
        assert excluded_types == frozenset()
        assert excluded_names == {}

    def test_returns_empty_when_config_absent(self, tmp_path: Path) -> None:
        """Returns empty sets when .vstack/config.yaml does not exist."""
        install_dir = tmp_path / ".github"
        excluded_types, excluded_names = CommandLineInterface._read_exclude(install_dir)
        assert excluded_types == frozenset()
        assert excluded_names == {}

    def test_returns_excluded_type_for_all(self, tmp_path: Path) -> None:
        """Returns excluded type when a type entry is 'all'."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text("exclude:\n  instructions: all\n", encoding="utf-8")
        excluded_types, excluded_names = CommandLineInterface._read_exclude(tmp_path / ".github")
        assert "instruction" in excluded_types
        assert excluded_names == {}

    def test_returns_excluded_names_for_list(self, tmp_path: Path) -> None:
        """Returns name list when a type entry is a list of artifact names."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "exclude:\n  skills:\n    - terraform\n    - helm\n", encoding="utf-8"
        )
        excluded_types, excluded_names = CommandLineInterface._read_exclude(tmp_path / ".github")
        assert excluded_types == frozenset()
        assert excluded_names == {"skill": ["terraform", "helm"]}

    def test_handles_mixed_all_and_list(self, tmp_path: Path) -> None:
        """Handles both 'all' and name-list entries in the same exclude block."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "exclude:\n  prompts: all\n  skills:\n    - helm\n", encoding="utf-8"
        )
        excluded_types, excluded_names = CommandLineInterface._read_exclude(tmp_path / ".github")
        assert "prompt" in excluded_types
        assert excluded_names == {"skill": ["helm"]}

    def test_ignores_unknown_keys(self, tmp_path: Path) -> None:
        """Unknown type keys in exclude block are silently ignored."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text("exclude:\n  workflows: all\n", encoding="utf-8")
        excluded_types, excluded_names = CommandLineInterface._read_exclude(tmp_path / ".github")
        assert excluded_types == frozenset()
        assert excluded_names == {}

    def test_returns_empty_when_exclude_key_absent(self, tmp_path: Path) -> None:
        """Returns empty sets when config.yaml has no exclude key."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text("artifacts:\n  root: docs\n", encoding="utf-8")
        excluded_types, excluded_names = CommandLineInterface._read_exclude(tmp_path / ".github")
        assert excluded_types == frozenset()
        assert excluded_names == {}

    def test_run_removes_excluded_type_from_only(self, monkeypatch, tmp_path: Path) -> None:
        """run() removes excluded types from effective_only when exclude: type: all."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "exclude:\n  prompts: all\n  instructions: all\n", encoding="utf-8"
        )
        install_dir = tmp_path / ".github"
        args = argparse.Namespace(command="install", only=None, use_global=False)
        parser = _Parser(args=args, resolved_target=install_dir)
        command = _Command(exit_code=0)

        monkeypatch.setattr(
            "vstack.cli.interface.build_command_registry",
            lambda service: {"install": command},
        )
        interface = CommandLineInterface(
            parser_cls=cast(Any, lambda: parser),
            service_cls=cast(Any, _Service),
            templates_root=tmp_path,
        )
        interface.run()

        assert command.calls[0].only is not None
        assert "prompt" not in command.calls[0].only
        assert "instruction" not in command.calls[0].only
        assert "skill" in command.calls[0].only
        assert "agent" in command.calls[0].only

    def test_run_passes_excluded_names_to_context(self, monkeypatch, tmp_path: Path) -> None:
        """run() passes name-level exclusions as context.excluded_names."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "exclude:\n  skills:\n    - terraform\n    - helm\n", encoding="utf-8"
        )
        install_dir = tmp_path / ".github"
        args = argparse.Namespace(command="install", only=None, use_global=False)
        parser = _Parser(args=args, resolved_target=install_dir)
        command = _Command(exit_code=0)

        monkeypatch.setattr(
            "vstack.cli.interface.build_command_registry",
            lambda service: {"install": command},
        )
        interface = CommandLineInterface(
            parser_cls=cast(Any, lambda: parser),
            service_cls=cast(Any, _Service),
            templates_root=tmp_path,
        )
        interface.run()

        assert command.calls[0].excluded_names == {"skill": ["terraform", "helm"]}
