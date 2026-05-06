"""Tests for InstallCommand — first-run project setup wizard."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from vstack.cli.base import CommandContext
from vstack.cli.install import InstallCommand
from vstack.cli.service import CommandService


class TestInstallCommand:
    """Test cases for InstallCommand wizard behavior."""

    # ------------------------------------------------------------------
    # run (wizard behaviour)
    # ------------------------------------------------------------------

    def test_run_seeds_project_and_calls_init_execute_for_local(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """run() seeds project files and calls InitCommand.execute() for local installs."""
        seeded: list[dict[str, Any]] = []
        executed: list[dict[str, Any]] = []

        def _fake_seed(**kw: Any) -> None:
            seeded.append(kw)

        def _fake_execute(*_a: Any, **kw: Any) -> int:
            executed.append(kw)
            return 0

        monkeypatch.setattr(
            "vstack.cli.install.InstallCommand._seed_project",
            staticmethod(_fake_seed),
        )
        monkeypatch.setattr(
            "vstack.cli.init.InitCommand.execute",
            staticmethod(_fake_execute),
        )

        from argparse import Namespace

        install_dir = tmp_path / ".github"
        fake_service = SimpleNamespace(root=tmp_path / "templates")
        context = CommandContext(
            args=Namespace(
                force=True,
                force_names=["a"],
                adopt_name=["b"],
                update=True,
                dry_run=False,
                use_global=False,
            ),
            install_dir=install_dir,
            only=["skill"],
        )
        result = InstallCommand(service=cast(CommandService, fake_service)).run(context=context)
        assert result == 0
        assert len(seeded) == 1
        assert seeded[0]["project_root"] == tmp_path
        assert len(executed) == 1
        assert executed[0]["force"] is True
        assert executed[0]["adopt_names"] == ["b"]

    def test_run_skips_seeding_for_global_install(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """run() skips seeding when --global is active."""
        seeded: list[dict[str, Any]] = []

        monkeypatch.setattr(
            "vstack.cli.install.InstallCommand._seed_project",
            staticmethod(lambda **kw: seeded.append(kw)),
        )
        monkeypatch.setattr("vstack.cli.init.InitCommand.execute", staticmethod(lambda *a, **kw: 0))

        from argparse import Namespace

        context = CommandContext(
            args=Namespace(
                force=False,
                force_names=None,
                adopt_name=None,
                update=False,
                dry_run=False,
                use_global=True,
            ),
            install_dir=tmp_path / ".github",
            only=None,
        )
        InstallCommand(service=cast(CommandService, object())).run(context=context)
        assert seeded == []

    def test_run_forwards_execute_kwargs(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """run() passes all context args through to InitCommand.execute()."""
        captured: dict[str, Any] = {}

        monkeypatch.setattr(
            "vstack.cli.install.InstallCommand._seed_project",
            staticmethod(lambda **kw: None),
        )

        def _fake_execute(*args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs
            return 1

        monkeypatch.setattr("vstack.cli.init.InitCommand.execute", staticmethod(_fake_execute))

        from argparse import Namespace

        fake_service = SimpleNamespace(root=tmp_path / "templates")
        context = CommandContext(
            args=Namespace(
                force=True,
                force_names=["a"],
                adopt_name=["b"],
                update=True,
                dry_run=True,
                use_global=False,
            ),
            install_dir=tmp_path,
            only=["skill"],
        )
        assert InstallCommand(service=cast(CommandService, fake_service)).run(context=context) == 1
        assert captured["kwargs"]["adopt_names"] == ["b"]
        assert captured["kwargs"]["force"] is True

    def test_run_forwards_excluded_names_to_execute(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """run() passes context.excluded_names through to InitCommand.execute()."""
        captured: dict[str, Any] = {}

        monkeypatch.setattr(
            "vstack.cli.install.InstallCommand._seed_project",
            staticmethod(lambda **kw: None),
        )
        monkeypatch.setattr(
            "vstack.cli.install.InstallCommand._write_vstack_gitignore",
            staticmethod(lambda **kw: None),
        )

        def _fake_execute(*args, **kwargs):
            captured["kwargs"] = kwargs
            return 0

        monkeypatch.setattr("vstack.cli.init.InitCommand.execute", staticmethod(_fake_execute))

        from argparse import Namespace

        fake_service = SimpleNamespace(root=tmp_path / "templates")
        context = CommandContext(
            args=Namespace(
                force=False,
                force_names=None,
                adopt_name=None,
                update=False,
                dry_run=False,
                use_global=False,
            ),
            install_dir=tmp_path / ".github",
            only=None,
            excluded_names={"skill": ["helm", "terraform"]},
        )
        result = InstallCommand(service=cast(CommandService, fake_service)).run(context=context)

        assert result == 0
        assert captured["kwargs"]["excluded_names"] == {"skill": ["helm", "terraform"]}

    # ------------------------------------------------------------------
    # _seed_project
    # ------------------------------------------------------------------

    def test_seed_project_copies_new_files(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """_seed_project writes files that do not yet exist in project_root."""
        templates_root = tmp_path / "templates"
        seed_dir = templates_root / "project" / ".vstack"
        seed_dir.mkdir(parents=True)
        (seed_dir / "config.yaml").write_text("project:\n  name: ''\n", encoding="utf-8")

        project_root = tmp_path / "project"
        colors = SimpleNamespace(YELLOW="", RESET="", BOLD="", DIM="", GREEN="")
        InstallCommand._seed_project(
            project_root=project_root,
            templates_root=templates_root,
            colors=colors,
            dry_run=False,
        )

        dst = project_root / ".vstack" / "config.yaml"
        assert dst.exists()
        assert dst.read_text(encoding="utf-8") == "project:\n  name: ''\n"
        assert "seeded" in capsys.readouterr().out

    def test_seed_project_skips_existing_files(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """_seed_project does not overwrite files that already exist."""
        templates_root = tmp_path / "templates"
        seed_dir = templates_root / "project" / ".vstack"
        seed_dir.mkdir(parents=True)
        (seed_dir / "config.yaml").write_text("new content", encoding="utf-8")

        project_root = tmp_path / "project"
        (project_root / ".vstack").mkdir(parents=True)
        (project_root / ".vstack" / "config.yaml").write_text("existing", encoding="utf-8")

        colors = SimpleNamespace(YELLOW="", RESET="", BOLD="", DIM="", GREEN="")
        InstallCommand._seed_project(
            project_root=project_root,
            templates_root=templates_root,
            colors=colors,
            dry_run=False,
        )

        assert (project_root / ".vstack" / "config.yaml").read_text(encoding="utf-8") == "existing"
        assert "skipped" in capsys.readouterr().out

    def test_seed_project_dry_run_does_not_write(self, tmp_path: Path) -> None:
        """_seed_project in dry_run mode prints but does not write files."""
        templates_root = tmp_path / "templates"
        seed_dir = templates_root / "project" / ".vstack"
        seed_dir.mkdir(parents=True)
        (seed_dir / "config.yaml").write_text("content", encoding="utf-8")

        project_root = tmp_path / "project"
        colors = SimpleNamespace(YELLOW="", RESET="", BOLD="", DIM="", GREEN="")
        InstallCommand._seed_project(
            project_root=project_root,
            templates_root=templates_root,
            colors=colors,
            dry_run=True,
        )

        assert not (project_root / ".vstack" / "config.yaml").exists()

    def test_seed_project_noop_when_no_project_templates(self, tmp_path: Path) -> None:
        """_seed_project does nothing when neither project/ nor agents/ dirs exist."""
        colors = SimpleNamespace(YELLOW="", RESET="", BOLD="", DIM="", GREEN="")
        project_root = tmp_path / "project"
        InstallCommand._seed_project(
            project_root=project_root,
            templates_root=tmp_path / "nonexistent",
            colors=colors,
            dry_run=False,
        )
        assert not project_root.exists()

    def test_seed_project_seeds_agent_artifacts_to_vstack_templates(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """_seed_project copies agent artifacts/ to .vstack/templates/{agent}/artifacts/."""
        templates_root = tmp_path / "templates"
        artifact = templates_root / "agents" / "tester" / "artifacts" / "test-report.md"
        artifact.parent.mkdir(parents=True)
        artifact.write_text("# Test Report\n", encoding="utf-8")

        project_root = tmp_path / "project"
        colors = SimpleNamespace(YELLOW="", RESET="", BOLD="", DIM="", GREEN="")
        InstallCommand._seed_project(
            project_root=project_root,
            templates_root=templates_root,
            colors=colors,
            dry_run=False,
        )

        dst = project_root / ".vstack" / "templates" / "tester" / "artifacts" / "test-report.md"
        assert dst.exists()
        assert dst.read_text(encoding="utf-8") == "# Test Report\n"
        assert "seeded" in capsys.readouterr().out

    def test_seed_project_skips_existing_agent_artifact(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """_seed_project does not overwrite existing agent artifact files."""
        templates_root = tmp_path / "templates"
        artifact = templates_root / "agents" / "tester" / "artifacts" / "test-report.md"
        artifact.parent.mkdir(parents=True)
        artifact.write_text("new content", encoding="utf-8")

        project_root = tmp_path / "project"
        dst = project_root / ".vstack" / "templates" / "tester" / "artifacts" / "test-report.md"
        dst.parent.mkdir(parents=True)
        dst.write_text("existing", encoding="utf-8")

        colors = SimpleNamespace(YELLOW="", RESET="", BOLD="", DIM="", GREEN="")
        InstallCommand._seed_project(
            project_root=project_root,
            templates_root=templates_root,
            colors=colors,
            dry_run=False,
        )

        assert dst.read_text(encoding="utf-8") == "existing"
        assert "skipped" in capsys.readouterr().out

    def test_seed_project_skips_non_directory_entries_in_agents_root(self, tmp_path: Path) -> None:
        """_seed_project ignores non-directory entries directly under agents/."""
        templates_root = tmp_path / "templates"
        agents_root = templates_root / "agents"
        agents_root.mkdir(parents=True)
        # A file directly in agents/ — not a directory, must be skipped
        (agents_root / "README.md").write_text("ignore me", encoding="utf-8")

        project_root = tmp_path / "project"
        colors = SimpleNamespace(YELLOW="", RESET="", BOLD="", DIM="", GREEN="")
        InstallCommand._seed_project(
            project_root=project_root,
            templates_root=templates_root,
            colors=colors,
            dry_run=False,
        )
        assert not project_root.exists()

    def test_seed_project_skips_agent_dir_without_artifacts_subdir(self, tmp_path: Path) -> None:
        """_seed_project skips agent directories that have no artifacts/ subdir."""
        templates_root = tmp_path / "templates"
        agent_dir = templates_root / "agents" / "engineer"
        agent_dir.mkdir(parents=True)
        # No artifacts/ subdir — nothing should be seeded
        (agent_dir / "config.yaml").write_text("name: engineer\n", encoding="utf-8")

        project_root = tmp_path / "project"
        colors = SimpleNamespace(YELLOW="", RESET="", BOLD="", DIM="", GREEN="")
        InstallCommand._seed_project(
            project_root=project_root,
            templates_root=templates_root,
            colors=colors,
            dry_run=False,
        )
        assert not project_root.exists()

    # ------------------------------------------------------------------
    # _write_vstack_gitignore
    # ------------------------------------------------------------------

    def test_write_vstack_gitignore_creates_file(self, tmp_path: Path) -> None:
        """_write_vstack_gitignore writes .vstack/.gitignore with correct content."""
        InstallCommand._write_vstack_gitignore(project_root=tmp_path, dry_run=False)

        gitignore = tmp_path / ".vstack" / ".gitignore"
        assert gitignore.exists()
        content = gitignore.read_text(encoding="utf-8")
        assert "tmp/\n" in content
        assert "*\n" not in content

    def test_write_vstack_gitignore_overwrites_existing(self, tmp_path: Path) -> None:
        """_write_vstack_gitignore replaces any existing .vstack/.gitignore."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir()
        (vstack_dir / ".gitignore").write_text("old content", encoding="utf-8")

        InstallCommand._write_vstack_gitignore(project_root=tmp_path, dry_run=False)

        assert (vstack_dir / ".gitignore").read_text(encoding="utf-8") != "old content"

    def test_write_vstack_gitignore_dry_run_does_not_write(self, tmp_path: Path) -> None:
        """_write_vstack_gitignore in dry_run mode does not create the file."""
        InstallCommand._write_vstack_gitignore(project_root=tmp_path, dry_run=True)

        assert not (tmp_path / ".vstack" / ".gitignore").exists()

    def test_write_vstack_gitignore_creates_parent_dirs(self, tmp_path: Path) -> None:
        """_write_vstack_gitignore creates .vstack/ if it does not exist."""
        project_root = tmp_path / "new_project"
        InstallCommand._write_vstack_gitignore(project_root=project_root, dry_run=False)

        assert (project_root / ".vstack" / ".gitignore").exists()

    def test_run_calls_write_vstack_gitignore_for_local(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """run() calls _write_vstack_gitignore for local (non-global) installs."""
        written: list[dict] = []

        monkeypatch.setattr(
            "vstack.cli.install.InstallCommand._seed_project",
            staticmethod(lambda **kw: None),
        )
        monkeypatch.setattr(
            "vstack.cli.install.InstallCommand._write_vstack_gitignore",
            staticmethod(lambda **kw: written.append(kw)),
        )
        monkeypatch.setattr("vstack.cli.init.InitCommand.execute", staticmethod(lambda *a, **kw: 0))

        from argparse import Namespace

        fake_service = SimpleNamespace(root=tmp_path / "templates")
        context = CommandContext(
            args=Namespace(
                force=False,
                force_names=None,
                adopt_name=None,
                update=False,
                dry_run=False,
                use_global=False,
            ),
            install_dir=tmp_path / ".github",
            only=None,
        )
        InstallCommand(service=cast(CommandService, fake_service)).run(context=context)
        assert len(written) == 1
        assert written[0]["project_root"] == tmp_path
        assert written[0]["dry_run"] is False

    def test_run_skips_write_vstack_gitignore_for_global(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """run() does not call _write_vstack_gitignore for global installs."""
        written: list[dict] = []

        monkeypatch.setattr(
            "vstack.cli.install.InstallCommand._write_vstack_gitignore",
            staticmethod(lambda **kw: written.append(kw)),
        )
        monkeypatch.setattr("vstack.cli.init.InitCommand.execute", staticmethod(lambda *a, **kw: 0))

        from argparse import Namespace

        context = CommandContext(
            args=Namespace(
                force=False,
                force_names=None,
                adopt_name=None,
                update=False,
                dry_run=False,
                use_global=True,
            ),
            install_dir=tmp_path / ".github",
            only=None,
        )
        InstallCommand(service=cast(CommandService, object())).run(context=context)
        assert written == []
