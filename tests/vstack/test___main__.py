"""Tests for the ``python -m vstack`` entrypoint."""

from __future__ import annotations

import importlib
import runpy

import pytest

from tests.conftest import run_vstack


class TestDunderMain:
    """Test cases for DunderMain."""

    def test_module_entrypoint_runs_version(self) -> None:
        """Test that module entrypoint runs version."""
        result = run_vstack(["--version"])
        assert result.returncode == 0
        assert result.stdout.startswith("vstack ")

    def test_dunder_main_invokes_main_function(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that dunder main invokes main function."""
        called = {"ok": False}
        main_mod = importlib.import_module("vstack.main")

        def _fake_main() -> None:
            """Internal helper to fake main."""
            called["ok"] = True

        monkeypatch.setattr(main_mod, "main", _fake_main)
        runpy.run_module("vstack.__main__", run_name="__main__")
        assert called["ok"]
