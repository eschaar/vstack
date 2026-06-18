"""Tests for InitCommand."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from vstack.cli.base import CommandContext
from vstack.cli.init import InitCommand
from vstack.cli.service import CommandService
from vstack.manifest import content_hash


class TestInitCommand:
    """Test cases for InitCommand."""

    # ------------------------------------------------------------------
    # _version_gt
    # ------------------------------------------------------------------

    def test_version_gt_true_for_higher(self) -> None:
        """Higher dotted numeric revision is strictly greater."""
        assert InitCommand._version_gt("1.2.0", "1.1.9")

    def test_version_gt_false_for_equal(self) -> None:
        """Equal versions are not greater."""
        assert not InitCommand._version_gt("1.2.0", "1.2.0")

    def test_version_gt_handles_invalid(self) -> None:
        """Non-numeric strings are treated as (0,) and not greater than a real revision."""
        assert not InitCommand._version_gt("abc", "1.0.0")

    def test_version_gt_handles_none_existing(self) -> None:
        """None for existing falls back to (0,) so any real version is greater."""
        assert InitCommand._version_gt("1.2.0", None) is True

    def test_version_gt_true_for_date_revision(self) -> None:
        """Higher date-based revision is strictly greater."""
        assert InitCommand._version_gt("20260502012", "20260502011")

    def test_version_gt_false_for_same_date_revision(self) -> None:
        """Equal date-based revisions are not greater."""
        assert not InitCommand._version_gt("20260502012", "20260502012")

    def test_version_gt_date_revision_gt_legacy_dotted(self) -> None:
        """YYYYMMDDNNN token is greater than a legacy dotted version from an existing manifest.

        This is the real upgrade path: a freshly installed repo may have artifacts
        versioned as e.g. 1.2.0 (legacy) and the new template uses 20260502012.
        The comparison must return True so the artifact is upgraded, not skipped.
        """
        assert InitCommand._version_gt("20260502012", "1.2.0")

    def test_version_gt_date_revision_gt_legacy_dotted_high_patch(self) -> None:
        """YYYYMMDDNNN token is greater than a legacy high-patch dotted version."""
        assert InitCommand._version_gt("20260421001", "9.99.999")

    def test_version_gt_legacy_dotted_not_gt_date_revision(self) -> None:
        """Legacy dotted version is never greater than a YYYYMMDDNNN token."""
        assert not InitCommand._version_gt("1.2.0", "20260502012")

    # ------------------------------------------------------------------
    # _installed_content_matches
    # ------------------------------------------------------------------

    def test_installed_content_matches_returns_none_for_unknown_algorithm(
        self, tmp_path: Path
    ) -> None:
        """Unknown checksum algorithm is treated as indeterminate (None)."""
        out_file = tmp_path / "artifact.txt"
        out_file.write_text("content", encoding="utf-8")
        entry = SimpleNamespace(checksum="x", checksum_algorithm="sha999")
        assert (
            InitCommand._installed_content_matches(out_file=out_file, existing_entry=entry) is None
        )

    # ------------------------------------------------------------------
    # _install_decision
    # ------------------------------------------------------------------

    def test_decision_preserves_when_tracked_file_has_no_checksum(self, tmp_path: Path) -> None:
        """Tracked file without stored checksum is always preserved."""
        out_file = tmp_path / "artifact.txt"
        out_file.write_text("content", encoding="utf-8")
        entry = SimpleNamespace(checksum=None, checksum_algorithm="sha256", version="1.0.0")
        action, reason = InitCommand._install_decision(
            force=False,
            force_name=False,
            adopt_name=False,
            update=False,
            out_file=out_file,
            existing_entry=entry,
            new_version="1.0.1",
        )
        assert action == "preserve"
        assert reason == "tracked file has no stored checksum"

    def test_decision_preserves_when_version_unknown_under_update(self, tmp_path: Path) -> None:
        """Update mode preserves tracked files that have no stored version metadata."""
        out_file = tmp_path / "artifact.txt"
        out_file.write_text("content", encoding="utf-8")
        entry = SimpleNamespace(
            checksum=content_hash("content"),
            checksum_algorithm="sha256",
            version=None,
        )
        action, reason = InitCommand._install_decision(
            force=False,
            force_name=False,
            adopt_name=False,
            update=True,
            out_file=out_file,
            existing_entry=entry,
            new_version="1.0.1",
        )
        assert action == "preserve"
        assert reason == "tracked file has no stored version"

    # ------------------------------------------------------------------
    # _load_existing_manifest
    # ------------------------------------------------------------------

    def test_load_existing_manifest_returns_none_tuple_on_read_error(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Returns a 4-tuple of None when the manifest file has a read error."""

        class _ManifestFile:
            read_error = "bad manifest"

            def read(self):
                return None

        class _Service:
            @staticmethod
            def manifest_for(_install_dir: Path) -> _ManifestFile:
                return _ManifestFile()

        result = InitCommand._load_existing_manifest(
            service=cast(CommandService, _Service()),
            install_dir=Path("/tmp/install"),
            gens=[],
        )
        assert result == (None, None, None, None)
        assert "ERROR: bad manifest" in capsys.readouterr().err

    # ------------------------------------------------------------------
    # execute
    # ------------------------------------------------------------------

    def test_execute_returns_nonzero_when_manifest_loading_fails(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """execute returns non-zero immediately when manifest loading returns None tuple."""
        monkeypatch.setattr(
            "vstack.cli.init.InitCommand._load_existing_manifest",
            staticmethod(lambda **_kwargs: (None, None, None, None)),
        )
        service = cast(CommandService, SimpleNamespace(generators=[]))
        assert InitCommand.execute(service, Path("/tmp/install")) == 1

    def test_adopt_records_version_from_disk_metadata(self, tmp_path: Path) -> None:
        """Adopted files should use on-disk artifact_version metadata, not new template version."""

        class _Gen:
            config = SimpleNamespace(
                type_name="skill",
                manifest_key="skills",
                output_subdir="skills",
            )

            @staticmethod
            def output_path(name: str) -> Path:
                return Path(name) / "SKILL.md"

            @staticmethod
            def install_relative_path(name: str) -> str:
                return f"skills/{name}/SKILL.md"

        existing_content = (
            "# Skill\n"
            "<!-- AUTO-GENERATED -->"
            "<!-- VSTACK-META: "
            '{"artifact_version":"1.2.3","artifact_name":"verify"}'
            " -->\n"
        )
        out_dir = tmp_path / "skills"
        out_file = out_dir / "verify" / "SKILL.md"
        out_file.parent.mkdir(parents=True)
        out_file.write_text(existing_content, encoding="utf-8")

        new_entries: dict[str, list[Any]] = {}
        InitCommand._install_single_artifact(
            service=cast(CommandService, SimpleNamespace(label=lambda path: str(path))),
            gen=_Gen(),
            artifact=SimpleNamespace(
                name="verify",
                frontmatter={"version": "9.9.9"},
                unresolved=[],
                content="new content",
            ),
            out_dir=out_dir,
            colors=SimpleNamespace(
                CYAN="",
                RESET="",
                DIM="",
                YELLOW="",
                GREEN="",
                BOLD="",
            ),
            prefix="",
            force=False,
            update=False,
            dry_run=True,
            targeted_force_names=set(),
            targeted_adopt_names={"verify"},
            existing_entries={},
            new_entries=new_entries,
            checksum_algorithm="sha256",
        )

        adopted_entry = cast(Any, new_entries["skills"][0])
        assert adopted_entry.version == "1.2.3"
        assert adopted_entry.checksum == content_hash(existing_content)

    def test_adopt_unreadable_file_preserves_without_crashing(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Unreadable adopt targets should be preserved and not crash init."""

        class _Gen:
            config = SimpleNamespace(
                type_name="skill",
                manifest_key="skills",
                output_subdir="skills",
            )

            @staticmethod
            def output_path(name: str) -> Path:
                return Path(name) / "SKILL.md"

            @staticmethod
            def install_relative_path(name: str) -> str:
                return f"skills/{name}/SKILL.md"

        out_dir = tmp_path / "skills"
        out_file = out_dir / "verify" / "SKILL.md"
        out_file.parent.mkdir(parents=True)
        out_file.write_text("content", encoding="utf-8")

        def _raise_oserror(self: Path, encoding: str = "utf-8") -> str:
            del self, encoding
            raise OSError("permission denied")

        monkeypatch.setattr(Path, "read_text", _raise_oserror)

        new_entries: dict[str, list[Any]] = {}
        InitCommand._install_single_artifact(
            service=cast(CommandService, SimpleNamespace(label=lambda path: str(path))),
            gen=_Gen(),
            artifact=SimpleNamespace(
                name="verify",
                frontmatter={"version": "9.9.9"},
                unresolved=[],
                content="new content",
            ),
            out_dir=out_dir,
            colors=SimpleNamespace(
                CYAN="",
                RESET="",
                DIM="",
                YELLOW="",
                GREEN="",
                BOLD="",
            ),
            prefix="",
            force=False,
            update=False,
            dry_run=True,
            targeted_force_names=set(),
            targeted_adopt_names={"verify"},
            existing_entries={},
            new_entries=new_entries,
            checksum_algorithm="sha256",
        )

        out = capsys.readouterr().out
        assert (
            "preserved — existing file is unreadable; could not adopt into vstack manifest" in out
        )
        assert "skills" not in new_entries

    # ------------------------------------------------------------------
    # _prune_planner_when_manual_mode
    # ------------------------------------------------------------------

    def test_prune_planner_when_manual_mode_removes_unchanged_tracked_file(
        self,
        tmp_path: Path,
    ) -> None:
        """Manual mode removes tracked planner file when checksum matches."""
        install_dir = tmp_path / ".github"
        planner_file = install_dir / "agents" / "planner.agent.md"
        planner_file.parent.mkdir(parents=True)
        content = "planner\n"
        planner_file.write_text(content, encoding="utf-8")

        entry = SimpleNamespace(
            name="planner",
            file="agents/planner.agent.md",
            checksum=content_hash(content),
            checksum_algorithm="sha256",
        )
        gen = SimpleNamespace(
            config=SimpleNamespace(type_name="agent", manifest_key="agents"),
            workflow_mode="manual",
        )
        new_entries: dict[str, list[Any]] = {}

        InitCommand._prune_planner_when_manual_mode(
            install_dir=install_dir,
            gen=gen,
            existing_entries={"agent/planner": entry},
            new_entries=new_entries,
            colors=SimpleNamespace(CYAN="", RESET="", DIM="", YELLOW="", GREEN="", BOLD=""),
            prefix="",
            dry_run=False,
        )

        assert not planner_file.exists()
        assert "agents" not in new_entries

    def test_prune_planner_when_manual_mode_preserves_modified_file(
        self,
        tmp_path: Path,
    ) -> None:
        """Manual mode preserves locally modified planner file and keeps it tracked."""
        install_dir = tmp_path / ".github"
        planner_file = install_dir / "agents" / "planner.agent.md"
        planner_file.parent.mkdir(parents=True)
        planner_file.write_text("planner modified\n", encoding="utf-8")

        entry = SimpleNamespace(
            name="planner",
            file="agents/planner.agent.md",
            checksum=content_hash("planner original\n"),
            checksum_algorithm="sha256",
        )
        gen = SimpleNamespace(
            config=SimpleNamespace(type_name="agent", manifest_key="agents"),
            workflow_mode="manual",
        )
        new_entries: dict[str, list[Any]] = {}

        InitCommand._prune_planner_when_manual_mode(
            install_dir=install_dir,
            gen=gen,
            existing_entries={"agent/planner": entry},
            new_entries=new_entries,
            colors=SimpleNamespace(CYAN="", RESET="", DIM="", YELLOW="", GREEN="", BOLD=""),
            prefix="",
            dry_run=False,
        )

        assert planner_file.exists()
        assert "agents" in new_entries
        assert len(new_entries["agents"]) == 1

    @pytest.mark.parametrize(
        ("type_name", "workflow_mode"),
        [("skill", "manual"), ("agent", "agentic")],
    )
    def test_prune_planner_noop_for_non_agent_or_non_manual_mode(
        self,
        tmp_path: Path,
        type_name: str,
        workflow_mode: str,
    ) -> None:
        """Prune helper should no-op unless generator is agent type in manual mode."""
        install_dir = tmp_path / ".github"
        planner_file = install_dir / "agents" / "planner.agent.md"
        planner_file.parent.mkdir(parents=True)
        planner_file.write_text("planner\n", encoding="utf-8")

        entry = SimpleNamespace(
            name="planner",
            file="agents/planner.agent.md",
            checksum=content_hash("planner\n"),
            checksum_algorithm="sha256",
        )
        gen = SimpleNamespace(
            config=SimpleNamespace(type_name=type_name, manifest_key="agents"),
            workflow_mode=workflow_mode,
        )
        new_entries: dict[str, list[Any]] = {}

        InitCommand._prune_planner_when_manual_mode(
            install_dir=install_dir,
            gen=gen,
            existing_entries={"agent/planner": entry},
            new_entries=new_entries,
            colors=SimpleNamespace(CYAN="", RESET="", DIM="", YELLOW="", GREEN="", BOLD=""),
            prefix="",
            dry_run=False,
        )

        assert planner_file.exists()
        assert new_entries == {}

    def test_prune_planner_noop_when_tracked_entry_file_is_missing(self, tmp_path: Path) -> None:
        """Tracked planner entry with missing file should be ignored safely."""
        install_dir = tmp_path / ".github"
        gen = SimpleNamespace(
            config=SimpleNamespace(type_name="agent", manifest_key="agents"),
            workflow_mode="manual",
        )
        new_entries: dict[str, list[Any]] = {}

        entry = SimpleNamespace(
            name="planner",
            file="agents/planner.agent.md",
            checksum=content_hash("planner\n"),
            checksum_algorithm="sha256",
        )

        InitCommand._prune_planner_when_manual_mode(
            install_dir=install_dir,
            gen=gen,
            existing_entries={"agent/planner": entry},
            new_entries=new_entries,
            colors=SimpleNamespace(CYAN="", RESET="", DIM="", YELLOW="", GREEN="", BOLD=""),
            prefix="",
            dry_run=False,
        )

        assert new_entries == {}

    def test_prune_planner_noop_when_planner_entry_not_tracked(self, tmp_path: Path) -> None:
        """Manual mode should no-op when manifest has no planner entry."""
        install_dir = tmp_path / ".github"
        gen = SimpleNamespace(
            config=SimpleNamespace(type_name="agent", manifest_key="agents"),
            workflow_mode="manual",
        )
        new_entries: dict[str, list[Any]] = {}

        InitCommand._prune_planner_when_manual_mode(
            install_dir=install_dir,
            gen=gen,
            existing_entries={},
            new_entries=new_entries,
            colors=SimpleNamespace(CYAN="", RESET="", DIM="", YELLOW="", GREEN="", BOLD=""),
            prefix="",
            dry_run=False,
        )

        assert new_entries == {}

    def test_prune_planner_preserves_when_checksum_algorithm_is_invalid(
        self,
        tmp_path: Path,
    ) -> None:
        """Invalid checksum algorithm should be treated as non-removable and preserved."""
        install_dir = tmp_path / ".github"
        planner_file = install_dir / "agents" / "planner.agent.md"
        planner_file.parent.mkdir(parents=True)
        planner_file.write_text("planner\n", encoding="utf-8")

        entry = SimpleNamespace(
            name="planner",
            file="agents/planner.agent.md",
            checksum="abc123",
            checksum_algorithm="sha999",
        )
        gen = SimpleNamespace(
            config=SimpleNamespace(type_name="agent", manifest_key="agents"),
            workflow_mode="manual",
        )
        new_entries: dict[str, list[Any]] = {}

        InitCommand._prune_planner_when_manual_mode(
            install_dir=install_dir,
            gen=gen,
            existing_entries={"agent/planner": entry},
            new_entries=new_entries,
            colors=SimpleNamespace(CYAN="", RESET="", DIM="", YELLOW="", GREEN="", BOLD=""),
            prefix="",
            dry_run=False,
        )

        assert planner_file.exists()
        assert "agents" in new_entries
        assert len(new_entries["agents"]) == 1

    def test_prune_planner_ignores_parent_rmdir_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Parent directory cleanup failure should be swallowed after planner removal."""
        install_dir = tmp_path / ".github"
        planner_file = install_dir / "agents" / "planner.agent.md"
        planner_file.parent.mkdir(parents=True)
        content = "planner\n"
        planner_file.write_text(content, encoding="utf-8")

        entry = SimpleNamespace(
            name="planner",
            file="agents/planner.agent.md",
            checksum=content_hash(content),
            checksum_algorithm="sha256",
        )
        gen = SimpleNamespace(
            config=SimpleNamespace(type_name="agent", manifest_key="agents"),
            workflow_mode="manual",
        )
        new_entries: dict[str, list[Any]] = {}

        def _raise_rmdir(self: Path) -> None:
            del self
            raise OSError("rmdir blocked")

        monkeypatch.setattr(Path, "rmdir", _raise_rmdir)

        InitCommand._prune_planner_when_manual_mode(
            install_dir=install_dir,
            gen=gen,
            existing_entries={"agent/planner": entry},
            new_entries=new_entries,
            colors=SimpleNamespace(CYAN="", RESET="", DIM="", YELLOW="", GREEN="", BOLD=""),
            prefix="",
            dry_run=False,
        )

        assert not planner_file.exists()

    # ------------------------------------------------------------------
    # _print_summary
    # ------------------------------------------------------------------

    def test_print_summary_no_conflicts_shows_installed_count(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Summary without preserves shows heading, fixed counters, and no guidance."""
        colors = SimpleNamespace(YELLOW="", RESET="", BOLD="", DIM="", GREEN="", CYAN="")
        InitCommand._print_summary(
            colors=colors,
            action_counts={"install": 7, "update": 1},
            preserved_selectors=[],
            dry_run=False,
            prune=False,
        )
        out = capsys.readouterr().out
        assert "Summary" in out
        assert "total processed : 8" in out
        assert "installed" in out and ": 7" in out
        assert "updated" in out and ": 1" in out
        assert "preserved" in out and ": 0" in out
        assert "skipped" in out and ": 0" in out
        assert "adopted" in out and ": 0" in out
        assert "--force" not in out

    def test_print_summary_with_conflicts_shows_guidance(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Summary with preserved files shows count, warning, and flag guidance."""
        colors = SimpleNamespace(YELLOW="", RESET="", BOLD="", DIM="", GREEN="", CYAN="")
        InitCommand._print_summary(
            colors=colors,
            action_counts={"install": 3, "preserve": 2},
            preserved_selectors=["agent/engineer", "skill/verify"],
            dry_run=False,
            prune=False,
        )
        out = capsys.readouterr().out
        assert "Summary" in out
        assert "⚠" in out
        assert "preserved" in out and ": 2" in out
        assert "2 files preserved" in out
        assert "Preserved selectors:" in out
        assert "Next steps:" in out
        assert "--force" in out
        assert "--force-name <name|type/name>" in out
        assert "--adopt-name <name|type/name>" in out
        assert "- agent/engineer" in out
        assert "- skill/verify" in out

    def test_print_summary_single_preserve_uses_singular_noun(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A single preserved file uses the singular 'file' noun."""
        colors = SimpleNamespace(YELLOW="", RESET="", BOLD="", DIM="", GREEN="", CYAN="")
        InitCommand._print_summary(
            colors=colors,
            action_counts={"install": 1, "preserve": 1},
            preserved_selectors=["agent/engineer"],
            dry_run=False,
            prune=False,
        )
        out = capsys.readouterr().out
        assert "1 file preserved" in out

    def test_print_summary_dry_run_marks_header_and_keeps_installed_label(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Dry-run mode marks the summary header and keeps action labels consistent."""
        colors = SimpleNamespace(YELLOW="", RESET="", BOLD="", DIM="", GREEN="", CYAN="")
        InitCommand._print_summary(
            colors=colors,
            action_counts={"install": 10},
            preserved_selectors=[],
            dry_run=True,
            prune=False,
        )
        out = capsys.readouterr().out
        assert "Summary (dry-run)" in out
        assert "installed" in out and ": 10" in out
        assert "would install" not in out

    def test_print_summary_shows_optional_counts_when_nonzero(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Skipped and adopted counters are rendered with their non-zero values."""
        colors = SimpleNamespace(YELLOW="", RESET="", BOLD="", DIM="", GREEN="", CYAN="")
        InitCommand._print_summary(
            colors=colors,
            action_counts={"install": 2, "skip": 3, "adopt": 1},
            preserved_selectors=[],
            dry_run=False,
            prune=False,
        )
        out = capsys.readouterr().out
        assert "skipped" in out and ": 3" in out
        assert "adopted" in out and ": 1" in out

    def test_print_summary_reports_obsolete_guidance_when_not_pruning(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Obsolete candidates are reported with guidance when --prune is not used."""
        colors = SimpleNamespace(YELLOW="", RESET="", BOLD="", DIM="", GREEN="", CYAN="")
        InitCommand._print_summary(
            colors=colors,
            action_counts={"install": 1, "obsolete": 2},
            preserved_selectors=[],
            dry_run=False,
            prune=False,
        )
        out = capsys.readouterr().out
        assert "obsolete" in out and ": 2" in out
        assert "vstack init --prune" in out

    # ------------------------------------------------------------------
    # _install_single_artifact — return value
    # ------------------------------------------------------------------

    def test_install_single_artifact_returns_preserve_for_untracked_file(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Returns 'preserve' when an existing untracked file blocks install."""

        class _Gen:
            config = SimpleNamespace(
                type_name="agent",
                manifest_key="agents",
                output_subdir="agents",
            )

            @staticmethod
            def output_path(name: str) -> Path:
                return Path(f"{name}.agent.md")

            @staticmethod
            def install_relative_path(name: str) -> str:
                return f"agents/{name}.agent.md"

        out_dir = tmp_path / "agents"
        out_dir.mkdir()
        (out_dir / "engineer.agent.md").write_text("existing", encoding="utf-8")

        colors = SimpleNamespace(CYAN="", RESET="", DIM="", YELLOW="", GREEN="", BOLD="")
        result = InitCommand._install_single_artifact(
            service=cast(CommandService, SimpleNamespace(label=lambda p: str(p))),
            gen=_Gen(),
            artifact=SimpleNamespace(
                name="engineer",
                frontmatter={"version": "1.0.0"},
                unresolved=[],
                content="new content",
            ),
            out_dir=out_dir,
            colors=colors,
            prefix="",
            force=False,
            update=False,
            dry_run=True,
            targeted_force_names=set(),
            targeted_adopt_names=set(),
            existing_entries={},
            new_entries={},
            checksum_algorithm="sha256",
        )
        assert result == "preserve"
        capsys.readouterr()

    def test_install_single_artifact_returns_adopt_when_adopting(
        self,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Returns 'adopt' when taking ownership of an existing untracked file."""

        class _Gen:
            config = SimpleNamespace(
                type_name="agent",
                manifest_key="agents",
                output_subdir="agents",
            )

            @staticmethod
            def output_path(name: str) -> Path:
                return Path(f"{name}.agent.md")

            @staticmethod
            def install_relative_path(name: str) -> str:
                return f"agents/{name}.agent.md"

        out_dir = tmp_path / "agents"
        out_dir.mkdir()
        (out_dir / "engineer.agent.md").write_text("existing", encoding="utf-8")

        new_entries: dict[str, list[Any]] = {}
        colors = SimpleNamespace(CYAN="", RESET="", DIM="", YELLOW="", GREEN="", BOLD="")
        result = InitCommand._install_single_artifact(
            service=cast(CommandService, SimpleNamespace(label=lambda p: str(p))),
            gen=_Gen(),
            artifact=SimpleNamespace(
                name="engineer",
                frontmatter={"version": "1.0.0"},
                unresolved=[],
                content="new content",
            ),
            out_dir=out_dir,
            colors=colors,
            prefix="",
            force=False,
            update=False,
            dry_run=True,
            targeted_force_names=set(),
            targeted_adopt_names={"engineer"},
            existing_entries={},
            new_entries=new_entries,
            checksum_algorithm="sha256",
        )
        assert result == "adopt"
        capsys.readouterr()

    # ------------------------------------------------------------------
    # run
    # ------------------------------------------------------------------

    def test_run_forwards_context_to_execute(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """run() unpacks CommandContext args and forwards them to execute()."""
        captured: dict[str, Any] = {}

        def _fake_execute(*args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs
            return 0

        monkeypatch.setattr("vstack.cli.init.InitCommand.execute", staticmethod(_fake_execute))

        context = CommandContext(
            args=Namespace(
                force=True,
                force_names=["a"],
                adopt_name=["b"],
                update=True,
                prune=True,
                dry_run=True,
            ),
            install_dir=tmp_path,
            only=["skill"],
        )
        result = InitCommand(service=cast(CommandService, object())).run(context=context)

        assert result == 0
        assert captured["kwargs"]["force"] is True
        assert captured["kwargs"]["force_names"] == ["a"]
        assert captured["kwargs"]["adopt_names"] == ["b"]
        assert captured["kwargs"]["update"] is True
        assert captured["kwargs"]["prune"] is True
        assert captured["kwargs"]["dry_run"] is True
        assert captured["kwargs"]["only"] == ["skill"]

    def test_run_raises_when_install_dir_missing(self) -> None:
        """run() raises ValueError when install_dir is None."""
        context = CommandContext(
            args=Namespace(),
            install_dir=None,
            only=None,
        )
        with pytest.raises(ValueError, match="init requires install_dir"):
            InitCommand(service=cast(CommandService, object())).run(context=context)

    def test_run_forwards_excluded_names_to_execute(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """run() passes context.excluded_names through to execute()."""
        captured: dict[str, Any] = {}

        def _fake_execute(*args, **kwargs):
            captured["kwargs"] = kwargs
            return 0

        monkeypatch.setattr("vstack.cli.init.InitCommand.execute", staticmethod(_fake_execute))

        context = CommandContext(
            args=Namespace(
                force=False,
                force_names=None,
                adopt_name=None,
                update=False,
                prune=False,
                dry_run=False,
            ),
            install_dir=tmp_path,
            only=None,
            excluded_names={"skill": ["terraform"]},
        )
        InitCommand(service=cast(CommandService, object())).run(context=context)

        assert captured["kwargs"]["excluded_names"] == {"skill": ["terraform"]}

    def test_execute_skips_artifact_in_excluded_names(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """execute() skips artifacts whose name is in excluded_names, prints message."""
        install_single_calls: list[str] = []

        def _fake_install_single(**kwargs):
            install_single_calls.append(kwargs["artifact"].name)
            return "install"

        monkeypatch.setattr(
            "vstack.cli.init.InitCommand._install_single_artifact",
            staticmethod(_fake_install_single),
        )
        monkeypatch.setattr(
            "vstack.cli.init.InitCommand._write_manifest",
            staticmethod(lambda **_kwargs: None),
        )
        monkeypatch.setattr(
            "vstack.cli.init.InitCommand._print_summary",
            staticmethod(lambda **_kwargs: None),
        )

        class _FakeGen:
            config = SimpleNamespace(
                type_name="skill",
                manifest_key="skills",
                output_subdir="skills",
            )

            @staticmethod
            def render_all():
                return [
                    SimpleNamespace(name="terraform", frontmatter={}, unresolved=[], content=""),
                    SimpleNamespace(name="k8s", frontmatter={}, unresolved=[], content=""),
                ]

            @staticmethod
            def install_relative_path(name: str) -> str:
                return f"skills/{name}/SKILL.md"

            @staticmethod
            def verify_input():
                return SimpleNamespace(messages=[])

        service = cast(
            CommandService,
            SimpleNamespace(
                generators=[_FakeGen()],
                label=lambda path: str(path),
                manifest_for=lambda _: SimpleNamespace(read=lambda: None, read_error=None),
            ),
        )
        monkeypatch.setattr(
            "vstack.cli.init.InitCommand._load_existing_manifest",
            staticmethod(lambda **_kwargs: (object(), None, {}, {})),
        )

        result = InitCommand.execute(
            service,
            tmp_path,
            excluded_names={"skill": ["terraform"]},
        )

        assert result == 0
        assert "terraform" not in install_single_calls
        assert "k8s" in install_single_calls
        out = capsys.readouterr().out
        assert "excluded by config" in out

    def test_obsolete_candidates_uses_missing_names_from_selected_families(self) -> None:
        """Candidates include tracked selected-family entries missing from regenerated output."""
        from vstack.manifest import ArtifactEntry, Manifest

        existing_manifest = Manifest(
            vstack_version="3.5.2",
            installed_at="2026-06-18T00:00:00+00:00",
            artifacts={
                "skills": [
                    ArtifactEntry(name="verify", file="skills/verify/SKILL.md"),
                    ArtifactEntry(name="legacy", file="skills/legacy/SKILL.md"),
                ]
            },
        )
        new_entries = {"skills": [ArtifactEntry(name="verify", file="skills/verify/SKILL.md")]}

        obsolete = InitCommand._obsolete_candidates(
            existing_manifest=existing_manifest,
            selected_manifest_keys={"skills"},
            new_entries=new_entries,
        )

        assert len(obsolete) == 1
        assert obsolete[0][0] == "skills"
        assert obsolete[0][1].name == "legacy"

    def test_process_obsolete_entry_report_only_preserves_manifest_entry(
        self,
        tmp_path: Path,
    ) -> None:
        """Report-only mode keeps obsolete entry tracked for future prune runs."""
        from vstack.manifest import ArtifactEntry

        new_entries: dict[str, list[Any]] = {}
        entry = ArtifactEntry(name="legacy", file="skills/legacy/SKILL.md")

        action, was_preserved = InitCommand._process_obsolete_entry(
            install_dir=tmp_path,
            manifest_key="skills",
            type_name="skill",
            entry=entry,
            prune=False,
            dry_run=False,
            colors=SimpleNamespace(CYAN="", RESET="", DIM="", YELLOW="", GREEN="", BOLD=""),
            prefix="",
            new_entries=new_entries,
        )

        assert action == "obsolete"
        assert was_preserved is False
        assert "skills" in new_entries
        assert len(new_entries["skills"]) == 1

    def test_process_obsolete_entry_prunes_when_checksum_matches(
        self,
        tmp_path: Path,
    ) -> None:
        """Prune mode removes obsolete tracked files when content is unchanged."""
        from vstack.manifest import ArtifactEntry

        install_dir = tmp_path / ".github"
        out_file = install_dir / "skills" / "legacy" / "SKILL.md"
        out_file.parent.mkdir(parents=True)
        content = "legacy\n"
        out_file.write_text(content, encoding="utf-8")
        entry = ArtifactEntry(
            name="legacy",
            file="skills/legacy/SKILL.md",
            checksum=content_hash(content),
            checksum_algorithm="sha256",
        )
        new_entries: dict[str, list[Any]] = {}

        action, was_preserved = InitCommand._process_obsolete_entry(
            install_dir=install_dir,
            manifest_key="skills",
            type_name="skill",
            entry=entry,
            prune=True,
            dry_run=False,
            colors=SimpleNamespace(CYAN="", RESET="", DIM="", YELLOW="", GREEN="", BOLD=""),
            prefix="",
            new_entries=new_entries,
        )

        assert action == "prune"
        assert was_preserved is False
        assert not out_file.exists()
        assert new_entries == {}

    def test_process_obsolete_entry_prune_preserves_when_locally_modified(
        self,
        tmp_path: Path,
    ) -> None:
        """Prune mode preserves obsolete files with checksum drift."""
        from vstack.manifest import ArtifactEntry

        install_dir = tmp_path / ".github"
        out_file = install_dir / "skills" / "legacy" / "SKILL.md"
        out_file.parent.mkdir(parents=True)
        out_file.write_text("local edit\n", encoding="utf-8")
        entry = ArtifactEntry(
            name="legacy",
            file="skills/legacy/SKILL.md",
            checksum=content_hash("generated\n"),
            checksum_algorithm="sha256",
        )
        new_entries: dict[str, list[Any]] = {}

        action, was_preserved = InitCommand._process_obsolete_entry(
            install_dir=install_dir,
            manifest_key="skills",
            type_name="skill",
            entry=entry,
            prune=True,
            dry_run=False,
            colors=SimpleNamespace(CYAN="", RESET="", DIM="", YELLOW="", GREEN="", BOLD=""),
            prefix="",
            new_entries=new_entries,
        )

        assert action == "preserve"
        assert was_preserved is True
        assert out_file.exists()
        assert "skills" in new_entries
        assert len(new_entries["skills"]) == 1

    def test_can_prune_obsolete_entry_true_when_file_is_missing(self, tmp_path: Path) -> None:
        """Missing files are safe prune targets and treated as already removed."""
        from vstack.manifest import ArtifactEntry

        entry = ArtifactEntry(
            name="legacy",
            file="skills/legacy/SKILL.md",
            checksum=content_hash("x"),
            checksum_algorithm="sha256",
        )
        removable, reason = InitCommand._can_prune_obsolete_entry(install_dir=tmp_path, entry=entry)
        assert removable is True
        assert reason == "file already missing"

    def test_can_prune_obsolete_entry_false_when_checksum_missing(self, tmp_path: Path) -> None:
        """Tracked obsolete files without checksum metadata are preserved."""
        from vstack.manifest import ArtifactEntry

        out_file = tmp_path / "skills" / "legacy" / "SKILL.md"
        out_file.parent.mkdir(parents=True)
        out_file.write_text("legacy\n", encoding="utf-8")
        entry = ArtifactEntry(name="legacy", file="skills/legacy/SKILL.md")

        removable, reason = InitCommand._can_prune_obsolete_entry(install_dir=tmp_path, entry=entry)
        assert removable is False
        assert reason == "tracked file has no stored checksum"

    def test_can_prune_obsolete_entry_false_when_file_is_unreadable(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Unreadable files are preserved instead of pruned."""
        from vstack.manifest import ArtifactEntry

        out_file = tmp_path / "skills" / "legacy" / "SKILL.md"
        out_file.parent.mkdir(parents=True)
        out_file.write_text("legacy\n", encoding="utf-8")
        entry = ArtifactEntry(
            name="legacy",
            file="skills/legacy/SKILL.md",
            checksum=content_hash("legacy\n"),
            checksum_algorithm="sha256",
        )

        def _raise_read_text(self: Path, *, encoding: str = "utf-8") -> str:
            del self, encoding
            raise OSError("unreadable")

        monkeypatch.setattr(Path, "read_text", _raise_read_text)

        removable, reason = InitCommand._can_prune_obsolete_entry(install_dir=tmp_path, entry=entry)
        assert removable is False
        assert reason == "file is unreadable"

    def test_can_prune_obsolete_entry_false_for_unknown_checksum_algorithm(
        self,
        tmp_path: Path,
    ) -> None:
        """Unknown checksum algorithms are treated as unsafe for prune."""
        from vstack.manifest import ArtifactEntry

        out_file = tmp_path / "skills" / "legacy" / "SKILL.md"
        out_file.parent.mkdir(parents=True)
        out_file.write_text("legacy\n", encoding="utf-8")
        entry = ArtifactEntry(
            name="legacy",
            file="skills/legacy/SKILL.md",
            checksum="abc123",
            checksum_algorithm="sha999",
        )

        removable, reason = InitCommand._can_prune_obsolete_entry(install_dir=tmp_path, entry=entry)
        assert removable is False
        assert reason == "unknown checksum algorithm"

    def test_remove_file_if_present_dry_run_keeps_file(self, tmp_path: Path) -> None:
        """Dry-run remove helper should not delete files."""
        out_file = tmp_path / "skills" / "legacy" / "SKILL.md"
        out_file.parent.mkdir(parents=True)
        out_file.write_text("legacy\n", encoding="utf-8")

        InitCommand._remove_file_if_present(out_file=out_file, dry_run=True)
        assert out_file.exists()

    def test_remove_file_if_present_ignores_parent_rmdir_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Parent cleanup failures are swallowed after file deletion."""
        out_file = tmp_path / "skills" / "legacy" / "SKILL.md"
        out_file.parent.mkdir(parents=True)
        out_file.write_text("legacy\n", encoding="utf-8")

        def _raise_rmdir(self: Path) -> None:
            del self
            raise OSError("rmdir blocked")

        monkeypatch.setattr(Path, "rmdir", _raise_rmdir)

        InitCommand._remove_file_if_present(out_file=out_file, dry_run=False)
        assert not out_file.exists()

    def test_execute_tracks_obsolete_and_prune_summary_counts(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """execute() increments obsolete/prune/preserve counters from obsolete processing."""
        from vstack.manifest import ArtifactEntry

        summary_calls: list[dict[str, Any]] = []

        monkeypatch.setattr(
            "vstack.cli.init.InitCommand._write_manifest",
            staticmethod(lambda **_kwargs: None),
        )

        def _fake_summary(**kwargs):
            summary_calls.append(kwargs)

        monkeypatch.setattr(
            "vstack.cli.init.InitCommand._print_summary",
            staticmethod(_fake_summary),
        )

        class _FakeGen:
            config = SimpleNamespace(
                type_name="skill",
                manifest_key="skills",
                output_subdir="skills",
            )

            @staticmethod
            def render_all():
                return []

            @staticmethod
            def verify_input():
                return SimpleNamespace(messages=[])

        service = cast(
            CommandService,
            SimpleNamespace(
                generators=[_FakeGen()],
                label=lambda path: str(path),
                manifest_for=lambda _: SimpleNamespace(read=lambda: None, read_error=None),
            ),
        )

        monkeypatch.setattr(
            "vstack.cli.init.InitCommand._load_existing_manifest",
            staticmethod(lambda **_kwargs: (object(), None, {}, {})),
        )

        obsolete_entries = [
            (
                "skills",
                ArtifactEntry(name="legacy-one", file="skills/legacy-one/SKILL.md"),
            ),
            (
                "skills",
                ArtifactEntry(name="legacy-two", file="skills/legacy-two/SKILL.md"),
            ),
        ]
        monkeypatch.setattr(
            "vstack.cli.init.InitCommand._obsolete_candidates",
            staticmethod(lambda **_kwargs: obsolete_entries),
        )

        process_actions = iter([("prune", False), ("preserve", True)])

        def _fake_process(**_kwargs):
            return next(process_actions)

        monkeypatch.setattr(
            "vstack.cli.init.InitCommand._process_obsolete_entry",
            staticmethod(_fake_process),
        )

        result = InitCommand.execute(service, tmp_path, prune=True)

        assert result == 0
        assert len(summary_calls) == 1
        action_counts = summary_calls[0]["action_counts"]
        assert action_counts["obsolete"] == 2
        assert action_counts["prune"] == 1
        assert action_counts["preserve"] == 1
        assert summary_calls[0]["preserved_selectors"] == ["skill/legacy-two"]


class TestWarnUnknownWorkflowRoles:
    """Tests for InitCommand._warn_unknown_workflow_roles."""

    def test_no_output_when_all_roles_known(self, capsys) -> None:
        """No warning is emitted when all roles match known agent names."""
        from vstack.cli.constants import Colors

        stages = [{"role": "product"}, {"role": "architect"}]
        known = {"product", "architect", "designer"}
        InitCommand._warn_unknown_workflow_roles(
            workflow_stages=stages,
            known_agent_names=known,
            colors=Colors,
        )
        assert capsys.readouterr().err == ""

    def test_warning_emitted_for_unknown_role(self, capsys) -> None:
        """A warning is printed to stderr for each unknown role in workflow stages."""
        from vstack.cli.constants import Colors

        stages = [{"role": "product"}, {"role": "custom-role"}]
        known = {"product", "architect"}
        InitCommand._warn_unknown_workflow_roles(
            workflow_stages=stages,
            known_agent_names=known,
            colors=Colors,
        )
        err = capsys.readouterr().err
        assert "custom-role" in err

    def test_empty_role_is_skipped(self, capsys) -> None:
        """Stages with empty or missing role key are silently skipped."""
        from vstack.cli.constants import Colors

        stages = [{"role": ""}, {"gate": "required"}]
        known: set[str] = set()
        InitCommand._warn_unknown_workflow_roles(
            workflow_stages=stages,
            known_agent_names=known,
            colors=Colors,
        )
        assert capsys.readouterr().err == ""

    def test_execute_calls_warn_for_unknown_workflow_role(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys
    ) -> None:
        """execute() emits a warning when a workflow stage references an unknown agent."""
        from vstack.agents.generator import AgentGenerator

        # Patch manifest loading so execute() terminates quickly.
        monkeypatch.setattr(
            "vstack.cli.init.InitCommand._load_existing_manifest",
            staticmethod(lambda **_kwargs: (None, None, None, None)),
        )

        stages = [
            {
                "role": "unknown-role",
                "gate": "required",
                "handoffs": [{"prompt": "x", "agent": "", "label": ""}],
            }
        ]
        gen = AgentGenerator(workflow_stages=stages)
        monkeypatch.setattr(AgentGenerator, "find_templates", lambda self: [])

        service = cast(Any, SimpleNamespace(generators=[gen]))
        InitCommand.execute(service, tmp_path)

        err = capsys.readouterr().err
        assert "unknown-role" in err
