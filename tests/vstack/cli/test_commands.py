"""Tests for CLI command handlers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, cast

from tests.conftest import run_vstack
from vstack.cli.commands import CommandLineInterface, _version_gt
from vstack.cli.constants import EXPECTED_CANONICAL_NAMES
from vstack.constants import TEMPLATES_ROOT
from vstack.models import CheckMessage, ValidationResult


class TestVersionGt:
    """Test cases for VersionGt."""

    def test_version_gt_true_for_higher(self) -> None:
        """Test that version gt true for higher."""
        assert _version_gt("1.2.0", "1.1.9")

    def test_version_gt_false_for_equal(self) -> None:
        """Test that version gt false for equal."""
        assert not _version_gt("1.2.0", "1.2.0")

    def test_version_gt_handles_invalid(self) -> None:
        """Test that version gt handles invalid."""
        assert not _version_gt("abc", "1.0.0")


class TestCommandLineInterface:
    """Test cases for CommandLineInterface."""

    def test_validate_exits_zero(self) -> None:
        """Test that validate exits zero."""
        result = run_vstack(["validate"])
        assert result.returncode == 0, f"vstack validate failed:\n{result.stderr}"

    def test_verify_exits_zero(self) -> None:
        """Test that verify exits zero."""
        result = run_vstack(["verify", "--no-output"])
        assert result.returncode == 0, (
            f"vstack verify --no-output failed:\n{result.stdout}\n{result.stderr}"
        )

    def test_verify_output_exits_zero(self, installed_target: Path) -> None:
        """Test that verify output exits zero."""
        result = run_vstack(["verify", "--no-source", "--target", str(installed_target)])
        assert result.returncode == 0, (
            f"vstack verify --no-source failed:\n{result.stdout}\n{result.stderr}"
        )

    def test_verify_only_filter_limits_checked_types(self, installed_target: Path) -> None:
        """Test that verify --only checks only requested artifact families."""
        result = run_vstack(
            ["verify", "--no-source", "--target", str(installed_target), "--only", "skill"]
        )
        assert result.returncode == 0, (
            f"vstack verify --only skill failed:\n{result.stdout}\n{result.stderr}"
        )

    def test_install_and_verify_exits_zero(self) -> None:
        """Test that install and verify exits zero."""
        install = run_vstack(["install"])
        assert install.returncode == 0, (
            f"vstack install failed:\n{install.stdout}\n{install.stderr}"
        )
        verify = run_vstack(["verify"])
        assert verify.returncode == 0, f"vstack verify failed:\n{verify.stdout}\n{verify.stderr}"

    def test_validate_with_empty_templates_returns_non_zero(self, tmp_path: Path) -> None:
        """Test that validate with empty templates returns non zero."""
        cli = CommandLineInterface(templates_root=tmp_path)
        assert cli.validate() == 1

    def test_label_prefers_relative(self, tmp_path: Path) -> None:
        """Test that label prefers relative."""
        cli = CommandLineInterface(templates_root=tmp_path)
        path = tmp_path / "x" / "y"
        assert cli._label(path) == "x/y"

    def test_label_falls_back_to_absolute(self, tmp_path: Path) -> None:
        """Test that label falls back to absolute."""
        cli = CommandLineInterface(templates_root=tmp_path)
        other = Path("/tmp/outside-path")
        assert cli._label(other) == str(other)

    def test_cli_class_uses_known_types(self) -> None:
        """Test that cli class uses known types."""
        cli = CommandLineInterface(templates_root=TEMPLATES_ROOT)
        names = {g.config.type_name for g in cli._generators}
        assert names == {"skill", "agent", "instruction", "prompt"}

    def test_install_only_skill_writes_skill_artifacts(self, tmp_path: Path) -> None:
        """Test that install only skill writes skill artifacts."""
        cli = CommandLineInterface(templates_root=TEMPLATES_ROOT)
        rc = cli.install(tmp_path / ".github", only=["skill"])
        assert rc == 0
        assert (tmp_path / ".github" / "skills").exists()

    def test_install_writes_expected_skill_count(self, tmp_path: Path) -> None:
        """Test that install writes expected skill count."""
        cli = CommandLineInterface(templates_root=TEMPLATES_ROOT)
        rc = cli.install(tmp_path / ".github", only=["skill"])
        assert rc == 0
        md_files = list((tmp_path / ".github" / "skills").glob("*/SKILL.md"))
        assert len(md_files) == len(EXPECTED_CANONICAL_NAMES)

    def test_install_only_preserves_manifest_entries_for_other_types(self, tmp_path: Path) -> None:
        """Test that --only install does not drop manifest entries from other artifact types."""
        install_dir = tmp_path / ".github"
        install_dir.mkdir(parents=True)
        manifest: dict[str, Any] = {
            "vstack_version": "0.1.0",
            "installed_at": "2026-01-01T00:00:00Z",
            "artifacts": {
                "agents": [
                    {
                        "name": "engineer",
                        "file": "agents/engineer.agent.md",
                        "version": "0.1.0",
                    }
                ],
                "skills": [
                    {
                        "name": "verify",
                        "file": "skills/verify/SKILL.md",
                        "version": "0.1.0",
                    }
                ],
            },
        }
        (install_dir / "vstack.json").write_text(json.dumps(manifest), encoding="utf-8")

        cli = CommandLineInterface(templates_root=TEMPLATES_ROOT)
        rc = cli.install(install_dir, only=["instruction"])
        assert rc == 0

        updated: dict[str, Any] = json.loads(
            (install_dir / "vstack.json").read_text(encoding="utf-8")
        )
        assert "instructions" in updated["artifacts"]
        assert updated["artifacts"]["agents"] == manifest["artifacts"]["agents"]
        assert updated["artifacts"]["skills"] == manifest["artifacts"]["skills"]

    def test_install_update_skips_when_version_not_newer(self, tmp_path: Path) -> None:
        """Test that install update skips when version not newer."""
        install_dir = tmp_path / ".github"
        manifest = {
            "vstack_version": "0.1.0",
            "installed_at": "2026-01-01T00:00:00Z",
            "artifacts": {
                "skills": [
                    {
                        "name": "vision",
                        "file": "skills/vision/SKILL.md",
                        "version": "999.0.0",
                    }
                ]
            },
        }
        install_dir.mkdir(parents=True)
        (install_dir / "vstack.json").write_text(json.dumps(manifest), encoding="utf-8")
        (install_dir / "skills" / "vision").mkdir(parents=True)
        (install_dir / "skills" / "vision" / "SKILL.md").write_text("old", encoding="utf-8")

        cli = CommandLineInterface(templates_root=TEMPLATES_ROOT)
        rc = cli.install(install_dir, only=["skill"], update=True)
        assert rc == 0
        assert (install_dir / "skills" / "vision" / "SKILL.md").read_text(encoding="utf-8") == "old"

    def test_install_dry_run_does_not_write_outputs(self, tmp_path: Path) -> None:
        """Test that install dry run does not write outputs."""
        cli = CommandLineInterface(templates_root=TEMPLATES_ROOT)
        rc = cli.install(tmp_path / ".github", only=["skill"], dry_run=True)
        assert rc == 0
        assert not (tmp_path / ".github" / "skills").exists()

    def test_verify_output_requires_install_dir(self) -> None:
        """Test that verify output requires install dir."""
        cli = CommandLineInterface(templates_root=TEMPLATES_ROOT)
        assert cli.verify(install_dir=None, source=False, output=True) == 1

    def test_verify_fails_when_output_missing(self, tmp_path: Path) -> None:
        """Test that verify fails when output missing."""
        cli = CommandLineInterface(templates_root=TEMPLATES_ROOT)
        rc = cli.verify(install_dir=tmp_path / ".github", source=False, output=True)
        assert rc == 1

    def test_uninstall_removes_manifest_and_outputs(self, tmp_path: Path) -> None:
        """Test that uninstall removes manifest and outputs."""
        install_dir = tmp_path / ".github"
        cli = CommandLineInterface(templates_root=TEMPLATES_ROOT)
        rc_install = cli.install(install_dir, only=["skill", "agent"])
        assert rc_install == 0
        assert (install_dir / "vstack.json").exists()
        rc_uninstall = cli.uninstall(install_dir)
        assert rc_uninstall == 0
        assert not (install_dir / "vstack.json").exists()

    def test_uninstall_without_manifest_and_without_files(self, tmp_path: Path) -> None:
        """Test that uninstall without manifest and without files."""
        cli = CommandLineInterface(templates_root=TEMPLATES_ROOT)
        rc = cli.uninstall(tmp_path / ".github")
        assert rc == 0

    def test_gen_for_returns_none_for_unknown_type(self) -> None:
        """Test that gen for returns none for unknown type."""
        cli = CommandLineInterface(templates_root=TEMPLATES_ROOT)
        assert cli._gen_for("unknown") is None

    def test_validate_returns_non_zero_on_unresolved(self, tmp_path: Path) -> None:
        """Test that validate returns non zero on unresolved."""

        class _FakeArtifact:
            """Test double for a rendered artifact."""

            def __init__(self) -> None:
                """Initialize instance state."""
                self.name = "a"
                self.unresolved = ["MISSING"]

        class _Cfg:
            """Minimal generator config for this test."""

            type_name = "skill"
            manifest_key = "skills"
            output_subdir = "skills"

        class _FakeGen:
            """Test double for an artifact generator."""

            config = _Cfg()

            def render_all(self):
                """Render all."""
                return [_FakeArtifact()]

            def load_partials(self):
                """Load partials."""
                return {"X": "y"}

            def output_path(self, name: str) -> str:
                """Output path."""
                return f"{name}/SKILL.md"

        cli = CommandLineInterface(templates_root=tmp_path)
        cli._generators = cast(Any, [_FakeGen()])
        assert cli.validate() == 1

    def test_install_force_and_verify_input_fail_path(self, tmp_path: Path) -> None:
        """Test that install force and verify input fail path."""

        class _FakeArtifact:
            """Test double for a rendered artifact."""

            def __init__(self) -> None:
                """Initialize instance state."""
                self.name = "x"
                self.unresolved = ["BROKEN"]
                self.frontmatter = {"version": "1.0.0"}
                self.content = "content"

        class _Cfg:
            """Minimal generator config for this test."""

            type_name = "skill"
            manifest_key = "skills"
            output_subdir = "skills"
            artifact_is_dir = True

        class _FakeGen:
            """Test double for an artifact generator."""

            config = _Cfg()

            def render_all(self):
                """Render all."""
                return [_FakeArtifact()]

            def output_path(self, name: str) -> str:
                """Output path."""
                return f"{name}/SKILL.md"

            def install_relative_path(self, name: str) -> str:
                """Install relative path."""
                return f"skills/{name}/SKILL.md"

            def verify_input(self):
                """Verify input."""
                return ValidationResult(messages=[CheckMessage("fail", "bad")])

        install_dir = tmp_path / ".github"
        out_file = install_dir / "skills" / "x" / "SKILL.md"
        out_file.parent.mkdir(parents=True)
        out_file.write_text("old", encoding="utf-8")

        cli = CommandLineInterface(templates_root=tmp_path)
        cli._generators = cast(Any, [_FakeGen()])
        rc = cli.install(install_dir, force=True)
        assert rc == 1
        assert out_file.read_text(encoding="utf-8") == "content"

    def test_verify_source_with_no_messages_and_all_passed(self, tmp_path: Path) -> None:
        """Test that verify source with no messages and all passed."""

        class _Cfg:
            """Minimal generator config for this test."""

            type_name = "skill"
            output_subdir = "skills"

        class _FakeGen:
            """Test double for an artifact generator."""

            config = _Cfg()

            def verify_input(self, expected=None):
                """Verify input."""
                return ValidationResult(messages=[])

            def verify_output(self, out_dir, expected=None):
                """Verify output."""
                return ValidationResult(messages=[])

        cli = CommandLineInterface(templates_root=tmp_path)
        cli._generators = cast(Any, [_FakeGen()])
        rc = cli.verify(install_dir=tmp_path / ".github", source=True, output=False)
        assert rc == 0

    def test_verify_output_uses_manifest_names(self, tmp_path: Path) -> None:
        """Test that verify output uses manifest names."""
        install_dir = tmp_path / ".github"
        (install_dir / "skills" / "custom").mkdir(parents=True)
        (install_dir / "skills" / "custom" / "SKILL.md").write_text(
            "---\nname: custom\ndescription: 'd'\n---\nbody\n<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->\n",
            encoding="utf-8",
        )
        manifest = {
            "vstack_version": "0.1.0",
            "installed_at": "2026-01-01T00:00:00Z",
            "artifacts": {"skill": [{"name": "custom", "file": "skills/custom/SKILL.md"}]},
        }
        install_dir.mkdir(parents=True, exist_ok=True)
        (install_dir / "vstack.json").write_text(json.dumps(manifest), encoding="utf-8")

        cli = CommandLineInterface(templates_root=TEMPLATES_ROOT)
        rc = cli.verify(install_dir=install_dir, source=False, output=True)
        assert rc == 1

    def test_uninstall_non_directory_artifact_removes_file(self, tmp_path: Path) -> None:
        """Test that uninstall non directory artifact removes file."""
        install_dir = tmp_path / ".github"
        file_path = install_dir / "agents" / "custom.agent.md"
        file_path.parent.mkdir(parents=True)
        file_path.write_text("x", encoding="utf-8")
        manifest = {
            "vstack_version": "0.1.0",
            "installed_at": "2026-01-01T00:00:00Z",
            "artifacts": {"agent": [{"name": "custom", "file": "agents/custom.agent.md"}]},
        }
        (install_dir / "vstack.json").write_text(json.dumps(manifest), encoding="utf-8")

        cli = CommandLineInterface(templates_root=TEMPLATES_ROOT)
        rc = cli.uninstall(install_dir)
        assert rc == 0
        assert not file_path.exists()

    def test_validate_returns_zero_when_all_clean(self, tmp_path: Path) -> None:
        """Test that validate returns zero when all clean."""

        class _FakeArtifact:
            """Test double for a rendered artifact."""

            def __init__(self) -> None:
                """Initialize instance state."""
                self.name = "a"
                self.unresolved: list[str] = []

        class _Cfg:
            """Minimal generator config for this test."""

            type_name = "skill"
            manifest_key = "skills"
            output_subdir = "skills"

        class _FakeGen:
            """Test double for an artifact generator."""

            config = _Cfg()

            def render_all(self):
                """Render all."""
                return [_FakeArtifact()]

            def load_partials(self):
                """Load partials."""
                return {"X": "y"}

            def output_path(self, name: str) -> str:
                """Output path."""
                return f"{name}/SKILL.md"

        cli = CommandLineInterface(templates_root=tmp_path)
        cli._generators = cast(Any, [_FakeGen()])
        assert cli.validate() == 0

    def test_validate_handles_missing_generator_for_type(self, tmp_path: Path) -> None:
        """Test that validate handles missing generator for type."""

        class _FakeArtifact:
            """Test double for a rendered artifact."""

            def __init__(self) -> None:
                """Initialize instance state."""
                self.name = "a"
                self.unresolved: list[str] = []

        class _Cfg:
            """Minimal generator config for this test."""

            type_name = "skill"

        class _FakeGen:
            """Test double for an artifact generator."""

            config = _Cfg()

            def render_all(self):
                """Render all."""
                return [_FakeArtifact()]

            def load_partials(self):
                """Load partials."""
                return {}

            def output_path(self, name: str) -> str:
                """Output path."""
                return f"{name}/SKILL.md"

        cli = CommandLineInterface(templates_root=tmp_path)
        cli._generators = cast(Any, [_FakeGen()])
        setattr(cli, "_gen_for", lambda _type_name: None)
        assert cli.validate() == 0

    def test_install_existing_without_update_skips(self, tmp_path: Path) -> None:
        """Test that install existing without update skips."""
        install_dir = tmp_path / ".github"
        manifest = {
            "vstack_version": "0.1.0",
            "installed_at": "2026-01-01T00:00:00Z",
            "artifacts": {
                "skills": [
                    {
                        "name": "vision",
                        "file": "skills/vision/SKILL.md",
                        "version": "1.0.0",
                    }
                ]
            },
        }
        install_dir.mkdir(parents=True)
        (install_dir / "vstack.json").write_text(json.dumps(manifest), encoding="utf-8")
        (install_dir / "skills" / "vision").mkdir(parents=True)
        (install_dir / "skills" / "vision" / "SKILL.md").write_text("old", encoding="utf-8")

        cli = CommandLineInterface(templates_root=TEMPLATES_ROOT)
        rc = cli.install(install_dir, only=["skill"], update=False)
        assert rc == 0
        assert (install_dir / "skills" / "vision" / "SKILL.md").read_text(encoding="utf-8") == "old"

    def test_install_update_newer_version_writes_file(self, tmp_path: Path) -> None:
        """Test that install update newer version writes file."""
        install_dir = tmp_path / ".github"
        manifest = {
            "vstack_version": "0.1.0",
            "installed_at": "2026-01-01T00:00:00Z",
            "artifacts": {
                "skills": [
                    {
                        "name": "vision",
                        "file": "skills/vision/SKILL.md",
                        "version": "0.0.1",
                    }
                ]
            },
        }
        install_dir.mkdir(parents=True)
        (install_dir / "vstack.json").write_text(json.dumps(manifest), encoding="utf-8")
        (install_dir / "skills" / "vision").mkdir(parents=True)
        (install_dir / "skills" / "vision" / "SKILL.md").write_text("old", encoding="utf-8")

        cli = CommandLineInterface(templates_root=TEMPLATES_ROOT)
        rc = cli.install(install_dir, only=["skill"], update=True)
        assert rc == 0
        new_content = (install_dir / "skills" / "vision" / "SKILL.md").read_text(encoding="utf-8")
        assert new_content != "old"
        assert "AUTO-GENERATED" in new_content

    def test_verify_fails_on_vstack_meta_version_mismatch(self, tmp_path: Path) -> None:
        """Test that verify fails when VSTACK-META footer differs from manifest values."""
        install_dir = tmp_path / ".github"
        cli = CommandLineInterface(templates_root=TEMPLATES_ROOT)
        rc_install = cli.install(install_dir, only=["instruction"])
        assert rc_install == 0

        instruction_file = install_dir / "instructions" / "python.instructions.md"
        content = instruction_file.read_text(encoding="utf-8")
        tampered = re.sub(
            r'"vstack_version":"[^"]+"',
            '"vstack_version":"tampered-version"',
            content,
            count=1,
        )
        instruction_file.write_text(tampered, encoding="utf-8")

        rc_verify = cli.verify(
            install_dir=install_dir,
            source=False,
            output=True,
            only=["instruction"],
        )
        assert rc_verify == 1

    def test_verify_accepts_legacy_artifact_without_vstack_meta(self, tmp_path: Path) -> None:
        """Test that verify accepts old artifacts that do not include VSTACK-META."""
        install_dir = tmp_path / ".github"
        cli = CommandLineInterface(templates_root=TEMPLATES_ROOT)
        rc_install = cli.install(install_dir, only=["instruction"])
        assert rc_install == 0

        instruction_file = install_dir / "instructions" / "python.instructions.md"
        content = instruction_file.read_text(encoding="utf-8")
        legacy_content = re.sub(r"\n<!-- VSTACK-META: \{.*?\} -->\n", "\n", content, count=1)
        instruction_file.write_text(legacy_content, encoding="utf-8")

        rc_verify = cli.verify(
            install_dir=install_dir,
            source=False,
            output=True,
            only=["instruction"],
        )
        assert rc_verify == 0

    def test_verify_rejects_legacy_artifact_without_vstack_meta_and_autogen(
        self, tmp_path: Path
    ) -> None:
        """Test that verify rejects legacy fallback when AUTO-GENERATED marker is missing."""
        install_dir = tmp_path / ".github"
        cli = CommandLineInterface(templates_root=TEMPLATES_ROOT)
        rc_install = cli.install(install_dir, only=["instruction"])
        assert rc_install == 0

        instruction_file = install_dir / "instructions" / "python.instructions.md"
        content = instruction_file.read_text(encoding="utf-8")
        no_meta = re.sub(r"\n<!-- VSTACK-META: \{.*?\} -->\n", "\n", content, count=1)
        no_autogen = re.sub(
            r"\n<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->\n",
            "\n",
            no_meta,
            count=1,
        )
        instruction_file.write_text(no_autogen, encoding="utf-8")

        rc_verify = cli.verify(
            install_dir=install_dir,
            source=False,
            output=True,
            only=["instruction"],
        )
        assert rc_verify == 1

    def test_verify_source_with_messages_path(self, tmp_path: Path) -> None:
        """Test that verify source with messages path."""

        class _Cfg:
            """Minimal generator config for this test."""

            type_name = "skill"
            output_subdir = "skills"

        class _FakeGen:
            """Test double for an artifact generator."""

            config = _Cfg()

            def verify_input(self, expected=None):
                """Verify input."""
                return ValidationResult(messages=[CheckMessage("pass", "ok")])

            def verify_output(self, out_dir, expected=None):
                """Verify output."""
                return ValidationResult(messages=[])

        cli = CommandLineInterface(templates_root=tmp_path)
        cli._generators = cast(Any, [_FakeGen()])
        rc = cli.verify(install_dir=tmp_path / ".github", source=True, output=False)
        assert rc == 0
