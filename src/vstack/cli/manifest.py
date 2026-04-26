"""Manifest compatibility exports and subcommand dispatch helpers.

The manifest domain implementation lives in ``vstack.manifest``.
This module re-exports manifest domain symbols for backward compatibility and
hosts dispatch for ``vstack manifest <action>`` subcommands.
"""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from vstack.cli.base import BaseCommand, CommandContext
from vstack.cli.service import CommandService
from vstack.cli.status import StatusCommand
from vstack.cli.verify import VerifyCommand


class ManifestCommand(BaseCommand):
    """Dispatch ``vstack manifest <action>`` subcommands."""

    def __init__(self, service: CommandService) -> None:
        self._service = service

    def _run_upgrade(self, *, args: Namespace, install_dir: Path) -> int:
        """Upgrade manifest schema for the active install directory."""
        return self._service.manifest_upgrade(
            install_dir,
            backfill=getattr(args, "backfill", False),
        )

    def _run_status(self, *, args: Namespace, install_dir: Path, only: list[str] | None) -> int:
        """Render manifest status for the active install directory."""
        return StatusCommand.execute(
            self._service,
            install_dir=install_dir,
            only=only,
            output_format=getattr(args, "output_format", "text"),
            verbose=getattr(args, "verbose", False),
            no_color=getattr(args, "no_color", False),
        )

    def _run_verify(self, *, install_dir: Path, only: list[str] | None) -> int:
        """Run manifest-scoped verification (output-only checks)."""
        return VerifyCommand.execute(
            self._service,
            install_dir=install_dir,
            source=False,
            output=True,
            only=only,
        )

    def run(
        self,
        *,
        context: CommandContext,
    ) -> int:
        install_dir = context.require_install_dir("manifest command")
        args = context.args
        only = context.only

        action = getattr(args, "manifest_action", None)
        if action == "upgrade":
            return self._run_upgrade(args=args, install_dir=install_dir)
        if action == "status":
            return self._run_status(args=args, install_dir=install_dir, only=only)
        if action == "verify":
            return self._run_verify(install_dir=install_dir, only=only)
        raise ValueError("manifest action is required")
