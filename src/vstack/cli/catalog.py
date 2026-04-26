"""Central command catalogs shared by parser, registry, and interface."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from vstack.cli.base import BaseCommand
from vstack.cli.install import InstallCommand
from vstack.cli.manifest import ManifestCommand
from vstack.cli.status import StatusCommand
from vstack.cli.uninstall import UninstallCommand
from vstack.cli.validate import ValidateCommand
from vstack.cli.verify import VerifyCommand

if TYPE_CHECKING:
    from vstack.cli.service import CommandService


@dataclass(frozen=True)
class TopLevelCommandConfig:
    """Configuration for one top-level CLI command."""

    command_factory: Callable[[CommandService], BaseCommand]
    help_text: str
    requires_install_dir: bool
    resolve_only_for_scope: bool
    include_scope_group: bool
    include_only_option: bool
    scope_help: str | None = None
    only_help: str | None = None
    include_status_output_options: bool = False


@dataclass(frozen=True)
class ManifestSubcommandConfig:
    """Configuration for one ``vstack manifest <action>`` subcommand."""

    help_text: str
    scope_help: str
    include_only_option: bool
    only_help: str | None = None
    include_status_output_options: bool = False


TOP_LEVEL_COMMAND_ORDER: tuple[str, ...] = (
    "validate",
    "verify",
    "status",
    "manifest",
    "install",
    "uninstall",
)


COMMAND_CATALOG: dict[str, TopLevelCommandConfig] = {
    "validate": TopLevelCommandConfig(
        command_factory=ValidateCommand,
        help_text="Validate source templates only; does not inspect installed files",
        requires_install_dir=False,
        resolve_only_for_scope=False,
        include_scope_group=False,
        include_only_option=True,
        only_help="Validate only these artifact types, e.g. --only skill agent",
    ),
    "verify": TopLevelCommandConfig(
        command_factory=VerifyCommand,
        help_text="Validate source templates and installed output against the manifest",
        requires_install_dir=True,
        resolve_only_for_scope=True,
        include_scope_group=True,
        include_only_option=True,
        scope_help="Verify output in <dir>/.github/",
        only_help="Verify only these artifact types, e.g. --only agent prompt",
    ),
    "status": TopLevelCommandConfig(
        command_factory=StatusCommand,
        help_text="Inspect installed artifacts against vstack.json checksums and manifest ownership",
        requires_install_dir=True,
        resolve_only_for_scope=True,
        include_scope_group=True,
        include_only_option=True,
        scope_help="Inspect output in <dir>/.github/",
        only_help="Inspect only these artifact types, e.g. --only skill agent",
        include_status_output_options=True,
    ),
    "manifest": TopLevelCommandConfig(
        command_factory=ManifestCommand,
        help_text="Manage manifest lifecycle (upgrade, status, verify)",
        requires_install_dir=True,
        resolve_only_for_scope=True,
        include_scope_group=False,
        include_only_option=False,
    ),
    "install": TopLevelCommandConfig(
        command_factory=InstallCommand,
        help_text="Generate and install artifacts (--only to filter types)",
        requires_install_dir=True,
        resolve_only_for_scope=True,
        include_scope_group=True,
        include_only_option=True,
        scope_help="Install into <dir>/.github/",
        only_help="Install only these artifact types, e.g. --only skill agent",
    ),
    "uninstall": TopLevelCommandConfig(
        command_factory=UninstallCommand,
        help_text="Safely remove vstack-managed files tracked in the manifest",
        requires_install_dir=True,
        resolve_only_for_scope=True,
        include_scope_group=True,
        include_only_option=True,
        scope_help="Uninstall from <dir>/.github/",
        only_help="Uninstall only these artifact types, e.g. --only skill agent",
    ),
}


MANIFEST_SUBCOMMAND_ORDER: tuple[str, ...] = (
    "upgrade",
    "status",
    "verify",
)


MANIFEST_SUBCOMMAND_CATALOG: dict[str, ManifestSubcommandConfig] = {
    "upgrade": ManifestSubcommandConfig(
        help_text="Upgrade legacy vstack.json schema to current version",
        scope_help="Upgrade manifest in <dir>/.github/",
        include_only_option=False,
        only_help=None,
    ),
    "status": ManifestSubcommandConfig(
        help_text="Inspect installed artifacts against vstack.json checksums and manifest ownership",
        scope_help="Inspect output in <dir>/.github/",
        include_only_option=True,
        only_help="Inspect only these artifact types, e.g. --only skill agent",
        include_status_output_options=True,
    ),
    "verify": ManifestSubcommandConfig(
        help_text="Verify installed output against manifest ownership and checksums",
        scope_help="Verify output in <dir>/.github/",
        include_only_option=True,
        only_help="Verify only these artifact types, e.g. --only agent prompt",
    ),
}
