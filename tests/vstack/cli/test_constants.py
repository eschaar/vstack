"""Utilities and tests for test constants."""

from __future__ import annotations

from vstack.cli.constants import EXPECTED_CANONICAL_NAMES as CLI_NAMES

EXPECTED_CLI_NAMES = [
    "vision",
    "architecture",
    "requirements",
    "adr",
    "design",
    "consult",
    "concise",
    "code-review",
    "release-notes",
    "pr",
    "verify",
    "inspect",
    "security",
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
