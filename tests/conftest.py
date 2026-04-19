"""Utilities and tests for conftest."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
VSTACK_ENV = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
SKILLS_TEMPLATES_DIR = ROOT / "src" / "vstack" / "_templates" / "skills"

EXPECTED_CANONICAL_NAMES = [
    "vision",
    "architecture",
    "requirements",
    "adr",
    "design",
    "consult",
    "code-review",
    "release-notes",
    "pr",
    "verify",
    "inspect",
    "security",
    "debug",
    "performance",
    "analyse",
    "explore",
    "docs",
    "guardrails",
    "container",
    "cicd",
    "migrate",
    "openapi",
    "refactor",
    "onboard",
    "dependency",
    "incident",
]


def run_vstack(args: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    """Run vstack."""
    return subprocess.run(
        [sys.executable, "-m", "vstack", *args],
        cwd=ROOT,
        env=VSTACK_ENV,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


@pytest.fixture(scope="session")
def generated_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Generated dir."""
    target = tmp_path_factory.mktemp("skills_target")
    result = run_vstack(["install", "--only", "skill", "--target", str(target)])
    assert result.returncode == 0, (
        f"vstack install --only skill failed:\n{result.stdout}\n{result.stderr}"
    )
    return target / ".github" / "skills"


@pytest.fixture(scope="session")
def installed_target(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Installed target."""
    target = tmp_path_factory.mktemp("install_target")
    result = run_vstack(["install", "--target", str(target)], timeout=60)
    assert result.returncode == 0, f"vstack install failed:\n{result.stdout}\n{result.stderr}"
    return target
