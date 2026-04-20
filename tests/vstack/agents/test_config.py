"""Tests for agent artifact configuration."""

from __future__ import annotations

from vstack.agents.config import AGENT_SCHEMA, AGENT_TYPE, HANDOFF_ITEM_SCHEMA


class TestAgentSchemas:
    """Test cases for AgentSchemas."""

    def test_handoff_schema_has_required_fields(self) -> None:
        """Test that handoff schema has required fields."""
        assert HANDOFF_ITEM_SCHEMA.get("label") is not None
        assert HANDOFF_ITEM_SCHEMA.get("agent") is not None

    def test_agent_schema_allows_valid_meta(self) -> None:
        """Test that agent schema allows valid meta."""
        errors = AGENT_SCHEMA.validate_meta(
            {
                "name": "architect",
                "description": "An architect agent",
                "tools": ["read", "edit"],
                "model": ["Claude Sonnet 4.5 (copilot)", "GPT-5.3-Codex (copilot)"],
                "handoffs": [
                    {
                        "label": "Continue",
                        "agent": "designer",
                        "prompt": "Translate architecture into design details.",
                    }
                ],
                "mcp-servers": "  github:\n    type: local\n    command: mcp-github",
                "user-invocable": "true",
                "target": "vscode",
            }
        )
        assert errors == []


class TestAgentType:
    """Test cases for AgentType."""

    def test_type_config_shape(self) -> None:
        """Test that type config shape."""
        assert AGENT_TYPE.type_name == "agent"
        assert AGENT_TYPE.auto_gen_footer is True
        assert AGENT_TYPE.partials_subdir == "_partials"
