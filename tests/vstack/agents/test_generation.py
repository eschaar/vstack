"""Tests for generated agent artifacts."""

from __future__ import annotations

from pathlib import Path

from tests.conftest import run_vstack
from vstack.agents.generator import AgentGenerator
from vstack.constants import TEMPLATES_ROOT
from vstack.frontmatter import FrontmatterParser


class TestAgentGeneration:
    """Test cases for AgentGeneration."""

    def test_architect_agent_includes_model_and_handoffs(self, tmp_path: Path) -> None:
        """Test that architect agent includes model and handoffs."""
        # Seed a minimal workflow config so handoffs include agent targets.
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir(parents=True, exist_ok=True)
        (vstack_dir / "config.yaml").write_text(
            "workflow:\n"
            "  mode: manual\n"
            "  version: 1\n"
            "  stages:\n"
            "    - role: product\n"
            "      gate: required\n"
            "      handoffs:\n"
            "        prompt: Product done.\n"
            "    - role: architect\n"
            "      gate: required\n"
            "      handoffs:\n"
            "        prompt: Architecture done.\n"
            "    - role: designer\n"
            "      gate: optional\n"
            "      handoffs:\n"
            "        prompt: Design done.\n",
            encoding="utf-8",
        )

        result = run_vstack(["install", "--only", "agent", "--target", str(tmp_path)], timeout=60)
        assert result.returncode == 0, (
            f"vstack install --only agent failed:\n{result.stdout}\n{result.stderr}"
        )

        out = tmp_path / ".github" / "agents" / "architect.agent.md"
        assert out.exists()

        content = out.read_text(encoding="utf-8")
        parsed = FrontmatterParser.parse(content)

        assert parsed.metadata.get("name") == "architect"
        assert parsed.metadata.get("model") == [
            "auto",
            "Claude Sonnet 4.6 (copilot)",
            "GPT-5.3-Codex (copilot)",
            "Claude Opus 4.7 (copilot)",
        ]

        handoffs = parsed.metadata.get("handoffs")
        assert isinstance(handoffs, list)
        assert handoffs
        assert handoffs[0].get("agent") == "designer"
        prompt = str(handoffs[0].get("prompt", ""))
        assert len(prompt) > 20
        assert handoffs[0].get("label")

        assert parsed.content.lstrip().startswith("# architect")

    def test_all_agents_include_generated_artifacts_section(self, tmp_path: Path) -> None:
        """Test that all generated agents include artifacts tables from config.yaml."""
        result = run_vstack(["install", "--only", "agent", "--target", str(tmp_path)], timeout=60)
        assert result.returncode == 0

        agents_dir = tmp_path / ".github" / "agents"
        for agent_file in agents_dir.glob("*.agent.md"):
            content = agent_file.read_text(encoding="utf-8")
            assert "## work items" in content, f"{agent_file.name} missing '## work items' section"
            assert "Agents do not write to items owned by other roles." in content, (
                f"{agent_file.name} missing role-boundary notice"
            )
            # Placeholders must not appear in rendered output
            for token in ("AGENT_ARTIFACTS_INPUT", "AGENT_ARTIFACTS_OUTPUT"):
                assert f"{{{{{token}}}}}" not in content, (
                    f"{agent_file.name} has unresolved {{{{{token}}}}} placeholder"
                )

    def test_agentic_mode_disables_worker_handoffs(self, tmp_path: Path) -> None:
        """In workflow.mode=agentic, worker agents should not emit handoff buttons."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir(parents=True, exist_ok=True)
        (vstack_dir / "config.yaml").write_text(
            "workflow:\n"
            "  mode: agentic\n"
            "  version: 1\n"
            "  stages:\n"
            "    - role: product\n"
            "      gate: required\n"
            "      handoffs:\n"
            "        prompt: Product done.\n"
            "    - role: architect\n"
            "      gate: required\n"
            "      handoffs:\n"
            "        prompt: Architecture done.\n",
            encoding="utf-8",
        )

        result = run_vstack(["install", "--only", "agent", "--target", str(tmp_path)], timeout=60)
        assert result.returncode == 0, (
            f"vstack install --only agent failed:\n{result.stdout}\n{result.stderr}"
        )

        out = tmp_path / ".github" / "agents" / "product.agent.md"
        parsed = FrontmatterParser.parse(out.read_text(encoding="utf-8"))
        assert not parsed.metadata.get("handoffs")
        assert (tmp_path / ".github" / "agents" / "planner.agent.md").exists()

    def test_manual_mode_keeps_worker_handoffs(self, tmp_path: Path) -> None:
        """In workflow.mode=manual, worker agents keep handoff buttons."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir(parents=True, exist_ok=True)
        (vstack_dir / "config.yaml").write_text(
            "workflow:\n"
            "  mode: manual\n"
            "  version: 1\n"
            "  stages:\n"
            "    - role: product\n"
            "      gate: required\n"
            "      handoffs:\n"
            "        prompt: Product done.\n"
            "    - role: architect\n"
            "      gate: required\n"
            "      handoffs:\n"
            "        prompt: Architecture done.\n",
            encoding="utf-8",
        )

        result = run_vstack(["install", "--only", "agent", "--target", str(tmp_path)], timeout=60)
        assert result.returncode == 0, (
            f"vstack install --only agent failed:\n{result.stdout}\n{result.stderr}"
        )

        out = tmp_path / ".github" / "agents" / "product.agent.md"
        parsed = FrontmatterParser.parse(out.read_text(encoding="utf-8"))
        handoffs = parsed.metadata.get("handoffs")
        assert isinstance(handoffs, list)
        assert handoffs
        assert not (tmp_path / ".github" / "agents" / "planner.agent.md").exists()

    def test_hybrid_mode_generates_planner_and_keeps_worker_handoffs(self, tmp_path: Path) -> None:
        """In workflow.mode=hybrid, planner exists and worker handoffs remain."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir(parents=True, exist_ok=True)
        (vstack_dir / "config.yaml").write_text(
            "workflow:\n"
            "  mode: hybrid\n"
            "  version: 1\n"
            "  stages:\n"
            "    - role: product\n"
            "      gate: required\n"
            "      handoffs:\n"
            "        prompt: Product done.\n"
            "    - role: architect\n"
            "      gate: required\n"
            "      handoffs:\n"
            "        prompt: Architecture done.\n",
            encoding="utf-8",
        )

        result = run_vstack(["install", "--only", "agent", "--target", str(tmp_path)], timeout=60)
        assert result.returncode == 0, (
            f"vstack install --only agent failed:\n{result.stdout}\n{result.stderr}"
        )

        assert (tmp_path / ".github" / "agents" / "planner.agent.md").exists()
        out = tmp_path / ".github" / "agents" / "product.agent.md"
        parsed = FrontmatterParser.parse(out.read_text(encoding="utf-8"))
        handoffs = parsed.metadata.get("handoffs")
        assert isinstance(handoffs, list)
        assert handoffs

    def test_mode_switch_agentic_to_manual_prunes_planner(self, tmp_path: Path) -> None:
        """Switching from agentic to manual removes tracked planner artifact on init."""
        vstack_dir = tmp_path / ".vstack"
        vstack_dir.mkdir(parents=True, exist_ok=True)
        config = vstack_dir / "config.yaml"

        config.write_text(
            "workflow:\n"
            "  mode: agentic\n"
            "  version: 1\n"
            "  stages:\n"
            "    - role: product\n"
            "      gate: required\n"
            "      handoffs:\n"
            "        prompt: Product done.\n"
            "    - role: architect\n"
            "      gate: required\n"
            "      handoffs:\n"
            "        prompt: Architecture done.\n",
            encoding="utf-8",
        )
        first = run_vstack(["install", "--only", "agent", "--target", str(tmp_path)], timeout=60)
        assert first.returncode == 0
        planner_file = tmp_path / ".github" / "agents" / "planner.agent.md"
        assert planner_file.exists()

        config.write_text(
            "workflow:\n"
            "  mode: manual\n"
            "  version: 1\n"
            "  stages:\n"
            "    - role: product\n"
            "      gate: required\n"
            "      handoffs:\n"
            "        prompt: Product done.\n"
            "    - role: architect\n"
            "      gate: required\n"
            "      handoffs:\n"
            "        prompt: Architecture done.\n",
            encoding="utf-8",
        )
        second = run_vstack(["init", "--only", "agent", "--target", str(tmp_path)], timeout=60)
        assert second.returncode == 0, f"init failed:\n{second.stdout}\n{second.stderr}"
        assert not planner_file.exists()

    def test_agentic_mode_directly_suppresses_worker_handoffs(self, tmp_path: Path) -> None:
        """AgentGenerator suppresses worker handoffs when workflow_mode is agentic."""
        gen = AgentGenerator(
            tmp_path,
            workflow_mode="agentic",
            workflow_stages=[
                {"role": "product", "gate": "required", "handoffs": []},
                {"role": "architect", "gate": "required", "handoffs": []},
            ],
        )
        handoffs = gen._resolve_handoffs("product", "Product done.")
        assert handoffs == []

    def test_find_templates_excludes_planner_in_manual_mode(self) -> None:
        """Manual mode should hide planner template from rendered artifact list."""
        gen = AgentGenerator(TEMPLATES_ROOT, workflow_mode="manual")
        names = {p.name for p in gen.find_templates()}
        assert "planner" not in names

    def test_find_templates_includes_planner_in_hybrid_mode(self) -> None:
        """Hybrid mode should keep planner in the rendered artifact list."""
        gen = AgentGenerator(TEMPLATES_ROOT, workflow_mode="hybrid")
        names = {p.name for p in gen.find_templates()}
        assert "planner" in names
