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


def _vstack_repo_root() -> Path | None:
    """Return the root of the vstack source checkout, or None if not in one.

    Walks up from the package directory looking for a .git directory.
    Returns None when invoked outside the vstack source tree, preventing
    accidental version reads from the user's working directory.
    """
    candidate = Path(str(_PACKAGE_ROOT)).resolve()
    for parent in [candidate, *candidate.parents]:
        if (parent / ".git").exists():
            # Confirm this is the vstack repo, not an arbitrary repo that
            # happens to contain the installed package somewhere inside it.
            if (parent / "src" / "vstack").exists():
                return parent
            break
    return None


def _head_semver_tag() -> str | None:
    """Return the highest plain semver tag pointing at HEAD, if available.

    Only runs git inside the vstack source checkout to prevent picking up
    tags from whatever repository the user is working in.
    """
    repo_root = _vstack_repo_root()
    if repo_root is None:
        return None
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo_root), "tag", "--points-at", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    tags = [line.strip() for line in out.splitlines() if _SEMVER_TAG_RE.fullmatch(line.strip())]
    if not tags:
        return None
    return max(tags, key=_version_tuple)


def _resolve_version() -> str:
    """Resolve the package version from git tags, package metadata, or fallback."""
    version = _head_semver_tag() or ""
    if version:
        return version

    try:
        # Reads from installed package metadata, populated by build-time versioning.
        return _pkg_version("vstack")
    except PackageNotFoundError:
        # Fallback: uninstalled source tree or shallow clone without any git tag.
        return "0.0.0"


# Prefer an exact semver tag on HEAD for source checkouts.
VERSION = _resolve_version()

MANIFEST_FILENAME = "vstack.json"
