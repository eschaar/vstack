"""Migrate command — apply docs artifact path migrations between major versions."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from vstack.cli.base import BaseCommand, CommandContext
from vstack.cli.constants import Colors
from vstack.constants import ARTIFACTS_DOCS_ROOT, MIGRATIONS_ROOT, VERSION, VSTACK_DIR_NAME
from vstack.frontmatter import FrontmatterParser
from vstack.manifest.store import ManifestFile

if TYPE_CHECKING:
    from vstack.cli.service import CommandService


class MigrateCommand(BaseCommand):
    """Apply docs artifact path migrations between major vstack versions.

    Reads migration records from the package ``_migrations/`` directory and
    moves files at old docs paths to their new locations.  Only files that
    exist at the old path are moved; absent files are silently skipped.
    """

    def __init__(self, service: CommandService) -> None:
        self._service = service

    @staticmethod
    def _resolve_project_root(args: object) -> Path:
        """Resolve the project root from ``--target`` or the current directory."""
        target = getattr(args, "target", None)
        if target:
            return Path(target).expanduser().resolve()
        return Path.cwd()

    @staticmethod
    def _detect_installed_major(project_root: Path) -> int | None:
        """Read ``vstack_version`` from the manifest and return its major number.

        Returns ``None`` when the manifest is absent or the version cannot be
        parsed as a semver-like string.
        """
        manifest_path = project_root / VSTACK_DIR_NAME / "vstack.json"
        if not manifest_path.exists():
            return None
        manifest_file = ManifestFile(project_root / VSTACK_DIR_NAME)
        try:
            manifest = manifest_file.read()
        except Exception:  # noqa: BLE001
            return None
        if manifest is None:
            return None
        version = manifest.vstack_version
        if not version:
            return None
        try:
            return int(version.split(".")[0])
        except (ValueError, IndexError):
            return None

    @staticmethod
    def _load_migration_record(from_major: int, to_major: int) -> list[dict] | None:
        """Load moves for a single *from_major* → *to_major* step.

        Returns the ``moves`` list from the YAML record, or ``None`` when no
        record file exists for this step.
        """
        record_path = MIGRATIONS_ROOT / f"v{from_major}_to_v{to_major}.yaml"
        if not record_path.exists():
            return None
        raw = yaml.safe_load(record_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return None
        moves = raw.get("moves", [])
        if not isinstance(moves, list):
            return None
        return [m for m in moves if isinstance(m, dict)]

    @staticmethod
    def _resolve_new_path(new_rel: str, artifacts_root: str) -> str:
        """Substitute the default docs root in *new_rel* with *artifacts_root*.

        Migration records store new paths using the default ``docs/`` root.
        When the project uses a custom root, the first path component is
        replaced so the file lands under the configured directory.
        """
        if artifacts_root == ARTIFACTS_DOCS_ROOT:
            return new_rel
        parts = Path(new_rel).parts
        if parts and parts[0] == ARTIFACTS_DOCS_ROOT:
            return str(Path(artifacts_root).joinpath(*parts[1:]))
        return new_rel

    @staticmethod
    def _read_artifacts_root(project_root: Path) -> str:
        """Read ``artifacts.root`` from ``.vstack/config.yaml``.

        Returns :data:`~vstack.constants.ARTIFACTS_DOCS_ROOT` when the config
        is absent or the key is not set.
        """
        config_path = project_root / VSTACK_DIR_NAME / "config.yaml"
        if not config_path.exists():
            return ARTIFACTS_DOCS_ROOT
        parsed = FrontmatterParser.parse_yaml(config_path.read_text(encoding="utf-8"))
        artifacts = parsed.get("artifacts", "")
        if not isinstance(artifacts, dict):
            return ARTIFACTS_DOCS_ROOT
        value = artifacts.get("root", "")
        if isinstance(value, str) and value.strip():
            return value.strip()
        return ARTIFACTS_DOCS_ROOT

    @staticmethod
    def _apply_moves(
        *,
        moves: list[dict],
        project_root: Path,
        artifacts_root: str,
        dry_run: bool,
        colors: type[Colors],
    ) -> tuple[int, int]:
        """Apply *moves* relative to *project_root*.

        Returns a ``(moved, skipped)`` count pair.
        """
        moved = 0
        skipped = 0
        prefix = f"{colors.DIM}[dry-run]{colors.RESET} " if dry_run else ""

        for move in moves:
            old_rel = move.get("old", "")
            new_rel_raw = move.get("new", "")
            if not old_rel or not new_rel_raw:
                continue

            new_rel = MigrateCommand._resolve_new_path(new_rel_raw, artifacts_root)
            old_path = project_root / old_rel
            new_path = project_root / new_rel

            if not old_path.exists():
                print(f"  {prefix}{colors.DIM}↷  {old_rel}  — absent, skipping{colors.RESET}")
                skipped += 1
                continue

            if new_path.exists():
                print(
                    f"  {prefix}{colors.YELLOW}↷{colors.RESET}  {old_rel}"
                    f"  {colors.DIM}→ {new_rel}"
                    f"  — destination exists, skipping{colors.RESET}"
                )
                skipped += 1
                continue

            print(
                f"  {prefix}{colors.GREEN}→{colors.RESET}  "
                f"{colors.BOLD}{old_rel}{colors.RESET}"
                f"  {colors.DIM}→{colors.RESET}  {new_rel}"
            )
            if not dry_run:
                new_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(old_path), str(new_path))
            moved += 1

        return moved, skipped

    def run(self, *, context: CommandContext) -> int:
        """Execute the migrate command and return a process-style status code."""
        args = context.args
        colors = Colors
        dry_run = getattr(args, "dry_run", False)
        project_root = self._resolve_project_root(args)
        from_major: int | None = getattr(args, "from_major", None)
        to_major: int | None = getattr(args, "to_major", None)

        if from_major is None:
            from_major = self._detect_installed_major(project_root)
            if from_major is None:
                print(
                    "ERROR: could not detect installed version from manifest. "
                    "Specify --from <major> explicitly.",
                    file=sys.stderr,
                )
                return 1

        if to_major is None:
            try:
                to_major = int(VERSION.split(".")[0])
            except (ValueError, IndexError):
                to_major = from_major + 1

        if from_major >= to_major:
            print(f"Nothing to migrate: already at v{to_major}.")
            return 0

        artifacts_root = self._read_artifacts_root(project_root)

        print(f"\n  {colors.BOLD}Migrating docs paths v{from_major} → v{to_major}{colors.RESET}")
        if dry_run:
            print(f"  {colors.DIM}(dry-run — no files will be moved){colors.RESET}")

        total_moved = 0
        total_skipped = 0

        for step_from in range(from_major, to_major):
            step_to = step_from + 1
            moves = self._load_migration_record(step_from, step_to)
            if moves is None:
                print(
                    f"\n  {colors.DIM}v{step_from} → v{step_to}:"
                    f" no migration record, skipping{colors.RESET}"
                )
                continue
            print(f"\n  {colors.DIM}v{step_from} → v{step_to}{colors.RESET}")
            moved, skipped = self._apply_moves(
                moves=moves,
                project_root=project_root,
                artifacts_root=artifacts_root,
                dry_run=dry_run,
                colors=colors,
            )
            total_moved += moved
            total_skipped += skipped

        print(
            f"\n  {colors.BOLD}Done.{colors.RESET}  Moved: {total_moved}  Skipped: {total_skipped}"
        )
        return 0
