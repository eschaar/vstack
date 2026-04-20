"""Tests for agent generator behavior."""

from __future__ import annotations

from vstack.agents.generator import AgentGenerator


class TestAgentGenerator:
    """Test cases for AgentGenerator."""

    def test_generator_uses_agent_type(self) -> None:
        """Test that generator uses agent type."""
        gen = AgentGenerator()
        assert gen.config.type_name == "agent"
