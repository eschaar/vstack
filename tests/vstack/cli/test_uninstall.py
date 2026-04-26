"""Tests for UninstallCommand."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from vstack.cli.base import CommandContext
from vstack.cli.service import CommandService
from vstack.cli.uninstall import UninstallCommand


class TestUninstallCommand:
    """Test cases for UninstallCommand."""

    def test_print_summary_handles_empty_lists(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Summary printer emits default text when nothing changed."""
        UninstallCommand._print_summary(removed=[], preserved=[])
        assert "Nothing to remove." in capsys.readouterr().out

    def test_execute_returns_error_when_manifest_read_fails(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """execute returns non-zero when manifest read has an error."""

        class _ManifestFile:
            read_error = "bad manifest"

            def read(self):
                return None

        service = cast(
            CommandService,
            SimpleNamespace(
                manifest_for=lambda _install_dir: _ManifestFile(),
                generators=[],
            ),
        )
        assert UninstallCommand.execute(service, Path("/tmp/install")) == 1
        assert "ERROR: bad manifest" in capsys.readouterr().err

    def test_run_forwards_context_to_execute(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """run() unpacks CommandContext args and forwards them to execute()."""
        captured: dict[str, Any] = {}

        def _fake_execute(*args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs
            return 2

        monkeypatch.setattr(
            "vstack.cli.uninstall.UninstallCommand.execute", staticmethod(_fake_execute)
        )

        context = CommandContext(
            args=Namespace(force=True, force_names=["x"]),
            install_dir=tmp_path,
            only=["agent"],
        )
        assert UninstallCommand(service=cast(CommandService, object())).run(context=context) == 2
        assert captured["kwargs"]["force_names"] == ["x"]
        # install_dir is passed as positional arg (second arg after service)
        assert captured["args"][1] == tmp_path
