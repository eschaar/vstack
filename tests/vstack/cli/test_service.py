"""Tests for CommandService (the main CLI orchestration facade)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from vstack.cli.constants import EXPECTED_CANONICAL_NAMES
from vstack.cli.service import CommandService
from vstack.cli.verify import VerifyCommand
from vstack.constants import TEMPLATES_ROOT, VERSION
from vstack.manifest import ArtifactEntry, Manifest, content_hash
from vstack.models import CheckMessage, ValidationResult


class TestCommandService:
    """Test cases for CommandService."""

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    def test_validate_exits_zero_against_real_templates(self) -> None:
        """validate() returns 0 for the real templates root."""
        svc = CommandService(templates_root=TEMPLATES_ROOT)
        assert svc.validate() == 0

    def test_validate_exits_nonzero_for_empty_templates(self, tmp_path: Path) -> None:
        """validate() returns 1 when templates root is empty."""
        svc = CommandService(templates_root=tmp_path)
        assert svc.validate() == 1

    def test_label_prefers_relative(self, tmp_path: Path) -> None:
        """label() returns a path relative to templates_root when possible."""
        svc = CommandService(templates_root=tmp_path)
        path = tmp_path / "x" / "y"
        assert svc.label(path) == "x/y"

    def test_label_falls_back_to_absolute(self, tmp_path: Path) -> None:
        """label() returns the absolute string when path is outside templates_root."""
        svc = CommandService(templates_root=tmp_path)
        other = Path("/tmp/outside-path")
        assert svc.label(other) == str(other)

    def test_cli_class_uses_known_types(self) -> None:
        """Service generators cover the four known artifact families."""
        svc = CommandService(templates_root=TEMPLATES_ROOT)
        names = {g.config.type_name for g in svc.generators}
        assert names == {"skill", "agent", "instruction", "prompt"}

    def test_gen_for_returns_none_for_unknown_type(self) -> None:
        """gen_for() returns None for an unrecognized type name."""
        svc = CommandService(templates_root=TEMPLATES_ROOT)
        assert svc.gen_for("unknown") is None

    @pytest.mark.parametrize(
        ("method_name", "module_path", "class_name", "kwargs", "expected"),
        [
            ("validate", "vstack.cli.validate", "ValidateCommand", {"only": ["skill"]}, 10),
            (
                "install",
                "vstack.cli.install",
                "InstallCommand",
                {
                    "install_dir": Path("/tmp/install"),
                    "only": ["skill"],
                    "force": True,
                    "force_names": ["x"],
                    "adopt_names": ["y"],
                    "update": True,
                    "dry_run": True,
                },
                11,
            ),
            (
                "verify",
                "vstack.cli.verify",
                "VerifyCommand",
                {
                    "install_dir": Path("/tmp/install"),
                    "source": False,
                    "output": True,
                    "only": ["skill"],
                },
                12,
            ),
            (
                "status",
                "vstack.cli.status",
                "StatusCommand",
                {
                    "install_dir": Path("/tmp/install"),
                    "only": ["skill"],
                    "output_format": "json",
                    "verbose": True,
                    "no_color": True,
                },
                13,
            ),
            (
                "uninstall",
                "vstack.cli.uninstall",
                "UninstallCommand",
                {
                    "install_dir": Path("/tmp/install"),
                    "only": ["skill"],
                    "force": True,
                    "force_names": ["x"],
                },
                14,
            ),
        ],
    )
    def test_service_command_wrappers_forward_arguments(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        method_name: str,
        module_path: str,
        class_name: str,
        kwargs: dict[str, object],
        expected: int,
    ) -> None:
        """CommandService helper methods forward parameters to command execute methods."""
        captured: dict[str, Any] = {}

        def _fake_execute(*args, **call_kwargs):
            captured["args"] = args
            captured["kwargs"] = call_kwargs
            return expected

        monkeypatch.setattr(f"{module_path}.{class_name}.execute", staticmethod(_fake_execute))

        svc = CommandService(templates_root=tmp_path)
        result = getattr(svc, method_name)(**kwargs)

        assert result == expected
        assert captured["args"][0] is svc

    # ------------------------------------------------------------------
    # install
    # ------------------------------------------------------------------

    def test_install_only_skill_writes_skill_artifacts(self, tmp_path: Path) -> None:
        """install() with only=['skill'] writes skills subdirectory."""
        svc = CommandService(templates_root=TEMPLATES_ROOT)
        rc = svc.install(tmp_path / ".github", only=["skill"])
        assert rc == 0
        assert (tmp_path / ".github" / "skills").exists()

    def test_install_writes_expected_skill_count(self, tmp_path: Path) -> None:
        """install() writes the full set of canonical skill files."""
        svc = CommandService(templates_root=TEMPLATES_ROOT)
        rc = svc.install(tmp_path / ".github", only=["skill"])
        assert rc == 0
        md_files = list((tmp_path / ".github" / "skills").glob("*/SKILL.md"))
        assert len(md_files) == len(EXPECTED_CANONICAL_NAMES)

    def test_install_only_preserves_manifest_entries_for_other_types(self, tmp_path: Path) -> None:
        """install() with --only does not drop manifest entries from other artifact types."""
        install_dir = tmp_path / ".github"
        install_dir.mkdir(parents=True)
        manifest: dict[str, Any] = {
            "manifest_version": 2,
            "hash_algorithm": "sha256",
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

        svc = CommandService(templates_root=TEMPLATES_ROOT)
        rc = svc.install(install_dir, only=["instruction"])
        assert rc == 0

        updated: dict[str, Any] = json.loads(
            (install_dir / "vstack.json").read_text(encoding="utf-8")
        )
        assert "instructions" in updated["artifacts"]
        assert updated["artifacts"]["agents"] == manifest["artifacts"]["agents"]
        assert updated["artifacts"]["skills"] == manifest["artifacts"]["skills"]

    def test_install_update_skips_when_version_not_newer(self, tmp_path: Path) -> None:
        """install() update mode skips artifacts when the installed version is already higher."""
        install_dir = tmp_path / ".github"
        manifest = {
            "manifest_version": 2,
            "hash_algorithm": "sha256",
            "vstack_version": "0.1.0",
            "installed_at": "2026-01-01T00:00:00Z",
            "artifacts": {
                "skills": [
                    {
                        "name": "vision",
                        "file": "skills/vision/SKILL.md",
                        "version": "999.0.0",
                        "checksum": content_hash("old"),
                    }
                ]
            },
        }
        install_dir.mkdir(parents=True)
        (install_dir / "vstack.json").write_text(json.dumps(manifest), encoding="utf-8")
        (install_dir / "skills" / "vision").mkdir(parents=True)
        (install_dir / "skills" / "vision" / "SKILL.md").write_text("old", encoding="utf-8")

        svc = CommandService(templates_root=TEMPLATES_ROOT)
        rc = svc.install(install_dir, only=["skill"], update=True)
        assert rc == 0
        assert (install_dir / "skills" / "vision" / "SKILL.md").read_text(encoding="utf-8") == "old"

    def test_install_preserves_existing_unmanaged_file(self, tmp_path: Path) -> None:
        """install() does not overwrite a pre-existing unmanaged file."""
        install_dir = tmp_path / ".github"
        artifact_path = install_dir / "skills" / "vision" / "SKILL.md"
        artifact_path.parent.mkdir(parents=True)
        artifact_path.write_text("user content", encoding="utf-8")

        svc = CommandService(templates_root=TEMPLATES_ROOT)
        rc = svc.install(install_dir, only=["skill"])

        assert rc == 0
        assert artifact_path.read_text(encoding="utf-8") == "user content"
        manifest = json.loads((install_dir / "vstack.json").read_text(encoding="utf-8"))
        skill_entries = manifest["artifacts"]["skills"]
        assert all(entry["name"] != "vision" for entry in skill_entries)

    def test_install_adopt_name_tracks_existing_unmanaged_file(self, tmp_path: Path) -> None:
        """install() adopt_names tracks an unmanaged file without overwriting it."""
        install_dir = tmp_path / ".github"
        artifact_path = install_dir / "skills" / "vision" / "SKILL.md"
        artifact_path.parent.mkdir(parents=True)
        artifact_path.write_text("user content", encoding="utf-8")

        svc = CommandService(templates_root=TEMPLATES_ROOT)
        rc = svc.install(install_dir, only=["skill"], adopt_names=["vision"])

        assert rc == 0
        assert artifact_path.read_text(encoding="utf-8") == "user content"
        manifest = json.loads((install_dir / "vstack.json").read_text(encoding="utf-8"))
        vision = next(
            entry for entry in manifest["artifacts"]["skills"] if entry["name"] == "vision"
        )
        assert vision["checksum"] == content_hash("user content")
        assert vision["checksum_algorithm"] == "sha256"

    def test_install_force_name_overwrites_existing_unmanaged_file(self, tmp_path: Path) -> None:
        """install() force_names overwrites one unmanaged artifact."""
        install_dir = tmp_path / ".github"
        artifact_path = install_dir / "skills" / "vision" / "SKILL.md"
        artifact_path.parent.mkdir(parents=True)
        artifact_path.write_text("user content", encoding="utf-8")

        svc = CommandService(templates_root=TEMPLATES_ROOT)
        rc = svc.install(install_dir, only=["skill"], force_names=["vision"])

        assert rc == 0
        assert artifact_path.read_text(encoding="utf-8") != "user content"
        manifest = json.loads((install_dir / "vstack.json").read_text(encoding="utf-8"))
        vision = next(
            entry for entry in manifest["artifacts"]["skills"] if entry["name"] == "vision"
        )
        assert vision["checksum"] == content_hash(artifact_path.read_text(encoding="utf-8"))

    def test_install_update_preserves_locally_modified_tracked_file(self, tmp_path: Path) -> None:
        """install() update preserves a tracked artifact with local modifications."""
        install_dir = tmp_path / ".github"
        svc = CommandService(templates_root=TEMPLATES_ROOT)

        assert svc.install(install_dir, only=["skill"]) == 0

        artifact_path = install_dir / "skills" / "vision" / "SKILL.md"
        original = artifact_path.read_text(encoding="utf-8")
        artifact_path.write_text(original + "\nlocal edit\n", encoding="utf-8")

        manifest_before = json.loads((install_dir / "vstack.json").read_text(encoding="utf-8"))
        vision_before = next(
            entry for entry in manifest_before["artifacts"]["skills"] if entry["name"] == "vision"
        )

        assert svc.install(install_dir, only=["skill"], update=True) == 0
        assert artifact_path.read_text(encoding="utf-8").endswith("local edit\n")

        manifest_after = json.loads((install_dir / "vstack.json").read_text(encoding="utf-8"))
        vision_after = next(
            entry for entry in manifest_after["artifacts"]["skills"] if entry["name"] == "vision"
        )
        assert vision_after == vision_before

    def test_install_force_name_overwrites_locally_modified_tracked_file(
        self, tmp_path: Path
    ) -> None:
        """install() force_names overwrites a modified tracked artifact."""
        install_dir = tmp_path / ".github"
        svc = CommandService(templates_root=TEMPLATES_ROOT)

        assert svc.install(install_dir, only=["skill"]) == 0

        artifact_path = install_dir / "skills" / "vision" / "SKILL.md"
        original = artifact_path.read_text(encoding="utf-8")
        artifact_path.write_text(original + "\nlocal edit\n", encoding="utf-8")

        assert svc.install(install_dir, only=["skill"], force_names=["vision"]) == 0
        updated = artifact_path.read_text(encoding="utf-8")
        assert updated != original + "\nlocal edit\n"
        assert updated == next(
            a.content for a in cast(Any, svc.gen_for("skill")).render_all() if a.name == "vision"
        )

    def test_install_dry_run_does_not_write_outputs(self, tmp_path: Path) -> None:
        """install() dry_run=True produces no file system changes."""
        svc = CommandService(templates_root=TEMPLATES_ROOT)
        rc = svc.install(tmp_path / ".github", only=["skill"], dry_run=True)
        assert rc == 0
        assert not (tmp_path / ".github" / "skills").exists()

    def test_install_force_and_verify_input_fail_path(self, tmp_path: Path) -> None:
        """install() force=True still writes content but returns 1 when verify_input fails."""

        class _FakeArtifact:
            def __init__(self) -> None:
                self.name = "x"
                self.unresolved = ["BROKEN"]
                self.frontmatter = {"version": "1.0.0"}
                self.content = "content"

        class _Cfg:
            type_name = "skill"
            manifest_key = "skills"
            output_subdir = "skills"
            artifact_is_dir = True

        class _FakeGen:
            config = _Cfg()

            def render_all(self):
                return [_FakeArtifact()]

            def output_path(self, name: str) -> str:
                return f"{name}/SKILL.md"

            def install_relative_path(self, name: str) -> str:
                return f"skills/{name}/SKILL.md"

            def verify_input(self):
                return ValidationResult(messages=[CheckMessage("fail", "bad")])

        install_dir = tmp_path / ".github"
        out_file = install_dir / "skills" / "x" / "SKILL.md"
        out_file.parent.mkdir(parents=True)
        out_file.write_text("old", encoding="utf-8")

        svc = CommandService(templates_root=tmp_path)
        svc.generators = cast(Any, [_FakeGen()])
        rc = svc.install(install_dir, force=True)
        assert rc == 1
        assert out_file.read_text(encoding="utf-8") == "content"

    def test_install_existing_without_update_rewrites_clean_tracked_file(
        self, tmp_path: Path
    ) -> None:
        """Default install rewrites a tracked artifact when its checksum still matches."""
        install_dir = tmp_path / ".github"
        old_content = "old"
        manifest = {
            "manifest_version": 2,
            "hash_algorithm": "sha256",
            "vstack_version": "0.1.0",
            "installed_at": "2026-01-01T00:00:00Z",
            "artifacts": {
                "skills": [
                    {
                        "name": "vision",
                        "file": "skills/vision/SKILL.md",
                        "version": "1.0.0",
                        "checksum": content_hash(old_content),
                        "checksum_algorithm": "sha256",
                    }
                ]
            },
        }
        install_dir.mkdir(parents=True)
        (install_dir / "vstack.json").write_text(json.dumps(manifest), encoding="utf-8")
        (install_dir / "skills" / "vision").mkdir(parents=True)
        artifact_path = install_dir / "skills" / "vision" / "SKILL.md"
        artifact_path.write_text(old_content, encoding="utf-8")

        svc = CommandService(templates_root=TEMPLATES_ROOT)
        rc = svc.install(install_dir, only=["skill"], update=False)
        assert rc == 0
        assert artifact_path.read_text(encoding="utf-8") != old_content

    def test_install_existing_without_update_preserves_modified_tracked_file(
        self, tmp_path: Path
    ) -> None:
        """Default install preserves tracked files with local checksum drift."""
        install_dir = tmp_path / ".github"
        old_content = "old"
        manifest = {
            "manifest_version": 2,
            "hash_algorithm": "sha256",
            "vstack_version": "0.1.0",
            "installed_at": "2026-01-01T00:00:00Z",
            "artifacts": {
                "skills": [
                    {
                        "name": "vision",
                        "file": "skills/vision/SKILL.md",
                        "version": "1.0.0",
                        "checksum": content_hash(old_content),
                        "checksum_algorithm": "sha256",
                    }
                ]
            },
        }
        install_dir.mkdir(parents=True)
        (install_dir / "vstack.json").write_text(json.dumps(manifest), encoding="utf-8")
        (install_dir / "skills" / "vision").mkdir(parents=True)
        artifact_path = install_dir / "skills" / "vision" / "SKILL.md"
        artifact_path.write_text(old_content + "-local-edit", encoding="utf-8")

        svc = CommandService(templates_root=TEMPLATES_ROOT)
        rc = svc.install(install_dir, only=["skill"], update=False)
        assert rc == 0
        assert artifact_path.read_text(encoding="utf-8") == old_content + "-local-edit"

    def test_install_update_newer_version_writes_file(self, tmp_path: Path) -> None:
        """install() update mode writes new content when installed version is outdated."""
        install_dir = tmp_path / ".github"
        old_content = "old"
        manifest = {
            "manifest_version": 2,
            "hash_algorithm": "sha256",
            "vstack_version": "0.1.0",
            "installed_at": "2026-01-01T00:00:00Z",
            "artifacts": {
                "skills": [
                    {
                        "name": "vision",
                        "file": "skills/vision/SKILL.md",
                        "version": "0.0.1",
                        "checksum": content_hash(old_content),
                    }
                ]
            },
        }
        install_dir.mkdir(parents=True)
        (install_dir / "vstack.json").write_text(json.dumps(manifest), encoding="utf-8")
        (install_dir / "skills" / "vision").mkdir(parents=True)
        (install_dir / "skills" / "vision" / "SKILL.md").write_text(old_content, encoding="utf-8")

        svc = CommandService(templates_root=TEMPLATES_ROOT)
        rc = svc.install(install_dir, only=["skill"], update=True)
        assert rc == 0
        new_content = (install_dir / "skills" / "vision" / "SKILL.md").read_text(encoding="utf-8")
        assert new_content != old_content
        assert "AUTO-GENERATED" in new_content

    def test_install_preserves_skipped_artifact_when_footer_version_mismatches(
        self, tmp_path: Path
    ) -> None:
        """install() preserves a modified artifact that has a stale VSTACK-META footer."""
        install_dir = tmp_path / ".github"
        svc = CommandService(templates_root=TEMPLATES_ROOT)

        assert svc.install(install_dir, only=["skill"]) == 0

        artifact_path = install_dir / "skills" / "vision" / "SKILL.md"
        original = artifact_path.read_text(encoding="utf-8")
        tampered = re.sub(
            r'"vstack_version":"[^"]+"',
            '"vstack_version":"stale-version"',
            original,
            count=1,
        )
        artifact_path.write_text(tampered, encoding="utf-8")

        assert svc.install(install_dir, only=["skill"], update=False) == 0

        updated = artifact_path.read_text(encoding="utf-8")
        assert '"vstack_version":"stale-version"' in updated
        assert updated == tampered

    # ------------------------------------------------------------------
    # verify
    # ------------------------------------------------------------------

    def test_verify_output_requires_install_dir(self) -> None:
        """verify() with output=True and no install_dir returns 1."""
        svc = CommandService(templates_root=TEMPLATES_ROOT)
        assert svc.verify(install_dir=None, source=False, output=True) == 1

    def test_verify_fails_when_output_missing(self, tmp_path: Path) -> None:
        """verify() returns 1 when the output directory does not exist."""
        svc = CommandService(templates_root=TEMPLATES_ROOT)
        rc = svc.verify(install_dir=tmp_path / ".github", source=False, output=True)
        assert rc == 1

    def test_verify_source_with_no_messages_and_all_passed(self, tmp_path: Path) -> None:
        """verify() source=True returns 0 when all checks pass with no messages."""

        class _Cfg:
            type_name = "skill"
            output_subdir = "skills"

        class _FakeGen:
            config = _Cfg()

            def verify_input(self, expected=None):
                return ValidationResult(messages=[])

            def verify_output(self, out_dir, expected=None):
                return ValidationResult(messages=[])

        svc = CommandService(templates_root=tmp_path)
        svc.generators = cast(Any, [_FakeGen()])
        rc = svc.verify(install_dir=tmp_path / ".github", source=True, output=False)
        assert rc == 0

    def test_verify_source_with_messages_path(self, tmp_path: Path) -> None:
        """verify() source=True returns 0 for pass-level CheckMessage results."""

        class _Cfg:
            type_name = "skill"
            output_subdir = "skills"

        class _FakeGen:
            config = _Cfg()

            def verify_input(self, expected=None):
                return ValidationResult(messages=[CheckMessage("pass", "ok")])

            def verify_output(self, out_dir, expected=None):
                return ValidationResult(messages=[])

        svc = CommandService(templates_root=tmp_path)
        svc.generators = cast(Any, [_FakeGen()])
        rc = svc.verify(install_dir=tmp_path / ".github", source=True, output=False)
        assert rc == 0

    def test_verify_output_uses_manifest_names(self, tmp_path: Path) -> None:
        """verify() uses manifest-tracked names when verifying output artifacts."""
        install_dir = tmp_path / ".github"
        (install_dir / "skills" / "custom").mkdir(parents=True)
        (install_dir / "skills" / "custom" / "SKILL.md").write_text(
            "---\nname: custom\ndescription: 'd'\n---\nbody\n<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->\n",
            encoding="utf-8",
        )
        manifest = {
            "manifest_version": 2,
            "hash_algorithm": "sha256",
            "vstack_version": "0.1.0",
            "installed_at": "2026-01-01T00:00:00Z",
            "artifacts": {"skill": [{"name": "custom", "file": "skills/custom/SKILL.md"}]},
        }
        install_dir.mkdir(parents=True, exist_ok=True)
        (install_dir / "vstack.json").write_text(json.dumps(manifest), encoding="utf-8")

        svc = CommandService(templates_root=TEMPLATES_ROOT)
        rc = svc.verify(install_dir=install_dir, source=False, output=True)
        assert rc == 1

    def test_verify_fails_when_tracked_checksum_does_not_match(self, tmp_path: Path) -> None:
        """verify() returns 1 when a tracked instruction file has checksum drift."""
        install_dir = tmp_path / ".github"
        svc = CommandService(templates_root=TEMPLATES_ROOT)
        assert svc.install(install_dir, only=["instruction"]) == 0

        instruction_file = install_dir / "instructions" / "python.instructions.md"
        instruction_file.write_text(
            instruction_file.read_text(encoding="utf-8") + "\nlocal drift\n",
            encoding="utf-8",
        )

        assert (
            svc.verify(install_dir=install_dir, source=False, output=True, only=["instruction"])
            == 1
        )

    def test_verify_fails_on_vstack_meta_version_mismatch(self, tmp_path: Path) -> None:
        """verify() returns 1 when VSTACK-META footer version disagrees with manifest."""
        install_dir = tmp_path / ".github"
        svc = CommandService(templates_root=TEMPLATES_ROOT)
        assert svc.install(install_dir, only=["instruction"]) == 0

        instruction_file = install_dir / "instructions" / "python.instructions.md"
        content = instruction_file.read_text(encoding="utf-8")
        tampered = re.sub(
            r'"vstack_version":"[^"]+"',
            '"vstack_version":"tampered-version"',
            content,
            count=1,
        )
        instruction_file.write_text(tampered, encoding="utf-8")

        assert (
            svc.verify(install_dir=install_dir, source=False, output=True, only=["instruction"])
            == 1
        )

    def test_verify_fails_on_legacy_artifact_without_vstack_meta_when_checksum_changes(
        self, tmp_path: Path
    ) -> None:
        """verify() returns 1 when a legacy artifact no longer matches the manifest checksum."""
        install_dir = tmp_path / ".github"
        svc = CommandService(templates_root=TEMPLATES_ROOT)
        assert svc.install(install_dir, only=["instruction"]) == 0

        instruction_file = install_dir / "instructions" / "python.instructions.md"
        content = instruction_file.read_text(encoding="utf-8")
        legacy_content = re.sub(r"\n<!-- VSTACK-META: \{.*?\} -->\n", "\n", content, count=1)
        instruction_file.write_text(legacy_content, encoding="utf-8")

        assert (
            svc.verify(install_dir=install_dir, source=False, output=True, only=["instruction"])
            == 1
        )

    def test_verify_rejects_legacy_artifact_without_vstack_meta_and_autogen(
        self, tmp_path: Path
    ) -> None:
        """verify() rejects legacy fallback when AUTO-GENERATED marker is missing."""
        install_dir = tmp_path / ".github"
        svc = CommandService(templates_root=TEMPLATES_ROOT)
        assert svc.install(install_dir, only=["instruction"]) == 0

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

        assert (
            svc.verify(install_dir=install_dir, source=False, output=True, only=["instruction"])
            == 1
        )

    # ------------------------------------------------------------------
    # status
    # ------------------------------------------------------------------

    def test_status_requires_manifest(self, tmp_path: Path) -> None:
        """status() returns 1 when manifest is missing."""
        svc = CommandService(templates_root=TEMPLATES_ROOT)
        assert svc.status(tmp_path / ".github", only=["skill"]) == 1

    def test_status_fails_when_manifest_schema_is_legacy(self, tmp_path: Path) -> None:
        """status() returns 1 and prints guidance for a schema-v1 manifest."""
        install_dir = tmp_path / ".github"
        install_dir.mkdir(parents=True)
        (install_dir / "vstack.json").write_text(
            json.dumps(
                {
                    "vstack_version": "1.3.6",
                    "installed_at": "2026-01-01T00:00:00Z",
                    "artifacts": {},
                }
            ),
            encoding="utf-8",
        )

        svc = CommandService(templates_root=TEMPLATES_ROOT)
        assert svc.status(install_dir, only=["skill"]) == 1

    def test_status_fails_when_untracked_collision_exists(self, tmp_path: Path) -> None:
        """status() returns 1 when files at managed paths are not tracked in the manifest."""
        install_dir = tmp_path / ".github"
        artifact_path = install_dir / "skills" / "vision" / "SKILL.md"
        artifact_path.parent.mkdir(parents=True)
        artifact_path.write_text("user content", encoding="utf-8")
        (install_dir / "vstack.json").write_text(
            json.dumps(
                {
                    "manifest_version": 2,
                    "hash_algorithm": "sha256",
                    "vstack_version": VERSION,
                    "installed_at": "2026-01-01T00:00:00Z",
                    "artifacts": {},
                }
            ),
            encoding="utf-8",
        )

        svc = CommandService(templates_root=TEMPLATES_ROOT)
        assert svc.status(install_dir, only=["skill"]) == 1

    def test_status_json_output_contains_summary(self, tmp_path: Path, capsys: Any) -> None:
        """status() json output contains a summary object with issues/warnings/types_checked."""
        install_dir = tmp_path / ".github"
        svc = CommandService(templates_root=TEMPLATES_ROOT)
        assert svc.install(install_dir, only=["instruction"]) == 0
        capsys.readouterr()

        rc = svc.status(install_dir, only=["instruction"], output_format="json")
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["ok"] is True
        assert payload["summary"]["issues"] == 0
        assert payload["summary"]["warnings"] == 0
        assert payload["summary"]["types_checked"] == 1

    def test_status_legacy_entry_without_checksum_is_warning_not_failure(
        self, tmp_path: Path, capsys: Any
    ) -> None:
        """Legacy manifest entries without checksum produce warnings, not failures."""
        install_dir = tmp_path / ".github"
        instruction_file = install_dir / "instructions" / "python.instructions.md"
        instruction_file.parent.mkdir(parents=True)
        instruction_file.write_text("legacy content\n", encoding="utf-8")
        (install_dir / "vstack.json").write_text(
            json.dumps(
                {
                    "manifest_version": 2,
                    "hash_algorithm": "sha256",
                    "vstack_version": VERSION,
                    "installed_at": "2026-01-01T00:00:00Z",
                    "artifacts": {
                        "instructions": [
                            {
                                "name": "python",
                                "file": "instructions/python.instructions.md",
                                "version": "0.1.0",
                            }
                        ]
                    },
                }
            ),
            encoding="utf-8",
        )

        svc = CommandService(templates_root=TEMPLATES_ROOT)
        rc = svc.status(install_dir, only=["instruction"], output_format="json")
        assert rc == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["ok"] is True
        assert payload["summary"]["issues"] == 0
        assert payload["summary"]["warnings"] == 1
        counts = payload["types"][0]["counts"]
        assert counts["managed_legacy"] == 1

    def test_status_yaml_output_contains_summary(self, tmp_path: Path, capsys: Any) -> None:
        """status() yaml output contains summary keys."""
        install_dir = tmp_path / ".github"
        svc = CommandService(templates_root=TEMPLATES_ROOT)
        assert svc.install(install_dir, only=["instruction"]) == 0
        capsys.readouterr()

        rc = svc.status(install_dir, only=["instruction"], output_format="yaml")
        assert rc == 0
        out = capsys.readouterr().out
        assert "summary:" in out
        assert "issues: 0" in out
        assert "types_checked: 1" in out

    # ------------------------------------------------------------------
    # uninstall
    # ------------------------------------------------------------------

    def test_uninstall_removes_manifest_and_outputs(self, tmp_path: Path) -> None:
        """uninstall() removes the manifest and all tracked artifacts."""
        install_dir = tmp_path / ".github"
        svc = CommandService(templates_root=TEMPLATES_ROOT)
        assert svc.install(install_dir, only=["skill", "agent"]) == 0
        assert (install_dir / "vstack.json").exists()
        assert svc.uninstall(install_dir) == 0
        assert not (install_dir / "vstack.json").exists()

    def test_uninstall_without_manifest_and_without_files(self, tmp_path: Path) -> None:
        """uninstall() returns 0 when there is no manifest and no tracked files."""
        svc = CommandService(templates_root=TEMPLATES_ROOT)
        assert svc.uninstall(tmp_path / ".github") == 0

    def test_uninstall_non_directory_artifact_removes_file(self, tmp_path: Path) -> None:
        """uninstall() removes individual tracked files, not just directories."""
        install_dir = tmp_path / ".github"
        file_path = install_dir / "agents" / "custom.agent.md"
        file_path.parent.mkdir(parents=True)
        file_path.write_text("x", encoding="utf-8")
        manifest = {
            "manifest_version": 2,
            "hash_algorithm": "sha256",
            "vstack_version": "0.1.0",
            "installed_at": "2026-01-01T00:00:00Z",
            "artifacts": {
                "agents": [
                    {
                        "name": "custom",
                        "file": "agents/custom.agent.md",
                        "checksum": content_hash("x"),
                    }
                ]
            },
        }
        (install_dir / "vstack.json").write_text(json.dumps(manifest), encoding="utf-8")

        svc = CommandService(templates_root=TEMPLATES_ROOT)
        assert svc.uninstall(install_dir) == 0
        assert not file_path.exists()

    def test_uninstall_preserves_locally_modified_tracked_file(self, tmp_path: Path) -> None:
        """uninstall() preserves a modified tracked file by default."""
        install_dir = tmp_path / ".github"
        svc = CommandService(templates_root=TEMPLATES_ROOT)
        assert svc.install(install_dir, only=["instruction"]) == 0

        instruction_file = install_dir / "instructions" / "python.instructions.md"
        original = instruction_file.read_text(encoding="utf-8")
        instruction_file.write_text(original + "\nlocal drift\n", encoding="utf-8")

        assert svc.uninstall(install_dir, only=["instruction"]) == 0
        assert instruction_file.exists()
        manifest_after = json.loads((install_dir / "vstack.json").read_text(encoding="utf-8"))
        assert manifest_after["artifacts"].get("instructions")

    def test_uninstall_force_name_removes_locally_modified_tracked_file(
        self, tmp_path: Path
    ) -> None:
        """uninstall() force_names removes one modified tracked file."""
        install_dir = tmp_path / ".github"
        svc = CommandService(templates_root=TEMPLATES_ROOT)
        assert svc.install(install_dir, only=["instruction"]) == 0

        instruction_file = install_dir / "instructions" / "python.instructions.md"
        original = instruction_file.read_text(encoding="utf-8")
        instruction_file.write_text(original + "\nlocal drift\n", encoding="utf-8")

        assert svc.uninstall(install_dir, only=["instruction"], force_names=["python"]) == 0
        assert not instruction_file.exists()

    # ------------------------------------------------------------------
    # validate
    # ------------------------------------------------------------------

    def test_validate_returns_non_zero_on_unresolved(self, tmp_path: Path) -> None:
        """validate() returns 1 when a rendered artifact has unresolved placeholders."""

        class _FakeArtifact:
            def __init__(self) -> None:
                self.name = "a"
                self.unresolved = ["MISSING"]

        class _Cfg:
            type_name = "skill"
            manifest_key = "skills"
            output_subdir = "skills"

        class _FakeGen:
            config = _Cfg()

            def render_all(self):
                return [_FakeArtifact()]

            def load_partials(self):
                return {"X": "y"}

            def output_path(self, name: str) -> str:
                return f"{name}/SKILL.md"

        svc = CommandService(templates_root=tmp_path)
        svc.generators = cast(Any, [_FakeGen()])
        assert svc.validate() == 1

    def test_validate_returns_zero_when_all_clean(self, tmp_path: Path) -> None:
        """validate() returns 0 when all rendered artifacts have no unresolved placeholders."""

        class _FakeArtifact:
            def __init__(self) -> None:
                self.name = "a"
                self.unresolved: list[str] = []

        class _Cfg:
            type_name = "skill"
            manifest_key = "skills"
            output_subdir = "skills"

        class _FakeGen:
            config = _Cfg()

            def render_all(self):
                return [_FakeArtifact()]

            def load_partials(self):
                return {"X": "y"}

            def output_path(self, name: str) -> str:
                return f"{name}/SKILL.md"

        svc = CommandService(templates_root=tmp_path)
        svc.generators = cast(Any, [_FakeGen()])
        assert svc.validate() == 0

    def test_validate_handles_missing_generator_for_type(self, tmp_path: Path) -> None:
        """validate() returns 0 when gen_for returns None for an artifact type."""

        class _FakeArtifact:
            def __init__(self) -> None:
                self.name = "a"
                self.unresolved: list[str] = []

        class _Cfg:
            type_name = "skill"

        class _FakeGen:
            config = _Cfg()

            def render_all(self):
                return [_FakeArtifact()]

            def load_partials(self):
                return {}

            def output_path(self, name: str) -> str:
                return f"{name}/SKILL.md"

        svc = CommandService(templates_root=tmp_path)
        svc.generators = cast(Any, [_FakeGen()])
        setattr(svc, "gen_for", lambda _type_name: None)
        assert svc.validate() == 0

    # ------------------------------------------------------------------
    # manifest helpers
    # ------------------------------------------------------------------

    def test_manifest_upgrade_returns_error_when_read_has_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """manifest_upgrade prints and returns non-zero when manifest read fails."""

        class _ManifestFile:
            path = tmp_path / "vstack.json"
            read_error = "invalid manifest"

            def read(self, *, allow_legacy: bool = False):
                assert allow_legacy is True
                return None

        svc = CommandService(templates_root=tmp_path)
        monkeypatch.setattr(svc, "manifest_for", lambda _install_dir: _ManifestFile())

        assert svc.manifest_upgrade(tmp_path) == 1
        assert "ERROR: invalid manifest" in capsys.readouterr().err

    def test_manifest_upgrade_returns_error_when_manifest_missing(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """manifest_upgrade returns non-zero when no manifest exists."""

        class _ManifestFile:
            path = tmp_path / "vstack.json"
            read_error = None

            def read(self, *, allow_legacy: bool = False):
                assert allow_legacy is True
                return None

        svc = CommandService(templates_root=tmp_path)
        monkeypatch.setattr(svc, "manifest_for", lambda _install_dir: _ManifestFile())

        assert svc.manifest_upgrade(tmp_path) == 1
        assert "No manifest found to upgrade." in capsys.readouterr().out

    def test_manifest_upgrade_noop_when_current_schema(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """manifest_upgrade short-circuits when schema is already current."""

        class _Manifest:
            manifest_version = 2

            def needs_upgrade(self) -> bool:
                return False

        class _ManifestFile:
            path = tmp_path / "vstack.json"
            read_error = None

            def read(self, *, allow_legacy: bool = False):
                assert allow_legacy is True
                return _Manifest()

        svc = CommandService(templates_root=tmp_path)
        monkeypatch.setattr(svc, "manifest_for", lambda _install_dir: _ManifestFile())

        assert svc.manifest_upgrade(tmp_path) == 0
        assert "Manifest already up to date" in capsys.readouterr().out

    def test_manifest_upgrade_backfill_runs_on_current_schema_unit(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """manifest_upgrade backfills and writes even when schema is already current."""

        class _Manifest:
            manifest_version = 2

            def needs_upgrade(self) -> bool:
                return False

            def with_backfilled_checksums(self, *, install_dir: Path):
                assert install_dir == tmp_path
                return self, ["skills:vision"], ["skills:verify (missing file)"]

        class _ManifestFile:
            path = tmp_path / "vstack.json"
            read_error = None
            written = None

            def read(self, *, allow_legacy: bool = False):
                assert allow_legacy is True
                return _Manifest()

            def write(self, manifest: object) -> None:
                self.written = manifest

        mf = _ManifestFile()
        svc = CommandService(templates_root=tmp_path)
        monkeypatch.setattr(svc, "manifest_for", lambda _install_dir: mf)

        assert svc.manifest_upgrade(tmp_path, backfill=True) == 0
        out = capsys.readouterr().out
        assert "schema already current" in out
        assert "Backfilled checksums for 1 tracked artifact(s); skipped 1." in out
        assert "skills:verify (missing file)" in out
        assert mf.written is not None

    def test_manifest_upgrade_writes_upgraded_manifest_unit(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """manifest_upgrade persists the upgraded manifest and returns success."""

        class _Manifest:
            manifest_version = 1

            def needs_upgrade(self) -> bool:
                return True

            def upgraded(self) -> object:
                return {"upgraded": True}

        class _ManifestFile:
            path = tmp_path / "vstack.json"
            read_error = None
            written: object | None = None

            def read(self, *, allow_legacy: bool = False):
                assert allow_legacy is True
                return _Manifest()

            def write(self, manifest: object) -> None:
                self.written = manifest

        mf = _ManifestFile()
        svc = CommandService(templates_root=tmp_path)
        monkeypatch.setattr(svc, "manifest_for", lambda _install_dir: mf)

        assert svc.manifest_upgrade(tmp_path) == 0
        assert mf.written == {"upgraded": True}
        assert "Upgraded manifest to schema" in capsys.readouterr().out

    def test_manifest_upgrade_migrates_legacy_schema(self, tmp_path: Path) -> None:
        """manifest_upgrade() migrates schema-v1 manifest to current schema."""
        install_dir = tmp_path / ".github"
        install_dir.mkdir(parents=True)
        (install_dir / "vstack.json").write_text(
            json.dumps(
                {
                    "vstack_version": "1.3.6",
                    "installed_at": "2026-01-01T00:00:00Z",
                    "artifacts": {},
                }
            ),
            encoding="utf-8",
        )

        svc = CommandService(templates_root=TEMPLATES_ROOT)
        assert svc.manifest_upgrade(install_dir) == 0

        upgraded = json.loads((install_dir / "vstack.json").read_text(encoding="utf-8"))
        assert upgraded["manifest_version"] == 2
        assert upgraded["hash_algorithm"] == "sha256"

    def test_manifest_upgrade_backfill_adds_checksum_for_footer_tagged_legacy_entry(
        self,
        tmp_path: Path,
    ) -> None:
        """manifest_upgrade(backfill=True) stores checksum for VSTACK-META-tagged entries."""
        install_dir = tmp_path / ".github"
        install_dir.mkdir(parents=True)

        artifact_rel = "skills/vision/SKILL.md"
        artifact_path = install_dir / artifact_rel
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(
            '# Vision\n\n<!-- VSTACK-META: {"artifact_name":"vision"} -->\n',
            encoding="utf-8",
        )

        (install_dir / "vstack.json").write_text(
            json.dumps(
                {
                    "manifest_version": 2,
                    "hash_algorithm": "sha256",
                    "vstack_version": "1.3.6",
                    "installed_at": "2026-01-01T00:00:00Z",
                    "artifacts": {
                        "skills": [
                            {
                                "name": "vision",
                                "file": artifact_rel,
                                "version": "1.0.0",
                            }
                        ]
                    },
                }
            ),
            encoding="utf-8",
        )

        svc = CommandService(templates_root=TEMPLATES_ROOT)
        assert svc.manifest_upgrade(install_dir, backfill=True) == 0

        upgraded = json.loads((install_dir / "vstack.json").read_text(encoding="utf-8"))
        entry = upgraded["artifacts"]["skills"][0]
        assert entry["checksum_algorithm"] == "sha256"
        assert isinstance(entry["checksum"], str)
        assert len(entry["checksum"]) == 64

    # ------------------------------------------------------------------
    # artifact_control_state
    # ------------------------------------------------------------------

    def test_artifact_control_state_reports_missing_tracked_file(self, tmp_path: Path) -> None:
        """Tracked entries missing on disk are reported as 'missing'."""
        svc = CommandService(templates_root=tmp_path)
        entry = SimpleNamespace(checksum="abc", checksum_algorithm="sha256")
        state, message = svc.artifact_control_state(
            out_file=tmp_path / "missing.txt",
            existing_entry=entry,
        )
        assert state == "missing"
        assert "tracked file missing from disk" in message

    def test_artifact_control_state_reports_unknown_algorithm(self, tmp_path: Path) -> None:
        """Unsupported checksum algorithm returns 'unknown' state."""
        svc = CommandService(templates_root=tmp_path)
        out_file = tmp_path / "artifact.txt"
        out_file.write_text("data", encoding="utf-8")
        entry = SimpleNamespace(checksum="abc", checksum_algorithm="sha999")
        state, message = svc.artifact_control_state(out_file=out_file, existing_entry=entry)
        assert state == "unknown"
        assert "unsupported checksum algorithm" in message

    def test_artifact_control_state_reports_read_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """I/O read errors while hashing map to 'unknown' state."""
        svc = CommandService(templates_root=tmp_path)
        out_file = tmp_path / "artifact.txt"
        out_file.write_text("data", encoding="utf-8")
        entry = SimpleNamespace(checksum="abc", checksum_algorithm="sha256")

        def _raise_oserror(self: Path, encoding: str = "utf-8") -> str:
            del self, encoding
            raise OSError("boom")

        monkeypatch.setattr(Path, "read_text", _raise_oserror)
        state, message = svc.artifact_control_state(out_file=out_file, existing_entry=entry)
        assert state == "unknown"
        assert "could not read file" in message

    def test_artifact_control_state_managed_returns_managed(self, tmp_path: Path) -> None:
        """artifact_control_state returns 'managed' for a clean tracked artifact."""
        install_dir = tmp_path / ".github"
        svc = CommandService(templates_root=TEMPLATES_ROOT)
        assert svc.install(install_dir, only=["instruction"]) == 0

        instruction_file = install_dir / "instructions" / "python.instructions.md"
        expected_hash = content_hash(instruction_file.read_text(encoding="utf-8"))

        entry = ArtifactEntry(
            name="python",
            file="instructions/python.instructions.md",
            checksum=expected_hash,
            checksum_algorithm="sha256",
        )
        state, _message = svc.artifact_control_state(
            out_file=instruction_file, existing_entry=entry
        )
        assert state == "managed"

    def test_artifact_control_state_modified_returns_modified(self, tmp_path: Path) -> None:
        """artifact_control_state returns 'modified' when file content drifts from checksum."""
        install_dir = tmp_path / ".github"
        svc = CommandService(templates_root=TEMPLATES_ROOT)
        assert svc.install(install_dir, only=["instruction"]) == 0

        instruction_file = install_dir / "instructions" / "python.instructions.md"
        entry = ArtifactEntry(
            name="python",
            file="instructions/python.instructions.md",
            checksum=content_hash("different"),
            checksum_algorithm="sha256",
        )
        state, _message = svc.artifact_control_state(
            out_file=instruction_file, existing_entry=entry
        )
        assert state == "modified"

    def test_artifact_control_state_absent_returns_missing(self, tmp_path: Path) -> None:
        """artifact_control_state returns 'missing' when a tracked file is not on disk."""
        svc = CommandService(templates_root=TEMPLATES_ROOT)
        entry = ArtifactEntry(
            name="ghost",
            file="skills/ghost/SKILL.md",
            checksum=content_hash("x"),
            checksum_algorithm="sha256",
        )
        state, _message = svc.artifact_control_state(
            out_file=tmp_path / ".github" / "skills" / "ghost" / "SKILL.md",
            existing_entry=entry,
        )
        assert state == "missing"

    # ------------------------------------------------------------------
    # verify (VerifyCommand helpers)
    # ------------------------------------------------------------------

    def test_expected_output_names_falls_back_without_manifest(self) -> None:
        """VerifyCommand._expected_output_names falls back to canonical list when manifest is absent."""
        svc = CommandService(templates_root=TEMPLATES_ROOT)
        gen = svc.gen_for("skill")
        assert gen is not None
        assert VerifyCommand._expected_output_names(gen, None) == EXPECTED_CANONICAL_NAMES

    def test_verify_manifest_metadata_skips_missing_artifact_files(self, tmp_path: Path) -> None:
        """VerifyCommand._verify_manifest_metadata returns None for manifest-only absent files."""
        svc = CommandService(templates_root=TEMPLATES_ROOT)
        gen = svc.gen_for("skill")
        assert gen is not None

        manifest_data = Manifest(
            vstack_version=VERSION,
            installed_at="2026-01-01T00:00:00Z",
            artifacts={
                "skills": [
                    ArtifactEntry(
                        name="missing-skill",
                        file="skills/missing-skill/SKILL.md",
                        version="1.0.0",
                    )
                ]
            },
        )

        result = VerifyCommand._verify_manifest_metadata(
            svc, gen, manifest_data, tmp_path / ".github"
        )
        assert result is None
