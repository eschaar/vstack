"""Install command wrapper."""

from __future__ import annotations

import datetime
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from vstack.cli.base import BaseCommand, CommandContext
from vstack.cli.constants import Colors
from vstack.cli.helpers import normalize_targeted_names
from vstack.constants import VERSION
from vstack.manifest import (
    Manifest,
    content_hash,
    hash_with_algorithm,
    preserve_existing_entry,
    preserved_manifest_entries,
)

if TYPE_CHECKING:
    from vstack.cli.service import CommandService


class InstallCommand(BaseCommand):
    """Install artifacts into the selected install directory."""

    def __init__(self, service: CommandService) -> None:
        self._service = service

    @staticmethod
    def _version_gt(new: str, existing: str | None) -> bool:
        """Return True when *new* semver string is strictly greater than *existing*."""

        def _tuple(v: str) -> tuple[int, ...]:
            """Convert a dotted version string to an integer tuple for comparison."""
            try:
                return tuple(int(x) for x in v.split("."))
            except (ValueError, AttributeError):
                return (0,)

        return _tuple(new) > _tuple(existing or "0")

    @staticmethod
    def _existing_entries_for_install(gens, existing_manifest: Manifest | None):
        """Build an existing-entry lookup for selected generators."""
        if existing_manifest is None:
            return {}

        existing_entries = {}
        for gen in gens:
            for entry in existing_manifest.entries_for(gen.config.manifest_key):
                key = f"{gen.config.type_name}/{entry.name}"
                existing_entries[key] = entry
        return existing_entries

    @staticmethod
    def _installed_content_matches(*, out_file: Path, existing_entry) -> bool | None:
        """Return whether on-disk content still matches the manifest checksum."""
        if not out_file.exists() or existing_entry.checksum is None:
            return None
        checksum_algorithm = (existing_entry.checksum_algorithm or "sha256").lower()
        try:
            return (
                hash_with_algorithm(out_file.read_text(encoding="utf-8"), checksum_algorithm)
                == existing_entry.checksum
            )
        except ValueError:
            return None

    @staticmethod
    def _install_decision(
        *,
        force: bool,
        force_name: bool,
        adopt_name: bool,
        update: bool,
        out_file: Path,
        existing_entry,
        new_version: str,
    ) -> tuple[str, str | None]:
        """Return install action and optional explanatory reason."""
        if force or force_name:
            return "install", None
        if not out_file.exists():
            return "install", None
        if existing_entry is None:
            if adopt_name:
                return "adopt", "existing file adopted into vstack manifest"
            return "preserve", "existing file is not tracked by vstack"
        current_matches = InstallCommand._installed_content_matches(
            out_file=out_file,
            existing_entry=existing_entry,
        )
        if current_matches is False:
            return "preserve", "local changes detected"
        if current_matches is None:
            return "preserve", "tracked file has no stored checksum"

        if not update:
            return "install", None

        if existing_entry.version is not None:
            return (
                ("update", None)
                if InstallCommand._version_gt(new_version, existing_entry.version)
                else ("skip", None)
            )
        return "preserve", "tracked file has no stored version"

    @staticmethod
    def _print_install_action(
        *,
        colors,
        prefix: str,
        rel: str,
        action: str,
        existing_version: str | None,
        new_version: str,
        out_file: Path,
        force: bool,
        force_name: bool = False,
        reason: str | None = None,
    ) -> None:
        """Print install/update/skip output line for one artifact."""
        if action == "adopt":
            print(
                f"  {colors.CYAN}≈{colors.RESET}  {rel}"
                f"  {colors.DIM}adopted — {reason}{colors.RESET}"
            )
            return

        if action == "preserve":
            force_hint = " Use --force or --force-name for this artifact."
            print(
                f"  {colors.YELLOW}↷{colors.RESET}  {rel}"
                f"  {colors.DIM}preserved — {reason}.{force_hint}{colors.RESET}"
            )
            return

        if action == "skip":
            print(
                f"  {colors.YELLOW}↷{colors.RESET}  {rel}"
                f"  {colors.DIM}skipped — already v{existing_version}{colors.RESET}"
            )
            return

        if action == "update":
            print(
                f"  {prefix}{colors.CYAN}↑{colors.RESET}  "
                f"{colors.BOLD}{rel}{colors.RESET}"
                f"  v{existing_version} → {colors.GREEN}v{new_version}{colors.RESET}"
            )
            return

        tag = "(forced) " if (force or force_name) and out_file.exists() else ""
        print(
            f"  {prefix}{colors.GREEN}✓{colors.RESET}  "
            f"{colors.BOLD}{rel}{colors.RESET}"
            f"  {colors.DIM}{tag}{colors.RESET}{colors.GREEN}v{new_version}{colors.RESET}"
        )

    @staticmethod
    def _record_manifest_entry(
        *,
        new_entries,
        gen,
        artifact_name: str,
        version: str,
        checksum: str,
        checksum_algorithm: str,
    ) -> None:
        """Append one installed artifact entry to in-memory manifest data."""
        from vstack.manifest import ArtifactEntry

        new_entries.setdefault(gen.config.manifest_key, []).append(
            ArtifactEntry(
                name=artifact_name,
                file=gen.install_relative_path(artifact_name),
                version=version,
                checksum=checksum,
                checksum_algorithm=checksum_algorithm,
            )
        )

    @staticmethod
    def _load_existing_manifest(
        *,
        service: CommandService,
        install_dir: Path,
        gens,
    ):
        """Read and validate current manifest state for an install run."""
        manifest_file = service.manifest_for(install_dir)
        existing_manifest = manifest_file.read()
        if existing_manifest is None and manifest_file.read_error:
            print(f"ERROR: {manifest_file.read_error}", file=sys.stderr)
            return None, None, None, None

        selected_manifest_keys = {gen.config.manifest_key for gen in gens}
        existing_entries = InstallCommand._existing_entries_for_install(gens, existing_manifest)
        new_entries = preserved_manifest_entries(
            existing_manifest,
            selected_manifest_keys,
        )
        return manifest_file, existing_manifest, existing_entries, new_entries

    @staticmethod
    def _install_single_artifact(
        *,
        service: CommandService,
        gen,
        artifact,
        out_dir: Path,
        colors,
        prefix: str,
        force: bool,
        update: bool,
        dry_run: bool,
        targeted_force_names: set[str],
        targeted_adopt_names: set[str],
        existing_entries,
        new_entries,
        checksum_algorithm: str,
    ) -> None:
        """Apply install decision flow for one rendered artifact."""
        out_file = out_dir / gen.output_path(artifact.name)
        new_version = (artifact.frontmatter or {}).get("version") or VERSION
        key = f"{gen.config.type_name}/{artifact.name}"
        existing_entry = existing_entries.get(key)
        existing_version = existing_entry.version if existing_entry is not None else None
        rel = service.label(out_file)
        force_name = artifact.name in targeted_force_names or rel in targeted_force_names
        adopt_name = artifact.name in targeted_adopt_names or rel in targeted_adopt_names

        if artifact.unresolved:
            print(
                f"  {colors.YELLOW}⚠{colors.RESET}  {rel}  unresolved: {artifact.unresolved}",
                file=sys.stderr,
            )

        action, reason = InstallCommand._install_decision(
            force=force,
            force_name=force_name,
            adopt_name=adopt_name,
            update=update,
            out_file=out_file,
            existing_entry=existing_entry,
            new_version=new_version,
        )

        InstallCommand._print_install_action(
            colors=colors,
            prefix=prefix,
            rel=rel,
            action=action,
            existing_version=existing_version,
            new_version=new_version,
            out_file=out_file,
            force=force,
            force_name=force_name,
            reason=reason,
        )

        if not dry_run and action in {"install", "update"}:
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(artifact.content, encoding="utf-8")

        if action in {"install", "update"}:
            InstallCommand._record_manifest_entry(
                new_entries=new_entries,
                gen=gen,
                artifact_name=artifact.name,
                version=new_version,
                checksum=content_hash(artifact.content),
                checksum_algorithm=checksum_algorithm,
            )
            return

        if action == "adopt" and out_file.exists():
            InstallCommand._record_manifest_entry(
                new_entries=new_entries,
                gen=gen,
                artifact_name=artifact.name,
                version=new_version,
                checksum=content_hash(out_file.read_text(encoding="utf-8")),
                checksum_algorithm=checksum_algorithm,
            )
            return

        if existing_entry is not None:
            preserve_existing_entry(
                new_entries=new_entries,
                manifest_key=gen.config.manifest_key,
                existing_entry=existing_entry,
            )

    @staticmethod
    def _write_manifest(
        *,
        service: CommandService,
        manifest_file,
        new_entries,
        checksum_algorithm: str,
        colors,
    ) -> None:
        """Persist the manifest after a non-dry-run install."""
        manifest = Manifest(
            manifest_version=2,
            hash_algorithm=checksum_algorithm,
            vstack_version=VERSION,
            installed_at=datetime.datetime.now(datetime.UTC).isoformat(),
            artifacts=new_entries,
        )
        manifest_file.write(manifest)
        print(f"  {colors.DIM}wrote  {service.label(manifest_file.path)}{colors.RESET}")

    @staticmethod
    def execute(
        service: CommandService,
        install_dir: Path,
        *,
        only: list[str] | None = None,
        force: bool = False,
        force_names: list[str] | None = None,
        adopt_names: list[str] | None = None,
        update: bool = False,
        dry_run: bool = False,
    ) -> int:
        """Generate and install artifacts into install_dir."""
        colors = Colors
        checksum_algorithm = "sha256"

        gens = [g for g in service.generators if only is None or g.config.type_name in only]
        targeted_force_names = normalize_targeted_names(force_names)
        targeted_adopt_names = normalize_targeted_names(adopt_names)

        manifest_file, _, existing_entries, new_entries = InstallCommand._load_existing_manifest(
            service=service,
            install_dir=install_dir,
            gens=gens,
        )
        if manifest_file is None or existing_entries is None or new_entries is None:
            return 1

        prefix = f"{colors.DIM}[dry-run]{colors.RESET} " if dry_run else ""
        all_ok = True

        for gen in gens:
            out_dir = install_dir / gen.config.output_subdir
            artifacts = gen.render_all()

            for artifact in artifacts:
                InstallCommand._install_single_artifact(
                    service=service,
                    gen=gen,
                    artifact=artifact,
                    out_dir=out_dir,
                    colors=colors,
                    prefix=prefix,
                    force=force,
                    update=update,
                    dry_run=dry_run,
                    targeted_force_names=targeted_force_names,
                    targeted_adopt_names=targeted_adopt_names,
                    existing_entries=existing_entries,
                    new_entries=new_entries,
                    checksum_algorithm=checksum_algorithm,
                )

            # Verify source for unresolvable issues.
            verify_result = gen.verify_input()
            for msg in verify_result.messages:
                if msg.level == "fail":
                    print(f"  ERROR [{gen.config.type_name}]: {msg.message}", file=sys.stderr)
                    all_ok = False

        if not dry_run:
            InstallCommand._write_manifest(
                service=service,
                manifest_file=manifest_file,
                new_entries=new_entries,
                checksum_algorithm=checksum_algorithm,
                colors=colors,
            )

        return 0 if all_ok else 1

    def run(
        self,
        *,
        context: CommandContext,
    ) -> int:
        install_dir = context.require_install_dir("install")

        return InstallCommand.execute(
            self._service,
            install_dir,
            only=context.only,
            force=getattr(context.args, "force", False),
            force_names=getattr(context.args, "force_names", None),
            adopt_names=getattr(context.args, "adopt_name", None),
            update=getattr(context.args, "update", False),
            dry_run=getattr(context.args, "dry_run", False),
        )
