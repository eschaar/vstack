"""Tests for COMMAND_CATALOG and MANIFEST_SUBCOMMAND_CATALOG configuration."""

from __future__ import annotations

import dataclasses
from typing import Any, cast

import pytest

from vstack.cli.catalog import (
    COMMAND_CATALOG,
    MANIFEST_SUBCOMMAND_CATALOG,
    TOP_LEVEL_COMMAND_ORDER,
    ManifestSubcommandConfig,
)


class TestTopLevelCommandConfig:
    """Test cases for TopLevelCommandConfig dataclass."""

    def test_catalog_contains_expected_commands(self) -> None:
        """COMMAND_CATALOG must contain all expected top-level commands."""
        assert set(COMMAND_CATALOG.keys()) == {
            "validate",
            "verify",
            "status",
            "manifest",
            "install",
            "uninstall",
        }

    def test_command_order_matches_catalog_keys(self) -> None:
        """TOP_LEVEL_COMMAND_ORDER must reference known catalog commands."""
        assert set(TOP_LEVEL_COMMAND_ORDER).issubset(set(COMMAND_CATALOG.keys()))

    def test_install_config_requires_install_dir(self) -> None:
        """install command must require install_dir."""
        assert COMMAND_CATALOG["install"].requires_install_dir is True

    def test_validate_config_does_not_require_install_dir(self) -> None:
        """validate command must not require install_dir."""
        assert COMMAND_CATALOG["validate"].requires_install_dir is False

    def test_frozen_dataclass_cannot_be_mutated(self) -> None:
        """TopLevelCommandConfig is frozen; attribute assignment must raise."""
        with pytest.raises((TypeError, dataclasses.FrozenInstanceError)):
            cast(Any, COMMAND_CATALOG["install"]).help_text = "changed"

    def test_all_commands_with_scope_have_scope_help(self) -> None:
        """Every command with include_scope_group=True must supply scope_help."""
        for name, cfg in COMMAND_CATALOG.items():
            if cfg.include_scope_group:
                assert cfg.scope_help, f"{name}: include_scope_group=True but scope_help is empty"


class TestManifestSubcommandConfig:
    """Test cases for ManifestSubcommandConfig dataclass."""

    def test_catalog_contains_expected_subcommands(self) -> None:
        """MANIFEST_SUBCOMMAND_CATALOG must contain expected manifest subcommands."""
        assert set(MANIFEST_SUBCOMMAND_CATALOG.keys()) >= {"upgrade", "status", "verify"}

    def test_scope_help_present_for_all_subcommands(self) -> None:
        """Every manifest subcommand must have a non-empty scope_help string."""
        for name, cfg in MANIFEST_SUBCOMMAND_CATALOG.items():
            assert cfg.scope_help, f"{name}: scope_help must not be empty"

    def test_frozen_dataclass_cannot_be_mutated(self) -> None:
        """ManifestSubcommandConfig is frozen."""
        cfg = ManifestSubcommandConfig(help_text="h", scope_help="s", include_only_option=False)
        with pytest.raises((TypeError, dataclasses.FrozenInstanceError)):
            cast(Any, cfg).help_text = "changed"
