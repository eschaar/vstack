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
        hook_mode_overrides=None,
        disabled_hook_names=None,
        excluded_names=None,
    ) -> None:
        self.templates_root = templates_root
        self.items_root = items_root
        self.workflow_stages = workflow_stages
        self.workflow_mode = workflow_mode
        self.hook_default_mode = hook_default_mode
        self.hook_mode_overrides = hook_mode_overrides
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
                hook_mode_overrides=None,
                disabled_hook_names=None,
                excluded_names=None,
            ) -> None:
                del (
                    templates_root,
                    workflow_stages,
                    workflow_mode,
                    hook_default_mode,
                    hook_mode_overrides,
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
                hook_mode_overrides=None,
                disabled_hook_names=None,
                excluded_names=None,
            ) -> None:
                del (
                    templates_root,
                    items_root,
                    workflow_stages,
                    hook_default_mode,
                    hook_mode_overrides,
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
        assert CommandLineInterface._read_hook_settings(None) == (True, "audit", [], {})

    def test_reads_global_and_per_hook_settings(self, tmp_path: Path) -> None:
        """Reads hooks.enabled, hooks.mode, and per-hook overrides from config."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text(
            "hooks:\n"
            "  enabled: true\n"
            "  mode: enforce\n"
            "  hooks:\n"
            "    session-audit:\n"
            "      enabled: false\n"
            "    pre-tool-safety-gate:\n"
            "      mode: audit\n",
            encoding="utf-8",
        )

        enabled, mode, disabled_names, mode_overrides = CommandLineInterface._read_hook_settings(
            tmp_path / ".github"
        )

        assert enabled is True
        assert mode == "enforce"
        assert disabled_names == ["session-audit"]
        assert mode_overrides == {"pre-tool-safety-gate": "audit"}

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

        enabled, mode, disabled_names, mode_overrides = CommandLineInterface._read_hook_settings(
            tmp_path / ".github"
        )

        assert enabled is True
        assert mode == "audit"
        assert disabled_names == []
        assert mode_overrides == {}

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
