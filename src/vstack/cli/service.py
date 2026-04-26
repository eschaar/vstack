"""All vstack CLI commands as instance methods on :class:`CommandService`.

The CLI is entirely type-generic: it iterates over
:data:`~vstack.artifacts.type_config.KNOWN_TYPES` for validate, install, and
verify instead of hard-coding skill-specific and agent-specific logic.

All commands that touch the install root accept a single ``install_dir``
(either workspace ``.github/`` or the VS Code user profile directory)
rather than separate ``skills_dir`` / ``agents_dir`` parameters — per-type
sub-directories are derived from
:attr:`~vstack.artifacts.type_config.ArtifactTypeConfig.output_subdir`.
"""

from __future__ import annotations

import sys
from pathlib import Path

from vstack.artifacts.generator import GenericArtifactGenerator
from vstack.cli.constants import KNOWN_TYPES, ArtifactState
from vstack.manifest import CURRENT_MANIFEST_VERSION, ManifestFile, hash_with_algorithm


class CommandService:
    """Coordinate validation, installation, verification, and uninstall flows.

    The class wires artifact-type generators into user-facing CLI operations,
    while keeping per-type behavior in ``ArtifactTypeConfig`` definitions.
    """

    def __init__(self, templates_root: Path) -> None:
        """Create generators for all known artifact families.

        Args:
            templates_root: Root directory containing the source templates.
        """
        self.root = templates_root
        self.generators: list[GenericArtifactGenerator] = [
            GenericArtifactGenerator(tc, templates_root) for tc in KNOWN_TYPES
        ]

    # ── Shared helpers ───────────────────────────────────────────────────────

    def label(self, path: Path) -> str:
        """Return *path* relative to template root when possible."""
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return str(path)

    def manifest_for(self, install_dir: Path):
        """Build the manifest accessor for a given install directory."""
        return ManifestFile(parent_dir=install_dir)

    def gen_for(self, type_name: str) -> GenericArtifactGenerator | None:
        """Return the generator for *type_name*, or ``None`` when unknown."""
        return next((g for g in self.generators if g.config.type_name == type_name), None)

    def artifact_control_state(
        self,
        *,
        out_file: Path,
        existing_entry,
    ) -> tuple[str, str]:
        """Classify ownership and drift state for one installed artifact path."""
        rel_path = self.label(out_file)

        if existing_entry is None:
            if out_file.exists():
                return (
                    ArtifactState.UNTRACKED,
                    f"{rel_path}: file exists but is not tracked by vstack",
                )
            return ArtifactState.ABSENT, f"{rel_path}: file is absent and not tracked by vstack"

        if not out_file.exists():
            return ArtifactState.MISSING, f"{rel_path}: tracked file missing from disk"

        if existing_entry.checksum is None:
            return (
                ArtifactState.MANAGED_LEGACY,
                f"{rel_path}: tracked legacy entry without checksum; treated as managed",
            )

        checksum_algorithm = (existing_entry.checksum_algorithm or "sha256").lower()
        try:
            current_checksum = hash_with_algorithm(
                out_file.read_text(encoding="utf-8"),
                checksum_algorithm,
            )
        except ValueError:
            return (
                ArtifactState.UNKNOWN,
                f"{rel_path}: unsupported checksum algorithm '{checksum_algorithm}' in manifest",
            )
        except OSError as exc:
            return (
                ArtifactState.UNKNOWN,
                f"{rel_path}: could not read file — {exc}",
            )

        if current_checksum == existing_entry.checksum:
            return ArtifactState.MANAGED, f"{rel_path}: checksum matches manifest"

        return ArtifactState.MODIFIED, f"{rel_path}: checksum differs from manifest"

    # ── validate ──────────────────────────────────────────────────────────────

    def validate(self, only: list[str] | None = None) -> int:
        """Render all templates in memory; report unresolved tokens. No files written."""
        from vstack.cli.validate import ValidateCommand

        return ValidateCommand.execute(self, only=only)

    # ── install ───────────────────────────────────────────────────────────────

    def install(
        self,
        install_dir: Path,
        *,
        only: list[str] | None = None,
        force: bool = False,
        force_names: list[str] | None = None,
        adopt_names: list[str] | None = None,
        update: bool = False,
        dry_run: bool = False,
    ) -> int:
        """Generate and install artifacts into install_dir.

        Args:
            install_dir: Workspace ``.github/`` or VS Code user profile install root.
            only:        Optional list of type names to restrict installation.
            force:       Overwrite existing artifacts unconditionally.
            force_names: Overwrite only the named artifacts, even when locally modified.
            adopt_names: Adopt only the named unmanaged artifacts into manifest tracking.
            update:      Install only when a newer version is available.
            dry_run:     Print what would happen without writing any files.
        """
        from vstack.cli.install import InstallCommand

        return InstallCommand.execute(
            self,
            install_dir,
            only=only,
            force=force,
            force_names=force_names,
            adopt_names=adopt_names,
            update=update,
            dry_run=dry_run,
        )

    # ── verify ────────────────────────────────────────────────────────────────

    def verify(
        self,
        install_dir: Path | None = None,
        *,
        source: bool = True,
        output: bool = True,
        only: list[str] | None = None,
    ) -> int:
        """Check source templates and/or installed output.

        Args:
            install_dir: Workspace ``.github/`` or VS Code user profile install root.
            source:      Verify source templates (metadata, tokens, structure).
            output:      Verify installed output files against the manifest.
            only:        Optional list of type names to restrict verification.
        """
        from vstack.cli.verify import VerifyCommand

        return VerifyCommand.execute(
            self,
            install_dir=install_dir,
            source=source,
            output=output,
            only=only,
        )

    def status(
        self,
        install_dir: Path,
        *,
        only: list[str] | None = None,
        output_format: str = "text",
        verbose: bool = False,
        no_color: bool = False,
    ) -> int:
        """Report which installed artifacts still match the manifest and which do not."""
        from vstack.cli.status import StatusCommand

        return StatusCommand.execute(
            self,
            install_dir=install_dir,
            only=only,
            output_format=output_format,
            verbose=verbose,
            no_color=no_color,
        )

    def manifest_upgrade(self, install_dir: Path, *, backfill: bool = False) -> int:
        """Upgrade a legacy manifest schema to the current schema version."""
        manifest_file = self.manifest_for(install_dir)
        manifest_data = manifest_file.read(allow_legacy=True)

        if manifest_data is None:
            if manifest_file.read_error:
                print(f"ERROR: {manifest_file.read_error}", file=sys.stderr)
                return 1
            print("No manifest found to upgrade.")
            return 1

        needs_upgrade = manifest_data.needs_upgrade()
        if not needs_upgrade and not backfill:
            print(f"Manifest already up to date at schema v{manifest_data.manifest_version}.")
            return 0

        upgraded = manifest_data.upgraded() if needs_upgrade else manifest_data
        backfilled: list[str] = []
        skipped: list[str] = []
        if backfill:
            upgraded, backfilled, skipped = upgraded.with_backfilled_checksums(
                install_dir=install_dir,
            )

        manifest_file.write(upgraded)

        if needs_upgrade:
            print(
                f"Upgraded manifest to schema v{CURRENT_MANIFEST_VERSION}: "
                f"{self.label(manifest_file.path)}"
            )
        else:
            print(f"Manifest schema already current at v{upgraded.manifest_version}.")

        if backfill:
            print(
                f"Backfilled checksums for {len(backfilled)} tracked artifact(s); "
                f"skipped {len(skipped)}."
            )
            for item in skipped:
                print(f"  ! {item}")
        return 0

    # ── uninstall ─────────────────────────────────────────────────────────────

    def uninstall(
        self,
        install_dir: Path,
        *,
        only: list[str] | None = None,
        force: bool = False,
        force_names: list[str] | None = None,
    ) -> int:
        """Remove tracked files whose ownership still matches the manifest."""
        from vstack.cli.uninstall import UninstallCommand

        return UninstallCommand.execute(
            self,
            install_dir,
            only=only,
            force=force,
            force_names=force_names,
        )
