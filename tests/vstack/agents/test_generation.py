"""Utilities and tests for test generation."""

from __future__ import annotations

from pathlib import Path

from tests.conftest import run_vstack
from vstack.frontmatter import FrontmatterParser


class TestAgentGeneration:
    """Test cases for AgentGeneration."""

    def test_architect_agent_includes_model_and_handoffs(self, tmp_path: Path) -> None:
        """Test that architect agent includes model and handoffs."""
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
            "Claude Opus 4.6 (copilot)",
            "Claude Sonnet 4.6 (copilot)",
            "GPT-5.3-Codex (copilot)",
        ]

        handoffs = parsed.metadata.get("handoffs")
        assert isinstance(handoffs, list)
        assert handoffs
        assert handoffs[0].get("agent") == "designer"
        assert "Translate docs/architecture/architecture.md" in str(handoffs[0].get("prompt"))

        assert parsed.content.lstrip().startswith("# architect")
