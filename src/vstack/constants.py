"""Utilities and tests for constants."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from importlib.resources import files
from pathlib import Path

# Package root — works both in editable installs and after pip install
_PACKAGE_ROOT = files("vstack")

TEMPLATES_ROOT = Path(str(_PACKAGE_ROOT / "_templates"))

try:
    # Reads from installed package metadata, populated by poetry-dynamic-versioning
    # at build time from the nearest reachable git tag (e.g. "1.2.3").
    VERSION = _pkg_version("vstack")
except PackageNotFoundError:
    # Fallback: uninstalled source tree or shallow clone without any git tag.
    VERSION = "0.0.0"

MANIFEST_FILENAME = "vstack.json"
