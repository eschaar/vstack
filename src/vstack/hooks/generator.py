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
    _ALLOWED_ACTION_TYPES = {"command"}

    def __init__(
        self,
        templates_root: Path | None = None,
        *,
        default_mode: str = "audit",
        mode_overrides: dict[str, str] | None = None,
        disabled_names: list[str] | None = None,
    ) -> None:
        """Create a hook generator bound to the built-in or provided template root."""
        super().__init__(HOOK_TYPE, templates_root or TEMPLATES_ROOT)
        self.default_mode = default_mode if default_mode in self._ALLOWED_MODES else "audit"
        self.mode_overrides = {
            name: mode
            for name, mode in (mode_overrides or {}).items()
            if mode in self._ALLOWED_MODES
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

    def _apply_mode_defaults(self, text: str, *, mode: str) -> str:
        """Replace audit fallbacks inside shell snippets with the configured mode."""
        return (
            text.replace("${VSTACK_HOOKS_MODE:-audit}", f"${{VSTACK_HOOKS_MODE:-{mode}}}")
            .replace("else { 'audit' }", f"else {{ '{mode}' }}")
            .replace('else { "audit" }', f'else {{ "{mode}" }}')
        )

    def _generate_json_from_yaml(self, yaml_data: dict) -> str:
        """Convert validated YAML data to the GitHub Copilot hooks envelope."""
        metadata = yaml_data.get("metadata", {})
        hook_name = str(metadata.get("name", ""))
        mode = self._mode_for_hook(hook_name)
        hooks_dict = yaml_data.get("hooks", {})

        rendered_hooks: dict[str, list[dict]] = {}
        for event, actions in hooks_dict.items():
            rendered_actions: list[dict] = []
            for action in actions:
                rendered_action = dict(action)
                for shell_name in ("bash", "powershell"):
                    command = rendered_action.get(shell_name)
                    if isinstance(command, str):
                        rendered_action[shell_name] = self._apply_mode_defaults(command, mode=mode)
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
