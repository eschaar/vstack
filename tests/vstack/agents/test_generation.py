"""Tests for generated agent artifacts."""

from __future__ import annotations

from pathlib import Path

from tests.conftest import run_vstack
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
        parsed = FrontmatterParser().parse(content)

        assert parsed.metadata.get("name") == "architect"
        assert parsed.metadata.get("model") == [
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
            assert "## artifacts you use" in content, (
                f"{agent_file.name} missing '## artifacts you use' section"
            )
            assert "Agents do not write to artifacts owned by other roles." in content, (
                f"{agent_file.name} missing role-boundary notice"
            )
            # Placeholders must not appear in rendered output
            for token in ("AGENT_ARTIFACTS_INPUT", "AGENT_ARTIFACTS_OUTPUT"):
                assert f"{{{{{token}}}}}" not in content, (
                    f"{agent_file.name} has unresolved {{{{{token}}}}} placeholder"
                )
