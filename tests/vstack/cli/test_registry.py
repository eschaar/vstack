"""Tests for build_command_registry catalog factory dispatch."""

from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import pytest

from vstack.cli.base import BaseCommand, CommandContext
from vstack.cli.registry import build_command_registry
from vstack.cli.service import CommandService


class _FakeCommand(BaseCommand):
    """Minimal concrete command for registry tests."""

    def run(self, *, context: CommandContext) -> int:
        del context
        return 0


class TestBuildCommandRegistry:
    """Test cases for build_command_registry."""

    def test_uses_catalog_factories(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Registry construction delegates to command_factory for each catalog entry."""
        created: list[str] = []

        def _factory(name: str):
            def _make(_service: object) -> _FakeCommand:
                created.append(name)
                return _FakeCommand()

            return _make

        monkeypatch.setattr(
            "vstack.cli.registry.COMMAND_CATALOG",
            {
                "alpha": SimpleNamespace(command_factory=_factory("alpha")),
                "beta": SimpleNamespace(command_factory=_factory("beta")),
            },
        )

        registry = build_command_registry(service=cast(CommandService, object()))
        assert set(registry.keys()) == {"alpha", "beta"}
        assert created == ["alpha", "beta"]

    def test_returns_all_catalog_commands(self) -> None:
        """Default registry contains one entry per COMMAND_CATALOG key."""
        from vstack.cli.catalog import COMMAND_CATALOG
        from vstack.constants import TEMPLATES_ROOT

        svc = CommandService(templates_root=TEMPLATES_ROOT)
        registry = build_command_registry(service=svc)
        assert set(registry.keys()) == set(COMMAND_CATALOG.keys())
