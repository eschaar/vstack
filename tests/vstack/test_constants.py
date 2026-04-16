"""Utilities and tests for test constants."""

from __future__ import annotations

import importlib.metadata as importlib_metadata
import subprocess
from pathlib import Path

import vstack.constants as constants_module
from vstack.constants import MANIFEST_FILENAME, TEMPLATES_ROOT, VERSION


class TestConstants:
    """Test cases for Constants."""

    def test_templates_root_exists(self) -> None:
        """Test that templates root exists."""
        assert isinstance(TEMPLATES_ROOT, Path)
        assert TEMPLATES_ROOT.exists()

    def test_version_non_empty(self) -> None:
        """Test that version non empty."""
        assert VERSION

    def test_manifest_filename(self) -> None:
        """Test that manifest filename."""
        assert MANIFEST_FILENAME == "vstack.json"

    def test_head_semver_tag_returns_none_when_head_has_no_semver_tags(self, monkeypatch) -> None:
        """Test that non-semver tags on HEAD are ignored."""
        monkeypatch.setattr(constants_module, "_vstack_repo_root", lambda: Path("/fake/root"))
        monkeypatch.setattr(subprocess, "check_output", lambda *_args, **_kwargs: "main\nv1.0.0\n")

        assert constants_module._head_semver_tag() is None

    def test_head_semver_tag_returns_none_when_git_lookup_fails(self, monkeypatch) -> None:
        """Test that git lookup failures fall back cleanly."""
        monkeypatch.setattr(constants_module, "_vstack_repo_root", lambda: Path("/fake/root"))

        def _raise_called_process_error(*_args, **_kwargs) -> str:
            """Internal helper to simulate git lookup failure."""
            raise subprocess.CalledProcessError(returncode=1, cmd=["git", "tag"])

        monkeypatch.setattr(subprocess, "check_output", _raise_called_process_error)

        assert constants_module._head_semver_tag() is None

    def test_head_semver_tag_returns_none_outside_vstack_repo(self, monkeypatch) -> None:
        """Test that git is not consulted when not inside the vstack source tree."""
        monkeypatch.setattr(constants_module, "_vstack_repo_root", lambda: None)
        called = []
        monkeypatch.setattr(subprocess, "check_output", lambda *_a, **_kw: called.append(1) or "")

        assert constants_module._head_semver_tag() is None
        assert not called, "git must not be invoked outside the vstack repo"

    def test_vstack_repo_root_returns_none_for_unrelated_git_repo(
        self, monkeypatch, tmp_path
    ) -> None:
        """Test that a .git dir without src/vstack does not match as vstack repo."""
        fake_git = tmp_path / ".git"
        fake_git.mkdir()
        monkeypatch.setattr(constants_module, "_PACKAGE_ROOT", tmp_path)  # type: ignore[attr-defined]

        assert constants_module._vstack_repo_root() is None

    def test_head_semver_tag_returns_highest_plain_semver(self, monkeypatch) -> None:
        """Test that the highest semver tag on HEAD is selected."""
        monkeypatch.setattr(constants_module, "_vstack_repo_root", lambda: Path("/fake/root"))
        monkeypatch.setattr(
            subprocess,
            "check_output",
            lambda *_args, **_kwargs: "1.0.0\n1.0.2\n1.0.1\nrelease-candidate\n",
        )

        assert constants_module._head_semver_tag() == "1.0.2"

    def test_version_uses_installed_package_metadata_when_git_tag_missing(
        self, monkeypatch
    ) -> None:
        """Test that installed metadata is used when no semver tag points at HEAD."""
        monkeypatch.setattr(constants_module, "_head_semver_tag", lambda: None)
        monkeypatch.setattr(constants_module, "_pkg_version", lambda _name: "1.0.1")

        assert constants_module._resolve_version() == "1.0.1"

    def test_version_prefers_head_semver_tag(self, monkeypatch) -> None:
        """Test that a semver tag on HEAD wins over package metadata."""
        monkeypatch.setattr(constants_module, "_head_semver_tag", lambda: "1.0.1")
        monkeypatch.setattr(constants_module, "_pkg_version", lambda _name: "9.9.9")

        assert constants_module._resolve_version() == "1.0.1"

    def test_version_fallback_when_package_metadata_missing(self, monkeypatch) -> None:
        """Test that version fallback when git and package metadata are unavailable."""

        def _raise_not_found(_: str) -> str:
            """Internal helper to raise not found."""
            raise importlib_metadata.PackageNotFoundError

        monkeypatch.setattr(constants_module, "_head_semver_tag", lambda: None)
        monkeypatch.setattr(constants_module, "_pkg_version", _raise_not_found)

        assert constants_module._resolve_version() == "0.0.0"
