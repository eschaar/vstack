"""Utilities and tests for test init."""

from __future__ import annotations

import vstack.agents


class TestAgentsInit:
    """Test cases for AgentsInit."""

    def test_exports_agent_generator(self) -> None:
        """Test that exports agent generator."""
        assert "AgentGenerator" in vstack.agents.__all__
