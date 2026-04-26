"""End-to-end integration tests for the vstack CLI."""

from __future__ import annotations

import json
from pathlib import Path

from tests.conftest import run_vstack


class TestRuntimeEntry:
    """Test cases for RuntimeEntry."""

    def test_help_command_exits_zero(self) -> None:
        """Test that help command exits zero."""
        result = run_vstack(["--help"])
        assert result.returncode == 0
        assert "Manage vstack skill generation" in result.stdout


class TestIntegrationVstack:
    """End-to-end subprocess tests for installed vstack CLI behavior."""

    def test_verify_exits_zero(self) -> None:
        """vstack verify --no-output exits zero against the real templates."""
        result = run_vstack(["verify", "--no-output"])
        assert result.returncode == 0, (
            f"vstack verify --no-output failed:\n{result.stdout}\n{result.stderr}"
        )

    def test_verify_output_exits_zero(self, installed_target: Path) -> None:
        """vstack verify --no-source exits zero against a freshly installed target."""
        result = run_vstack(["verify", "--no-source", "--target", str(installed_target)])
        assert result.returncode == 0, (
            f"vstack verify --no-source failed:\n{result.stdout}\n{result.stderr}"
        )

    def test_manifest_verify_output_exits_zero(self, installed_target: Path) -> None:
        """vstack manifest verify exits zero for a clean installed target."""
        result = run_vstack(["manifest", "verify", "--target", str(installed_target)])
        assert result.returncode == 0, (
            f"vstack manifest verify failed:\n{result.stdout}\n{result.stderr}"
        )

    def test_manifest_status_output_exits_zero(self, installed_target: Path) -> None:
        """vstack manifest status exits zero for a clean installed target."""
        result = run_vstack(["manifest", "status", "--target", str(installed_target)])
        assert result.returncode == 0, (
            f"vstack manifest status failed:\n{result.stdout}\n{result.stderr}"
        )

    def test_verify_only_filter_limits_checked_types(self, installed_target: Path) -> None:
        """vstack verify --only skill exits zero for a clean installed target."""
        result = run_vstack(
            ["verify", "--no-source", "--target", str(installed_target), "--only", "skill"]
        )
        assert result.returncode == 0, (
            f"vstack verify --only skill failed:\n{result.stdout}\n{result.stderr}"
        )

    def test_install_and_verify_exits_zero(self, tmp_path: Path) -> None:
        """Fresh install followed by verify exits zero."""
        install = run_vstack(["install", "--target", str(tmp_path)])
        assert install.returncode == 0, (
            f"vstack install failed:\n{install.stdout}\n{install.stderr}"
        )
        verify = run_vstack(["verify", "--target", str(tmp_path)])
        assert verify.returncode == 0, f"vstack verify failed:\n{verify.stdout}\n{verify.stderr}"

    def test_manifest_upgrade_migrates_legacy_schema(self, tmp_path: Path) -> None:
        """vstack manifest upgrade migrates schema-v1 manifest to current schema."""
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

        upgrade = run_vstack(["manifest", "upgrade", "--target", str(tmp_path)])
        assert upgrade.returncode == 0, (
            f"vstack manifest upgrade failed:\n{upgrade.stdout}\n{upgrade.stderr}"
        )

        upgraded = json.loads((install_dir / "vstack.json").read_text(encoding="utf-8"))
        assert upgraded["manifest_version"] == 2
        assert upgraded["hash_algorithm"] == "sha256"

    def test_manifest_upgrade_backfill_adds_checksum_for_footer_tagged_legacy_entry(
        self,
        tmp_path: Path,
    ) -> None:
        """vstack manifest upgrade --backfill stores checksum for VSTACK-META-tagged entries."""
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

        upgrade = run_vstack(["manifest", "upgrade", "--backfill", "--target", str(tmp_path)])
        assert upgrade.returncode == 0, (
            f"vstack manifest upgrade --backfill failed:\n{upgrade.stdout}\n{upgrade.stderr}"
        )

        upgraded = json.loads((install_dir / "vstack.json").read_text(encoding="utf-8"))
        entry = upgraded["artifacts"]["skills"][0]
        assert entry["checksum_algorithm"] == "sha256"
        assert isinstance(entry["checksum"], str)
        assert len(entry["checksum"]) == 64
