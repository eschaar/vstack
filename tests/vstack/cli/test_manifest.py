"""Tests for install manifest handling."""

from __future__ import annotations

import json

from vstack.cli.constants import EXPECTED_CANONICAL_NAMES
from vstack.cli.manifest import ArtifactEntry, Manifest, ManifestFile


class TestArtifactEntry:
    """Test cases for ArtifactEntry."""

    def test_artifact_entry_fields(self) -> None:
        """Test that artifact entry fields."""
        e = ArtifactEntry(name="vision", file="skills/vision/SKILL.md", version="1.0.0")
        assert e.name == "vision"
        assert e.file.endswith("SKILL.md")


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
            artifacts={"skills": [ArtifactEntry(name="vision", file="skills/vision/SKILL.md")]},
        )
        out = Manifest.from_dict(src.to_dict())
        assert out.vstack_version == "0.1.0"
        assert out.names_for("skills") == ["vision"]


class TestManifestFile:
    """Test cases for ManifestFile."""

    def test_read_none_when_missing(self, tmp_path) -> None:
        """Test that read none when missing."""
        mf = ManifestFile(parent_dir=tmp_path)
        assert mf.read() is None

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
