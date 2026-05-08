"""CLI orchestration facade for parsing and command dispatch."""

from __future__ import annotations

import argparse
from pathlib import Path

from vstack.cli.base import CommandContext
from vstack.cli.catalog import COMMAND_CATALOG
from vstack.cli.constants import GLOBAL_SUPPORTED_TYPE_NAMES, KNOWN_TYPE_NAMES
from vstack.cli.parser import CommandLineParser
from vstack.cli.registry import build_command_registry
from vstack.cli.service import CommandService
from vstack.constants import ARTIFACTS_DOCS_ROOT
from vstack.frontmatter import FrontmatterParser

# Maps plural config.yaml keys to singular internal type names.
_CONFIG_TYPE_ALIAS: dict[str, str] = {
    "agents": "agent",
    "instructions": "instruction",
    "prompts": "prompt",
    "skills": "skill",
}


class CommandLineInterface:
    """Facade that coordinates parser, service construction, and dispatch."""

    def __init__(
        self,
        *,
        parser_cls: type[CommandLineParser] = CommandLineParser,
        service_cls: type[CommandService] = CommandService,
        templates_root,
    ) -> None:
        self._parser_cls = parser_cls
        self._service_cls = service_cls
        self._templates_root = templates_root

    @classmethod
    def resolve_only_for_scope(cls, args: argparse.Namespace) -> list[str] | None:
        """Resolve effective ``--only`` values for the active command scope."""
        requested_only = getattr(args, "only", None)
        if not getattr(args, "use_global", False):
            return requested_only

        if requested_only is None:
            return list(GLOBAL_SUPPORTED_TYPE_NAMES)

        disallowed = [t for t in requested_only if t not in GLOBAL_SUPPORTED_TYPE_NAMES]
        if disallowed:
            allowed = ", ".join(GLOBAL_SUPPORTED_TYPE_NAMES)
            raise ValueError(
                f"--global supports only: {allowed}. Unsupported type(s): {', '.join(disallowed)}"
            )

        return requested_only

    def _resolve_install_dir(
        self,
        *,
        cli_parser: CommandLineParser,
        args: argparse.Namespace,
        requires_install_dir: bool,
    ) -> Path | None:
        """Resolve the install directory only for commands that need one."""
        if not requires_install_dir:
            return None
        return cli_parser.resolve_targets(args, command_name=args.command)

    def _resolve_only_filter(
        self,
        *,
        args: argparse.Namespace,
        resolve_only_for_scope: bool,
    ) -> list[str] | None:
        """Resolve effective ``--only`` filter for the active command."""
        if resolve_only_for_scope:
            return self.resolve_only_for_scope(args)
        return getattr(args, "only", None)

    @staticmethod
    def _read_exclude(
        install_dir: Path | None,
    ) -> tuple[frozenset[str], dict[str, list[str]]]:
        """Read ``exclude:`` from ``.vstack/config.yaml`` when available.

        Returns a pair:

        - *excluded_types*: set of singular type names to skip entirely
          (from ``type: all``).
        - *excluded_names*: mapping of singular type name → artifact names
          to skip within that type (from ``type: [name, …]``).

        Both are empty when *install_dir* is ``None``, when the config file
        does not exist, or when the ``exclude:`` key is absent.
        """
        if install_dir is None:
            return frozenset(), {}
        config_path = install_dir.parent / ".vstack" / "config.yaml"
        if not config_path.exists():
            return frozenset(), {}
        parsed = FrontmatterParser.parse_yaml(config_path.read_text(encoding="utf-8"))
        raw_exclude = parsed.get("exclude", "")
        # The minimal YAML parser stores nested mappings as raw indented strings.
        # Re-parse by stripping the 2-space indent to access sub-keys.
        if isinstance(raw_exclude, str) and raw_exclude.strip():
            dedented = "\n".join(
                line[2:] if line.startswith("  ") else line for line in raw_exclude.split("\n")
            )
            raw_exclude = FrontmatterParser.parse_yaml(dedented) or {}
        if not isinstance(raw_exclude, dict):
            return frozenset(), {}
        excluded_types: set[str] = set()
        excluded_names: dict[str, list[str]] = {}
        for config_key, value in raw_exclude.items():
            type_name = _CONFIG_TYPE_ALIAS.get(config_key)
            if type_name is None:
                continue  # unknown key, ignore gracefully
            if type_name == "agent":
                raise ValueError(
                    "exclude: agents is not supported. "
                    "The six-role agent chain is an atomic unit and cannot be partially "
                    "excluded. See ADR-022."
                )
            if isinstance(value, str) and value.strip().lower() == "all":
                excluded_types.add(type_name)
            elif isinstance(value, list):
                names = [str(n) for n in value if isinstance(n, str)]
                if names:
                    excluded_names[type_name] = names
        return frozenset(excluded_types), excluded_names

    @staticmethod
    def _read_artifacts_root(install_dir: Path | None) -> str:
        """Read ``artifacts.root`` from ``.vstack/config.yaml`` when available.

        Returns :data:`~vstack.constants.ARTIFACTS_DOCS_ROOT` when *install_dir*
        is ``None``, when the config file does not exist, or when the key is
        absent or blank.
        """
        if install_dir is None:
            return ARTIFACTS_DOCS_ROOT
        config_path = install_dir.parent / ".vstack" / "config.yaml"
        if not config_path.exists():
            return ARTIFACTS_DOCS_ROOT
        parsed = FrontmatterParser.parse_yaml(config_path.read_text(encoding="utf-8"))
        artifacts = parsed.get("artifacts", "")
        # The minimal YAML parser stores nested mappings as raw indented strings.
        # Re-parse by stripping the 2-space indent to access sub-keys.
        if isinstance(artifacts, str) and artifacts.strip():
            dedented = "\n".join(
                line[2:] if line.startswith("  ") else line for line in artifacts.split("\n")
            )
            artifacts = FrontmatterParser.parse_yaml(dedented) or {}
        if not isinstance(artifacts, dict):
            return ARTIFACTS_DOCS_ROOT
        value = artifacts.get("root", "")
        if isinstance(value, str) and value.strip():
            return value.strip()
        return ARTIFACTS_DOCS_ROOT

    @staticmethod
    def _read_workflow_stages(install_dir: Path | None) -> list[dict]:
        """Read ``workflow.stages`` from ``.vstack/config.yaml`` when available.

        Returns an empty list when *install_dir* is ``None``, when the config
        file does not exist, or when the ``workflow:`` block is absent or
        contains no valid stages.

        Each returned dict has at minimum a ``role`` key.  Optional keys are
        ``gate``, ``hitl``, and ``handoffs`` (a list of handoff dicts, each with
        at minimum a ``prompt`` key and optionally ``agent`` and ``label``
        overrides).  Unknown extra keys in the stage dict are silently ignored.
        """
        if install_dir is None:
            return []
        config_path = install_dir.parent / ".vstack" / "config.yaml"
        if not config_path.exists():
            return []
        parsed = FrontmatterParser.parse_yaml(config_path.read_text(encoding="utf-8"))
        workflow = parsed.get("workflow", "")
        if isinstance(workflow, str) and workflow.strip():
            dedented = "\n".join(
                line[2:] if line.startswith("  ") else line for line in workflow.split("\n")
            )
            workflow = FrontmatterParser.parse_yaml(dedented) or {}
        if not isinstance(workflow, dict):
            return []
        stages_raw = workflow.get("stages", [])
        if not isinstance(stages_raw, list):
            return []
        result: list[dict] = []
        for item in stages_raw:
            if isinstance(item, dict) and isinstance(item.get("role"), str):
                handoffs = CommandLineInterface._parse_stage_handoffs(item)
                stage: dict = {
                    "role": item["role"],
                    "gate": str(item.get("gate", "required")),
                    "handoffs": handoffs,
                }
                if "hitl" in item:
                    stage["hitl"] = str(item["hitl"])
                result.append(stage)
        return result

    @staticmethod
    def _parse_stage_handoffs(item: dict) -> list[dict[str, str]]:
        """Parse the ``handoffs`` entry from a workflow stage dict.

        Supports the nested block form (``handoffs: {prompt: ...}``) and
        the nested list form (``handoffs: [{prompt: ...}, ...]``).  Falls
        back to the legacy ``handoff_prompt`` flat key for backward
        compatibility with pre-3.x configs.

        Each returned dict has ``prompt``, ``agent``, and ``label`` keys
        (empty string when absent).
        """
        raw = item.get("handoffs", "")
        parsed_block: dict | list | None = None

        if isinstance(raw, str) and raw.strip():
            parsed_block = FrontmatterParser.parse_yaml(raw.strip())
        elif isinstance(raw, (dict, list)):
            parsed_block = raw

        if isinstance(parsed_block, dict):
            # Single-handoff dict form: {prompt: ..., agent?: ..., label?: ...}
            return [
                {
                    "prompt": str(parsed_block.get("prompt", "") or ""),
                    "agent": str(parsed_block.get("agent", "") or ""),
                    "label": str(parsed_block.get("label", "") or ""),
                }
            ]
        if isinstance(parsed_block, list):
            # Multi-handoff list form: [{prompt: ..., agent?: ..., label?: ...}, ...]
            result = []
            for h in parsed_block:
                if isinstance(h, dict):
                    result.append(
                        {
                            "prompt": str(h.get("prompt", "") or ""),
                            "agent": str(h.get("agent", "") or ""),
                            "label": str(h.get("label", "") or ""),
                        }
                    )
            return result

        # Backward compat: legacy flat ``handoff_prompt`` key.
        legacy = str(item.get("handoff_prompt", "") or "")
        if legacy:
            return [{"prompt": legacy, "agent": "", "label": ""}]
        return []

    def run(self) -> int:
        """Run one CLI invocation and return a process-style status code."""
        cli_parser = self._parser_cls()
        parser = cli_parser.build()
        args = parser.parse_args()
        command_config = COMMAND_CATALOG[args.command]

        resolved_install_dir = self._resolve_install_dir(
            cli_parser=cli_parser,
            args=args,
            requires_install_dir=command_config.requires_install_dir,
        )
        artifacts_root = self._read_artifacts_root(resolved_install_dir)
        workflow_stages = self._read_workflow_stages(resolved_install_dir)
        service = self._service_cls(
            templates_root=self._templates_root,
            artifacts_root=artifacts_root,
            workflow_stages=workflow_stages,
        )
        commands = build_command_registry(service)
        effective_only = self._resolve_only_filter(
            args=args,
            resolve_only_for_scope=command_config.resolve_only_for_scope,
        )
        excluded_types, excluded_names = self._read_exclude(resolved_install_dir)
        if excluded_types:
            base = effective_only if effective_only is not None else list(KNOWN_TYPE_NAMES)
            effective_only = [t for t in base if t not in excluded_types]

        command = commands[args.command]
        context = CommandContext(
            args=args,
            install_dir=resolved_install_dir,
            only=effective_only,
            excluded_names=excluded_names or None,
        )
        return command.run(context=context)
