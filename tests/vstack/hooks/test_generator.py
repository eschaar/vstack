"""Tests for hook generator behavior."""

from __future__ import annotations

import json
from pathlib import Path

from vstack.hooks.generator import HookGenerator


class _ExposedHookGenerator(HookGenerator):
    """Test helper exposing selected internals through public wrappers."""

    def load_yaml_template_public(self, yaml_path: Path) -> dict:
        """Expose YAML loading for focused failure-path tests."""
        return self._load_yaml_template(yaml_path)


class TestHookGenerator:
    """Test cases for HookGenerator."""

    def test_generator_uses_hook_type(self) -> None:
        """Test that generator uses hook type."""
        gen = HookGenerator()
        assert gen.config.type_name == "hook"

    def test_verify_input_accepts_current_hook_templates(self) -> None:
        """Built-in hook templates satisfy hook YAML structure checks."""
        gen = HookGenerator()
        result = gen.verify_input()
        assert result.failures == 0

    def test_verify_input_reports_invalid_yaml(self, tmp_path: Path) -> None:
        """Invalid YAML hook files are reported as source verification failures."""
        tmpl_dir = tmp_path / "hooks" / "broken"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "hook.yaml").write_text(
            "version: 20260510001\ninvalid: [yaml: structure:\n", encoding="utf-8"
        )

        gen = HookGenerator()
        gen.templates_dir = tmp_path / "hooks"
        result = gen.verify_input()

        assert result.failures == 1
        assert any("invalid YAML" in msg.message for msg in result.messages)

    def test_verify_input_requires_version_and_hooks_wrapper(self, tmp_path: Path) -> None:
        """Hook templates must use the official version/hooks wrapper structure."""
        tmpl_dir = tmp_path / "hooks" / "legacy"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "hook.yaml").write_text(
            "preToolUse:\n  - type: command\n    bash: 'echo hi'\n",
            encoding="utf-8",
        )

        gen = HookGenerator()
        gen.templates_dir = tmp_path / "hooks"
        result = gen.verify_input()

        assert result.failures == 2
        assert any("version" in msg.message.lower() for msg in result.messages)
        assert any("hooks" in msg.message.lower() for msg in result.messages)

    def test_verify_input_rejects_non_dict_top_level(self, tmp_path: Path) -> None:
        """Hook YAML must be a top-level object, not an array or primitive."""
        tmpl_dir = tmp_path / "hooks" / "array-hook"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "hook.yaml").write_text("- item1\n- item2\n", encoding="utf-8")

        gen = HookGenerator()
        gen.templates_dir = tmp_path / "hooks"
        result = gen.verify_input()

        assert result.failures == 1
        assert any("must contain a top-level YAML object" in msg.message for msg in result.messages)

    def test_verify_input_rejects_unsupported_hook_events(self, tmp_path: Path) -> None:
        """Hook templates cannot use unsupported event names."""
        tmpl_dir = tmp_path / "hooks" / "bad-events"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "hook.yaml").write_text(
            "version: 20260510003\nmetadata:\n  name: bad-events\n"
            "  description: 'test'\n  purpose: audit\n  security_level: low\n"
            "  mode_default: audit\n  execution_context: copilot-hook-runtime\n"
            "  dependencies:\n    required: []\n    optional: []\n"
            "hooks:\n  unknownEvent:\n    - type: command\n      bash: 'echo hi'\n",
            encoding="utf-8",
        )

        gen = HookGenerator()
        gen.templates_dir = tmp_path / "hooks"
        result = gen.verify_input()

        assert result.failures == 1
        assert any("unsupported hook events:" in msg.message for msg in result.messages)

    def test_verify_input_rejects_empty_actions_list(self, tmp_path: Path) -> None:
        """Hook events must have at least one action."""
        tmpl_dir = tmp_path / "hooks" / "empty-actions"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "hook.yaml").write_text(
            "version: 20260510003\nmetadata:\n  name: empty-actions\n"
            "  description: 'test'\n  purpose: audit\n  security_level: low\n"
            "  mode_default: audit\n  execution_context: copilot-hook-runtime\n"
            "  dependencies:\n    required: []\n    optional: []\n"
            "hooks:\n  preToolUse: []\n",
            encoding="utf-8",
        )

        gen = HookGenerator()
        gen.templates_dir = tmp_path / "hooks"
        result = gen.verify_input()

        assert result.failures == 1
        assert any("must be a non-empty list" in msg.message for msg in result.messages)

    def test_verify_input_rejects_non_dict_action(self, tmp_path: Path) -> None:
        """Hook actions must be objects, not arrays or primitives."""
        tmpl_dir = tmp_path / "hooks" / "bad-action"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "hook.yaml").write_text(
            "version: 20260510003\nmetadata:\n  name: bad-action\n"
            "  description: 'test'\n  purpose: audit\n  security_level: low\n"
            "  mode_default: audit\n  execution_context: copilot-hook-runtime\n"
            "  dependencies:\n    required: []\n    optional: []\n"
            "hooks:\n  preToolUse:\n    - 'not an object'\n",
            encoding="utf-8",
        )

        gen = HookGenerator()
        gen.templates_dir = tmp_path / "hooks"
        result = gen.verify_input()

        assert result.failures == 1
        assert any("must be an object" in msg.message for msg in result.messages)

    def test_verify_input_rejects_wrong_action_type(self, tmp_path: Path) -> None:
        """Hook actions must set type='command'."""
        tmpl_dir = tmp_path / "hooks" / "wrong-type"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "hook.yaml").write_text(
            "version: 20260510003\nmetadata:\n  name: wrong-type\n"
            "  description: 'test'\n  purpose: audit\n  security_level: low\n"
            "  mode_default: audit\n  execution_context: copilot-hook-runtime\n"
            "  dependencies:\n    required: []\n    optional: []\n"
            "hooks:\n  preToolUse:\n    - type: webhook\n      bash: 'echo hi'\n",
            encoding="utf-8",
        )

        gen = HookGenerator()
        gen.templates_dir = tmp_path / "hooks"
        result = gen.verify_input()

        assert result.failures == 1
        assert any("type must be one of:" in msg.message for msg in result.messages)

    def test_verify_input_rejects_missing_shell_commands(self, tmp_path: Path) -> None:
        """Hook actions must have at least bash or powershell field."""
        tmpl_dir = tmp_path / "hooks" / "no-shell"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "hook.yaml").write_text(
            "version: 20260510003\nmetadata:\n  name: no-shell\n"
            "  description: 'test'\n  purpose: audit\n  security_level: low\n"
            "  mode_default: audit\n  execution_context: copilot-hook-runtime\n"
            "  dependencies:\n    required: []\n    optional: []\n"
            "hooks:\n  preToolUse:\n    - type: command\n      description: 'no shell command'\n",
            encoding="utf-8",
        )

        gen = HookGenerator()
        gen.templates_dir = tmp_path / "hooks"
        result = gen.verify_input()

        assert result.failures == 1
        assert any(
            "must define 'bash' and/or 'powershell'" in msg.message for msg in result.messages
        )

    def test_render_generates_valid_json_from_yaml(self, tmp_path: Path) -> None:
        """render() converts valid YAML templates to GitHub Copilot JSON."""
        tmpl_dir = tmp_path / "hooks" / "valid"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "hook.yaml").write_text(
            "version: 20260510003\nmetadata:\n  name: valid\n"
            "  description: 'test hook'\n  purpose: audit\n  security_level: low\n"
            "  mode_default: audit\n  execution_context: copilot-hook-runtime\n"
            "  dependencies:\n    required: []\n    optional: []\n"
            "hooks:\n  sessionStart:\n    - type: command\n      bash: 'echo start'\n",
            encoding="utf-8",
        )

        gen = HookGenerator()
        gen.templates_dir = tmp_path / "hooks"
        artifacts = gen.render_all()

        assert len(artifacts) == 1
        artifact = artifacts[0]
        assert artifact.name == "valid"

        content = json.loads(artifact.content)
        assert content["version"] == 1
        assert "hooks" in content
        assert "sessionStart" in content["hooks"]

    def test_render_uses_project_default_mode_for_shell_fallbacks(self, tmp_path: Path) -> None:
        """Configured project hook mode is injected into generated shell fallbacks."""
        tmpl_dir = tmp_path / "hooks" / "mode-test"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "hook.yaml").write_text(
            "version: 20260510003\nmetadata:\n  name: mode-test\n"
            "  description: 'test hook'\n  purpose: audit\n  security_level: low\n"
            "  mode_default: audit\n  execution_context: copilot-hook-runtime\n"
            "  dependencies:\n    required: []\n    optional: []\n"
            "hooks:\n  postToolUse:\n    - type: command\n"
            "      bash: 'mode=${VSTACK_HOOKS_MODE:-audit}'\n"
            "      powershell: '$mode = if ($env:VSTACK_HOOKS_MODE) { $env:VSTACK_HOOKS_MODE } else { ''audit'' }'\n",
            encoding="utf-8",
        )

        gen = HookGenerator(default_mode="enforce")
        gen.templates_dir = tmp_path / "hooks"
        artifact = gen.render_all()[0]

        content = json.loads(artifact.content)
        action = content["hooks"]["postToolUse"][0]
        assert "${VSTACK_HOOKS_MODE:-enforce}" in action["bash"]
        assert "else { 'enforce' }" in action["powershell"]

    def test_render_replaces_mode_fallback_even_with_nonstandard_template_default(
        self, tmp_path: Path
    ) -> None:
        """Mode replacement should not depend on one hard-coded source default value."""
        tmpl_dir = tmp_path / "hooks" / "mode-default-variant"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "hook.yaml").write_text(
            "version: 20260510003\nmetadata:\n  name: mode-default-variant\n"
            "  description: 'test hook'\n  purpose: audit\n  security_level: low\n"
            "  mode_default: audit\n  execution_context: copilot-hook-runtime\n"
            "  dependencies:\n    required: []\n    optional: []\n"
            "hooks:\n  postToolUse:\n    - type: command\n"
            "      bash: 'mode=${VSTACK_HOOKS_MODE:-legacy-default}'\n"
            "      powershell: '$mode = if ($env:VSTACK_HOOKS_MODE) { $env:VSTACK_HOOKS_MODE } else { ''legacy-default'' }'\n",
            encoding="utf-8",
        )

        gen = HookGenerator(default_mode="enforce")
        gen.templates_dir = tmp_path / "hooks"
        artifact = gen.render_all()[0]

        content = json.loads(artifact.content)
        action = content["hooks"]["postToolUse"][0]
        assert "${VSTACK_HOOKS_MODE:-enforce}" in action["bash"]
        assert "else { 'enforce' }" in action["powershell"]

    def test_render_uses_project_default_log_level_for_shell_fallbacks(
        self, tmp_path: Path
    ) -> None:
        """Configured project hook log level is injected into generated shell fallbacks."""
        tmpl_dir = tmp_path / "hooks" / "log-level-test"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "hook.yaml").write_text(
            "version: 20260510003\nmetadata:\n  name: log-level-test\n"
            "  description: 'test hook'\n  purpose: audit\n  security_level: low\n"
            "  mode_default: audit\n  execution_context: copilot-hook-runtime\n"
            "  dependencies:\n    required: []\n    optional: []\n"
            "hooks:\n  sessionStart:\n    - type: command\n"
            "      bash: 'level=${VSTACK_HOOKS_LOG_LEVEL:-minimal}'\n"
            "      powershell: '$level = if ($env:VSTACK_HOOKS_LOG_LEVEL) { $env:VSTACK_HOOKS_LOG_LEVEL } else { ''minimal'' }'\n",
            encoding="utf-8",
        )

        gen = HookGenerator(default_log_level="verbose")
        gen.templates_dir = tmp_path / "hooks"
        artifact = gen.render_all()[0]

        content = json.loads(artifact.content)
        action = content["hooks"]["sessionStart"][0]
        assert "${VSTACK_HOOKS_LOG_LEVEL:-verbose}" in action["bash"]
        assert "else { 'verbose' }" in action["powershell"]

    def test_render_uses_project_default_log_name_for_shell_targets(self, tmp_path: Path) -> None:
        """Configured project hook log name is injected into generated shell fallbacks."""
        tmpl_dir = tmp_path / "hooks" / "path-test"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "hook.yaml").write_text(
            "version: 20260510003\nmetadata:\n  name: path-test\n"
            "  description: 'test hook'\n  purpose: quality\n  security_level: low\n"
            "  log:\n    name: hook-quality-alerts.log\n"
            "  mode_default: audit\n  execution_context: copilot-hook-runtime\n"
            "  dependencies:\n    required: []\n    optional: []\n"
            "hooks:\n  postToolUse:\n    - type: command\n"
            "      bash: 'log_name=${VSTACK_HOOK_LOG_NAME:-hook-quality-alerts.log}'\n"
            "      powershell: '$name = if ($env:VSTACK_HOOK_LOG_NAME) { $env:VSTACK_HOOK_LOG_NAME } else { ''hook-quality-alerts.log'' }'\n",
            encoding="utf-8",
        )

        gen = HookGenerator(log_name_overrides={"path-test": "custom-quality.log"})
        gen.templates_dir = tmp_path / "hooks"
        artifact = gen.render_all()[0]

        content = json.loads(artifact.content)
        action = content["hooks"]["postToolUse"][0]
        assert "${VSTACK_HOOK_LOG_NAME:-custom-quality.log}" in action["bash"]
        assert "else { 'custom-quality.log' }" in action["powershell"]

    def test_render_sanitizes_log_name_override_to_basename(self, tmp_path: Path) -> None:
        """Configured log filename overrides should drop path traversal segments."""
        tmpl_dir = tmp_path / "hooks" / "sanitize-log-name"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "hook.yaml").write_text(
            "version: 20260510003\nmetadata:\n  name: sanitize-log-name\n"
            "  description: 'test hook'\n  purpose: quality\n  security_level: low\n"
            "  log:\n    name: hook-quality-alerts.log\n"
            "  mode_default: audit\n  execution_context: copilot-hook-runtime\n"
            "  dependencies:\n    required: []\n    optional: []\n"
            "hooks:\n  postToolUse:\n    - type: command\n"
            "      bash: 'log_name=${VSTACK_HOOK_LOG_NAME:-hook-quality-alerts.log}'\n"
            "      powershell: '$name = if ($env:VSTACK_HOOK_LOG_NAME) { $env:VSTACK_HOOK_LOG_NAME } else { ''hook-quality-alerts.log'' }'\n",
            encoding="utf-8",
        )

        gen = HookGenerator(log_name_overrides={"sanitize-log-name": "../unsafe.log"})
        gen.templates_dir = tmp_path / "hooks"
        artifact = gen.render_all()[0]

        content = json.loads(artifact.content)
        action = content["hooks"]["postToolUse"][0]
        assert "${VSTACK_HOOK_LOG_NAME:-unsafe.log}" in action["bash"]
        assert "else { 'unsafe.log' }" in action["powershell"]

    def test_render_ignores_invalid_log_name_override(self, tmp_path: Path) -> None:
        """Invalid basename results should be ignored and keep template defaults."""
        tmpl_dir = tmp_path / "hooks" / "ignore-invalid-log-name"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "hook.yaml").write_text(
            "version: 20260510003\nmetadata:\n  name: ignore-invalid-log-name\n"
            "  description: 'test hook'\n  purpose: quality\n  security_level: low\n"
            "  log:\n    name: hook-quality-alerts.log\n"
            "  mode_default: audit\n  execution_context: copilot-hook-runtime\n"
            "  dependencies:\n    required: []\n    optional: []\n"
            "hooks:\n  postToolUse:\n    - type: command\n"
            "      bash: 'log_name=${VSTACK_HOOK_LOG_NAME:-hook-quality-alerts.log}'\n"
            "      powershell: '$name = if ($env:VSTACK_HOOK_LOG_NAME) { $env:VSTACK_HOOK_LOG_NAME } else { ''hook-quality-alerts.log'' }'\n",
            encoding="utf-8",
        )

        gen = HookGenerator(log_name_overrides={"ignore-invalid-log-name": "../"})
        gen.templates_dir = tmp_path / "hooks"
        artifact = gen.render_all()[0]

        content = json.loads(artifact.content)
        action = content["hooks"]["postToolUse"][0]
        assert "${VSTACK_HOOK_LOG_NAME:-hook-quality-alerts.log}" in action["bash"]
        assert "else { 'hook-quality-alerts.log' }" in action["powershell"]

    def test_render_uses_per_hook_retention_days_override(self, tmp_path: Path) -> None:
        """Per-hook retention_days overrides are applied to shell fallbacks."""
        tmpl_dir = tmp_path / "hooks" / "retention-test"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "hook.yaml").write_text(
            "version: 20260510003\nmetadata:\n  name: retention-test\n"
            "  description: 'test hook'\n  purpose: security\n  security_level: high\n"
            "  mode_default: audit\n  execution_context: copilot-hook-runtime\n"
            "  dependencies:\n    required: []\n    optional: []\n"
            "hooks:\n  postToolUse:\n    - type: command\n"
            "      bash: 'retention_days=\"${VSTACK_HOOKS_LOG_RETENTION_DAYS:-7}\"'\n"
            "      powershell: '$retention = if ($env:VSTACK_HOOKS_LOG_RETENTION_DAYS) { $env:VSTACK_HOOKS_LOG_RETENTION_DAYS } else { \"7\" }'\n",
            encoding="utf-8",
        )

        gen = HookGenerator(
            default_log_retention_days=7,
            log_retention_days_overrides={"retention-test": 30},
        )
        gen.templates_dir = tmp_path / "hooks"
        artifact = gen.render_all()[0]

        content = json.loads(artifact.content)
        action = content["hooks"]["postToolUse"][0]
        # Verify retention_days override was applied to bash fallback
        assert "${VSTACK_HOOKS_LOG_RETENTION_DAYS:-30}" in action["bash"]
        # Verify retention_days override was applied to powershell fallback
        assert "else { '30' }" in action["powershell"]

    def test_render_uses_project_default_log_dir_for_shell_fallbacks(self, tmp_path: Path) -> None:
        """Configured project hook log directory is injected into shell fallbacks."""
        tmpl_dir = tmp_path / "hooks" / "log-dir-test"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "hook.yaml").write_text(
            "version: 20260510003\nmetadata:\n  name: log-dir-test\n"
            "  description: 'test hook'\n  purpose: quality\n  security_level: low\n"
            "  log:\n    name: log-dir-test.log\n"
            "  mode_default: audit\n  execution_context: copilot-hook-runtime\n"
            "  dependencies:\n    required: []\n    optional: []\n"
            "hooks:\n  postToolUse:\n    - type: command\n"
            "      bash: 'log_root=${VSTACK_HOOK_LOG_DIR:-.vstack/logs}'\n"
            "      powershell: '$root = if ($env:VSTACK_HOOK_LOG_DIR) { $env:VSTACK_HOOK_LOG_DIR } else { ''.vstack/logs'' }'\n",
            encoding="utf-8",
        )

        gen = HookGenerator(default_log_dir=".vstack/custom-logs")
        gen.templates_dir = tmp_path / "hooks"
        artifact = gen.render_all()[0]

        content = json.loads(artifact.content)
        action = content["hooks"]["postToolUse"][0]
        assert "${VSTACK_HOOK_LOG_DIR:-.vstack/custom-logs}" in action["bash"]
        assert "else { '.vstack/custom-logs' }" in action["powershell"]

    def test_find_templates_skips_disabled_hook_names(self, tmp_path: Path) -> None:
        """Disabled hook names are excluded from rendering and validation."""
        enabled_dir = tmp_path / "hooks" / "enabled-hook"
        enabled_dir.mkdir(parents=True)
        (enabled_dir / "hook.yaml").write_text(
            "version: 20260510003\nmetadata:\n  name: enabled-hook\n"
            "  description: 'test hook'\n  purpose: audit\n  security_level: low\n"
            "  mode_default: audit\n  execution_context: copilot-hook-runtime\n"
            "  dependencies:\n    required: []\n    optional: []\n"
            "hooks:\n  sessionStart:\n    - type: command\n      bash: 'echo hi'\n",
            encoding="utf-8",
        )
        disabled_dir = tmp_path / "hooks" / "disabled-hook"
        disabled_dir.mkdir(parents=True)
        (disabled_dir / "hook.yaml").write_text(
            "version: 20260510003\nmetadata:\n  name: disabled-hook\n"
            "  description: 'test hook'\n  purpose: audit\n  security_level: low\n"
            "  mode_default: audit\n  execution_context: copilot-hook-runtime\n"
            "  dependencies:\n    required: []\n    optional: []\n"
            "hooks:\n  sessionStart:\n    - type: command\n      bash: 'echo hi'\n",
            encoding="utf-8",
        )

        gen = HookGenerator(disabled_names=["disabled-hook"])
        gen.templates_dir = tmp_path / "hooks"

        assert [template.name for template in gen.find_templates()] == ["enabled-hook"]

    def test_load_yaml_template_rejects_invalid_yaml(self, tmp_path: Path) -> None:
        """_load_yaml_template raises ValueError for invalid YAML source."""
        hook_path = tmp_path / "hook.yaml"
        hook_path.write_text("invalid: [yaml\n", encoding="utf-8")

        gen = _ExposedHookGenerator()

        try:
            gen.load_yaml_template_public(hook_path)
        except ValueError as exc:
            assert "YAML parsing error" in str(exc)
        else:
            raise AssertionError("Expected ValueError for invalid YAML")

    def test_load_yaml_template_rejects_non_object_yaml(self, tmp_path: Path) -> None:
        """_load_yaml_template raises ValueError for non-object YAML."""
        hook_path = tmp_path / "hook.yaml"
        hook_path.write_text("- item\n", encoding="utf-8")

        gen = _ExposedHookGenerator()

        try:
            gen.load_yaml_template_public(hook_path)
        except ValueError as exc:
            assert "top-level object" in str(exc)
        else:
            raise AssertionError("Expected ValueError for non-object YAML")

    def test_find_extra_files_returns_empty_list(self, tmp_path: Path) -> None:
        """Hook templates do not copy sidecar files during generation."""
        gen = HookGenerator()
        assert gen.find_extra_files(tmp_path) == []

    def test_verify_input_rejects_missing_metadata_fields(self, tmp_path: Path) -> None:
        """verify_input reports invalid hook metadata fields individually."""
        tmpl_dir = tmp_path / "hooks" / "bad-metadata"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "hook.yaml").write_text(
            "version: 20260510003\nmetadata:\n  name: 1\n  description: 2\n"
            "  purpose: unknown\n  security_level: medium\n  mode_default: strict\n"
            "hooks:\n  sessionStart:\n    - type: command\n      bash: 'echo hi'\n",
            encoding="utf-8",
        )

        gen = HookGenerator()
        gen.templates_dir = tmp_path / "hooks"
        result = gen.verify_input()

        assert result.failures == 5
        assert any("metadata.name" in msg.message for msg in result.messages)
        assert any("metadata.description" in msg.message for msg in result.messages)
        assert any("metadata.purpose" in msg.message for msg in result.messages)
        assert any("metadata.security_level" in msg.message for msg in result.messages)
        assert any("metadata.mode_default" in msg.message for msg in result.messages)

    def test_verify_input_requires_positive_integer_version_and_hooks_object(
        self, tmp_path: Path
    ) -> None:
        """verify_input rejects invalid version values and missing hooks."""
        tmpl_dir = tmp_path / "hooks" / "missing-hooks"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "hook.yaml").write_text(
            "version: broken\nmetadata:\n  name: missing-hooks\n"
            "  description: 'test'\n  purpose: audit\n  security_level: low\n"
            "  mode_default: audit\n  execution_context: copilot-hook-runtime\n"
            "  dependencies:\n    required: []\n    optional: []\n",
            encoding="utf-8",
        )

        gen = HookGenerator()
        gen.templates_dir = tmp_path / "hooks"
        result = gen.verify_input()

        assert result.failures == 2
        assert any("positive integer 'version'" in msg.message for msg in result.messages)
        assert any("non-empty 'hooks' object" in msg.message for msg in result.messages)
