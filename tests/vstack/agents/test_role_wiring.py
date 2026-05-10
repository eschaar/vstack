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
    roles = ["product", "architect", "designer", "engineer", "tester", "release", "planner"]
    for role in roles:
        content = _read(f"{role}/template.md")
        assert "@#concise" in content


def test_role_configs_follow_stage_handoff_policy() -> None:
    """Worker roles expose defaults.handoffs prompts; release and planner are terminal."""
    roles_with_forward_handoff = ["product", "architect", "designer", "engineer", "tester"]
    for role in roles_with_forward_handoff:
        config = _read(f"{role}/config.yaml")
        assert "defaults:" in config
        assert "handoffs:" in config
        assert "prompt:" in config

    release_config = _read("release/config.yaml")
    assert "handoffs:" not in release_config

    planner_config = _read("planner/config.yaml")
    assert "handoffs:" not in planner_config


def test_planner_config_declares_coordinator_tools_and_worker_agents() -> None:
    """Planner should be user-invocable and limited to orchestration tools + worker agents."""
    config = _read("planner/config.yaml")
    for tool in ("read", "search", "todo", "agent"):
        assert f"- {tool}" in config

    for worker in ("product", "architect", "designer", "engineer", "tester", "release"):
        assert f"- {worker}" in config

    assert "user-invocable: true" in config


def test_all_role_handoff_targets_are_known_roles() -> None:
    """Handoff targets in generated agent files should reference known roles."""
    from vstack.frontmatter import FrontmatterParser

    github_dir = Path(__file__).parents[3] / ".github" / "agents"
    roles = ["product", "architect", "designer", "engineer", "tester", "release", "planner"]
    valid_targets = set(roles)

    for role in roles:
        agent_file = github_dir / f"{role}.agent.md"
        if not agent_file.exists():
            continue
        text = agent_file.read_text(encoding="utf-8")
        parsed = FrontmatterParser.parse(text)
        handoffs = parsed.metadata.get("handoffs") or []
        for handoff in handoffs:
            target = handoff.get("agent")
            if target is not None:
                assert target in valid_targets, f"{role} has unknown handoff target: {target!r}"
