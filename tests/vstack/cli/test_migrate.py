"""Tests for MigrateCommand."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Any, cast
from unittest.mock import MagicMock, patch

import pytest
import yaml

from vstack.cli.base import CommandContext
from vstack.cli.constants import Colors
from vstack.cli.migrate import MigrateCommand
from vstack.cli.service import CommandService
from vstack.constants import ARTIFACTS_DOCS_ROOT


def _service() -> CommandService:
    return cast(CommandService, MagicMock(spec=CommandService))


def _context(args: Namespace) -> CommandContext:
    return CommandContext(args=args, install_dir=None, only=None)


class TestResolveProjectRoot:
    """_resolve_project_root returns cwd or explicit --target."""

    def test_returns_cwd_when_no_target(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Uses cwd when --target is absent."""
        monkeypatch.chdir(tmp_path)
        args = Namespace(target=None)
        assert MigrateCommand._resolve_project_root(args) == tmp_path

    def test_returns_target_when_set(self, tmp_path: Path) -> None:
        """Uses the explicit --target path."""
        args = Namespace(target=str(tmp_path))
        assert MigrateCommand._resolve_project_root(args) == tmp_path

    def test_expands_user_in_target(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Expands ~ in --target."""
        monkeypatch.setenv("HOME", str(tmp_path))
        args = Namespace(target="~")
        assert MigrateCommand._resolve_project_root(args) == tmp_path


class TestDetectInstalledMajor:
    """_detect_installed_major reads vstack_version from the manifest."""

    def test_returns_major_from_manifest(self, tmp_path: Path) -> None:
        """Parses major version from a valid semver string in the manifest."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        manifest = {
            "manifest_version": 2,
            "hash_algorithm": "sha256",
            "vstack_version": "2.2.0",
            "installed_at": "2026-01-01T00:00:00+00:00",
            "artifacts": {},
        }
        (vstack_dir / "vstack.json").write_text(
            __import__("json").dumps(manifest), encoding="utf-8"
        )
        assert MigrateCommand._detect_installed_major(tmp_path) == 2

    def test_returns_none_when_manifest_absent(self, tmp_path: Path) -> None:
        """Returns None when no manifest file exists."""
        assert MigrateCommand._detect_installed_major(tmp_path) is None

    def test_returns_none_when_version_unparseable(self, tmp_path: Path) -> None:
        """Returns None when vstack_version cannot be split into a major int."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        manifest = {
            "manifest_version": 2,
            "hash_algorithm": "sha256",
            "vstack_version": "not-a-version",
            "installed_at": "2026-01-01T00:00:00+00:00",
            "artifacts": {},
        }
        (vstack_dir / "vstack.json").write_text(
            __import__("json").dumps(manifest), encoding="utf-8"
        )
        assert MigrateCommand._detect_installed_major(tmp_path) is None

    def test_returns_none_when_manifest_read_raises(self, tmp_path: Path) -> None:
        """Returns None when ManifestFile.read() raises an unexpected exception."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "vstack.json").write_text("{}", encoding="utf-8")
        with patch("vstack.cli.migrate.ManifestFile") as mock_cls:
            mock_cls.return_value.read.side_effect = RuntimeError("boom")
            assert MigrateCommand._detect_installed_major(tmp_path) is None

    def test_returns_none_when_manifest_read_returns_none(self, tmp_path: Path) -> None:
        """Returns None when ManifestFile.read() returns None (legacy schema)."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        # manifest_version=1 triggers needs_upgrade() → read() returns None
        manifest = {
            "manifest_version": 1,
            "hash_algorithm": "sha256",
            "vstack_version": "1.3.6",
            "installed_at": "2026-01-01T00:00:00+00:00",
            "artifacts": {},
        }
        (vstack_dir / "vstack.json").write_text(
            __import__("json").dumps(manifest), encoding="utf-8"
        )
        assert MigrateCommand._detect_installed_major(tmp_path) is None

    def test_returns_none_when_version_empty(self, tmp_path: Path) -> None:
        """Returns None when vstack_version is an empty string."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        manifest = {
            "manifest_version": 2,
            "hash_algorithm": "sha256",
            "vstack_version": "",
            "installed_at": "2026-01-01T00:00:00+00:00",
            "artifacts": {},
        }
        (vstack_dir / "vstack.json").write_text(
            __import__("json").dumps(manifest), encoding="utf-8"
        )
        assert MigrateCommand._detect_installed_major(tmp_path) is None


class TestLoadMigrationRecord:
    """_load_migration_record reads YAML files from the migrations directory."""

    def test_returns_none_when_file_absent(self, tmp_path: Path) -> None:
        """Returns None when no migration record exists for the given versions."""
        with patch("vstack.cli.migrate.MIGRATIONS_ROOT", tmp_path):
            assert MigrateCommand._load_migration_record(9, 10) is None

    def test_returns_moves_from_yaml(self, tmp_path: Path) -> None:
        """Returns the moves list from a valid YAML record."""
        record = {
            "from_version": "1.x",
            "to_version": "2.0",
            "moves": [
                {"old": "docs/a.md", "new": "docs/b.md", "type": "docs"},
            ],
        }
        (tmp_path / "v1_to_v2.yaml").write_text(yaml.dump(record), encoding="utf-8")
        with patch("vstack.cli.migrate.MIGRATIONS_ROOT", tmp_path):
            result = MigrateCommand._load_migration_record(1, 2)
        assert result == [{"old": "docs/a.md", "new": "docs/b.md", "type": "docs"}]

    def test_returns_empty_list_when_moves_absent(self, tmp_path: Path) -> None:
        """Returns an empty list when the YAML record has no moves key."""
        record = {"from_version": "1.x", "to_version": "2.0"}
        (tmp_path / "v1_to_v2.yaml").write_text(yaml.dump(record), encoding="utf-8")
        with patch("vstack.cli.migrate.MIGRATIONS_ROOT", tmp_path):
            result = MigrateCommand._load_migration_record(1, 2)
        assert result == []

    def test_filters_non_dict_moves(self, tmp_path: Path) -> None:
        """Filters out non-dict entries from the moves list."""
        record = {
            "from_version": "1.x",
            "to_version": "2.0",
            "moves": [
                {"old": "docs/a.md", "new": "docs/b.md", "type": "docs"},
                "not-a-dict",
                42,
            ],
        }
        (tmp_path / "v1_to_v2.yaml").write_text(yaml.dump(record), encoding="utf-8")
        with patch("vstack.cli.migrate.MIGRATIONS_ROOT", tmp_path):
            result = MigrateCommand._load_migration_record(1, 2)
        assert result == [{"old": "docs/a.md", "new": "docs/b.md", "type": "docs"}]

    def test_returns_none_when_moves_not_a_list(self, tmp_path: Path) -> None:
        """Returns None when moves is not a list."""
        record = {"from_version": "1.x", "to_version": "2.0", "moves": "bad"}
        (tmp_path / "v1_to_v2.yaml").write_text(yaml.dump(record), encoding="utf-8")
        with patch("vstack.cli.migrate.MIGRATIONS_ROOT", tmp_path):
            assert MigrateCommand._load_migration_record(1, 2) is None

    def test_returns_none_when_yaml_not_dict(self, tmp_path: Path) -> None:
        """Returns None when the YAML root is not a mapping."""
        (tmp_path / "v1_to_v2.yaml").write_text("- item1\n- item2\n", encoding="utf-8")
        with patch("vstack.cli.migrate.MIGRATIONS_ROOT", tmp_path):
            assert MigrateCommand._load_migration_record(1, 2) is None


class TestResolveNewPath:
    """_resolve_new_path substitutes the docs root when configured."""

    def test_returns_path_unchanged_when_root_matches_default(self) -> None:
        """Does not modify the path when the root equals the default."""
        result = MigrateCommand._resolve_new_path(
            "docs/architecture/overview.md", ARTIFACTS_DOCS_ROOT
        )
        assert result == "docs/architecture/overview.md"

    def test_substitutes_custom_root(self) -> None:
        """Replaces the default docs/ prefix with the configured root."""
        result = MigrateCommand._resolve_new_path("docs/architecture/overview.md", "content")
        assert result == "content/architecture/overview.md"

    def test_leaves_path_unchanged_when_prefix_does_not_match(self) -> None:
        """Does not modify paths whose first component is not the default root."""
        result = MigrateCommand._resolve_new_path("other/architecture/overview.md", "content")
        assert result == "other/architecture/overview.md"


class TestReadItemsRoot:
    """_read_items_root reads items.root from config.yaml."""

    def test_returns_default_when_config_absent(self, tmp_path: Path) -> None:
        """Returns the default docs root when no config.yaml exists."""
        assert MigrateCommand._read_items_root(tmp_path) == ARTIFACTS_DOCS_ROOT

    def test_returns_configured_root(self, tmp_path: Path) -> None:
        """Returns the custom root from config.yaml."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text("items:\n  root: content\n", encoding="utf-8")
        assert MigrateCommand._read_items_root(tmp_path) == "content"

    def test_returns_default_when_items_not_dict(self, tmp_path: Path) -> None:
        """Returns default when items key is not a mapping."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text("items: all\n", encoding="utf-8")
        assert MigrateCommand._read_items_root(tmp_path) == ARTIFACTS_DOCS_ROOT

    def test_returns_legacy_artifacts_root_when_items_missing(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Legacy artifacts.root remains accepted and emits a deprecation warning."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text("artifacts:\n  root: content\n", encoding="utf-8")
        MigrateCommand._legacy_items_root_warned = False
        assert MigrateCommand._read_items_root(tmp_path) == "content"
        captured = capsys.readouterr()
        assert "legacy 'artifacts.root'" in captured.err

    def test_returns_default_when_root_blank(self, tmp_path: Path) -> None:
        """Returns default when items.root is blank."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text("artifacts:\n  root: ''\n", encoding="utf-8")
        assert MigrateCommand._read_items_root(tmp_path) == ARTIFACTS_DOCS_ROOT


class _FakeColors(Colors):
    DIM = ""
    RESET = ""
    GREEN = ""
    YELLOW = ""
    BOLD = ""
    RED = ""
    CYAN = ""
    BLUE = ""


class TestUpgradeLegacyKeys:
    """Legacy key upgrades for items migration."""

    def test_upgrades_project_config_root_key(self, tmp_path: Path) -> None:
        """Adds items.root when only artifacts.root is configured."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        config_path = vstack_dir / "config.yaml"
        config_path.write_text("artifacts:\n  root: content\n", encoding="utf-8")

        changed = MigrateCommand._upgrade_project_items_root_key(
            project_root=tmp_path,
            dry_run=False,
        )

        assert changed == 1
        content = config_path.read_text(encoding="utf-8")
        assert "items:" in content
        assert "root: content" in content

    def test_project_config_upgrade_is_dry_run_only(self, tmp_path: Path) -> None:
        """Dry-run reports project config upgrade without writing the file."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        config_path = vstack_dir / "config.yaml"
        original = "artifacts:\n  root: content\n"
        config_path.write_text(original, encoding="utf-8")

        changed = MigrateCommand._upgrade_project_items_root_key(
            project_root=tmp_path,
            dry_run=True,
        )

        assert changed == 1
        assert config_path.read_text(encoding="utf-8") == original

    def test_project_config_upgrade_skips_when_items_root_already_set(self, tmp_path: Path) -> None:
        """Does not change config when items.root is already present."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        config_path = vstack_dir / "config.yaml"
        config_path.write_text("items:\n  root: docs\n", encoding="utf-8")

        changed = MigrateCommand._upgrade_project_items_root_key(
            project_root=tmp_path,
            dry_run=False,
        )

        assert changed == 0

    def test_project_config_upgrade_skips_when_artifacts_block_invalid(
        self, tmp_path: Path
    ) -> None:
        """Does not change config when artifacts is not a mapping."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text("artifacts: all\n", encoding="utf-8")

        changed = MigrateCommand._upgrade_project_items_root_key(
            project_root=tmp_path,
            dry_run=False,
        )

        assert changed == 0

    def test_project_config_upgrade_skips_when_artifacts_root_blank(self, tmp_path: Path) -> None:
        """Does not change config when legacy artifacts.root is blank."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text("artifacts:\n  root: ''\n", encoding="utf-8")

        changed = MigrateCommand._upgrade_project_items_root_key(
            project_root=tmp_path,
            dry_run=False,
        )

        assert changed == 0

    def test_upgrades_agent_template_defaults_key(self, tmp_path: Path) -> None:
        """Adds defaults.items from legacy defaults.artifacts in local templates."""
        config_path = tmp_path / ".vstack" / "templates" / "architect" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(
            "name: architect\ndefaults:\n  artifacts:\n    dir: architecture\n",
            encoding="utf-8",
        )

        changed = MigrateCommand._upgrade_agent_template_items_keys(
            project_root=tmp_path,
            dry_run=False,
        )

        assert changed == 1
        parsed = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert parsed["defaults"]["items"]["dir"] == "architecture"

    def test_agent_template_upgrade_is_dry_run_only(self, tmp_path: Path) -> None:
        """Dry-run reports agent template upgrade without writing files."""
        config_path = tmp_path / ".vstack" / "templates" / "architect" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        original = "name: architect\ndefaults:\n  artifacts:\n    dir: architecture\n"
        config_path.write_text(original, encoding="utf-8")

        changed = MigrateCommand._upgrade_agent_template_items_keys(
            project_root=tmp_path,
            dry_run=True,
        )

        assert changed == 1
        assert config_path.read_text(encoding="utf-8") == original

    def test_agent_template_upgrade_skips_non_mapping_yaml(self, tmp_path: Path) -> None:
        """Skips template config files whose YAML root is not a mapping."""
        config_path = tmp_path / ".vstack" / "templates" / "architect" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text("- just\n- a\n- list\n", encoding="utf-8")

        changed = MigrateCommand._upgrade_agent_template_items_keys(
            project_root=tmp_path,
            dry_run=False,
        )

        assert changed == 0

    def test_agent_template_upgrade_skips_when_defaults_invalid(self, tmp_path: Path) -> None:
        """Skips template config files with non-mapping defaults."""
        config_path = tmp_path / ".vstack" / "templates" / "architect" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text("name: architect\ndefaults: all\n", encoding="utf-8")

        changed = MigrateCommand._upgrade_agent_template_items_keys(
            project_root=tmp_path,
            dry_run=False,
        )

        assert changed == 0

    def test_agent_template_upgrade_skips_when_items_already_present(self, tmp_path: Path) -> None:
        """Skips template config files that already define defaults.items."""
        config_path = tmp_path / ".vstack" / "templates" / "architect" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(
            "name: architect\ndefaults:\n  items:\n    dir: architecture\n",
            encoding="utf-8",
        )

        changed = MigrateCommand._upgrade_agent_template_items_keys(
            project_root=tmp_path,
            dry_run=False,
        )

        assert changed == 0

    def test_agent_template_upgrade_skips_when_artifacts_invalid(self, tmp_path: Path) -> None:
        """Skips template config files where defaults.artifacts is not a mapping."""
        config_path = tmp_path / ".vstack" / "templates" / "architect" / "config.yaml"
        config_path.parent.mkdir(parents=True)
        config_path.write_text(
            "name: architect\ndefaults:\n  artifacts: all\n",
            encoding="utf-8",
        )

        changed = MigrateCommand._upgrade_agent_template_items_keys(
            project_root=tmp_path,
            dry_run=False,
        )

        assert changed == 0

    def test_cleanup_removes_legacy_commented_workflow_example(self, tmp_path: Path) -> None:
        """Removes trailing commented ACTIVE CONFIGURATION example block."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        config_path = vstack_dir / "config.yaml"
        config_path.write_text(
            "workflow:\n"
            "  mode: agentic\n"
            "# -----------------------------------------------------------------------------\n"
            "# ACTIVE CONFIGURATION (UNCOMMENT AND EDIT)\n"
            "# -----------------------------------------------------------------------------\n"
            "# workflow:\n"
            "#   mode: agentic\n",
            encoding="utf-8",
        )

        changed = MigrateCommand._cleanup_commented_workflow_example(
            project_root=tmp_path,
            dry_run=False,
        )

        assert changed == 1
        content = config_path.read_text(encoding="utf-8")
        assert "ACTIVE CONFIGURATION (UNCOMMENT AND EDIT)" not in content
        assert "workflow:\n  mode: agentic" in content

    def test_cleanup_dry_run_does_not_write(self, tmp_path: Path) -> None:
        """Dry-run reports cleanup without changing file content."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        config_path = vstack_dir / "config.yaml"
        original = "# ACTIVE CONFIGURATION (UNCOMMENT AND EDIT)\n# workflow:\n#   mode: agentic\n"
        config_path.write_text(original, encoding="utf-8")

        changed = MigrateCommand._cleanup_commented_workflow_example(
            project_root=tmp_path,
            dry_run=True,
        )

        assert changed == 1
        assert config_path.read_text(encoding="utf-8") == original

    def test_cleanup_is_noop_when_marker_absent(self, tmp_path: Path) -> None:
        """No changes are reported when the marker block is absent."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        config_path = vstack_dir / "config.yaml"
        config_path.write_text("workflow:\n  mode: agentic\n", encoding="utf-8")

        changed = MigrateCommand._cleanup_commented_workflow_example(
            project_root=tmp_path,
            dry_run=False,
        )

        assert changed == 0

    def test_cleanup_preserves_non_comment_lines_after_marker(self, tmp_path: Path) -> None:
        """Marker cleanup stops once active YAML resumes after commented lines."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        config_path = vstack_dir / "config.yaml"
        config_path.write_text(
            "# ACTIVE CONFIGURATION (UNCOMMENT AND EDIT)\n"
            "# workflow:\n"
            "workflow:\n"
            "  mode: agentic\n",
            encoding="utf-8",
        )

        changed = MigrateCommand._cleanup_commented_workflow_example(
            project_root=tmp_path,
            dry_run=False,
        )

        assert changed == 1
        content = config_path.read_text(encoding="utf-8")
        assert content == "workflow:\n  mode: agentic\n"

    def test_cleanup_preserves_active_workflow_handoffs(self, tmp_path: Path) -> None:
        """Cleanup never removes active workflow and handoff settings."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        config_path = vstack_dir / "config.yaml"
        config_path.write_text(
            "# ACTIVE CONFIGURATION (UNCOMMENT AND EDIT)\n"
            "# workflow:\n"
            "workflow:\n"
            "  mode: manual\n"
            "  stages:\n"
            "    - role: architect\n"
            "      gate: required\n"
            "      handoffs:\n"
            "        prompt: Keep this\n",
            encoding="utf-8",
        )

        changed = MigrateCommand._cleanup_commented_workflow_example(
            project_root=tmp_path,
            dry_run=False,
        )

        assert changed == 1
        content = config_path.read_text(encoding="utf-8")
        assert "workflow:" in content
        assert "mode: manual" in content
        assert "handoffs:" in content
        assert "prompt: Keep this" in content


class TestApplyMoves:
    """_apply_moves relocates files and reports results."""

    def test_moves_file_to_new_path(self, tmp_path: Path) -> None:
        """Moves an existing file from old to new path."""
        old = tmp_path / "docs" / "a.md"
        old.parent.mkdir(parents=True)
        old.write_text("content", encoding="utf-8")

        moves = [{"old": "docs/a.md", "new": "docs/sub/b.md"}]
        moved, skipped = MigrateCommand._apply_moves(
            moves=moves,
            project_root=tmp_path,
            items_root="docs",
            dry_run=False,
            colors=_FakeColors,
        )
        assert moved == 1
        assert skipped == 0
        assert not old.exists()
        assert (tmp_path / "docs" / "sub" / "b.md").read_text(encoding="utf-8") == "content"

    def test_skips_absent_old_path(self, tmp_path: Path) -> None:
        """Counts absent old paths as skipped without error."""
        moves = [{"old": "docs/missing.md", "new": "docs/new.md"}]
        moved, skipped = MigrateCommand._apply_moves(
            moves=moves,
            project_root=tmp_path,
            items_root="docs",
            dry_run=False,
            colors=_FakeColors,
        )
        assert moved == 0
        assert skipped == 1

    def test_skips_when_destination_exists(self, tmp_path: Path) -> None:
        """Counts existing destinations as skipped without overwriting."""
        old = tmp_path / "docs" / "a.md"
        old.parent.mkdir(parents=True)
        old.write_text("old content", encoding="utf-8")
        new = tmp_path / "docs" / "b.md"
        new.write_text("existing content", encoding="utf-8")

        moves = [{"old": "docs/a.md", "new": "docs/b.md"}]
        moved, skipped = MigrateCommand._apply_moves(
            moves=moves,
            project_root=tmp_path,
            items_root="docs",
            dry_run=False,
            colors=_FakeColors,
        )
        assert moved == 0
        assert skipped == 1
        assert new.read_text(encoding="utf-8") == "existing content"

    def test_dry_run_does_not_move_files(self, tmp_path: Path) -> None:
        """Dry-run reports a move without actually moving the file."""
        old = tmp_path / "docs" / "a.md"
        old.parent.mkdir(parents=True)
        old.write_text("content", encoding="utf-8")

        moves = [{"old": "docs/a.md", "new": "docs/b.md"}]
        moved, skipped = MigrateCommand._apply_moves(
            moves=moves,
            project_root=tmp_path,
            items_root="docs",
            dry_run=True,
            colors=_FakeColors,
        )
        assert moved == 1
        assert skipped == 0
        assert old.exists()
        assert not (tmp_path / "docs" / "b.md").exists()

    def test_skips_moves_with_empty_paths(self, tmp_path: Path) -> None:
        """Ignores move entries that are missing old or new keys."""
        moves: list[dict[str, Any]] = [
            {"old": "", "new": "docs/b.md"},
            {"old": "docs/a.md", "new": ""},
        ]
        moved, skipped = MigrateCommand._apply_moves(
            moves=moves,
            project_root=tmp_path,
            items_root="docs",
            dry_run=False,
            colors=_FakeColors,
        )
        assert moved == 0
        assert skipped == 0

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """Creates missing parent directories for the new path."""
        old = tmp_path / "docs" / "a.md"
        old.parent.mkdir(parents=True)
        old.write_text("content", encoding="utf-8")

        moves = [{"old": "docs/a.md", "new": "docs/deep/nested/b.md"}]
        MigrateCommand._apply_moves(
            moves=moves,
            project_root=tmp_path,
            items_root="docs",
            dry_run=False,
            colors=_FakeColors,
        )
        assert (tmp_path / "docs" / "deep" / "nested" / "b.md").exists()

    def test_substitutes_custom_items_root_in_new_path(self, tmp_path: Path) -> None:
        """Applies the custom items.root when resolving new paths."""
        old = tmp_path / "docs" / "a.md"
        old.parent.mkdir(parents=True)
        old.write_text("content", encoding="utf-8")

        moves = [{"old": "docs/a.md", "new": "docs/b.md"}]
        MigrateCommand._apply_moves(
            moves=moves,
            project_root=tmp_path,
            items_root="content",
            dry_run=False,
            colors=_FakeColors,
        )
        assert (tmp_path / "content" / "b.md").exists()


class TestMigrateCommandRun:
    """MigrateCommand.run end-to-end scenarios."""

    def test_detects_to_major_from_package_version(self, tmp_path: Path) -> None:
        """Detects to_major from the current package VERSION when --to is absent."""
        record_dir = tmp_path / "_migrations"
        record_dir.mkdir()

        cmd = MigrateCommand(_service())
        context = _context(
            Namespace(dry_run=True, target=str(tmp_path), from_major=1, to_major=None)
        )
        with patch("vstack.cli.migrate.MIGRATIONS_ROOT", record_dir):
            # Should complete without error regardless of what VERSION resolves to
            result = cmd.run(context=context)
        assert result == 0

    def test_to_major_falls_back_when_version_unparseable(self, tmp_path: Path) -> None:
        """Falls back to from_major+1 when VERSION cannot be parsed."""
        record_dir = tmp_path / "_migrations"
        record_dir.mkdir()

        cmd = MigrateCommand(_service())
        context = _context(
            Namespace(dry_run=True, target=str(tmp_path), from_major=2, to_major=None)
        )
        with (
            patch("vstack.cli.migrate.MIGRATIONS_ROOT", record_dir),
            patch("vstack.cli.migrate.VERSION", "not-semver"),
        ):
            result = cmd.run(context=context)
        assert result == 0

    def test_returns_0_when_nothing_to_migrate(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Returns 0 and prints a message when from >= to."""
        cmd = MigrateCommand(_service())
        context = _context(Namespace(dry_run=False, target=str(tmp_path), from_major=3, to_major=3))
        assert cmd.run(context=context) == 0
        assert "Nothing to migrate" in capsys.readouterr().out

    def test_prints_config_upgrade_message_when_from_gte_to(self, tmp_path: Path) -> None:
        """Reports config upgrade when no path move is required."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / "config.yaml").write_text("artifacts:\n  root: content\n", encoding="utf-8")

        cmd = MigrateCommand(_service())
        context = _context(Namespace(dry_run=False, target=str(tmp_path), from_major=3, to_major=3))

        with patch("builtins.print") as mock_print:
            result = cmd.run(context=context)

        assert result == 0
        printed = "\n".join(str(call.args[0]) for call in mock_print.call_args_list if call.args)
        assert "Updated legacy config keys" in printed

    def test_returns_1_when_major_not_detectable(self, tmp_path: Path) -> None:
        """Returns 1 and writes to stderr when from_major cannot be detected."""
        cmd = MigrateCommand(_service())
        context = _context(
            Namespace(dry_run=False, target=str(tmp_path), from_major=None, to_major=3)
        )
        assert cmd.run(context=context) == 1

    def test_applies_moves_for_range(self, tmp_path: Path) -> None:
        """Applies migration records across the full from→to range."""
        # Create old-style docs
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "architecture.md").write_text("arch", encoding="utf-8")

        # Fake migration record: v2→v3
        record_dir = tmp_path / "_migrations"
        record_dir.mkdir()
        record = {
            "from_version": "2.x",
            "to_version": "3.0",
            "moves": [
                {"old": "docs/architecture.md", "new": "docs/overview.md", "type": "docs"},
            ],
        }
        (record_dir / "v2_to_v3.yaml").write_text(yaml.dump(record), encoding="utf-8")

        cmd = MigrateCommand(_service())
        context = _context(Namespace(dry_run=False, target=str(tmp_path), from_major=2, to_major=3))
        with patch("vstack.cli.migrate.MIGRATIONS_ROOT", record_dir):
            result = cmd.run(context=context)

        assert result == 0
        assert not (tmp_path / "docs" / "architecture.md").exists()
        assert (tmp_path / "docs" / "overview.md").read_text(encoding="utf-8") == "arch"

    def test_skips_steps_with_no_record(
        self, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """Skips version steps that have no migration record file."""
        record_dir = tmp_path / "_migrations"
        record_dir.mkdir()  # empty — no records

        cmd = MigrateCommand(_service())
        context = _context(Namespace(dry_run=False, target=str(tmp_path), from_major=1, to_major=3))
        with patch("vstack.cli.migrate.MIGRATIONS_ROOT", record_dir):
            result = cmd.run(context=context)

        assert result == 0
        out = capsys.readouterr().out
        assert "no migration record" in out

    def test_dry_run_does_not_move_files(self, tmp_path: Path) -> None:
        """Dry-run leaves files in place while reporting counts."""
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "architecture.md").write_text("arch", encoding="utf-8")

        record_dir = tmp_path / "_migrations"
        record_dir.mkdir()
        record = {
            "from_version": "2.x",
            "to_version": "3.0",
            "moves": [
                {"old": "docs/architecture.md", "new": "docs/overview.md", "type": "docs"},
            ],
        }
        (record_dir / "v2_to_v3.yaml").write_text(yaml.dump(record), encoding="utf-8")

        cmd = MigrateCommand(_service())
        context = _context(Namespace(dry_run=True, target=str(tmp_path), from_major=2, to_major=3))
        with patch("vstack.cli.migrate.MIGRATIONS_ROOT", record_dir):
            result = cmd.run(context=context)

        assert result == 0
        assert (tmp_path / "docs" / "architecture.md").exists()
        assert not (tmp_path / "docs" / "overview.md").exists()

    def test_detects_from_major_from_manifest(self, tmp_path: Path) -> None:
        """Detects from_major from the manifest when --from is absent."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        manifest = {
            "manifest_version": 2,
            "hash_algorithm": "sha256",
            "vstack_version": "2.1.0",
            "installed_at": "2026-01-01T00:00:00+00:00",
            "artifacts": {},
        }
        (vstack_dir / "vstack.json").write_text(
            __import__("json").dumps(manifest), encoding="utf-8"
        )

        record_dir = tmp_path / "_migrations"
        record_dir.mkdir()

        cmd = MigrateCommand(_service())
        context = _context(
            Namespace(dry_run=True, target=str(tmp_path), from_major=None, to_major=3)
        )
        with patch("vstack.cli.migrate.MIGRATIONS_ROOT", record_dir):
            result = cmd.run(context=context)

        assert result == 0

    def test_chains_multiple_migration_steps(self, tmp_path: Path) -> None:
        """Applies v1→v2 and v2→v3 moves in sequence for a v1→v3 migration."""
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "old_v1.md").write_text("v1", encoding="utf-8")
        (tmp_path / "docs" / "old_v2.md").write_text("v2", encoding="utf-8")

        record_dir = tmp_path / "_migrations"
        record_dir.mkdir()

        (record_dir / "v1_to_v2.yaml").write_text(
            yaml.dump(
                {
                    "from_version": "1.x",
                    "to_version": "2.0",
                    "moves": [{"old": "docs/old_v1.md", "new": "docs/new_v1.md", "type": "docs"}],
                }
            ),
            encoding="utf-8",
        )
        (record_dir / "v2_to_v3.yaml").write_text(
            yaml.dump(
                {
                    "from_version": "2.x",
                    "to_version": "3.0",
                    "moves": [{"old": "docs/old_v2.md", "new": "docs/new_v2.md", "type": "docs"}],
                }
            ),
            encoding="utf-8",
        )

        cmd = MigrateCommand(_service())
        context = _context(Namespace(dry_run=False, target=str(tmp_path), from_major=1, to_major=3))
        with patch("vstack.cli.migrate.MIGRATIONS_ROOT", record_dir):
            result = cmd.run(context=context)

        assert result == 0
        assert (tmp_path / "docs" / "new_v1.md").exists()
        assert (tmp_path / "docs" / "new_v2.md").exists()
