"""CLI argument parser and install target resolution."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Protocol

from vstack.cli.catalog import (
    COMMAND_CATALOG,
    MANIFEST_SUBCOMMAND_CATALOG,
    MANIFEST_SUBCOMMAND_ORDER,
    TOP_LEVEL_COMMAND_ORDER,
    ManifestSubcommandConfig,
    TopLevelCommandConfig,
)
from vstack.cli.constants import KNOWN_TYPE_NAMES
from vstack.constants import VERSION


class SubparserFactory(Protocol):
    """Protocol for parser objects that can register subcommands."""

    def add_parser(self, name: str, **kwargs: Any) -> argparse.ArgumentParser:
        """Register and return a parser for one subcommand."""
        ...


class CommandLineParser:
    """Create the vstack command-line parser and resolve install targets."""

    @staticmethod
    def _add_scope_group(parser: argparse.ArgumentParser, *, help_text: str) -> None:
        """Add mutually-exclusive target scope flags to a parser."""
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--target", metavar="<dir>", help=help_text)
        group.add_argument(
            "--global",
            dest="use_global",
            action="store_true",
            help="VS Code user profile (agents/prompts/instructions/skills)",
        )

    @staticmethod
    def _add_only_option(parser: argparse.ArgumentParser, *, help_text: str) -> None:
        """Add the shared ``--only`` option used by multi-type commands."""
        parser.add_argument(
            "--only",
            nargs="+",
            choices=KNOWN_TYPE_NAMES,
            metavar="<type>",
            help=help_text,
        )

    def _add_scoped_only_command(
        self,
        sub: SubparserFactory,
        *,
        command_name: str,
        config: TopLevelCommandConfig | ManifestSubcommandConfig,
    ) -> argparse.ArgumentParser:
        """Register a command that supports scope flags and optional ``--only`` filtering."""
        parser = sub.add_parser(command_name, help=config.help_text)
        scope_help = config.scope_help
        if scope_help is None:
            raise ValueError("scope_help is required for scoped commands")
        self._add_scope_group(parser, help_text=scope_help)
        if config.include_only_option:
            if config.only_help is None:
                raise ValueError("only_help is required when include_only_option is True")
            self._add_only_option(parser, help_text=config.only_help)
        if config.include_status_output_options:
            self._add_status_output_options(parser)
        return parser

    def _add_validate_command(self, sub: SubparserFactory) -> None:
        """Register the ``validate`` subcommand."""
        command_config = COMMAND_CATALOG["validate"]
        parser = sub.add_parser(
            "validate",
            help=command_config.help_text,
        )
        self._add_only_option(
            parser,
            help_text=command_config.only_help or "",
        )

    def _add_verify_command(self, sub: SubparserFactory) -> None:
        """Register the ``verify`` subcommand."""
        verify_config = COMMAND_CATALOG["verify"]
        parser = self._add_scoped_only_command(sub, command_name="verify", config=verify_config)
        parser.add_argument(
            "--no-source",
            dest="source",
            action="store_false",
            default=True,
            help="Skip source template checks",
        )
        parser.add_argument(
            "--no-output",
            dest="output",
            action="store_false",
            default=True,
            help="Skip installed output checks",
        )

    def _add_status_output_options(self, parser: argparse.ArgumentParser) -> None:
        """Add shared status formatting options."""
        parser.add_argument(
            "--format",
            dest="output_format",
            choices=["text", "json", "yaml"],
            default="text",
            help="Output format: compact text (default), json, or yaml",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show managed entries in text output (default shows issues-focused view)",
        )
        parser.add_argument(
            "--no-color",
            action="store_true",
            help="Disable ANSI colors in text output",
        )

    def _add_status_command(self, sub: SubparserFactory) -> None:
        """Register the top-level ``status`` subcommand."""
        status_config = COMMAND_CATALOG["status"]
        self._add_scoped_only_command(sub, command_name="status", config=status_config)

    def _add_manifest_command(self, sub: SubparserFactory) -> None:
        """Register the ``manifest`` subcommand and nested actions."""
        manifest_config = COMMAND_CATALOG["manifest"]
        manifest = sub.add_parser(
            "manifest",
            help=manifest_config.help_text,
        )
        manifest_sub = manifest.add_subparsers(dest="manifest_action", metavar="<action>")
        manifest_sub.required = True

        for subcommand_name in MANIFEST_SUBCOMMAND_ORDER:
            subcommand_config = MANIFEST_SUBCOMMAND_CATALOG[subcommand_name]
            subcommand_parser = self._add_scoped_only_command(
                manifest_sub,
                command_name=subcommand_name,
                config=subcommand_config,
            )
            if subcommand_name == "upgrade":
                subcommand_parser.add_argument(
                    "--backfill",
                    action="store_true",
                    help=(
                        "Backfill checksums for tracked legacy entries whose on-disk files "
                        "still contain a VSTACK-META footer"
                    ),
                )

    def _add_install_command(self, sub: SubparserFactory) -> None:
        """Register the ``install`` subcommand."""
        install_config = COMMAND_CATALOG["install"]
        parser = self._add_scoped_only_command(sub, command_name="install", config=install_config)

        mode = parser.add_mutually_exclusive_group()
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

        parser.add_argument(
            "--force-name",
            dest="force_names",
            action="append",
            metavar="<artifact-name>",
            help="Force install one named artifact without overwriting everything",
        )
        parser.add_argument(
            "--adopt-name",
            action="append",
            default=None,
            metavar="NAME",
            help=(
                "Adopt only the named existing unmanaged artifact into the manifest without overwriting it. "
                "Repeat this option to target multiple names."
            ),
        )
        parser.add_argument(
            "--dry-run",
            dest="dry_run",
            action="store_true",
            help="Show what would be installed without writing files",
        )

    def _add_uninstall_command(self, sub: SubparserFactory) -> None:
        """Register the ``uninstall`` subcommand."""
        uninstall_config = COMMAND_CATALOG["uninstall"]
        parser = self._add_scoped_only_command(
            sub,
            command_name="uninstall",
            config=uninstall_config,
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Remove tracked artifacts even when checksum drift is detected",
        )
        parser.add_argument(
            "--force-name",
            dest="force_names",
            action="append",
            metavar="<artifact-name>",
            help="Force uninstall one named artifact without removing every modified file",
        )

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

    def resolve_targets(self, args: argparse.Namespace, *, command_name: str = "command") -> Path:
        """Resolve the install root directory from parsed CLI arguments.

        Args:
            args: Parsed ``argparse`` namespace for an install-like command.

        Returns:
            The effective install root directory.

        Raises:
            ValueError: If ``--global`` cannot be resolved or the explicit
                ``--target`` directory does not exist.
        """
        if getattr(args, "use_global", False):
            user_dir = self.vscode_user_dir()
            if user_dir is None:
                raise ValueError(
                    "Could not detect VS Code user data directory for --global. "
                    f"Specify manually with: vstack {command_name} --target ~/.config/Code/User"
                )
            return user_dir

        if getattr(args, "target", None):
            target = Path(args.target).expanduser().resolve()
            if not target.exists():
                raise ValueError(f"target directory does not exist: {target}")
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

        command_adders = {
            "validate": self._add_validate_command,
            "verify": self._add_verify_command,
            "status": self._add_status_command,
            "manifest": self._add_manifest_command,
            "install": self._add_install_command,
            "uninstall": self._add_uninstall_command,
        }
        for command_name in TOP_LEVEL_COMMAND_ORDER:
            command_adders[command_name](sub)

        return parser
