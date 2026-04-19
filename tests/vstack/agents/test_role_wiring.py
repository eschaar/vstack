"""Regression tests for role-skill wiring and handoff coverage."""

from __future__ import annotations

from pathlib import Path

TEMPLATES_ROOT = Path(__file__).resolve().parents[3] / "src" / "vstack" / "_templates" / "agents"


def _read(rel_path: str) -> str:
    """Read a UTF-8 text file from the agent templates root."""
    return (TEMPLATES_ROOT / rel_path).read_text(encoding="utf-8")


def test_product_template_references_requirements_and_adr() -> None:
    """Product role should explicitly call requirements and ADR skills."""
    content = _read("product/template.md")
    assert "@#requirements" in content
    assert "@#adr" in content


def test_architect_template_references_explore_and_analyse() -> None:
    """Architect role should include analysis and discovery support skills."""
    content = _read("architect/template.md")
    assert "@#explore" in content
    assert "@#analyse" in content


def test_designer_template_references_consult() -> None:
    """Designer role should include DX/API consult support."""
    content = _read("designer/template.md")
    assert "@#consult" in content


def test_engineer_template_references_explore_and_analyse() -> None:
    """Engineer role should include discovery and tradeoff analysis skills."""
    content = _read("engineer/template.md")
    assert "@#explore" in content
    assert "@#analyse" in content


def test_all_role_templates_reference_concise() -> None:
    """Every role should expose concise runtime style controls."""
    roles = ["product", "architect", "designer", "engineer", "tester", "release"]
    for role in roles:
        content = _read(f"{role}/template.md")
        assert "@#concise" in content


def test_all_role_configs_define_handoffs_block() -> None:
    """Each role config should include at least one handoff entry."""
    roles = ["product", "architect", "designer", "engineer", "tester", "release"]
    for role in roles:
        config = _read(f"{role}/config.yaml")
        assert "handoffs:" in config
        assert "label:" in config
        assert "agent:" in config
