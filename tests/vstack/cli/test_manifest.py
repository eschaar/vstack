"""Tests for ManifestCommand dispatch logic."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Any, cast

import pytest

from vstack.cli.base import CommandContext
from vstack.cli.manifest import ManifestCommand
from vstack.cli.service import CommandService


class TestManifestCommand:
    """Test cases for ManifestCommand."""

    def test_dispatches_upgrade(self) -> None:
        """Routes upgrade action to service.manifest_upgrade with correct arguments."""

        class _Service:
            def manifest_upgrade(self, install_dir: Path, *, backfill: bool = False) -> int:
                assert install_dir == Path("/tmp/install")
                assert backfill is True
                return 17

        command = ManifestCommand(cast(CommandService, _Service()))
        context = CommandContext(
            args=Namespace(manifest_action="upgrade", backfill=True),
            install_dir=Path("/tmp/install"),
            only=None,
        )
        assert command.run(context=context) == 17

    def test_dispatches_status_with_flags(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Status action forwards output format and filter flags to StatusCommand.execute."""
        seen: dict[str, object] = {}

        def _fake_execute(service, **kwargs):
            seen["service"] = service
            seen.update(kwargs)
            return 9

        monkeypatch.setattr(
            "vstack.cli.manifest.StatusCommand.execute", staticmethod(_fake_execute)
        )

        service: Any = object()
        command = ManifestCommand(cast(CommandService, service))
        context = CommandContext(
            args=Namespace(
                manifest_action="status", output_format="yaml", verbose=True, no_color=True
            ),
            install_dir=Path("/tmp/install"),
            only=["skill"],
        )

        assert command.run(context=context) == 9
        assert seen["service"] is service
        assert seen["install_dir"] == Path("/tmp/install")
        assert seen["only"] == ["skill"]
        assert seen["output_format"] == "yaml"
        assert seen["verbose"] is True
        assert seen["no_color"] is True

    def test_dispatches_verify(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify action forces output-only verify and forwards only filter."""
        seen: dict[str, object] = {}

        def _fake_execute(service, **kwargs):
            seen["service"] = service
            seen.update(kwargs)
            return 3

        monkeypatch.setattr(
            "vstack.cli.manifest.VerifyCommand.execute", staticmethod(_fake_execute)
        )

        service2: Any = object()
        command = ManifestCommand(cast(CommandService, service2))
        context = CommandContext(
            args=Namespace(manifest_action="verify"),
            install_dir=Path("/tmp/install"),
            only=["agent"],
        )

        assert command.run(context=context) == 3
        assert seen["service"] is service2
        assert seen["source"] is False
        assert seen["output"] is True
        assert seen["only"] == ["agent"]

    def test_requires_action(self) -> None:
        """Raises ValueError when no manifest_action is present in args."""
        command = ManifestCommand(service=cast(CommandService, object()))
        context = CommandContext(args=Namespace(), install_dir=Path("/tmp/install"), only=None)
        with pytest.raises(ValueError, match="manifest action is required"):
            command.run(context=context)
