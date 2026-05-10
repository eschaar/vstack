"""Canonical structure checks for role agent templates."""

from __future__ import annotations

from pathlib import Path

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
