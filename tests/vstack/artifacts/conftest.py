"""Shared pytest fixtures for artifact golden-fixture tests."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest


@pytest.fixture(scope="session", name="repo_root")
def fixture_repo_root() -> Path:
    """Return the repository root from this test package location."""
    return Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session", name="templates_root")
def fixture_templates_root(repo_root: Path) -> Path:
    """Return the source templates root used by artifact generators."""
    return repo_root / "src" / "vstack" / "_templates"


@pytest.fixture(scope="session", name="golden_fixtures_root")
def fixture_golden_fixtures_root(repo_root: Path) -> Path:
    """Return the centralized golden-fixtures root for artifact tests."""
    return repo_root / "tests" / "_fixtures" / "golden"


@pytest.fixture(scope="session", name="agent_fixture_path")
def fixture_agent_fixture_path(golden_fixtures_root: Path) -> Callable[[str], Path]:
    """Build the fixture path for an agent artifact."""

    def _build(name: str) -> Path:
        return golden_fixtures_root / "agents" / f"{name}.agent.md"

    return _build


@pytest.fixture(scope="session", name="prompt_fixture_path")
def fixture_prompt_fixture_path(golden_fixtures_root: Path) -> Callable[[str], Path]:
    """Build the fixture path for a prompt artifact."""

    def _build(name: str) -> Path:
        return golden_fixtures_root / "prompts" / f"{name}.prompt.md"

    return _build


@pytest.fixture(scope="session", name="instruction_fixture_path")
def fixture_instruction_fixture_path(golden_fixtures_root: Path) -> Callable[[str], Path]:
    """Build the fixture path for an instruction artifact."""

    def _build(name: str) -> Path:
        return golden_fixtures_root / "instructions" / f"{name}.instructions.md"

    return _build


@pytest.fixture(scope="session", name="skill_fixture_path")
def fixture_skill_fixture_path(golden_fixtures_root: Path) -> Callable[[str], Path]:
    """Build the fixture path for a skill artifact."""

    def _build(name: str) -> Path:
        return golden_fixtures_root / "skills" / f"{name}.SKILL.md"

    return _build
