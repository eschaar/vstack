"""CLI entrypoint and command dispatch helpers."""

from __future__ import annotations

import sys

from vstack.cli.interface import CommandLineInterface
from vstack.cli.parser import CommandLineParser
from vstack.cli.service import CommandService
from vstack.constants import TEMPLATES_ROOT


def main() -> None:
    """Parse CLI arguments and dispatch the selected top-level command."""
    try:
        interface = CommandLineInterface(
            parser_cls=CommandLineParser,
            service_cls=CommandService,
            templates_root=TEMPLATES_ROOT,
        )
        sys.exit(interface.run())
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
