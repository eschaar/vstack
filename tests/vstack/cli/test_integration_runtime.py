"""Utilities and tests for test integration runtime."""

from __future__ import annotations

from tests.conftest import run_vstack


class TestRuntimeEntry:
    """Test cases for RuntimeEntry."""

    def test_help_command_exits_zero(self) -> None:
        """Test that help command exits zero."""
        result = run_vstack(["--help"])
        assert result.returncode == 0
        assert "Manage vstack skill generation" in result.stdout
