"""Tests for StatusCommand."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Any, cast

import pytest

from vstack.cli.base import CommandContext
from vstack.cli.service import CommandService
from vstack.cli.status import StatusCommand


class TestStatusCommand:
    """Test cases for StatusCommand."""

    def test_run_forwards_context_to_execute(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """run() unpacks CommandContext args and forwards them to execute()."""
        captured: dict[str, Any] = {}

        def _fake_execute(*args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs
            return 3

        monkeypatch.setattr("vstack.cli.status.StatusCommand.execute", staticmethod(_fake_execute))

        context = CommandContext(
            args=Namespace(output_format="json", verbose=True, no_color=True),
            install_dir=tmp_path,
            only=["prompt"],
        )
        assert StatusCommand(service=cast(CommandService, object())).run(context=context) == 3
        assert captured["kwargs"]["output_format"] == "json"
        assert captured["kwargs"]["verbose"] is True
        assert captured["kwargs"]["no_color"] is True
        assert captured["kwargs"]["install_dir"] == tmp_path
