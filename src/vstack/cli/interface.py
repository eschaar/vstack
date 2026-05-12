"""CLI orchestration facade for parsing and command dispatch."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, cast

from vstack.cli.base import BaseCommand, CommandContext
from vstack.cli.catalog import COMMAND_CATALOG
from vstack.cli.constants import GLOBAL_SUPPORTED_TYPE_NAMES, KNOWN_TYPE_NAMES
from vstack.cli.parser import CommandLineParser
from vstack.cli.service import CommandService
from vstack.constants import ARTIFACTS_DOCS_ROOT
from vstack.frontmatter import FrontmatterParser

# Maps plural config.yaml keys to singular internal type names.
_CONFIG_TYPE_ALIAS: dict[str, str] = {
    "agents": "agent",
    "hooks": "hook",
    "instructions": "instruction",
    "prompts": "prompt",
    "skills": "skill",
}


class CommandLineInterface:
    """Facade that coordinates parser, service construction, and dispatch."""

    _legacy_items_root_warned = False

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
    def _is_valid_hook_log_name(name: str) -> bool:
        """Return whether *name* is an allowed per-hook log filename.

        Allowed names are plain filenames (no path separators), ending in ``.log``
        and containing only alphanumeric characters, ``.``, ``_`` and ``-``.
        """
        candidate = name.strip()
        if not candidate:
            return False
        if "/" in candidate or "\\" in candidate:
            return False
        if not candidate.endswith(".log"):
            return False
        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
        return all(char in allowed for char in candidate)

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
                    "The role-agent set is an atomic unit and cannot be partially "
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
    def _read_items_root(install_dir: Path | None) -> str:
        """Read ``items.root`` for agent work-item paths from ``.vstack/config.yaml``.

        Returns :data:`~vstack.constants.ARTIFACTS_DOCS_ROOT` when *install_dir*
        is ``None``, when the config file does not exist, or when the key is
        absent or blank.

        Backward compatibility: if ``items.root`` is not set, the legacy
        ``artifacts.root`` key is still accepted and triggers a deprecation warning.
        """
        if install_dir is None:
            return ARTIFACTS_DOCS_ROOT
        config_path = install_dir.parent / ".vstack" / "config.yaml"
        if not config_path.exists():
            return ARTIFACTS_DOCS_ROOT
        parsed = FrontmatterParser.parse_yaml(config_path.read_text(encoding="utf-8"))
        items = parsed.get("items", "")
        if isinstance(items, dict):
            value = items.get("root", "")
            if isinstance(value, str) and value.strip():
                return value.strip()

        artifacts = parsed.get("artifacts", "")
        if isinstance(artifacts, dict):
            value = artifacts.get("root", "")
            if isinstance(value, str) and value.strip():
                if not CommandLineInterface._legacy_items_root_warned:
                    print(
                        "WARNING: '.vstack/config.yaml' uses legacy 'artifacts.root'. "
                        "Use 'items.root' for agent work-item paths. "
                        "Run 'vstack migrate --target <dir>' to auto-upgrade.",
                        file=sys.stderr,
                    )
                    CommandLineInterface._legacy_items_root_warned = True
                return value.strip()
        return ARTIFACTS_DOCS_ROOT

    @staticmethod
    def _read_workflow_stages(install_dir: Path | None) -> list[dict]:
        """Read ``workflow.stages`` from ``.vstack/config.yaml`` when available.

        Returns an empty list when *install_dir* is ``None``, when the config
        file does not exist, or when the ``workflow:`` block is absent or
        contains no valid stages.

        Each returned dict has at minimum a ``role`` key.  Optional keys are
        ``gate``, ``hitl``, ``depends_on``, and ``handoffs`` (a list of handoff
        dicts, each with at minimum a ``prompt`` key and optionally ``agent``
        and ``label`` overrides). Unknown extra keys in the stage dict are
        silently ignored.
        """
        if install_dir is None:
            return []
        config_path = install_dir.parent / ".vstack" / "config.yaml"
        if not config_path.exists():
            return []
        parsed = FrontmatterParser.parse_yaml(config_path.read_text(encoding="utf-8"))
        workflow = parsed.get("workflow", "")
        if not isinstance(workflow, dict):
            return []
        stages_raw = workflow.get("stages", [])
        if not isinstance(stages_raw, list):
            return []
        result: list[dict] = []
        for stage_index, item in enumerate(stages_raw):
            if isinstance(item, dict) and isinstance(item.get("role"), str):
                handoffs = CommandLineInterface._parse_stage_handoffs(item)
                normalized_role = item["role"].strip()
                stage: dict = {
                    "role": normalized_role,
                    "gate": str(item.get("gate", "required")),
                    "handoffs": handoffs,
                }
                if "hitl" in item:
                    stage["hitl"] = str(item["hitl"])
                if "depends_on" in item:
                    raw_depends_on = item.get("depends_on", [])
                    if not isinstance(raw_depends_on, list):
                        raise ValueError(
                            "Invalid workflow config: "
                            f"workflow.stages[{stage_index}].depends_on must be a list"
                        )
                    depends_on: list[str] = []
                    for dep_index, dep in enumerate(raw_depends_on):
                        if not isinstance(dep, str):
                            raise ValueError(
                                "Invalid workflow config: "
                                f"workflow.stages[{stage_index}].depends_on[{dep_index}] must be a string"
                            )
                        dep_name = dep.strip()
                        if dep_name and dep_name not in depends_on:
                            depends_on.append(dep_name)
                    stage["depends_on"] = depends_on
                result.append(stage)
        CommandLineInterface._validate_workflow_stages(result)
        return result

    @staticmethod
    def _validate_workflow_stages(stages: list[dict]) -> None:
        """Validate parsed workflow stages for consistency and graph safety.

        Validation rules:

        - Every stage role must be a non-empty string after trimming.
        - Stage roles must be unique.
        - Explicit handoff targets (``handoffs[].agent``) must reference an
          existing stage role.
        - The implied workflow graph must be acyclic.

        The graph includes explicit handoff edges and implicit sequential
        fallback edges used when a stage has no explicit handoffs.
        """
        if not stages:
            return

        role_to_index: dict[str, int] = {}
        roles: list[str] = []
        for index, stage in enumerate(stages):
            role = str(stage.get("role", "")).strip()
            if not role:
                raise ValueError(
                    f"Invalid workflow config: workflow.stages[{index}].role must be a non-empty string"
                )
            if role in role_to_index:
                previous_index = role_to_index[role]
                raise ValueError(
                    "Invalid workflow config: duplicate stage role "
                    f"'{role}' at workflow.stages[{index}] "
                    f"(already defined at workflow.stages[{previous_index}])"
                )
            role_to_index[role] = index
            roles.append(role)

        role_set = set(roles)
        dependencies_by_role: dict[str, list[str]] = {}
        edges: dict[str, set[str]] = {role: set() for role in roles}

        for stage_index, stage in enumerate(stages):
            stage_role = roles[stage_index]
            if "depends_on" in stage:
                raw_depends_on = stage.get("depends_on", [])
                if not isinstance(raw_depends_on, list):
                    raise ValueError(
                        "Invalid workflow config: "
                        f"workflow.stages[{stage_index}].depends_on must be a list"
                    )
                depends_on = raw_depends_on
            else:
                # Backward compatibility: without depends_on, keep canonical
                # sequential dependency semantics.
                depends_on = [roles[stage_index - 1]] if stage_index > 0 else []

            normalized_depends_on: list[str] = []
            for dep_index, dep in enumerate(depends_on):
                if not isinstance(dep, str):
                    raise ValueError(
                        "Invalid workflow config: "
                        f"workflow.stages[{stage_index}].depends_on[{dep_index}] must be a string"
                    )
                dep_role = str(dep).strip()
                if not dep_role:
                    continue
                if dep_role not in role_set:
                    raise ValueError(
                        "Invalid workflow config: "
                        f"workflow.stages[{stage_index}].depends_on[{dep_index}] "
                        f"references unknown stage role '{dep_role}'"
                    )
                if dep_role == stage_role:
                    raise ValueError(
                        "Invalid workflow config: "
                        f"workflow.stages[{stage_index}].depends_on[{dep_index}] "
                        "cannot reference the same stage role"
                    )
                if dep_role not in normalized_depends_on:
                    normalized_depends_on.append(dep_role)

            dependencies_by_role[stage_role] = normalized_depends_on
            for dep_role in normalized_depends_on:
                edges[dep_role].add(stage_role)

        dependents_by_role: dict[str, list[str]] = {role: [] for role in roles}
        for role in roles:
            for dependent in roles:
                if role in dependencies_by_role.get(dependent, []):
                    dependents_by_role[role].append(dependent)

        for stage_index, stage in enumerate(stages):
            source_role = roles[stage_index]
            next_roles = dependents_by_role.get(source_role, [])
            primary_next_role = next_roles[0] if next_roles else ""
            raw_handoffs = stage.get("handoffs", [])
            handoffs = raw_handoffs if isinstance(raw_handoffs, list) else []

            if not handoffs:
                for next_role in next_roles:
                    edges[source_role].add(next_role)
                continue

            for handoff_index, handoff in enumerate(handoffs):
                if not isinstance(handoff, dict):
                    continue

                prompt = str(handoff.get("prompt", "") or "").strip()
                target_override = str(handoff.get("agent", "") or "").strip()

                if target_override and target_override not in role_set:
                    raise ValueError(
                        "Invalid workflow config: "
                        f"workflow.stages[{stage_index}].handoffs[{handoff_index}].agent "
                        f"references unknown stage role '{target_override}'"
                    )

                # Empty prompts do not generate handoff edges at runtime.
                if not prompt:
                    continue

                target_role = target_override or primary_next_role
                if target_role:
                    edges[source_role].add(target_role)

        cycle = CommandLineInterface._find_workflow_cycle(edges)
        if cycle:
            cycle_path = " -> ".join(cycle)
            raise ValueError(
                f"Invalid workflow config: cycle detected in workflow graph: {cycle_path}"
            )

    @staticmethod
    def _find_workflow_cycle(edges: dict[str, set[str]]) -> list[str]:
        """Return a cycle path when the workflow graph contains a cycle."""
        unvisited = 0
        visiting = 1
        visited = 2

        state: dict[str, int] = {node: unvisited for node in edges}
        path_stack: list[str] = []

        def visit(node: str) -> list[str] | None:
            state[node] = visiting
            path_stack.append(node)

            for neighbor in edges.get(node, set()):
                neighbor_state = state.get(neighbor, unvisited)
                if neighbor_state == visiting:
                    start_index = path_stack.index(neighbor)
                    return path_stack[start_index:] + [neighbor]
                if neighbor_state == unvisited:
                    cycle = visit(neighbor)
                    if cycle is not None:
                        return cycle

            path_stack.pop()
            state[node] = visited
            return None

        for node in edges:
            if state[node] == unvisited:
                cycle = visit(node)
                if cycle is not None:
                    return cycle
        return []

    @staticmethod
    def _read_workflow_mode(install_dir: Path | None) -> str:
        """Read ``workflow.mode`` from ``.vstack/config.yaml`` when available.

        Supported values are ``manual``, ``agentic``, and ``hybrid``.
        Returns ``agentic`` when missing, invalid, or unavailable.
        """
        if install_dir is None:
            return "agentic"
        config_path = install_dir.parent / ".vstack" / "config.yaml"
        if not config_path.exists():
            return "agentic"
        parsed = FrontmatterParser.parse_yaml(config_path.read_text(encoding="utf-8"))
        workflow = parsed.get("workflow", "")
        if not isinstance(workflow, dict):
            return "agentic"
        raw_mode = workflow.get("mode", "agentic")
        if not isinstance(raw_mode, str):
            return "agentic"
        mode = raw_mode.strip().lower()
        if mode in {"manual", "agentic", "hybrid"}:
            return mode
        return "agentic"

    @staticmethod
    def _read_hook_settings(
        install_dir: Path | None,
    ) -> tuple[
        bool,
        str,
        str,
        int,
        str,
        list[str],
        dict[str, str],
        dict[str, str],
        dict[str, str],
        dict[str, int],
    ]:
        """Read project-level hook enablement, mode, and log-level settings."""
        allowed_modes = {"audit", "enforce"}
        allowed_log_levels = {"off", "minimal", "verbose"}
        if install_dir is None:
            return True, "audit", "minimal", 7, ".vstack/logs", [], {}, {}, {}, {}
        config_path = install_dir.parent / ".vstack" / "config.yaml"
        if not config_path.exists():
            return True, "audit", "minimal", 7, ".vstack/logs", [], {}, {}, {}, {}

        parsed = FrontmatterParser.parse_yaml(config_path.read_text(encoding="utf-8"))
        hooks_config = parsed.get("hooks", "")
        if not isinstance(hooks_config, dict):
            return True, "audit", "minimal", 7, ".vstack/logs", [], {}, {}, {}, {}

        enabled = hooks_config.get("enabled", True)
        global_enabled = enabled if isinstance(enabled, bool) else True

        mode_value = hooks_config.get("mode", "audit")
        default_mode = (
            mode_value if isinstance(mode_value, str) and mode_value in allowed_modes else "audit"
        )

        log_level_value = hooks_config.get("log_level", "minimal")
        default_log_level = (
            log_level_value
            if isinstance(log_level_value, str) and log_level_value in allowed_log_levels
            else "minimal"
        )

        retention_value = hooks_config.get("log_retention_days", 7)
        if isinstance(retention_value, int) and retention_value >= 0:
            default_retention_days = retention_value
        else:
            default_retention_days = 7

        log_dir_value = hooks_config.get("log_dir", ".vstack/logs")
        if isinstance(log_dir_value, str) and log_dir_value.strip():
            default_log_dir = log_dir_value.strip()
        else:
            default_log_dir = ".vstack/logs"

        disabled_names: list[str] = []
        mode_overrides: dict[str, str] = {}
        log_level_overrides: dict[str, str] = {}
        log_name_overrides: dict[str, str] = {}
        log_retention_days_overrides: dict[str, int] = {}
        per_hook = hooks_config.get("hooks", "")
        if isinstance(per_hook, dict):
            for hook_name, hook_config in per_hook.items():
                if not isinstance(hook_name, str) or not isinstance(hook_config, dict):
                    continue
                if hook_config.get("enabled") is False:
                    disabled_names.append(hook_name)
                    continue

                nested_log = hook_config.get("log", "")
                nested_log_config = nested_log if isinstance(nested_log, dict) else {}

                hook_mode = hook_config.get("mode", "")
                if isinstance(hook_mode, str) and hook_mode in allowed_modes:
                    mode_overrides[hook_name] = hook_mode

                hook_log_level = nested_log_config.get("level", "")
                if isinstance(hook_log_level, str) and hook_log_level in allowed_log_levels:
                    log_level_overrides[hook_name] = hook_log_level

                hook_log_name = nested_log_config.get("name", "")
                if isinstance(hook_log_name, str):
                    normalized_log_name = hook_log_name.strip()
                    if CommandLineInterface._is_valid_hook_log_name(normalized_log_name):
                        log_name_overrides[hook_name] = normalized_log_name

                hook_retention_days = nested_log_config.get("retention_days", None)
                if isinstance(hook_retention_days, int) and hook_retention_days >= 0:
                    log_retention_days_overrides[hook_name] = hook_retention_days

        return (
            global_enabled,
            default_mode,
            default_log_level,
            default_retention_days,
            default_log_dir,
            disabled_names,
            mode_overrides,
            log_level_overrides,
            log_name_overrides,
            log_retention_days_overrides,
        )

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

        if isinstance(raw, (dict, list)):
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

    def _build_command_registry(self, service: CommandService) -> dict[str, BaseCommand]:
        """Instantiate all catalog commands against *service*."""
        return {
            command_name: config.command_factory(service)
            for command_name, config in COMMAND_CATALOG.items()
        }

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
        items_root = self._read_items_root(resolved_install_dir)
        workflow_stages = self._read_workflow_stages(resolved_install_dir)
        workflow_mode = self._read_workflow_mode(resolved_install_dir)
        (
            hooks_enabled,
            hook_default_mode,
            hook_default_log_level,
            hook_log_retention_days,
            hook_log_dir,
            disabled_hook_names,
            hook_mode_overrides,
            hook_log_level_overrides,
            hook_log_name_overrides,
            hook_log_retention_days_overrides,
        ) = self._read_hook_settings(resolved_install_dir)
        service = cast(Any, self._service_cls)(
            templates_root=self._templates_root,
            items_root=items_root,
            workflow_stages=workflow_stages,
            workflow_mode=workflow_mode,
            hook_default_mode=hook_default_mode,
            hook_default_log_level=hook_default_log_level,
            hook_log_retention_days=hook_log_retention_days,
            hook_log_dir=hook_log_dir,
            hook_mode_overrides=hook_mode_overrides,
            hook_log_level_overrides=hook_log_level_overrides,
            hook_log_name_overrides=hook_log_name_overrides,
            hook_log_retention_days_overrides=hook_log_retention_days_overrides,
            disabled_hook_names=disabled_hook_names,
        )
        commands = self._build_command_registry(service)
        effective_only = self._resolve_only_filter(
            args=args,
            resolve_only_for_scope=command_config.resolve_only_for_scope,
        )
        excluded_types, excluded_names = self._read_exclude(resolved_install_dir)
        if not hooks_enabled:
            excluded_types = frozenset(set(excluded_types) | {"hook"})
        elif disabled_hook_names:
            merged = dict(excluded_names)
            merged.setdefault("hook", [])
            merged["hook"] = sorted(set(merged["hook"]) | set(disabled_hook_names))
            excluded_names = merged
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
