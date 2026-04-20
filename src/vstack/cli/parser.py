"""CLI argument parser and install target resolution."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from vstack.constants import VERSION


class CommandLineParser:
    """Create the vstack command-line parser and resolve install targets."""

    def vscode_user_dir(self) -> Path | None:
        """Return the first detected VS Code user data directory.

        Returns:
            The detected VS Code or VS Code Server user directory, or ``None``
            when no known location exists on the current machine.
        """
        candidates = [
            Path.home() / ".vscode-server" / "data" / "User",
            Path.home() / ".config" / "Code" / "User",
            Path.home() / "Library" / "Application Support" / "Code" / "User",
            Path.home() / "AppData" / "Roaming" / "Code" / "User",
        ]
        return next((p for p in candidates if p.exists()), None)

    def resolve_targets(self, args: argparse.Namespace) -> Path:
        """Resolve the install root directory from parsed CLI arguments.

        Args:
            args: Parsed ``argparse`` namespace for an install-like command.

        Returns:
            The effective install root directory.

        Raises:
            SystemExit: If ``--global`` cannot be resolved or the explicit
                ``--target`` directory does not exist.
        """
        if getattr(args, "use_global", False):
            user_dir = self.vscode_user_dir()
            if user_dir is None:
                print(
                    "ERROR: Could not detect VS Code user data directory.\n"
                    "Specify manually with:  vstack install --target ~/.config/Code/User",
                    file=sys.stderr,
                )
                sys.exit(1)
            return user_dir

        if getattr(args, "target", None):
            target = Path(args.target).expanduser().resolve()
            if not target.exists():
                print(f"ERROR: target directory does not exist: {target}", file=sys.stderr)
                sys.exit(1)
            return target / ".github"

        # default: current working directory
        return Path.cwd() / ".github"

    def build(self) -> argparse.ArgumentParser:
        """Create and configure the top-level ``argparse`` parser for vstack.

        Returns:
            A fully configured parser with all supported subcommands and flags.
        """
        parser = argparse.ArgumentParser(
            prog="vstack",
            description="Manage vstack skill generation and installation.",
        )
        parser.add_argument("--version", action="version", version=f"vstack {VERSION}")
        sub = parser.add_subparsers(dest="command", metavar="<command>")
        sub.required = True

        p_validate = sub.add_parser(
            "validate", help="Render templates in memory, report unresolved tokens"
        )
        p_validate.add_argument(
            "--only",
            nargs="+",
            metavar="<type>",
            help="Validate only these artifact types, e.g. --only skill agent",
        )

        p = sub.add_parser("verify", help="Validate source templates and/or installed output")
        group = p.add_mutually_exclusive_group()
        group.add_argument("--target", metavar="<dir>", help="Install into <dir>/.github/")
        group.add_argument(
            "--global",
            dest="use_global",
            action="store_true",
            help="VS Code user profile (agents/prompts/instructions/skills)",
        )
        p.add_argument(
            "--only",
            nargs="+",
            metavar="<type>",
            help="Verify only these artifact types, e.g. --only agent prompt",
        )
        p.add_argument(
            "--no-source",
            dest="source",
            action="store_false",
            default=True,
            help="Skip source template checks",
        )
        p.add_argument(
            "--no-output",
            dest="output",
            action="store_false",
            default=True,
            help="Skip installed output checks",
        )

        for cmd, help_text in [
            ("install", "Generate and install artifacts (--only to filter types)"),
            ("uninstall", "Remove vstack-managed files"),
        ]:
            p = sub.add_parser(cmd, help=help_text)
            group = p.add_mutually_exclusive_group()
            group.add_argument("--target", metavar="<dir>", help="Install into <dir>/.github/")
            group.add_argument(
                "--global",
                dest="use_global",
                action="store_true",
                help="VS Code user profile (agents/prompts/instructions/skills)",
            )
            if cmd == "install":
                p.add_argument(
                    "--only",
                    nargs="+",
                    metavar="<type>",
                    help="Install only these artifact types, e.g. --only skill agent",
                )
                mode = p.add_mutually_exclusive_group()
                mode.add_argument(
                    "--force",
                    action="store_true",
                    help="Overwrite existing artifacts unconditionally",
                )
                mode.add_argument(
                    "--update",
                    action="store_true",
                    help="Install only when a newer version is available",
                )
                p.add_argument(
                    "--dry-run",
                    dest="dry_run",
                    action="store_true",
                    help="Show what would be installed without writing files",
                )

        return parser
