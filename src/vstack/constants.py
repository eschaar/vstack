"""Project-wide constants and version helpers."""

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
MIGRATIONS_ROOT = Path(str(_PACKAGE_ROOT / "_migrations"))

# Default root directory for all role work items. Individual agent configs
# specify only the subdirectory via ``items.dir``; this root is applied at
# render time. Override per project via ``items.root`` in
# ``.vstack/config.yaml`` (legacy ``artifacts.root`` is still accepted).
ARTIFACTS_DOCS_ROOT = "docs"

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
        out = subprocess.check_output(  # nosec B603 B607
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


def _nearest_semver_tag() -> str | None:
    """Return the nearest plain semver tag reachable from HEAD, if available.

    Uses ``git describe --tags --abbrev=0`` to find the most recent reachable
    tag on any branch, not just tags that point exactly at HEAD.  This gives
    a useful version string in development checkouts where HEAD is ahead of
    the last release tag.

    Only runs git inside the vstack source checkout.
    """
    repo_root = _vstack_repo_root()
    if repo_root is None:
        return None
    try:
        out = subprocess.check_output(  # nosec B603 B607
            ["git", "-C", str(repo_root), "describe", "--tags", "--abbrev=0"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None

    return out if _SEMVER_TAG_RE.fullmatch(out) else None


def _resolve_version() -> str:
    """Resolve the package version from git tags, package metadata, or fallback.

    Resolution order:

    1. Exact semver tag on HEAD — used on release commits in the source checkout.
    2. Nearest reachable semver tag (``git describe``) — gives the base version
       on development branches where HEAD is ahead of the last release.
    3. Installed package metadata — used when running from a built distribution
       (``pip install vstack``) where ``poetry-dynamic-versioning`` has already
       embedded the real version string.
    4. Hard-coded ``"0.0.0"`` fallback — shallow clones, untagged repos, or
       environments where neither git nor package metadata is available.
    """
    version = _head_semver_tag() or _nearest_semver_tag() or ""
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
VSTACK_DIR_NAME = ".vstack"
