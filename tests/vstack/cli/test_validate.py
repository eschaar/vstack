"""Tests for ValidateCommand."""

from __future__ import annotations

from argparse import Namespace
from typing import Any, cast

import pytest

from vstack.cli.base import CommandContext
from vstack.cli.service import CommandService
from vstack.cli.validate import ValidateCommand


class TestValidateCommand:
    """Test cases for ValidateCommand."""

    def test_run_forwards_context_to_execute(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """run() unpacks CommandContext args and forwards them to execute()."""
        captured: dict[str, Any] = {}

        def _fake_execute(*args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs
            return 4

        monkeypatch.setattr(
            "vstack.cli.validate.ValidateCommand.execute", staticmethod(_fake_execute)
        )

        context = CommandContext(
            args=Namespace(),
            install_dir=None,
            only=["skill"],
        )
        assert ValidateCommand(service=cast(CommandService, object())).run(context=context) == 4
        assert captured["kwargs"]["only"] == ["skill"]
