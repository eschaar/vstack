"""Utilities and tests for constants."""

from __future__ import annotations

import re
import subprocess
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from importlib.resources import files
from pathlib import Path

# Package root — works both in editable installs and after pip install
_PACKAGE_ROOT = files("vstack")

TEMPLATES_ROOT = Path(str(_PACKAGE_ROOT / "_templates"))

_SEMVER_TAG_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _version_tuple(tag: str) -> tuple[int, int, int]:
    major, minor, patch = tag.split(".")
    return int(major), int(minor), int(patch)


def _head_semver_tag() -> str | None:
    """Return the highest plain semver tag pointing at HEAD, if available."""
    try:
        out = subprocess.check_output(
            ["git", "tag", "--points-at", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    tags = [line.strip() for line in out.splitlines() if _SEMVER_TAG_RE.fullmatch(line.strip())]
    if not tags:
        return None
    return max(tags, key=_version_tuple)


# Prefer an exact semver tag on HEAD for source checkouts.
VERSION = _head_semver_tag() or ""

if not VERSION:
    try:
        # Reads from installed package metadata, populated by build-time versioning.
        VERSION = _pkg_version("vstack")
    except PackageNotFoundError:
        # Fallback: uninstalled source tree or shallow clone without any git tag.
        VERSION = "0.0.0"

MANIFEST_FILENAME = "vstack.json"
