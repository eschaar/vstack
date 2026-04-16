"""Utilities and tests for test constants."""

from __future__ import annotations

from vstack.agents.constants import AGENT_OUTPUT_SUBDIR, AGENT_OUTPUT_SUFFIX, AGENT_TEMPLATES_DIR


class TestAgentConstants:
    """Test cases for AgentConstants."""

    def test_agent_constants(self) -> None:
        """Test that agent constants."""
        assert AGENT_OUTPUT_SUBDIR == "agents"
        assert AGENT_OUTPUT_SUFFIX == ".agent.md"

    def test_templates_dir_exists(self) -> None:
        """Test that templates dir exists."""
        assert AGENT_TEMPLATES_DIR.exists()
