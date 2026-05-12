"""Tests for CLI interface dispatch orchestration."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, cast

import pytest

from vstack.cli.base import BaseCommand, CommandContext
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


class _ExposedCommandLineInterface(CommandLineInterface):
    """Test helper exposing selected internals through public wrappers."""

    def build_command_registry_public(self, service: Any) -> dict[str, BaseCommand]:
        """Expose registry construction for direct branch coverage."""
        return self._build_command_registry(cast(Any, service))


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

    def __init__(
        self,
        *,
        templates_root,
        items_root: str = "docs",
        workflow_stages=None,
        workflow_mode: str = "agentic",
        hook_default_mode: str = "audit",
        hook_default_log_level: str = "minimal",
        hook_log_retention_days: int = 7,
        hook_log_dir: str = ".vstack/logs",
        hook_mode_overrides=None,
        hook_log_level_overrides=None,
        hook_log_name_overrides=None,
        hook_log_retention_days_overrides=None,
        disabled_hook_names=None,
        excluded_names=None,
    ) -> None:
        self.templates_root = templates_root
        self.items_root = items_root
        self.workflow_stages = workflow_stages
        self.workflow_mode = workflow_mode
        self.hook_default_mode = hook_default_mode
        self.hook_default_log_level = hook_default_log_level
        self.hook_log_retention_days = hook_log_retention_days
        self.hook_log_dir = hook_log_dir
        self.hook_mode_overrides = hook_mode_overrides
        self.hook_log_level_overrides = hook_log_level_overrides
        self.hook_log_name_overrides = hook_log_name_overrides
        self.hook_log_retention_days_overrides = hook_log_retention_days_overrides
        self.disabled_hook_names = disabled_hook_names
        self.excluded_names = excluded_names


class TestCommandLineInterface:
    """Test cases for interface-level parser and command dispatch."""

    def test_build_command_registry_instantiates_catalog_commands(self, tmp_path: Path) -> None:
        """_build_command_registry returns instantiated command handlers."""
        interface = _ExposedCommandLineInterface(templates_root=tmp_path)
        registry = interface.build_command_registry_public(_Service(templates_root=tmp_path))
        assert "install" in registry
        assert "validate" in registry

    def test_run_dispatches_validate_without_resolving_target(self, monkeypatch, tmp_path) -> None:
        """Test that validate passes through only-filter and no install_dir."""
        args = argparse.Namespace(command="validate", only=["skill"], use_global=False)
        parser = _Parser(args=args)
        command = _Command(exit_code=5)

        monkeypatch.setattr(
            CommandLineInterface,
            "_build_command_registry",
            lambda self, service: {"validate": command},
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
            CommandLineInterface,
            "_build_command_registry",
            lambda self, service: {"install": command},
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
        assert command.calls[0].only == ["agent", "hook", "instruction", "prompt", "skill"]

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


class TestReadItemsRoot:
    """Tests for CommandLineInterface._read_items_root."""

    def test_returns_default_when_install_dir_is_none(self) -> None:
        """Returns ARTIFACTS_DOCS_ROOT when no install dir is provided."""
        from vstack.constants import ARTIFACTS_DOCS_ROOT

        assert CommandLineInterface._read_items_root(None) == ARTIFACTS_DOCS_ROOT

    def test_returns_default_when_config_file_absent(self, tmp_path: Path) -> None:
        """Returns ARTIFACTS_DOCS_ROOT when .vstack/config.yaml does not exist."""
        from vstack.constants import ARTIFACTS_DOCS_ROOT

        install_dir = tmp_path / ".github"
        assert CommandLineInterface._read_items_root(install_dir) == ARTIFACTS_DOCS_ROOT

    def test_returns_value_from_config(self, tmp_path: Path) -> None:
        """Returns the items.root value from .vstack/config.yaml."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text("items:\n  root: documentation\n", encoding="utf-8")

        install_dir = tmp_path / ".github"
        assert CommandLineInterface._read_items_root(install_dir) == "documentation"

    def test_returns_default_when_value_is_blank(self, tmp_path: Path) -> None:
        """Returns ARTIFACTS_DOCS_ROOT when items.root is present but blank."""
        from vstack.constants import ARTIFACTS_DOCS_ROOT

        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text("items:\n  root:\n", encoding="utf-8")

        install_dir = tmp_path / ".github"
        assert CommandLineInterface._read_items_root(install_dir) == ARTIFACTS_DOCS_ROOT

    def test_returns_default_when_key_absent_in_config(self, tmp_path: Path) -> None:
        """Returns ARTIFACTS_DOCS_ROOT when config.yaml exists but has no items.root key."""
        from vstack.constants import ARTIFACTS_DOCS_ROOT

        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text("exclude:\n  prompts: all\n", encoding="utf-8")

        install_dir = tmp_path / ".github"
        assert CommandLineInterface._read_items_root(install_dir) == ARTIFACTS_DOCS_ROOT

    def test_run_passes_items_root_from_config_to_service(
        self, monkeypatch, tmp_path: Path
    ) -> None:
        """run() reads items.root from .vstack/config.yaml and passes it to the service."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text("items:\n  root: custom\n", encoding="utf-8")

        install_dir = tmp_path / ".github"
        args = argparse.Namespace(command="install", only=None, use_global=False)
        parser = _Parser(args=args, resolved_target=install_dir)
        command = _Command(exit_code=0)
        captured: list[str] = []

        class _CapturingService:
            def __init__(
                self,
                *,
                templates_root,
                items_root: str = "docs",
                workflow_stages=None,
                workflow_mode: str = "agentic",
                hook_default_mode: str = "audit",
                hook_default_log_level: str = "minimal",
                hook_log_retention_days: int = 7,
                hook_log_dir: str = ".vstack/logs",
                hook_mode_overrides=None,
                hook_log_level_overrides=None,
                hook_log_name_overrides=None,
                hook_log_retention_days_overrides=None,
                disabled_hook_names=None,
                excluded_names=None,
            ) -> None:
                del (
                    templates_root,
                    workflow_stages,
                    workflow_mode,
                    hook_default_mode,
                    hook_default_log_level,
                    hook_log_retention_days,
                    hook_log_dir,
                    hook_mode_overrides,
                    hook_log_level_overrides,
                    hook_log_name_overrides,
                    hook_log_retention_days_overrides,
                    disabled_hook_names,
                    excluded_names,
                )
                captured.append(items_root)

        monkeypatch.setattr(
            CommandLineInterface,
            "_build_command_registry",
            lambda self, service: {"install": command},
        )

        interface = CommandLineInterface(
            parser_cls=cast(Any, lambda: parser),
            service_cls=cast(Any, _CapturingService),
            templates_root=tmp_path,
        )
        interface.run()

        assert captured == ["custom"]

    def test_returns_legacy_artifacts_root_when_items_root_missing(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Legacy artifacts.root still works and emits a deprecation warning."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "artifacts:\n  root: legacy-docs\n", encoding="utf-8"
        )

        install_dir = tmp_path / ".github"
        CommandLineInterface._legacy_items_root_warned = False
        assert CommandLineInterface._read_items_root(install_dir) == "legacy-docs"
        captured = capsys.readouterr()
        assert "legacy 'artifacts.root'" in captured.err


class TestReadWorkflowStages:
    """Tests for CommandLineInterface._read_workflow_stages."""

    def test_returns_empty_when_install_dir_is_none(self) -> None:
        """Returns empty list when install_dir is None."""
        assert CommandLineInterface._read_workflow_stages(None) == []

    def test_returns_empty_when_config_absent(self, tmp_path: Path) -> None:
        """Returns empty list when .vstack/config.yaml does not exist."""
        assert CommandLineInterface._read_workflow_stages(tmp_path / ".github") == []

    def test_returns_empty_when_workflow_block_absent(self, tmp_path: Path) -> None:
        """Returns empty list when config.yaml has no workflow block."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text("exclude:\n  prompts: all\n", encoding="utf-8")
        assert CommandLineInterface._read_workflow_stages(tmp_path / ".github") == []

    def test_returns_stages_from_config(self, tmp_path: Path) -> None:
        """Returns parsed stage list from workflow.stages block."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "workflow:\n"
            "  version: 1\n"
            "  stages:\n"
            "    - role: product\n"
            "      gate: required\n"
            "      handoffs:\n"
            "        prompt: Product done.\n"
            "    - role: architect\n"
            "      gate: optional\n"
            "      handoffs:\n"
            "        prompt: Arch done.\n",
            encoding="utf-8",
        )
        result = CommandLineInterface._read_workflow_stages(tmp_path / ".github")
        assert result == [
            {
                "role": "product",
                "gate": "required",
                "handoffs": [{"prompt": "Product done.", "agent": "", "label": ""}],
            },
            {
                "role": "architect",
                "gate": "optional",
                "handoffs": [{"prompt": "Arch done.", "agent": "", "label": ""}],
            },
        ]

    def test_preserves_hitl_field(self, tmp_path: Path) -> None:
        """hitl field is preserved in the parsed stage dict."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "workflow:\n"
            "  version: 1\n"
            "  stages:\n"
            "    - role: engineer\n"
            "      gate: required\n"
            "      hitl: always\n"
            "      handoffs:\n"
            "        prompt: Impl done.\n"
            "    - role: designer\n"
            "      gate: optional\n"
            "      hitl: on-change\n"
            "      handoffs:\n"
            "        prompt: Design done.\n",
            encoding="utf-8",
        )
        result = CommandLineInterface._read_workflow_stages(tmp_path / ".github")
        assert result == [
            {
                "role": "engineer",
                "gate": "required",
                "hitl": "always",
                "handoffs": [{"prompt": "Impl done.", "agent": "", "label": ""}],
            },
            {
                "role": "designer",
                "gate": "optional",
                "hitl": "on-change",
                "handoffs": [{"prompt": "Design done.", "agent": "", "label": ""}],
            },
        ]

    def test_skips_items_without_role(self, tmp_path: Path) -> None:
        """Items lacking a string 'role' key are silently skipped."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "workflow:\n  stages:\n    - gate: required\n    - role: engineer\n",
            encoding="utf-8",
        )
        result = CommandLineInterface._read_workflow_stages(tmp_path / ".github")
        assert result == [{"role": "engineer", "gate": "required", "handoffs": []}]

    def test_returns_empty_when_stages_not_a_list(self, tmp_path: Path) -> None:
        """Returns empty list when workflow.stages is not a list."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "workflow:\n  stages: not-a-list\n",
            encoding="utf-8",
        )
        result = CommandLineInterface._read_workflow_stages(tmp_path / ".github")
        assert result == []

    def test_parses_depends_on_list_when_present(self, tmp_path: Path) -> None:
        """depends_on is parsed as a normalized string list when configured."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "workflow:\n"
            "  stages:\n"
            "    - role: product\n"
            "    - role: designer\n"
            "      depends_on:\n"
            "        - product\n"
            "        - ' product '\n"
            "        - ''\n",
            encoding="utf-8",
        )

        result = CommandLineInterface._read_workflow_stages(tmp_path / ".github")
        assert result == [
            {"role": "product", "gate": "required", "handoffs": []},
            {
                "role": "designer",
                "gate": "required",
                "handoffs": [],
                "depends_on": ["product"],
            },
        ]

    def test_raises_when_depends_on_is_not_a_list(self, tmp_path: Path) -> None:
        """Scalar depends_on values fail fast instead of being treated as empty."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "workflow:\n"
            "  stages:\n"
            "    - role: product\n"
            "    - role: designer\n"
            "      depends_on: product\n",
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match=r"depends_on must be a list"):
            CommandLineInterface._read_workflow_stages(tmp_path / ".github")

    def test_raises_when_depends_on_contains_non_string_entry(self, tmp_path: Path) -> None:
        """Mixed-type depends_on lists are rejected instead of being partially ignored."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "workflow:\n"
            "  stages:\n"
            "    - role: product\n"
            "    - role: designer\n"
            "      depends_on:\n"
            "        - product\n"
            "        - 123\n",
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match=r"depends_on\[1\].*must be a string"):
            CommandLineInterface._read_workflow_stages(tmp_path / ".github")

    def test_raises_when_stage_role_is_blank(self, tmp_path: Path) -> None:
        """Blank stage role values fail with an actionable validation error."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "workflow:\n  stages:\n    - role: '   '\n",
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match=r"workflow\.stages\[0\]\.role"):
            CommandLineInterface._read_workflow_stages(tmp_path / ".github")

    def test_raises_when_stage_roles_are_duplicated(self, tmp_path: Path) -> None:
        """Duplicate stage roles are rejected to avoid ambiguous graph edges."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "workflow:\n  stages:\n    - role: product\n    - role: product\n",
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match="duplicate stage role 'product'"):
            CommandLineInterface._read_workflow_stages(tmp_path / ".github")

    def test_raises_when_handoff_targets_unknown_stage(self, tmp_path: Path) -> None:
        """Unknown explicit handoff agent targets are rejected."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "workflow:\n"
            "  stages:\n"
            "    - role: product\n"
            "      handoffs:\n"
            "        prompt: Next\n"
            "        agent: nonexistent\n"
            "    - role: architect\n",
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match=r"references unknown stage role 'nonexistent'"):
            CommandLineInterface._read_workflow_stages(tmp_path / ".github")

    def test_raises_when_workflow_graph_contains_cycle(self, tmp_path: Path) -> None:
        """Cycle detection rejects workflow handoff graphs that loop."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "workflow:\n"
            "  stages:\n"
            "    - role: product\n"
            "      handoffs:\n"
            "        prompt: To architect\n"
            "        agent: architect\n"
            "    - role: architect\n"
            "      handoffs:\n"
            "        prompt: Back to product\n"
            "        agent: product\n",
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match=r"cycle detected in workflow graph"):
            CommandLineInterface._read_workflow_stages(tmp_path / ".github")

    def test_raises_when_depends_on_references_unknown_stage(self, tmp_path: Path) -> None:
        """depends_on entries must reference known stage roles."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "workflow:\n"
            "  stages:\n"
            "    - role: product\n"
            "    - role: engineer\n"
            "      depends_on:\n"
            "        - missing\n",
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match=r"depends_on\[0\].*unknown stage role 'missing'"):
            CommandLineInterface._read_workflow_stages(tmp_path / ".github")

    def test_raises_when_depends_on_self_reference(self, tmp_path: Path) -> None:
        """depends_on entries cannot reference the stage itself."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "workflow:\n  stages:\n    - role: tester\n      depends_on:\n        - tester\n",
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match=r"depends_on\[0\].*cannot reference the same stage"):
            CommandLineInterface._read_workflow_stages(tmp_path / ".github")

    def test_raises_when_depends_on_graph_contains_cycle(self, tmp_path: Path) -> None:
        """Dependency cycles in depends_on are rejected."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "workflow:\n"
            "  stages:\n"
            "    - role: product\n"
            "      depends_on:\n"
            "        - architect\n"
            "    - role: architect\n"
            "      depends_on:\n"
            "        - product\n",
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match=r"cycle detected in workflow graph"):
            CommandLineInterface._read_workflow_stages(tmp_path / ".github")


class TestValidateWorkflowStages:
    """Tests for CommandLineInterface._validate_workflow_stages."""

    def test_accepts_linear_workflow_without_explicit_handoffs(self) -> None:
        """A plain stage list without handoffs is treated as a valid acyclic flow."""
        CommandLineInterface._validate_workflow_stages(
            [
                {"role": "product", "handoffs": []},
                {"role": "architect", "handoffs": []},
            ]
        )

    def test_ignores_non_dict_handoff_entries(self) -> None:
        """Non-dict handoff entries are ignored without failing validation."""
        CommandLineInterface._validate_workflow_stages(
            [
                {"role": "product", "handoffs": ["invalid-entry"]},
                {"role": "architect", "handoffs": []},
            ]
        )

    def test_ignores_empty_prompt_handoff_edges(self) -> None:
        """Handoffs with blank prompts do not contribute graph edges."""
        CommandLineInterface._validate_workflow_stages(
            [
                {
                    "role": "product",
                    "handoffs": [{"prompt": "   ", "agent": "architect", "label": ""}],
                },
                {"role": "architect", "handoffs": []},
            ]
        )

    def test_ignores_blank_depends_on_entries(self) -> None:
        """Blank depends_on entries are ignored during dependency normalization."""
        CommandLineInterface._validate_workflow_stages(
            [
                {"role": "product", "handoffs": []},
                {"role": "architect", "handoffs": [], "depends_on": ["  ", "product"]},
            ]
        )

    def test_raises_when_validate_sees_scalar_depends_on(self) -> None:
        """Validator rejects malformed scalar depends_on values."""
        with pytest.raises(ValueError, match=r"depends_on must be a list"):
            CommandLineInterface._validate_workflow_stages(
                [
                    {"role": "product", "handoffs": []},
                    {"role": "architect", "handoffs": [], "depends_on": "product"},
                ]
            )


class TestReadWorkflowMode:
    """Tests for CommandLineInterface._read_workflow_mode."""

    def test_returns_manual_when_install_dir_is_none(self) -> None:
        """Defaults to agentic mode when no install dir is available."""
        assert CommandLineInterface._read_workflow_mode(None) == "agentic"

    def test_returns_manual_when_config_absent(self, tmp_path: Path) -> None:
        """Defaults to agentic mode when .vstack/config.yaml is missing."""
        assert CommandLineInterface._read_workflow_mode(tmp_path / ".github") == "agentic"

    def test_returns_mode_from_config_when_valid(self, tmp_path: Path) -> None:
        """Returns parsed workflow.mode when value is supported."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text("workflow:\n  mode: agentic\n", encoding="utf-8")
        assert CommandLineInterface._read_workflow_mode(tmp_path / ".github") == "agentic"

    def test_returns_manual_when_mode_invalid(self, tmp_path: Path) -> None:
        """Invalid mode values are normalized to agentic."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "workflow:\n  mode: orchestration\n", encoding="utf-8"
        )
        assert CommandLineInterface._read_workflow_mode(tmp_path / ".github") == "agentic"

    def test_returns_manual_when_mode_not_string(self, tmp_path: Path) -> None:
        """Non-string workflow.mode values are normalized to agentic."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text("workflow:\n  mode: 1\n", encoding="utf-8")
        assert CommandLineInterface._read_workflow_mode(tmp_path / ".github") == "agentic"

    def test_run_passes_workflow_mode_to_service(self, monkeypatch, tmp_path: Path) -> None:
        """run() reads workflow.mode and passes it into service construction."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text("workflow:\n  mode: hybrid\n", encoding="utf-8")

        install_dir = tmp_path / ".github"
        args = argparse.Namespace(command="install", only=None, use_global=False)
        parser = _Parser(args=args, resolved_target=install_dir)
        command = _Command(exit_code=0)
        captured: list[str] = []

        class _CapturingService:
            def __init__(
                self,
                *,
                templates_root,
                items_root: str = "docs",
                workflow_stages=None,
                workflow_mode: str = "agentic",
                hook_default_mode: str = "audit",
                hook_default_log_level: str = "minimal",
                hook_log_retention_days: int = 7,
                hook_log_dir: str = ".vstack/logs",
                hook_mode_overrides=None,
                hook_log_level_overrides=None,
                hook_log_name_overrides=None,
                hook_log_retention_days_overrides=None,
                disabled_hook_names=None,
                excluded_names=None,
            ) -> None:
                del (
                    templates_root,
                    items_root,
                    workflow_stages,
                    hook_default_mode,
                    hook_default_log_level,
                    hook_log_retention_days,
                    hook_log_dir,
                    hook_mode_overrides,
                    hook_log_level_overrides,
                    hook_log_name_overrides,
                    hook_log_retention_days_overrides,
                    disabled_hook_names,
                    excluded_names,
                )
                captured.append(workflow_mode)

        monkeypatch.setattr(
            CommandLineInterface,
            "_build_command_registry",
            lambda self, service: {"install": command},
        )

        interface = CommandLineInterface(
            parser_cls=cast(Any, lambda: parser),
            service_cls=cast(Any, _CapturingService),
            templates_root=tmp_path,
        )
        interface.run()

        assert captured == ["hybrid"]


class TestReadHookSettings:
    """Tests for CommandLineInterface._read_hook_settings."""

    def test_returns_defaults_when_install_dir_is_none(self) -> None:
        """Missing install dir yields enabled audit defaults."""
        assert CommandLineInterface._read_hook_settings(None) == (
            True,
            "audit",
            "minimal",
            7,
            ".vstack/logs",
            [],
            {},
            {},
            {},
            {},
        )

    def test_reads_global_and_per_hook_settings(self, tmp_path: Path) -> None:
        """Reads hooks.enabled, hooks.mode, and per-hook overrides from config."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "hooks:\n"
            "  enabled: true\n"
            "  mode: enforce\n"
            "  log_level: verbose\n"
            "  log_retention_days: 14\n"
            "  hooks:\n"
            "    session-audit:\n"
            "      enabled: false\n"
            "    pre-tool-safety-gate:\n"
            "      mode: audit\n"
            "      log:\n"
            "        level: minimal\n"
            "        name: custom-security.log\n",
            encoding="utf-8",
        )

        (
            enabled,
            mode,
            log_level,
            retention_days,
            log_dir,
            disabled_names,
            mode_overrides,
            log_level_overrides,
            log_name_overrides,
            retention_days_overrides,
        ) = CommandLineInterface._read_hook_settings(tmp_path / ".github")

        assert enabled is True
        assert mode == "enforce"
        assert log_level == "verbose"
        assert retention_days == 14
        assert log_dir == ".vstack/logs"
        assert disabled_names == ["session-audit"]
        assert mode_overrides == {"pre-tool-safety-gate": "audit"}
        assert log_level_overrides == {"pre-tool-safety-gate": "minimal"}
        assert log_name_overrides == {"pre-tool-safety-gate": "custom-security.log"}
        assert retention_days_overrides == {}

    def test_run_applies_disabled_hooks_to_context_and_service(
        self, monkeypatch, tmp_path: Path
    ) -> None:
        """run() forwards hook settings into service construction and exclusions."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "hooks:\n"
            "  enabled: true\n"
            "  mode: enforce\n"
            "  hooks:\n"
            "    session-audit:\n"
            "      enabled: false\n",
            encoding="utf-8",
        )
        install_dir = tmp_path / ".github"
        args = argparse.Namespace(command="install", only=None, use_global=False)
        parser = _Parser(args=args, resolved_target=install_dir)
        command = _Command(exit_code=0)

        monkeypatch.setattr(
            CommandLineInterface,
            "_build_command_registry",
            lambda self, service: {"install": command},
        )

        interface = CommandLineInterface(
            parser_cls=cast(Any, lambda: parser),
            service_cls=cast(Any, _Service),
            templates_root=tmp_path,
        )
        interface.run()

        assert command.calls[0].excluded_names == {"hook": ["session-audit"]}

    def test_read_hook_settings_ignores_non_dict_hook_entries(self, tmp_path: Path) -> None:
        """Non-dict per-hook config entries are ignored gracefully."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "hooks:\n  hooks:\n    session-audit: disabled\n",
            encoding="utf-8",
        )

        (
            enabled,
            mode,
            log_level,
            retention_days,
            log_dir,
            disabled_names,
            mode_overrides,
            log_level_overrides,
            log_name_overrides,
            retention_days_overrides,
        ) = CommandLineInterface._read_hook_settings(tmp_path / ".github")

        assert enabled is True
        assert mode == "audit"
        assert log_level == "minimal"
        assert retention_days == 7
        assert log_dir == ".vstack/logs"
        assert disabled_names == []
        assert mode_overrides == {}
        assert log_level_overrides == {}
        assert log_name_overrides == {}
        assert retention_days_overrides == {}

    def test_invalid_log_retention_days_falls_back_to_default(self, tmp_path: Path) -> None:
        """Invalid hooks.log_retention_days values fall back to seven days."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "hooks:\n  log_retention_days: not-a-number\n",
            encoding="utf-8",
        )

        (
            enabled,
            mode,
            log_level,
            retention_days,
            log_dir,
            disabled_names,
            mode_overrides,
            log_level_overrides,
            log_name_overrides,
            retention_days_overrides,
        ) = CommandLineInterface._read_hook_settings(tmp_path / ".github")

        assert enabled is True
        assert mode == "audit"
        assert log_level == "minimal"
        assert retention_days == 7
        assert log_dir == ".vstack/logs"
        assert disabled_names == []
        assert mode_overrides == {}
        assert log_level_overrides == {}
        assert log_name_overrides == {}
        assert retention_days_overrides == {}

    def test_run_disables_hook_type_when_hooks_enabled_is_false(
        self, monkeypatch, tmp_path: Path
    ) -> None:
        """run() removes hook from effective_only when hooks.enabled is false."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "hooks:\n  enabled: false\n",
            encoding="utf-8",
        )
        install_dir = tmp_path / ".github"
        args = argparse.Namespace(command="install", only=None, use_global=False)
        parser = _Parser(args=args, resolved_target=install_dir)
        command = _Command(exit_code=0)

        monkeypatch.setattr(
            CommandLineInterface,
            "_build_command_registry",
            lambda self, service: {"install": command},
        )

        interface = CommandLineInterface(
            parser_cls=cast(Any, lambda: parser),
            service_cls=cast(Any, _Service),
            templates_root=tmp_path,
        )
        interface.run()

        assert command.calls[0].only is not None
        assert "hook" not in command.calls[0].only

    def test_per_hook_log_retention_days_override(self, tmp_path: Path) -> None:
        """Per-hook log.retention_days overrides are parsed correctly."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "hooks:\n"
            "  log_retention_days: 7\n"
            "  hooks:\n"
            "    post-commit-security-scan:\n"
            "      log:\n"
            "        retention_days: 30\n"
            "    session-audit:\n"
            "      log:\n"
            "        retention_days: 14\n",
            encoding="utf-8",
        )

        (
            enabled,
            mode,
            log_level,
            retention_days,
            _log_dir,
            disabled_names,
            mode_overrides,
            log_level_overrides,
            log_name_overrides,
            retention_days_overrides,
        ) = CommandLineInterface._read_hook_settings(tmp_path / ".github")

        assert enabled is True
        assert retention_days == 7
        assert retention_days_overrides == {
            "post-commit-security-scan": 30,
            "session-audit": 14,
        }

    def test_nested_per_hook_log_block_parses_name_level_and_retention(
        self, tmp_path: Path
    ) -> None:
        """Nested hooks.hooks.<name>.log.* keys are parsed for overrides."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "hooks:\n"
            "  hooks:\n"
            "    post-commit-security-scan:\n"
            "      log:\n"
            "        name: nested-security.log\n"
            "        level: verbose\n"
            "        retention_days: 45\n",
            encoding="utf-8",
        )

        (
            enabled,
            mode,
            log_level,
            retention_days,
            log_dir,
            disabled_names,
            mode_overrides,
            log_level_overrides,
            log_name_overrides,
            retention_days_overrides,
        ) = CommandLineInterface._read_hook_settings(tmp_path / ".github")

        assert enabled is True
        assert mode == "audit"
        assert log_level == "minimal"
        assert retention_days == 7
        assert log_dir == ".vstack/logs"
        assert disabled_names == []
        assert mode_overrides == {}
        assert log_level_overrides == {"post-commit-security-scan": "verbose"}
        assert log_name_overrides == {"post-commit-security-scan": "nested-security.log"}
        assert retention_days_overrides == {"post-commit-security-scan": 45}

    def test_flat_per_hook_log_keys_are_ignored(self, tmp_path: Path) -> None:
        """Flat per-hook log keys are ignored; only hooks.hooks.<name>.log.* applies."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "hooks:\n"
            "  hooks:\n"
            "    pre-tool-safety-gate:\n"
            "      log_level: minimal\n"
            "      log_name: flat.log\n"
            "      log_retention_days: 10\n",
            encoding="utf-8",
        )

        (
            enabled,
            mode,
            log_level,
            retention_days,
            log_dir,
            disabled_names,
            mode_overrides,
            log_level_overrides,
            log_name_overrides,
            retention_days_overrides,
        ) = CommandLineInterface._read_hook_settings(tmp_path / ".github")

        assert enabled is True
        assert mode == "audit"
        assert log_level == "minimal"
        assert retention_days == 7
        assert log_dir == ".vstack/logs"
        assert disabled_names == []
        assert mode_overrides == {}
        assert log_level_overrides == {}
        assert log_name_overrides == {}
        assert retention_days_overrides == {}

    def test_per_hook_log_name_validation_accepts_only_safe_log_filenames(
        self, tmp_path: Path
    ) -> None:
        """Only safe basename log names ending with .log are accepted."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "hooks:\n"
            "  hooks:\n"
            "    post-edit-format:\n"
            "      log:\n"
            "        name: quality-custom.log\n"
            "    pre-tool-safety-gate:\n"
            "      log:\n"
            "        name: ../escape.log\n"
            "    post-commit-security-scan:\n"
            "      log:\n"
            "        name: security/alerts.log\n"
            "    session-audit:\n"
            "      log:\n"
            "        name: absolute.log.tmp\n"
            "    post-edit-markdown-quality:\n"
            "      log:\n"
            "        name: bad*chars.log\n",
            encoding="utf-8",
        )

        (
            _enabled,
            _mode,
            _log_level,
            _retention_days,
            _log_dir,
            _disabled_names,
            _mode_overrides,
            _log_level_overrides,
            log_name_overrides,
            _retention_days_overrides,
        ) = CommandLineInterface._read_hook_settings(tmp_path / ".github")

        assert log_name_overrides == {"post-edit-format": "quality-custom.log"}

    def test_per_hook_log_name_strips_outer_whitespace(self, tmp_path: Path) -> None:
        """Per-hook log.name values are trimmed before validation and storage."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "hooks:\n"
            "  hooks:\n"
            "    post-edit-format:\n"
            "      log:\n"
            "        name: '  windows-style.log  '\n",
            encoding="utf-8",
        )

        (
            _enabled,
            _mode,
            _log_level,
            _retention_days,
            _log_dir,
            _disabled_names,
            _mode_overrides,
            _log_level_overrides,
            log_name_overrides,
            _retention_days_overrides,
        ) = CommandLineInterface._read_hook_settings(tmp_path / ".github")

        assert log_name_overrides == {"post-edit-format": "windows-style.log"}

    def test_global_hook_log_dir_override_is_parsed(self, tmp_path: Path) -> None:
        """hooks.log_dir overrides the default log root for generated hook scripts."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "hooks:\n  log_dir: .vstack/custom-logs\n",
            encoding="utf-8",
        )

        (
            _enabled,
            _mode,
            _log_level,
            _retention_days,
            log_dir,
            _disabled_names,
            _mode_overrides,
            _log_level_overrides,
            _log_name_overrides,
            _retention_days_overrides,
        ) = CommandLineInterface._read_hook_settings(tmp_path / ".github")

        assert log_dir == ".vstack/custom-logs"

    def test_global_hook_log_dir_invalid_value_falls_back_to_default(self, tmp_path: Path) -> None:
        """Invalid hooks.log_dir values fall back to the default generated log root."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "hooks:\n  log_dir: []\n",
            encoding="utf-8",
        )

        (
            _enabled,
            _mode,
            _log_level,
            _retention_days,
            log_dir,
            _disabled_names,
            _mode_overrides,
            _log_level_overrides,
            _log_name_overrides,
            _retention_days_overrides,
        ) = CommandLineInterface._read_hook_settings(tmp_path / ".github")

        assert log_dir == ".vstack/logs"


class TestParseStageHandoffs:
    """Tests for CommandLineInterface._parse_stage_handoffs."""

    def test_dict_handoffs_returns_single_entry(self) -> None:
        """A dict handoffs value is returned as a single-entry list."""
        item = {
            "role": "architect",
            "handoffs": {"prompt": "Arch done.", "agent": "designer", "label": "Go"},
        }
        result = CommandLineInterface._parse_stage_handoffs(item)
        assert result == [{"prompt": "Arch done.", "agent": "designer", "label": "Go"}]

    def test_list_handoffs_returns_multiple_entries(self) -> None:
        """A list handoffs value returns multiple normalized entries."""
        item = {
            "role": "architect",
            "handoffs": [
                {"prompt": "Go to designer.", "agent": "", "label": ""},
                {"prompt": "Skip to engineer.", "agent": "engineer", "label": "Skip design"},
            ],
        }
        result = CommandLineInterface._parse_stage_handoffs(item)
        assert len(result) == 2
        assert result[0]["prompt"] == "Go to designer."
        assert result[1]["agent"] == "engineer"

    def test_backward_compat_handoff_prompt_key(self) -> None:
        """Legacy flat handoff_prompt key is wrapped as single-entry handoffs."""
        item = {"role": "architect", "handoff_prompt": "Legacy prompt."}
        result = CommandLineInterface._parse_stage_handoffs(item)
        assert result == [{"prompt": "Legacy prompt.", "agent": "", "label": ""}]

    def test_no_handoffs_returns_empty(self) -> None:
        """Returns empty list when no handoffs or handoff_prompt key is present."""
        result = CommandLineInterface._parse_stage_handoffs({"role": "architect"})
        assert result == []


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

    def test_raises_when_agents_excluded(self, tmp_path: Path) -> None:
        """Configuring exclude: agents raises ValueError referencing ADR-022."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text("exclude:\n  agents: all\n", encoding="utf-8")
        with pytest.raises(ValueError, match="ADR-022"):
            CommandLineInterface._read_exclude(tmp_path / ".github")

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
            CommandLineInterface,
            "_build_command_registry",
            lambda self, service: {"install": command},
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
            CommandLineInterface,
            "_build_command_registry",
            lambda self, service: {"install": command},
        )
        interface = CommandLineInterface(
            parser_cls=cast(Any, lambda: parser),
            service_cls=cast(Any, _Service),
            templates_root=tmp_path,
        )
        interface.run()

        assert command.calls[0].excluded_names == {"skill": ["terraform", "helm"]}
