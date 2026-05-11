"""Hook generator with YAML source support and project-level hook settings."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from vstack.artifacts.generator import GenericArtifactGenerator
from vstack.artifacts.models import RenderedArtifact
from vstack.constants import TEMPLATES_ROOT
from vstack.hooks.config import HOOK_TYPE
from vstack.models import CheckMessage, ValidationResult


class HookGenerator(GenericArtifactGenerator):
    """Generate hook artifacts using YAML templates and project hook settings."""

    _ALLOWED_EVENTS = {
        "sessionStart",
        "sessionEnd",
        "userPromptSubmitted",
        "preToolUse",
        "postToolUse",
        "errorOccurred",
    }
    _ALLOWED_PURPOSES = {"audit", "security", "quality"}
    _ALLOWED_SECURITY_LEVELS = {"low", "high"}
    _ALLOWED_MODES = {"audit", "enforce"}
    _ALLOWED_LOG_LEVELS = {"off", "minimal", "verbose"}
    _ALLOWED_ACTION_TYPES = {"command"}

    def __init__(
        self,
        templates_root: Path | None = None,
        *,
        default_mode: str = "audit",
        default_log_level: str = "minimal",
        default_log_retention_days: int = 7,
        default_log_dir: str = ".vstack/logs",
        mode_overrides: dict[str, str] | None = None,
        log_level_overrides: dict[str, str] | None = None,
        log_name_overrides: dict[str, str] | None = None,
        log_retention_days_overrides: dict[str, int] | None = None,
        disabled_names: list[str] | None = None,
    ) -> None:
        """Create a hook generator bound to the built-in or provided template root."""
        super().__init__(HOOK_TYPE, templates_root or TEMPLATES_ROOT)
        self.default_mode = default_mode if default_mode in self._ALLOWED_MODES else "audit"
        self.default_log_level = (
            default_log_level if default_log_level in self._ALLOWED_LOG_LEVELS else "minimal"
        )
        self.default_log_retention_days = (
            default_log_retention_days if default_log_retention_days >= 0 else 7
        )
        self.default_log_dir = (
            default_log_dir.strip() if default_log_dir.strip() else ".vstack/logs"
        )
        self.mode_overrides = {
            name: mode
            for name, mode in (mode_overrides or {}).items()
            if mode in self._ALLOWED_MODES
        }
        self.log_level_overrides = {
            name: level
            for name, level in (log_level_overrides or {}).items()
            if level in self._ALLOWED_LOG_LEVELS
        }
        self.log_name_overrides = {
            name: log_name
            for name, log_name in (log_name_overrides or {}).items()
            if isinstance(log_name, str) and log_name
        }
        self.log_retention_days_overrides = {
            name: days
            for name, days in (log_retention_days_overrides or {}).items()
            if isinstance(days, int) and days >= 0
        }
        self.disabled_names = set(disabled_names or [])

    def find_templates(self) -> list[Path]:
        """Return hook templates, excluding hooks disabled by project config."""
        return [tmpl for tmpl in super().find_templates() if tmpl.name not in self.disabled_names]

    def _load_yaml_template(self, yaml_path: Path) -> dict:
        """Load and parse a YAML hook template file."""
        try:
            content = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ValueError(f"YAML parsing error: {exc}") from exc
        if not isinstance(content, dict):
            raise ValueError("YAML must contain a top-level object")
        return content

    def _mode_for_hook(self, hook_name: str) -> str:
        """Resolve the configured default mode for one hook."""
        return self.mode_overrides.get(hook_name, self.default_mode)

    def _log_level_for_hook(self, hook_name: str) -> str:
        """Resolve the configured default log level for one hook."""
        return self.log_level_overrides.get(hook_name, self.default_log_level)

    def _retention_days_for_hook(self, hook_name: str) -> int:
        """Resolve the configured retention days for one hook."""
        return self.log_retention_days_overrides.get(hook_name, self.default_log_retention_days)

    def _log_name_for_hook(self, hook_name: str) -> str | None:
        """Resolve the configured log filename override for one hook."""
        return self.log_name_overrides.get(hook_name)

    def _apply_runtime_defaults(
        self,
        text: str,
        *,
        mode: str,
        log_level: str,
        retention_days: int,
        log_dir: str,
        log_name: str | None,
        default_log_name: str | None,
    ) -> str:
        """Inject configured mode and log level fallbacks into shell snippets."""
        rendered = (
            text.replace("${VSTACK_HOOKS_MODE:-audit}", f"${{VSTACK_HOOKS_MODE:-{mode}}}")
            .replace(
                "${VSTACK_HOOKS_LOG_LEVEL:-minimal}",
                f"${{VSTACK_HOOKS_LOG_LEVEL:-{log_level}}}",
            )
            .replace(
                "${VSTACK_HOOKS_LOG_RETENTION_DAYS:-7}",
                f"${{VSTACK_HOOKS_LOG_RETENTION_DAYS:-{retention_days}}}",
            )
            .replace(
                "${VSTACK_HOOK_LOG_DIR:-.vstack/logs}",
                f"${{VSTACK_HOOK_LOG_DIR:-{log_dir}}}",
            )
            .replace("else { 'audit' }", f"else {{ '{mode}' }}")
            .replace("else { 'minimal' }", f"else {{ '{log_level}' }}")
            .replace("else { '7' }", f"else {{ '{retention_days}' }}")
            .replace("else { '.vstack/logs' }", f"else {{ '{log_dir}' }}")
            .replace('else { "audit" }', f'else {{ "{mode}" }}')
            .replace('else { "minimal" }', f'else {{ "{log_level}" }}')
            .replace('else { "7" }', f'else {{ "{retention_days}" }}')
            .replace('else { ".vstack/logs" }', f'else {{ "{log_dir}" }}')
        )
        if (
            isinstance(log_name, str)
            and log_name
            and isinstance(default_log_name, str)
            and default_log_name
        ):
            rendered = (
                rendered.replace(
                    f"${{VSTACK_HOOK_LOG_NAME:-{default_log_name}}}",
                    f"${{VSTACK_HOOK_LOG_NAME:-{log_name}}}",
                )
                .replace(
                    f"else {{ '{default_log_name}' }}",
                    f"else {{ '{log_name}' }}",
                )
                .replace(
                    f'else {{ "{default_log_name}" }}',
                    f'else {{ "{log_name}" }}',
                )
            )
        return rendered

    def _generate_json_from_yaml(self, yaml_data: dict) -> str:
        """Convert validated YAML data to the GitHub Copilot hooks envelope."""
        metadata = yaml_data.get("metadata", {})
        hook_name = str(metadata.get("name", ""))
        mode = self._mode_for_hook(hook_name)
        log_level = self._log_level_for_hook(hook_name)
        retention_days = self._retention_days_for_hook(hook_name)
        log_name = self._log_name_for_hook(hook_name)
        log_metadata = metadata.get("log", "")
        default_log_name = ""
        if isinstance(log_metadata, dict):
            default_log_name = str(log_metadata.get("name", ""))
        hooks_dict = yaml_data.get("hooks", {})

        rendered_hooks: dict[str, list[dict]] = {}
        for event, actions in hooks_dict.items():
            rendered_actions: list[dict] = []
            for action in actions:
                rendered_action = dict(action)
                for shell_name in ("bash", "powershell"):
                    command = rendered_action.get(shell_name)
                    if isinstance(command, str):
                        rendered_action[shell_name] = self._apply_runtime_defaults(
                            command,
                            mode=mode,
                            log_level=log_level,
                            retention_days=retention_days,
                            log_dir=self.default_log_dir,
                            log_name=log_name,
                            default_log_name=str(default_log_name),
                        )
                rendered_actions.append(rendered_action)
            rendered_hooks[event] = rendered_actions

        return json.dumps({"version": 1, "hooks": rendered_hooks}, indent=2)

    def find_extra_files(self, tmpl_dir: Path) -> list[Path]:
        """Hook templates use a single YAML file and do not copy sidecar files."""
        return []

    def render(self, tmpl_dir: Path) -> RenderedArtifact:
        """Render one YAML hook template to a JSON hook artifact."""
        tmpl_file = tmpl_dir / self.config.template_filename
        yaml_data = self._load_yaml_template(tmpl_file)
        metadata = yaml_data.get("metadata", {})
        name = str(metadata.get("name", tmpl_dir.name))
        json_content = self._generate_json_from_yaml(yaml_data)
        return RenderedArtifact(
            name=name,
            content=json_content,
            source_path=tmpl_file,
            frontmatter=None,
            unresolved=[],
        )

    def verify_input(self, expected_names: list[str] | None = None) -> ValidationResult:
        """Verify hook templates and enforce the hook YAML schema constraints."""
        result = super().verify_input(expected_names)

        for tmpl_dir in self.find_templates():
            hook_path = tmpl_dir / self.config.template_filename
            rel_path = f"templates/{self.config.templates_dir}/{tmpl_dir.name}/{hook_path.name}"

            try:
                payload = yaml.safe_load(hook_path.read_text(encoding="utf-8"))
            except yaml.YAMLError as exc:
                result.messages.append(CheckMessage("fail", f"{rel_path} invalid YAML ({exc})"))
                continue

            if not isinstance(payload, dict):
                result.messages.append(
                    CheckMessage("fail", f"{rel_path} must contain a top-level YAML object")
                )
                continue

            version = payload.get("version")
            if isinstance(version, int) and version > 0:
                result.messages.append(CheckMessage("pass", f"{rel_path} has supported version"))
            else:
                result.messages.append(
                    CheckMessage("fail", f"{rel_path} must set a positive integer 'version'")
                )

            metadata = payload.get("metadata")
            if not isinstance(metadata, dict):
                result.messages.append(
                    CheckMessage("fail", f"{rel_path} must define 'metadata' section as object")
                )
                continue

            if not isinstance(metadata.get("name"), str):
                result.messages.append(
                    CheckMessage("fail", f"{rel_path} metadata.name must be string")
                )
            if not isinstance(metadata.get("description"), str):
                result.messages.append(
                    CheckMessage("fail", f"{rel_path} metadata.description must be string")
                )

            purpose = metadata.get("purpose")
            if purpose not in self._ALLOWED_PURPOSES:
                result.messages.append(
                    CheckMessage(
                        "fail",
                        f"{rel_path} metadata.purpose must be one of: {', '.join(sorted(self._ALLOWED_PURPOSES))}",
                    )
                )

            security_level = metadata.get("security_level")
            if security_level not in self._ALLOWED_SECURITY_LEVELS:
                result.messages.append(
                    CheckMessage(
                        "fail",
                        f"{rel_path} metadata.security_level must be one of: {', '.join(sorted(self._ALLOWED_SECURITY_LEVELS))}",
                    )
                )

            mode_default = metadata.get("mode_default")
            if mode_default not in self._ALLOWED_MODES:
                result.messages.append(
                    CheckMessage(
                        "fail",
                        f"{rel_path} metadata.mode_default must be one of: {', '.join(sorted(self._ALLOWED_MODES))}",
                    )
                )

            hooks = payload.get("hooks")
            if not isinstance(hooks, dict) or not hooks:
                result.messages.append(
                    CheckMessage("fail", f"{rel_path} must define a non-empty 'hooks' object")
                )
                continue

            unknown_events = [event for event in hooks if event not in self._ALLOWED_EVENTS]
            if unknown_events:
                quoted = ", ".join(sorted(unknown_events))
                result.messages.append(
                    CheckMessage("fail", f"{rel_path} contains unsupported hook events: {quoted}")
                )

            for event, actions in hooks.items():
                if not isinstance(actions, list) or not actions:
                    result.messages.append(
                        CheckMessage("fail", f"{rel_path} event '{event}' must be a non-empty list")
                    )
                    continue

                for idx, action in enumerate(actions):
                    action_label = f"{rel_path} event '{event}' action[{idx}]"
                    if not isinstance(action, dict):
                        result.messages.append(
                            CheckMessage("fail", f"{action_label} must be an object")
                        )
                        continue

                    if action.get("type") not in self._ALLOWED_ACTION_TYPES:
                        result.messages.append(
                            CheckMessage(
                                "fail",
                                f"{action_label} type must be one of: {', '.join(sorted(self._ALLOWED_ACTION_TYPES))}",
                            )
                        )
                        continue

                    has_shell_cmd = isinstance(action.get("bash"), str) or isinstance(
                        action.get("powershell"), str
                    )
                    if not has_shell_cmd:
                        result.messages.append(
                            CheckMessage(
                                "fail",
                                f"{action_label} must define 'bash' and/or 'powershell' as string",
                            )
                        )

        return result
