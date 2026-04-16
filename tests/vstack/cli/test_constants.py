"""Utilities and tests for test constants."""

from __future__ import annotations

from tests.conftest import EXPECTED_CANONICAL_NAMES
from vstack.cli.constants import EXPECTED_CANONICAL_NAMES as CLI_NAMES


class TestCliConstants:
    """Test cases for CliConstants."""

    def test_expected_names_match_project_expectation(self) -> None:
        """Test that expected names match project expectation."""
        assert CLI_NAMES == EXPECTED_CANONICAL_NAMES
