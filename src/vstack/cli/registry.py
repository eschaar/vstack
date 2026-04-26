"""Command registry construction for CLI dispatch."""

from __future__ import annotations

from vstack.cli.base import BaseCommand
from vstack.cli.catalog import COMMAND_CATALOG
from vstack.cli.service import CommandService


def build_command_registry(service: CommandService) -> dict[str, BaseCommand]:
    """Build the map of top-level command names to command handlers."""
    return {
        command_name: config.command_factory(service)
        for command_name, config in COMMAND_CATALOG.items()
    }
