"""Utilities and tests for test constants."""

from __future__ import annotations

import importlib
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

    def test_version_fallback_when_package_metadata_missing(self, monkeypatch) -> None:
        """Test that version fallback when git and package metadata are unavailable."""
        original_version = importlib_metadata.version
        original_check_output = subprocess.check_output

        def _no_git(*_args, **_kwargs) -> str:
            """Internal helper to simulate missing git binary/context."""
            raise FileNotFoundError

        def _raise_not_found(_: str) -> str:
            """Internal helper to raise not found."""
            raise importlib_metadata.PackageNotFoundError

        monkeypatch.setattr(subprocess, "check_output", _no_git)
        monkeypatch.setattr(importlib_metadata, "version", _raise_not_found)
        fallback_loaded = importlib.reload(constants_module)
        assert fallback_loaded.VERSION == "0.0.0"

        monkeypatch.setattr(subprocess, "check_output", original_check_output)
        monkeypatch.setattr(importlib_metadata, "version", original_version)
        restored = importlib.reload(constants_module)
        assert restored.VERSION
