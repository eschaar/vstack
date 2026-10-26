"""Canonical structure checks for role agent templates."""

from __future__ import annotations

from pathlib import Path

import pytest

TEMPLATES_ROOT = Path(__file__).resolve().parents[3] / "src" / "vstack" / "_templates" / "agents"
ROLES = ["product", "architect", "designer", "engineer", "tester", "release", "planner"]
REQUIRED_HEADINGS_IN_ORDER = [
    "## identity and purpose",
    "## responsibilities",
    "## scope and boundaries",
    "## limitations and do not do",
    "## working principles",
    "## decision guidelines",
    "## communication style",
    "## workflow and handoffs",
    "## success criteria",
    "## failure and escalation rules",
    "## work items",
    "## completion checklist",
    "## skills you use",
]


def _read(role: str) -> str:
    """Read one role template from the source templates directory."""
    return (TEMPLATES_ROOT / role / "template.md").read_text(encoding="utf-8")


def _headings(content: str) -> list[str]:
    """Return level-2 headings in declaration order."""
    return [line.strip() for line in content.splitlines() if line.startswith("## ")]


def test_all_role_templates_follow_canonical_section_order() -> None:
    """Each role template should include canonical sections in the required order."""
    for role in ROLES:
        headings = _headings(_read(role))

        positions: list[int] = []
        for heading in REQUIRED_HEADINGS_IN_ORDER:
            assert heading in headings, f"{role} missing heading: {heading}"
            positions.append(headings.index(heading))

        assert positions == sorted(positions), f"{role} canonical headings out of order"


@pytest.mark.parametrize("role", ["product", "planner"])
def test_rendered_intake_allows_focused_work_without_weakening_lifecycle(
    installed_target: Path, role: str
) -> None:
    """Focused routing preserves authorization and rejects archived-state ordering."""
    text = " ".join(
        (installed_target / ".github" / "agents" / f"{role}.agent.md")
        .read_text(encoding="utf-8")
        .split()
    )
    assert "low-risk work" in text
    assert "conversation context" in text
    assert "observable acceptance" in text
    for status in ("CONCEPT", "BUILD", "IMPLEMENTED", "ARCHIVED"):
        assert f"`{status}`" in text
    assert "at least `BUILD`" not in text
    assert "never authoriz" in text
    assert "gates" in text and "approval" in text


@pytest.mark.parametrize("role", ROLES)
def test_rendered_roles_keep_shared_stage_report_contract(
    installed_target: Path, role: str
) -> None:
    """Evidence references use existing fields, not an expanded report schema."""
    contract = (TEMPLATES_ROOT / "_partials" / "stage-report-contract.md").read_text(
        encoding="utf-8"
    )
    rendered = (installed_target / ".github" / "agents" / f"{role}.agent.md").read_text(
        encoding="utf-8"
    )
    assert contract.strip() in rendered
    assert "{{" not in rendered


def test_rendered_contributors_preserve_scope_ownership(installed_target: Path) -> None:
    """Engineer/tester can record evidence without rewriting product acceptance."""
    for role in ("engineer", "tester"):
        text = (installed_target / ".github" / "agents" / f"{role}.agent.md").read_text(
            encoding="utf-8"
        )
        assert "not product scope or acceptance" in text


@pytest.mark.parametrize(
    ("role", "obligations"),
    [
        ("architect", ("constraints", "acceptance", "migration risks")),
        ("designer", ("acceptance", "error/compatibility", "data-lifecycle")),
        ("engineer", ("verifiable slices", "real prerequisites", "failed/unrun checks")),
        ("tester", ("absent from the diff", "no longer current", "otherwise use")),
        ("release", ("criterion/check/result", "evidence freshness", "exceptions")),
    ],
)
def test_rendered_specialists_connect_scope_to_evidence(
    installed_target: Path, role: str, obligations: tuple[str, ...]
) -> None:
    """Relevant owners retain concrete acceptance and evidence responsibilities."""
    text = " ".join(
        (installed_target / ".github" / "agents" / f"{role}.agent.md")
        .read_text(encoding="utf-8")
        .split()
    )
    for obligation in obligations:
        assert obligation in text
