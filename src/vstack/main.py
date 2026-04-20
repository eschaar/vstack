"""CLI entrypoint and command dispatch helpers."""

from __future__ import annotations

import sys

from vstack.cli.commands import CommandLineInterface
from vstack.cli.parser import build_parser, resolve_targets
from vstack.constants import TEMPLATES_ROOT

_GLOBAL_SUPPORTED_TYPES = ["agent", "instruction", "prompt", "skill"]


def _resolve_only_for_scope(args: object) -> list[str] | None:
    """Return the artifact type filter for the active command scope."""
    requested_only = getattr(args, "only", None)
    if not getattr(args, "use_global", False):
        return requested_only

    if requested_only is None:
        return list(_GLOBAL_SUPPORTED_TYPES)

    disallowed = [t for t in requested_only if t not in _GLOBAL_SUPPORTED_TYPES]
    if disallowed:
        print(
            "ERROR: --global supports only agents, prompts, and instructions. "
            f"Unsupported type(s): {', '.join(disallowed)}",
            file=sys.stderr,
        )
        sys.exit(1)

    return requested_only


def main() -> None:
    """Parse CLI arguments and dispatch the selected command."""
    parser = build_parser()
    args = parser.parse_args()
    cli = CommandLineInterface(templates_root=TEMPLATES_ROOT)

    if args.command == "validate":
        sys.exit(cli.validate(only=getattr(args, "only", None)))

    install_dir = resolve_targets(args)
    only = _resolve_only_for_scope(args) if args.command in {"install", "verify"} else None
    dispatch = {
        "verify": lambda: cli.verify(
            install_dir=install_dir,
            source=getattr(args, "source", True),
            output=getattr(args, "output", True),
            only=only,
        ),
        "install": lambda: cli.install(
            install_dir,
            only=only,
            force=getattr(args, "force", False),
            update=getattr(args, "update", False),
            dry_run=getattr(args, "dry_run", False),
        ),
        "uninstall": lambda: cli.uninstall(install_dir),
    }
    sys.exit(dispatch[args.command]())
