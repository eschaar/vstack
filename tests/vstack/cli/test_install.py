"""Tests for InstallCommand."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from vstack.cli.base import CommandContext
from vstack.cli.install import InstallCommand
from vstack.cli.service import CommandService
from vstack.manifest import content_hash


class TestInstallCommand:
    """Test cases for InstallCommand."""

    # ------------------------------------------------------------------
    # _version_gt
    # ------------------------------------------------------------------

    def test_version_gt_true_for_higher(self) -> None:
        """Newer semver string is strictly greater."""
        assert InstallCommand._version_gt("1.2.0", "1.1.9")

    def test_version_gt_false_for_equal(self) -> None:
        """Equal versions are not greater."""
        assert not InstallCommand._version_gt("1.2.0", "1.2.0")

    def test_version_gt_handles_invalid(self) -> None:
        """Non-semver strings are treated as (0,) and not greater than a real version."""
        assert not InstallCommand._version_gt("abc", "1.0.0")

    def test_version_gt_handles_none_existing(self) -> None:
        """None for existing falls back to (0,) so any real version is greater."""
        assert InstallCommand._version_gt("1.2.0", None) is True

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
            InstallCommand._installed_content_matches(out_file=out_file, existing_entry=entry)
            is None
        )

    # ------------------------------------------------------------------
    # _install_decision
    # ------------------------------------------------------------------

    def test_decision_preserves_when_tracked_file_has_no_checksum(self, tmp_path: Path) -> None:
        """Tracked file without stored checksum is always preserved."""
        out_file = tmp_path / "artifact.txt"
        out_file.write_text("content", encoding="utf-8")
        entry = SimpleNamespace(checksum=None, checksum_algorithm="sha256", version="1.0.0")
        action, reason = InstallCommand._install_decision(
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
        action, reason = InstallCommand._install_decision(
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

        result = InstallCommand._load_existing_manifest(
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
            "vstack.cli.install.InstallCommand._load_existing_manifest",
            staticmethod(lambda **_kwargs: (None, None, None, None)),
        )
        service = cast(CommandService, SimpleNamespace(generators=[]))
        assert InstallCommand.execute(service, Path("/tmp/install")) == 1

    # ------------------------------------------------------------------
    # run (context forwarding)
    # ------------------------------------------------------------------

    def test_run_forwards_context_to_execute(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """run() unpacks CommandContext args and forwards them to execute()."""
        captured: dict[str, Any] = {}

        def _fake_execute(*args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs
            return 1

        monkeypatch.setattr(
            "vstack.cli.install.InstallCommand.execute", staticmethod(_fake_execute)
        )

        from argparse import Namespace

        context = CommandContext(
            args=Namespace(
                force=True, force_names=["a"], adopt_name=["b"], update=True, dry_run=True
            ),
            install_dir=tmp_path,
            only=["skill"],
        )
        assert InstallCommand(service=cast(CommandService, object())).run(context=context) == 1
        assert captured["kwargs"]["adopt_names"] == ["b"]
        assert captured["kwargs"]["force"] is True
