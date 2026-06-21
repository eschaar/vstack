"""Tests for canonical CLI names."""

from __future__ import annotations

from vstack.cli.constants import EXPECTED_CANONICAL_NAMES as CLI_NAMES
from vstack.cli.constants import EXPECTED_INPUT_NAMES

EXPECTED_CLI_NAMES = [
    "ask",
    "vision",
    "architecture",
    "requirements",
    "adr",
    "design",
    "consult",
    "concise",
    "conventional-commit",
    "code-review",
    "release-notes",
    "pr",
    "gh-release",
    "verify",
    "inspect",
    "security",
    "threat-model",
    "debug",
    "performance",
    "analyse",
    "explore",
    "docs",
    "guardrails",
    "container",
    "cicd",
    "migrate",
    "openapi",
    "refactor",
    "onboard",
    "dependency",
    "incident",
    "rca",
    "postmortem",
    "gh-issues",
    "codeql",
    "dependabot",
    "secret-scan",
    "gdpr",
    "terraform",
    "terragrunt",
    "cloudformation",
    "aws-cli",
    "k8s",
    "helm",
    "rancher",
    "space-setup",
    "copilot-ops",
]


class TestCliConstants:
    """Test cases for CliConstants."""

    def test_expected_canonical_names_content(self) -> None:
        """Test that EXPECTED_CLI_NAMES has the correct, project-wide canonical values."""
        assert CLI_NAMES == EXPECTED_CLI_NAMES, (
            f"EXPECTED_CLI_NAMES does not match the project-wide canonical values.\n"
            f"Expected:   {EXPECTED_CLI_NAMES}\n"
            f"Found: {CLI_NAMES}"
        )

    def test_expected_hook_input_names_content(self) -> None:
        """Verify source checks require the complete built-in hook set."""
        assert EXPECTED_INPUT_NAMES["hook"] == [
            "agent-call-audit",
            "log-retention-cleanup",
            "post-edit-markdown-quality",
            "post-edit-format",
            "post-commit-security-scan",
            "pre-tool-safety-gate",
            "session-audit",
        ]

    def test_expected_agent_input_names_content(self) -> None:
        """Verify source checks require all built-in agents including planner."""
        assert EXPECTED_INPUT_NAMES["agent"] == [
            "architect",
            "designer",
            "engineer",
            "planner",
            "product",
            "release",
            "tester",
        ]
