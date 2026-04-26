"""Uninstall command wrapper."""

from __future__ import annotations

import datetime
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from vstack.cli.base import BaseCommand, CommandContext
from vstack.cli.constants import ArtifactState
from vstack.cli.helpers import normalize_targeted_names
from vstack.constants import VERSION
from vstack.manifest import Manifest, preserve_existing_entry, preserved_manifest_entries

if TYPE_CHECKING:
    from vstack.cli.service import CommandService


class UninstallCommand(BaseCommand):
    """Uninstall tracked artifacts from the selected install directory."""

    def __init__(self, service: CommandService) -> None:
        self._service = service

    @staticmethod
    def _remove_or_preserve_entry(
        *,
        service: CommandService,
        gen,
        out_dir: Path,
        install_dir: Path,
        entry,
        force: bool,
        targeted_force_names: set[str],
        removed: list[str],
        preserved: list[str],
        new_entries: dict,
    ) -> None:
        """Handle uninstall decision for one manifest-tracked artifact."""
        full_path = install_dir / entry.file
        force_name = (
            entry.name in targeted_force_names or service.label(full_path) in targeted_force_names
        )
        state, message = service.artifact_control_state(
            out_file=full_path,
            existing_entry=entry,
        )

        if (
            state in {ArtifactState.MANAGED, ArtifactState.MANAGED_LEGACY, ArtifactState.MISSING}
            or force
            or force_name
        ):
            if full_path.exists():
                full_path.unlink()
                removed.append(service.label(full_path))
            if gen.config.artifact_is_dir:
                artifact_dir = full_path.parent
                if (
                    artifact_dir.exists()
                    and artifact_dir != out_dir
                    and not any(artifact_dir.iterdir())
                ):
                    artifact_dir.rmdir()
                    removed.append(service.label(artifact_dir))
            return

        preserved.append(message)
        preserve_existing_entry(
            new_entries=new_entries,
            manifest_key=gen.config.manifest_key,
            existing_entry=entry,
        )

    @staticmethod
    def _write_updated_manifest(
        *,
        service: CommandService,
        manifest_file,
        manifest_data,
        new_entries: dict[str, list],
        removed: list[str],
    ) -> None:
        """Persist updated manifest data after uninstall decisions are applied."""
        if new_entries:
            manifest = Manifest(
                manifest_version=manifest_data.manifest_version,
                hash_algorithm=manifest_data.hash_algorithm,
                vstack_version=VERSION,
                installed_at=datetime.datetime.now(datetime.UTC).isoformat(),
                artifacts=new_entries,
            )
            manifest_file.write(manifest)
            return

        if manifest_file.exists():
            manifest_file.path.unlink()
            removed.append(service.label(manifest_file.path))

    @staticmethod
    def _print_summary(*, removed: list[str], preserved: list[str]) -> None:
        """Render uninstall summary output."""
        if removed:
            for path in removed:
                print(f"  removed  {path}")
        if preserved:
            for message in preserved:
                print(f"  preserved  {message}. Use --force or --force-name to remove it anyway.")
        if not removed and not preserved:
            print("Nothing to remove.")

    @staticmethod
    def execute(
        service: CommandService,
        install_dir: Path,
        *,
        only: list[str] | None = None,
        force: bool = False,
        force_names: list[str] | None = None,
    ) -> int:
        """Remove tracked files whose ownership still matches the manifest."""
        removed: list[str] = []
        preserved: list[str] = []
        manifest_file = service.manifest_for(install_dir)
        manifest_data = manifest_file.read()
        gens = [g for g in service.generators if only is None or g.config.type_name in only]
        targeted_force_names = normalize_targeted_names(force_names)

        if manifest_data is None:
            if manifest_file.read_error:
                print(f"ERROR: {manifest_file.read_error}", file=sys.stderr)
                return 1
            print("Nothing to remove.")
            return 0

        selected_manifest_keys = {gen.config.manifest_key for gen in gens}
        new_entries = preserved_manifest_entries(
            manifest_data,
            selected_manifest_keys,
        )

        for gen in gens:
            out_dir = install_dir / gen.config.output_subdir
            entries = manifest_data.entries_for(gen.config.manifest_key)

            for entry in entries:
                UninstallCommand._remove_or_preserve_entry(
                    service=service,
                    gen=gen,
                    out_dir=out_dir,
                    install_dir=install_dir,
                    entry=entry,
                    force=force,
                    targeted_force_names=targeted_force_names,
                    removed=removed,
                    preserved=preserved,
                    new_entries=new_entries,
                )

            if out_dir.exists() and not any(out_dir.iterdir()):
                out_dir.rmdir()
                removed.append(service.label(out_dir) + "/")

        UninstallCommand._write_updated_manifest(
            service=service,
            manifest_file=manifest_file,
            manifest_data=manifest_data,
            new_entries=new_entries,
            removed=removed,
        )
        UninstallCommand._print_summary(removed=removed, preserved=preserved)
        return 0

    def run(
        self,
        *,
        context: CommandContext,
    ) -> int:
        install_dir = context.require_install_dir("uninstall")

        return UninstallCommand.execute(
            self._service,
            install_dir,
            only=context.only,
            force=getattr(context.args, "force", False),
            force_names=getattr(context.args, "force_names", None),
        )
