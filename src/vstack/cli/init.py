"""Init command — idempotent artifact regeneration for CI and day-to-day use."""

from __future__ import annotations

import datetime
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from vstack.cli.base import BaseCommand, CommandContext
from vstack.cli.constants import Colors
from vstack.constants import VERSION
from vstack.manifest import (
    CURRENT_HASH_ALGORITHM,
    CURRENT_MANIFEST_VERSION,
    ArtifactEntry,
    Manifest,
    content_hash,
    hash_with_algorithm,
)

if TYPE_CHECKING:
    from vstack.cli.service import CommandService


class InitCommand(BaseCommand):
    """Regenerate and install artifacts idempotently into the selected install directory.

    ``vstack init`` is the day-to-day and CI regeneration command.  It is safe
    to re-run at any time — in CI pipelines and after ``pip install --upgrade vstack``.
    Conservative install semantics apply: untracked files are never overwritten,
    tracked files with local modifications are skipped and reported.
    """

    def __init__(self, service: CommandService) -> None:
        self._service = service

    @staticmethod
    def _version_gt(new: str, existing: str | None) -> bool:
        """Return ``True`` when *new* template revision is strictly greater than *existing*.

        Supported formats are numeric dot-separated revisions (legacy) and plain
        numeric revisions such as ``YYYYMMDDNNN``.
        """

        def _tuple(v: str) -> tuple[int, ...]:
            """Convert a version-like string to an integer tuple for comparison."""
            try:
                return tuple(int(x) for x in v.split("."))
            except (ValueError, AttributeError):
                return (0,)

        return _tuple(new) > _tuple(existing or "0")

    @staticmethod
    def _existing_entries_for_init(gens, existing_manifest: Manifest | None):
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
        checksum_algorithm = (existing_entry.checksum_algorithm or CURRENT_HASH_ALGORITHM).lower()
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
        current_matches = InitCommand._installed_content_matches(
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
                if InitCommand._version_gt(new_version, existing_entry.version)
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
                f"  {prefix}{colors.CYAN}≈{colors.RESET}  {rel}"
                f"  {colors.DIM}adopted — {reason}{colors.RESET}"
            )
            return

        if action == "preserve":
            print(
                f"  {prefix}{colors.YELLOW}↷{colors.RESET}  {rel}"
                f"  {colors.DIM}preserved — {reason}{colors.RESET}"
            )
            return

        if action == "skip":
            print(
                f"  {prefix}{colors.YELLOW}↷{colors.RESET}  {rel}"
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
        version: str | None,
        checksum: str,
        checksum_algorithm: str,
    ) -> None:
        """Append one installed artifact entry to in-memory manifest data."""
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
    def _adopted_manifest_values(
        *,
        out_file: Path,
    ) -> tuple[str | None, str] | None:
        """Return adopted version/checksum from on-disk content.

        Version is read from ``VSTACK-META.artifact_version`` when present.
        """
        from vstack.artifacts.generator import GenericArtifactGenerator

        try:
            content = out_file.read_text(encoding="utf-8")
        except OSError:
            return None

        metadata = GenericArtifactGenerator.parse_generation_metadata(content)
        adopted_version = metadata.get("artifact_version") if metadata else None
        return adopted_version, content_hash(content)

    @staticmethod
    def _load_existing_manifest(
        *,
        service: CommandService,
        install_dir: Path,
        gens,
    ):
        """Read and validate current manifest state for an init run."""
        manifest_file = service.manifest_for(install_dir)
        existing_manifest = manifest_file.read()
        if existing_manifest is None and manifest_file.read_error:
            print(f"ERROR: {manifest_file.read_error}", file=sys.stderr)
            return None, None, None, None

        selected_manifest_keys = {gen.config.manifest_key for gen in gens}
        existing_entries = InitCommand._existing_entries_for_init(gens, existing_manifest)
        new_entries = (
            existing_manifest.preserved_entries(selected_manifest_keys)
            if existing_manifest is not None
            else {}
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
    ) -> str:
        """Apply install decision flow for one rendered artifact and return the action taken."""
        out_file = out_dir / gen.output_path(artifact.name)
        new_version = str((artifact.frontmatter or {}).get("version") or VERSION)
        key = f"{gen.config.type_name}/{artifact.name}"
        existing_entry = existing_entries.get(key)
        existing_version = existing_entry.version if existing_entry is not None else None
        rel = service.label(out_file)
        force_name = (
            artifact.name in targeted_force_names
            or key in targeted_force_names
            or rel in targeted_force_names
        )
        adopt_name = (
            artifact.name in targeted_adopt_names
            or key in targeted_adopt_names
            or rel in targeted_adopt_names
        )
        adopted_values: tuple[str | None, str] | None = None

        if artifact.unresolved:
            print(
                f"  {colors.YELLOW}⚠{colors.RESET}  {rel}  unresolved: {artifact.unresolved}",
                file=sys.stderr,
            )

        action, reason = InitCommand._install_decision(
            force=force,
            force_name=force_name,
            adopt_name=adopt_name,
            update=update,
            out_file=out_file,
            existing_entry=existing_entry,
            new_version=new_version,
        )

        if action == "adopt" and out_file.exists():
            adopted_values = InitCommand._adopted_manifest_values(out_file=out_file)
            if adopted_values is None:
                action = "preserve"
                reason = "existing file is unreadable; could not adopt into vstack manifest"

        InitCommand._print_install_action(
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
            InitCommand._record_manifest_entry(
                new_entries=new_entries,
                gen=gen,
                artifact_name=artifact.name,
                version=new_version,
                checksum=content_hash(artifact.content),
                checksum_algorithm=checksum_algorithm,
            )
            return action

        if action == "adopt" and adopted_values is not None:
            adopted_version, adopted_checksum = adopted_values
            InitCommand._record_manifest_entry(
                new_entries=new_entries,
                gen=gen,
                artifact_name=artifact.name,
                version=adopted_version,
                checksum=adopted_checksum,
                checksum_algorithm=checksum_algorithm,
            )
            return action

        if existing_entry is not None:
            Manifest.preserve_existing_entry(
                new_entries=new_entries,
                manifest_key=gen.config.manifest_key,
                existing_entry=existing_entry,
            )
        return action

    @staticmethod
    def _write_manifest(
        *,
        service: CommandService,
        manifest_file,
        new_entries,
        checksum_algorithm: str,
        colors,
    ) -> None:
        """Persist the manifest after a non-dry-run init."""
        manifest = Manifest(
            manifest_version=CURRENT_MANIFEST_VERSION,
            hash_algorithm=checksum_algorithm,
            vstack_version=VERSION,
            installed_at=datetime.datetime.now(datetime.UTC).isoformat(),
            artifacts=new_entries,
        )
        manifest_file.write(manifest)
        print(f"  {colors.DIM}wrote  {service.label(manifest_file.path)}{colors.RESET}")

    @staticmethod
    def _obsolete_candidates(
        *,
        existing_manifest: Manifest | None,
        selected_manifest_keys: set[str],
        new_entries,
    ) -> list[tuple[str, ArtifactEntry]]:
        """Return tracked entries that are no longer produced by current templates.

        Candidates are entries for selected artifact families that existed in the
        previous manifest but are absent from the newly built entry set.
        """
        if existing_manifest is None:
            return []

        obsolete: list[tuple[str, ArtifactEntry]] = []
        for manifest_key in selected_manifest_keys:
            existing_by_name = {
                entry.name: entry for entry in existing_manifest.entries_for(manifest_key)
            }
            kept_names = {entry.name for entry in new_entries.get(manifest_key, [])}
            for artifact_name, entry in existing_by_name.items():
                if artifact_name not in kept_names:
                    obsolete.append((manifest_key, entry))
        return obsolete

    @staticmethod
    def _can_prune_obsolete_entry(*, install_dir: Path, entry) -> tuple[bool, str]:
        """Return whether an obsolete entry can be removed safely and why."""
        out_file = install_dir / entry.file
        if not out_file.exists():
            return True, "file already missing"

        if entry.checksum is None:
            return False, "tracked file has no stored checksum"

        checksum_algorithm = (entry.checksum_algorithm or CURRENT_HASH_ALGORITHM).lower()
        try:
            current = hash_with_algorithm(out_file.read_text(encoding="utf-8"), checksum_algorithm)
        except OSError:
            return False, "file is unreadable"
        except ValueError:
            return False, "unknown checksum algorithm"

        if current != entry.checksum:
            return False, "local changes detected"
        return True, ""

    @staticmethod
    def _remove_file_if_present(*, out_file: Path, dry_run: bool) -> None:
        """Remove one file and prune an empty parent directory when possible."""
        if dry_run:
            return

        out_file.unlink(missing_ok=True)
        parent = out_file.parent
        try:
            if parent.exists() and not any(parent.iterdir()):
                parent.rmdir()
        except OSError:
            pass

    @staticmethod
    def _process_obsolete_entry(
        *,
        install_dir: Path,
        manifest_key: str,
        type_name: str,
        entry: ArtifactEntry,
        prune: bool,
        dry_run: bool,
        colors,
        prefix: str,
        new_entries,
    ) -> tuple[str, bool]:
        """Handle one obsolete manifest entry and return (action, was_preserved)."""
        selector = f"{type_name}/{entry.name}"
        rel = str(entry.file)

        if not prune:
            print(
                f"  {prefix}{colors.YELLOW}?{colors.RESET}  {rel}"
                f"  {colors.DIM}obsolete candidate ({selector}) — run vstack init --prune to remove{colors.RESET}"
            )
            Manifest.preserve_existing_entry(
                new_entries=new_entries,
                manifest_key=manifest_key,
                existing_entry=entry,
            )
            return "obsolete", False

        removable, reason = InitCommand._can_prune_obsolete_entry(
            install_dir=install_dir,
            entry=entry,
        )
        if not removable:
            print(
                f"  {prefix}{colors.YELLOW}↷{colors.RESET}  {rel}"
                f"  {colors.DIM}obsolete preserved ({selector}) — {reason}{colors.RESET}"
            )
            Manifest.preserve_existing_entry(
                new_entries=new_entries,
                manifest_key=manifest_key,
                existing_entry=entry,
            )
            return "preserve", True

        reason_suffix = "" if reason == "" else f" — {reason}"
        print(
            f"  {prefix}{colors.CYAN}−{colors.RESET}  {rel}"
            f"  {colors.DIM}removed obsolete tracked artifact ({selector}){reason_suffix}{colors.RESET}"
        )
        InitCommand._remove_file_if_present(
            out_file=install_dir / entry.file,
            dry_run=dry_run,
        )
        return "prune", False

    @staticmethod
    def _print_summary(
        *,
        colors,
        action_counts: dict[str, int],
        preserved_selectors: list[str],
        dry_run: bool,
        prune: bool,
    ) -> None:
        """Print a readable summary and conflict guidance after an init run."""
        installed = action_counts.get("install", 0)
        updated = action_counts.get("update", 0)
        preserved = action_counts.get("preserve", 0)
        skipped = action_counts.get("skip", 0)
        adopted = action_counts.get("adopt", 0)
        obsolete = action_counts.get("obsolete", 0)
        pruned = action_counts.get("prune", 0)

        install_label = "installed"
        summary_title = "Summary (dry-run)" if dry_run else "Summary"
        total = installed + updated + preserved + skipped + adopted + obsolete

        print()
        print(f"  {colors.BOLD}{summary_title}{colors.RESET}")
        print(f"    total processed : {colors.BOLD}{total}{colors.RESET}")
        print(f"    {install_label:<15}: {colors.BOLD}{installed}{colors.RESET}")
        print(f"    updated         : {colors.BOLD}{updated}{colors.RESET}")
        print(f"    preserved       : {colors.BOLD}{preserved}{colors.RESET}")
        print(f"    skipped         : {colors.BOLD}{skipped}{colors.RESET}")
        print(f"    adopted         : {colors.BOLD}{adopted}{colors.RESET}")
        print(f"    obsolete        : {colors.BOLD}{obsolete}{colors.RESET}")
        print(f"    pruned          : {colors.BOLD}{pruned}{colors.RESET}")

        if obsolete and not prune:
            print()
            print(
                f"  {colors.YELLOW}⚠{colors.RESET}  "
                "obsolete candidates were reported and preserved in manifest state."
            )
            print("  Next step:")
            print(
                f"     {colors.DIM}vstack init --prune{colors.RESET}  remove safe obsolete artifacts"
            )

        if preserved:
            noun = "file" if preserved == 1 else "files"
            selectors_suffix = " Preserved selectors:" if preserved_selectors else ""
            print()
            print(
                f"  {colors.YELLOW}⚠{colors.RESET}  "
                f"{preserved} {noun} preserved — existing files were not overwritten."
                f"{selectors_suffix}"
            )
            if preserved_selectors:
                for selector in sorted(preserved_selectors):
                    print(f"     - {selector}")
            print("  Next steps:")
            print(f"     {colors.DIM}--force{colors.RESET}               overwrite all")
            print(
                f"     {colors.DIM}--force-name <name|type/name>{colors.RESET} "
                "overwrite one artifact"
            )
            print(
                f"     {colors.DIM}--adopt-name <name|type/name>{colors.RESET} "
                "take ownership without overwriting"
            )

    @staticmethod
    def _warn_unknown_workflow_roles(
        *,
        workflow_stages: list[dict[str, str]],
        known_agent_names: set[str],
        colors,
    ) -> None:
        """Emit a warning for any workflow stage that references an unknown agent.

        Unknown roles are not fatal — a project may define custom agents.
        The warning is informational only and does not affect the exit code.

        :param workflow_stages: Parsed stage list from ``workflow.stages``.
        :param known_agent_names: Agent names available in the current template root.
        :param colors: CLI colours helper.
        """
        for stage in workflow_stages:
            role = stage.get("role", "")
            if role and role not in known_agent_names:
                print(
                    f"  {colors.YELLOW}⚠{colors.RESET}  workflow: unknown role "
                    f"{colors.BOLD}{role!r}{colors.RESET} — no matching agent template found",
                    file=sys.stderr,
                )

    @staticmethod
    def _prune_planner_when_manual_mode(
        *,
        install_dir: Path,
        gen,
        existing_entries,
        new_entries,
        colors,
        prefix: str,
        dry_run: bool,
    ) -> None:
        """Remove tracked planner artifact when agent workflow mode is ``manual``.

        In manual mode planner is not generated. If a tracked planner file
        exists from a previous non-manual mode, remove it when unchanged.
        Locally modified planner files are preserved and kept tracked.
        """
        if gen.config.type_name != "agent":
            return
        if getattr(gen, "workflow_mode", "manual") != "manual":
            return

        existing_entry = existing_entries.get("agent/planner")
        if existing_entry is None:
            return

        planner_file = install_dir / existing_entry.file
        rel = str(existing_entry.file)

        if not planner_file.exists():
            return

        removable = True
        checksum = existing_entry.checksum
        if checksum:
            checksum_algorithm = (existing_entry.checksum_algorithm or "sha256").lower()
            try:
                current = hash_with_algorithm(
                    planner_file.read_text(encoding="utf-8"), checksum_algorithm
                )
                removable = current == checksum
            except (OSError, ValueError):
                removable = False

        if not removable:
            print(
                f"  {prefix}{colors.YELLOW}↷{colors.RESET}  {rel}"
                f"  {colors.DIM}preserved — local changes detected{colors.RESET}"
            )
            Manifest.preserve_existing_entry(
                new_entries=new_entries,
                manifest_key=gen.config.manifest_key,
                existing_entry=existing_entry,
            )
            return

        print(
            f"  {prefix}{colors.CYAN}−{colors.RESET}  {rel}"
            f"  {colors.DIM}removed — planner disabled in workflow.mode=manual{colors.RESET}"
        )
        if not dry_run:
            planner_file.unlink(missing_ok=True)
            parent = planner_file.parent
            try:
                if parent.exists() and not any(parent.iterdir()):
                    parent.rmdir()
            except OSError:
                pass

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
        prune: bool = False,
        dry_run: bool = False,
        excluded_names: dict[str, list[str]] | None = None,
    ) -> int:
        """Generate and install artifacts idempotently into *install_dir*.

        :param excluded_names: Optional mapping of singular type name
            (e.g. ``"skill"``) to a list of artifact names to skip for that
            type.  Populated from the ``exclude:`` block in
            ``.vstack/config.yaml`` and applied before any install action.
            Excluded artifacts are reported on screen but not written to disk
            and not recorded in the manifest.
        """
        colors = Colors
        checksum_algorithm = CURRENT_HASH_ALGORITHM

        gens = [g for g in service.generators if only is None or g.config.type_name in only]
        targeted_force_names = InitCommand._normalize_targeted_names(force_names)
        targeted_adopt_names = InitCommand._normalize_targeted_names(adopt_names)

        # Validate workflow stages against known agent names (warning only).
        from vstack.agents.generator import AgentGenerator

        for gen in service.generators:
            if isinstance(gen, AgentGenerator) and gen.workflow_stages:
                known_names = {p.name for p in gen.find_templates()}
                InitCommand._warn_unknown_workflow_roles(
                    workflow_stages=gen.workflow_stages,
                    known_agent_names=known_names,
                    colors=colors,
                )
                break

        manifest_file, existing_manifest, existing_entries, new_entries = (
            InitCommand._load_existing_manifest(
                service=service,
                install_dir=install_dir,
                gens=gens,
            )
        )
        if manifest_file is None or existing_entries is None or new_entries is None:
            return 1

        prefix = f"{colors.DIM}[dry-run]{colors.RESET} " if dry_run else ""
        all_ok = True
        action_counts: dict[str, int] = {}
        preserved_selectors: set[str] = set()

        for gen in gens:
            out_dir = install_dir / gen.config.output_subdir
            artifacts = gen.render_all()

            for artifact in artifacts:
                if excluded_names and artifact.name in excluded_names.get(gen.config.type_name, []):
                    out_file = out_dir / gen.install_relative_path(artifact.name)
                    rel = service.label(out_file)
                    print(
                        f"  {prefix}{colors.DIM}↷{colors.RESET}  {rel}"
                        f"  {colors.DIM}excluded by config{colors.RESET}"
                    )
                    continue
                artifact_action = InitCommand._install_single_artifact(
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
                action_counts[artifact_action] = action_counts.get(artifact_action, 0) + 1
                if artifact_action == "preserve":
                    preserved_selectors.add(f"{gen.config.type_name}/{artifact.name}")

            InitCommand._prune_planner_when_manual_mode(
                install_dir=install_dir,
                gen=gen,
                existing_entries=existing_entries,
                new_entries=new_entries,
                colors=colors,
                prefix=prefix,
                dry_run=dry_run,
            )

            # Verify source for unresolvable issues.
            verify_result = gen.verify_input()
            for msg in verify_result.messages:
                if msg.level == "fail":
                    print(f"  ERROR [{gen.config.type_name}]: {msg.message}", file=sys.stderr)
                    all_ok = False

        selected_manifest_keys = {gen.config.manifest_key for gen in gens}
        type_name_by_manifest_key = {gen.config.manifest_key: gen.config.type_name for gen in gens}
        for manifest_key, entry in InitCommand._obsolete_candidates(
            existing_manifest=existing_manifest,
            selected_manifest_keys=selected_manifest_keys,
            new_entries=new_entries,
        ):
            action_counts["obsolete"] = action_counts.get("obsolete", 0) + 1
            type_name = type_name_by_manifest_key.get(manifest_key, manifest_key.rstrip("s"))
            obsolete_action, was_preserved = InitCommand._process_obsolete_entry(
                install_dir=install_dir,
                manifest_key=manifest_key,
                type_name=type_name,
                entry=entry,
                prune=prune,
                dry_run=dry_run,
                colors=colors,
                prefix=prefix,
                new_entries=new_entries,
            )
            if obsolete_action == "prune":
                action_counts["prune"] = action_counts.get("prune", 0) + 1
            elif obsolete_action == "preserve":
                action_counts["preserve"] = action_counts.get("preserve", 0) + 1
            if was_preserved:
                preserved_selectors.add(f"{type_name}/{entry.name}")

        InitCommand._print_summary(
            colors=colors,
            action_counts=action_counts,
            preserved_selectors=sorted(preserved_selectors),
            dry_run=dry_run,
            prune=prune,
        )

        if not dry_run:
            InitCommand._write_manifest(
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
        """Execute the init command and return a process-style status code."""
        install_dir = context.require_install_dir("init")

        return InitCommand.execute(
            self._service,
            install_dir,
            only=context.only,
            excluded_names=context.excluded_names,
            force=getattr(context.args, "force", False),
            force_names=getattr(context.args, "force_names", None),
            adopt_names=getattr(context.args, "adopt_name", None),
            update=getattr(context.args, "update", False),
            prune=getattr(context.args, "prune", False),
            dry_run=getattr(context.args, "dry_run", False),
        )
