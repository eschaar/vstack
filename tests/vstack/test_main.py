"""Tests for CLI entrypoint behavior."""

from __future__ import annotations

import importlib

import pytest

main_module = importlib.import_module("vstack.main")


class _Interface:
    """Simple command-line interface test double."""

    def __init__(self, exit_code: int = 0, error: Exception | None = None) -> None:
        self.exit_code = exit_code
        self.error = error

    def run(self) -> int:
        """Return the configured exit code or raise the configured error."""
        if self.error is not None:
            raise self.error
        return self.exit_code


class TestMain:
    """Test cases for the CLI entrypoint."""

    def test_main_exits_with_interface_code(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that main exits with the code returned by the interface."""
        interface = _Interface(exit_code=7)

        monkeypatch.setattr(main_module, "CommandLineInterface", lambda **kwargs: interface)
        monkeypatch.setattr(
            main_module.sys, "exit", lambda code: (_ for _ in ()).throw(SystemExit(code))
        )

        with pytest.raises(SystemExit) as exc:
            main_module.main()

        assert exc.value.code == 7

    def test_main_prints_value_error_and_exits_non_zero(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that main prints ValueError messages and exits with code 1."""
        interface = _Interface(error=ValueError("boom"))

        monkeypatch.setattr(main_module, "CommandLineInterface", lambda **kwargs: interface)
        monkeypatch.setattr(
            main_module.sys, "exit", lambda code: (_ for _ in ()).throw(SystemExit(code))
        )

        with pytest.raises(SystemExit) as exc:
            main_module.main()

        assert exc.value.code == 1
        assert "ERROR: boom" in capsys.readouterr().err
