"""Tests for manifest store model, serialization, and file operations."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from vstack.cli.constants import EXPECTED_CANONICAL_NAMES
from vstack.manifest import (
    CURRENT_HASH_ALGORITHM,
    CURRENT_MANIFEST_VERSION,
    ArtifactEntry,
    Manifest,
    ManifestFile,
    hash_with_algorithm,
)


class TestArtifactEntry:
    """Test cases for ArtifactEntry."""

    def test_artifact_entry_fields(self) -> None:
        """Test that artifact entry fields."""
        e = ArtifactEntry(
            name="vision",
            file="skills/vision/SKILL.md",
            version="1.0.0",
            checksum="abc123",
            checksum_algorithm="sha256",
        )
        assert e.name == "vision"
        assert e.file.endswith("SKILL.md")
        assert e.checksum == "abc123"
        assert e.checksum_algorithm == "sha256"


class TestChecksumHelpers:
    """Test cases for checksum helper functions."""

    def test_hash_with_algorithm_supports_md5(self) -> None:
        """Test that md5 remains supported for legacy manifest compatibility."""
        digest = hash_with_algorithm("hello", "md5")
        assert len(digest) == 32

    def test_hash_with_algorithm_rejects_unknown_algorithm(self) -> None:
        """Test that unknown algorithms raise a clear ValueError."""
        with pytest.raises(ValueError, match="Unsupported checksum algorithm"):
            hash_with_algorithm("hello", "sha999")


class TestManifest:
    """Test cases for Manifest."""

    def test_entries_names_files_for(self) -> None:
        """Test that entries names files for."""
        m = Manifest(
            vstack_version="0.1.0",
            installed_at="2026-01-01T00:00:00Z",
            artifacts={"skills": [ArtifactEntry(name="vision", file="skills/vision/SKILL.md")]},
        )
        assert len(m.entries_for("skills")) == 1
        assert m.names_for("skills") == ["vision"]
        assert m.files_for("skills") == ["skills/vision/SKILL.md"]

    def test_to_dict_and_from_dict_roundtrip(self) -> None:
        """Test that to dict and from dict roundtrip."""
        src = Manifest(
            vstack_version="0.1.0",
            installed_at="2026-01-01T00:00:00Z",
            artifacts={
                "skills": [
                    ArtifactEntry(
                        name="vision",
                        file="skills/vision/SKILL.md",
                        checksum="hash-1",
                    )
                ]
            },
        )
        out = Manifest.from_dict(src.to_dict())
        assert out.vstack_version == "0.1.0"
        assert out.manifest_version == 2
        assert out.hash_algorithm == "sha256"
        assert out.names_for("skills") == ["vision"]
        assert out.entries_for("skills")[0].checksum == "hash-1"
        assert out.entries_for("skills")[0].checksum_algorithm == "sha256"

    def test_from_dict_accepts_legacy_content_hash_field(self) -> None:
        """Test that legacy content_hash manifests are still readable."""
        manifest = Manifest.from_dict(
            {
                "vstack_version": "0.1.0",
                "installed_at": "2026-01-01T00:00:00Z",
                "artifacts": {
                    "skills": [
                        {
                            "name": "vision",
                            "file": "skills/vision/SKILL.md",
                            "content_hash": "legacy-hash",
                        }
                    ]
                },
            }
        )
        assert manifest.entries_for("skills")[0].checksum == "legacy-hash"
        assert manifest.entries_for("skills")[0].checksum_algorithm is None

    def test_from_dict_accepts_unknown_manifest_fields(self) -> None:
        """Test that unknown manifest-level fields are ignored safely."""
        manifest = Manifest.from_dict(
            {
                "manifest_version": 2,
                "hash_algorithm": "sha256",
                "vstack_version": "0.1.0",
                "installed_at": "2026-01-01T00:00:00Z",
                "extra": {"future": True},
                "artifacts": {
                    "skills": [
                        {
                            "name": "vision",
                            "file": "skills/vision/SKILL.md",
                            "unknown": "x",
                        }
                    ]
                },
            }
        )
        assert manifest.names_for("skills") == ["vision"]

    def test_needs_upgrade_true_for_legacy_schema(self) -> None:
        """Test that schema v1 manifests are marked as upgrade candidates."""
        legacy = Manifest.from_dict(
            {
                "vstack_version": "0.1.0",
                "installed_at": "2026-01-01T00:00:00Z",
                "artifacts": {
                    "skills": [
                        {
                            "name": "vision",
                            "file": "skills/vision/SKILL.md",
                            "content_hash": "a" * 32,
                        }
                    ]
                },
            }
        )
        assert legacy.needs_upgrade() is True

    def test_upgraded_normalizes_manifest_metadata(self) -> None:
        """Test that upgraded converts legacy metadata to current schema values."""
        legacy = Manifest.from_dict(
            {
                "manifest_version": 1,
                "hash_algorithm": "md5",
                "vstack_version": "0.1.0",
                "installed_at": "2026-01-01T00:00:00Z",
                "artifacts": {
                    "skills": [
                        {
                            "name": "vision",
                            "file": "skills/vision/SKILL.md",
                            "checksum": "a" * 64,
                        }
                    ]
                },
            }
        )

        upgraded = legacy.upgraded()
        assert upgraded.manifest_version == CURRENT_MANIFEST_VERSION
        assert upgraded.hash_algorithm == CURRENT_HASH_ALGORITHM
        assert upgraded.entries_for("skills")[0].checksum_algorithm == "sha256"

    def test_upgraded_is_idempotent(self) -> None:
        """Test that upgrading twice results in the same serialized manifest."""
        manifest = Manifest.from_dict(
            {
                "manifest_version": 1,
                "vstack_version": "0.1.0",
                "installed_at": "2026-01-01T00:00:00Z",
                "artifacts": {
                    "skills": [
                        {
                            "name": "vision",
                            "file": "skills/vision/SKILL.md",
                            "content_hash": "legacy-hash",
                        }
                    ]
                },
            }
        )

        once = manifest.upgraded()
        twice = once.upgraded()
        assert once.to_dict() == twice.to_dict()

    def test_with_backfilled_checksums_updates_footer_tagged_legacy_entry(
        self,
        tmp_path,
    ) -> None:
        """Backfill should add checksum metadata when footer-tagged file exists."""
        install_dir = tmp_path / ".github"
        artifact_rel = "skills/vision/SKILL.md"
        artifact_path = install_dir / artifact_rel
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(
            '# Vision\n<!-- VSTACK-META: {"artifact_name":"vision"} -->\n',
            encoding="utf-8",
        )

        manifest = Manifest(
            vstack_version="1.3.6",
            installed_at="2026-01-01T00:00:00Z",
            artifacts={
                "skills": [
                    ArtifactEntry(
                        name="vision",
                        file=artifact_rel,
                        version="1.0.0",
                    )
                ]
            },
        )

        updated, backfilled, skipped = manifest.with_backfilled_checksums(install_dir=install_dir)
        entry = updated.entries_for("skills")[0]
        assert entry.checksum_algorithm == "sha256"
        assert entry.checksum is not None
        assert backfilled == ["skills:vision"]
        assert skipped == []

    def test_with_backfilled_checksums_skips_entry_without_footer(self, tmp_path) -> None:
        """Backfill should skip legacy entries when VSTACK-META footer is missing."""
        install_dir = tmp_path / ".github"
        artifact_rel = "skills/vision/SKILL.md"
        artifact_path = install_dir / artifact_rel
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text("# user-managed content\n", encoding="utf-8")

        manifest = Manifest(
            vstack_version="1.3.6",
            installed_at="2026-01-01T00:00:00Z",
            artifacts={
                "skills": [
                    ArtifactEntry(
                        name="vision",
                        file=artifact_rel,
                        version="1.0.0",
                    )
                ]
            },
        )

        updated, backfilled, skipped = manifest.with_backfilled_checksums(install_dir=install_dir)
        entry = updated.entries_for("skills")[0]
        assert entry.checksum is None
        assert backfilled == []
        assert skipped == ["skills:vision (missing VSTACK-META footer)"]

    def test_with_backfilled_checksums_keeps_entries_with_existing_checksum(self, tmp_path) -> None:
        """Backfill should keep entries that already have checksum metadata untouched."""
        manifest = Manifest(
            vstack_version="1.3.6",
            installed_at="2026-01-01T00:00:00Z",
            artifacts={
                "skills": [
                    ArtifactEntry(
                        name="vision",
                        file="skills/vision/SKILL.md",
                        version="1.0.0",
                        checksum="abc",
                        checksum_algorithm="sha256",
                    )
                ]
            },
        )

        updated, backfilled, skipped = manifest.with_backfilled_checksums(
            install_dir=tmp_path / ".github"
        )
        entry = updated.entries_for("skills")[0]
        assert entry.checksum == "abc"
        assert entry.checksum_algorithm == "sha256"
        assert backfilled == []
        assert skipped == []

    def test_with_backfilled_checksums_skips_missing_files(self, tmp_path) -> None:
        """Backfill should skip legacy entries when the tracked file is missing."""
        manifest = Manifest(
            vstack_version="1.3.6",
            installed_at="2026-01-01T00:00:00Z",
            artifacts={
                "skills": [
                    ArtifactEntry(
                        name="vision",
                        file="skills/vision/SKILL.md",
                        version="1.0.0",
                    )
                ]
            },
        )

        updated, backfilled, skipped = manifest.with_backfilled_checksums(
            install_dir=tmp_path / ".github"
        )
        assert updated.entries_for("skills")[0].checksum is None
        assert backfilled == []
        assert skipped == ["skills:vision (missing file)"]

    def test_with_backfilled_checksums_skips_unreadable_files(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path,
    ) -> None:
        """Backfill should skip entries when file reads raise OSError."""
        install_dir = tmp_path / ".github"
        artifact_rel = "skills/vision/SKILL.md"
        artifact_path = install_dir / artifact_rel
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text("# Vision\n", encoding="utf-8")

        original_read_text = Path.read_text

        def _raise_for_target(self: Path, *args, **kwargs):
            if self == artifact_path:
                raise OSError("boom")
            return original_read_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", _raise_for_target)

        manifest = Manifest(
            vstack_version="1.3.6",
            installed_at="2026-01-01T00:00:00Z",
            artifacts={
                "skills": [
                    ArtifactEntry(
                        name="vision",
                        file=artifact_rel,
                        version="1.0.0",
                    )
                ]
            },
        )

        updated, backfilled, skipped = manifest.with_backfilled_checksums(install_dir=install_dir)
        assert updated.entries_for("skills")[0].checksum is None
        assert backfilled == []
        assert skipped == ["skills:vision (unreadable file)"]

    def test_with_backfilled_checksums_falls_back_to_sha256_for_unknown_algorithm(
        self,
        tmp_path,
    ) -> None:
        """Backfill should fall back to sha256 when manifest hash_algorithm is unsupported."""
        install_dir = tmp_path / ".github"
        artifact_rel = "skills/vision/SKILL.md"
        artifact_path = install_dir / artifact_rel
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(
            '# Vision\n<!-- VSTACK-META: {"artifact_name":"vision"} -->\n',
            encoding="utf-8",
        )

        manifest = Manifest(
            vstack_version="1.3.6",
            installed_at="2026-01-01T00:00:00Z",
            hash_algorithm="sha999",
            artifacts={
                "skills": [
                    ArtifactEntry(
                        name="vision",
                        file=artifact_rel,
                        version="1.0.0",
                    )
                ]
            },
        )

        updated, backfilled, skipped = manifest.with_backfilled_checksums(install_dir=install_dir)
        entry = updated.entries_for("skills")[0]
        assert entry.checksum_algorithm == "sha256"
        assert entry.checksum is not None
        assert backfilled == ["skills:vision"]
        assert skipped == []

    def test_from_dict_parses_manifest_entries_with_checksum_algorithm(self) -> None:
        """Test that from_dict builds ArtifactEntry fields for modern manifest entries."""
        manifest = Manifest.from_dict(
            {
                "manifest_version": 2,
                "hash_algorithm": "sha256",
                "vstack_version": "1.0.0",
                "installed_at": "2026-01-01T00:00:00Z",
                "artifacts": {
                    "skills": [
                        {
                            "name": "verify",
                            "file": "skills/verify/SKILL.md",
                            "version": "1.0.0",
                            "checksum": "a" * 64,
                            "checksum_algorithm": "sha256",
                        }
                    ]
                },
            }
        )
        entries = manifest.entries_for("skills")
        assert len(entries) == 1
        assert entries[0].name == "verify"
        assert entries[0].file == "skills/verify/SKILL.md"
        assert entries[0].checksum_algorithm == "sha256"

    def test_from_dict_handles_non_dict_artifacts_container(self) -> None:
        """Test that non-dict artifacts payload is safely treated as empty."""
        manifest = Manifest.from_dict(
            {
                "manifest_version": 2,
                "hash_algorithm": "sha256",
                "vstack_version": "1.0.0",
                "installed_at": "2026-01-01T00:00:00Z",
                "artifacts": ["not", "a", "dict"],
            }
        )
        assert manifest.artifacts == {}

    def test_from_dict_skips_non_list_entries_for_manifest_type(self) -> None:
        """Test that per-type entries must be a list and invalid shapes are ignored."""
        manifest = Manifest.from_dict(
            {
                "manifest_version": 2,
                "hash_algorithm": "sha256",
                "vstack_version": "1.0.0",
                "installed_at": "2026-01-01T00:00:00Z",
                "artifacts": {"skills": "invalid"},
            }
        )
        assert manifest.entries_for("skills") == []


class TestManifestFile:
    """Test cases for ManifestFile."""

    def test_read_none_when_missing(self, tmp_path) -> None:
        """Test that read none when missing."""
        mf = ManifestFile(parent_dir=tmp_path)
        assert mf.read() is None
        assert mf.read_error is None

    def test_write_and_read_manifest(self, tmp_path) -> None:
        """Test that write and read manifest."""
        mf = ManifestFile(parent_dir=tmp_path)
        manifest = Manifest(
            vstack_version="0.1.0",
            installed_at="2026-01-01T00:00:00Z",
            artifacts={"skills": [ArtifactEntry(name="vision", file="skills/vision/SKILL.md")]},
        )
        mf.write(manifest)
        loaded = mf.read()
        assert loaded is not None
        assert loaded.names_for("skills") == ["vision"]

    def test_manifest_contains_all_expected_canonical_names(self, installed_target) -> None:
        """Test that manifest contains all expected canonical names."""
        data = json.loads(
            (installed_target / ".github" / "vstack.json").read_text(encoding="utf-8")
        )
        skill_names = [s["name"] for s in data["artifacts"]["skills"]]
        for name in EXPECTED_CANONICAL_NAMES:
            assert name in skill_names

    def test_read_none_when_manifest_is_invalid_json(self, tmp_path) -> None:
        """Test that read none when manifest is invalid json."""
        mf = ManifestFile(parent_dir=tmp_path)
        (tmp_path / "vstack.json").write_text("{broken", encoding="utf-8")
        assert mf.read() is None
        assert mf.read_error is not None

    def test_read_none_when_manifest_version_is_invalid(self, tmp_path) -> None:
        """Test that read rejects non-numeric manifest_version values."""
        mf = ManifestFile(parent_dir=tmp_path)
        (tmp_path / "vstack.json").write_text(
            json.dumps(
                {
                    "manifest_version": "abc",
                    "vstack_version": "0.1.0",
                    "installed_at": "2026-01-01T00:00:00Z",
                    "artifacts": {},
                }
            ),
            encoding="utf-8",
        )
        assert mf.read() is None
        assert mf.read_error == "Invalid manifest format in vstack.json"

    def test_read_none_when_manifest_schema_is_legacy(self, tmp_path) -> None:
        """Test that read blocks legacy schema manifests with upgrade guidance."""
        mf = ManifestFile(parent_dir=tmp_path)
        (tmp_path / "vstack.json").write_text(
            json.dumps(
                {
                    "vstack_version": "1.3.6",
                    "installed_at": "2026-01-01T00:00:00Z",
                    "artifacts": {},
                }
            ),
            encoding="utf-8",
        )
        assert mf.read() is None
        assert mf.read_error is not None
        assert "vstack manifest upgrade --target" in mf.read_error

    def test_write_manifest_does_not_leave_tmp_file(self, tmp_path) -> None:
        """Test that manifest write atomically replaces output without stale tmp file."""
        mf = ManifestFile(parent_dir=tmp_path)
        manifest = Manifest(
            vstack_version="0.1.0",
            installed_at="2026-01-01T00:00:00Z",
            artifacts={
                "skills": [
                    ArtifactEntry(
                        name="vision",
                        file="skills/vision/SKILL.md",
                        checksum="abc123",
                        checksum_algorithm="sha256",
                    )
                ]
            },
        )

        mf.write(manifest)

        assert mf.path.exists()
        assert not mf.path.with_suffix(".tmp").exists()

    def test_read_none_when_manifest_entry_missing_required_file_key(self, tmp_path) -> None:
        """Test that read none when manifest entry missing required file key."""
        mf = ManifestFile(parent_dir=tmp_path)
        (tmp_path / "vstack.json").write_text(
            json.dumps(
                {
                    "vstack_version": "0.1.0",
                    "installed_at": "2026-01-01T00:00:00Z",
                    "artifacts": {"skills": [{"name": "vision"}]},
                }
            ),
            encoding="utf-8",
        )
        assert mf.read() is None
