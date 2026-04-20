"""All vstack CLI commands as instance methods on :class:`CommandLineInterface`.

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

import datetime
import shutil
import sys
from pathlib import Path

from vstack.agents.config import AGENT_TYPE
from vstack.artifacts.generator import GenericArtifactGenerator
from vstack.cli.constants import EXPECTED_CANONICAL_NAMES
from vstack.cli.manifest import ArtifactEntry, Manifest, ManifestFile
from vstack.constants import VERSION
from vstack.instructions.config import INSTRUCTION_TYPE
from vstack.models import CheckMessage, ValidationResult
from vstack.prompts.config import PROMPT_TYPE
from vstack.skills.config import SKILL_TYPE

KNOWN_TYPES = [SKILL_TYPE, AGENT_TYPE, INSTRUCTION_TYPE, PROMPT_TYPE]

# Names that must exist for the "skill" artifact type (used in verify --source).
_EXPECTED_INPUT_NAMES: dict[str, list[str]] = {
    "skill": EXPECTED_CANONICAL_NAMES,
}


class _Colors:
    """ANSI colour codes used in install output."""

    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def _version_gt(new: str, existing: str) -> bool:
    """Return True when *new* semver string is strictly greater than *existing*."""

    def _t(v: str) -> tuple[int, ...]:
        """Convert a dotted version string to an integer tuple for comparison.

        Invalid or non-semver-like inputs collapse to ``(0,)`` so the caller
        can treat them as older than any valid semantic version.
        """
        try:
            return tuple(int(x) for x in v.split("."))
        except (ValueError, AttributeError):
            return (0,)

    return _t(new) > _t(existing)


class CommandLineInterface:
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
        self._generators: list[GenericArtifactGenerator] = [
            GenericArtifactGenerator(tc, templates_root) for tc in KNOWN_TYPES
        ]

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _label(self, path: Path) -> str:
        """Return *path* relative to template root when possible.

        This keeps CLI output concise while still handling absolute paths that
        are outside the template tree.
        """
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return str(path)

    def _manifest(self, install_dir: Path) -> ManifestFile:
        """Build the manifest accessor for a given install directory."""
        return ManifestFile(parent_dir=install_dir)

    def _gen_for(self, type_name: str) -> GenericArtifactGenerator | None:
        """Return the generator for *type_name*, or ``None`` when unknown."""
        return next((g for g in self._generators if g.config.type_name == type_name), None)

    def _expected_output_names(
        self,
        gen: GenericArtifactGenerator,
        manifest_data: Manifest | None,
    ) -> list[str] | None:
        """Resolve expected output names for verify output checks."""
        if manifest_data:
            return manifest_data.names_for(gen.config.manifest_key)
        return _EXPECTED_INPUT_NAMES.get(gen.config.type_name)

    def _expected_manifest_metadata(
        self,
        gen: GenericArtifactGenerator,
        manifest_data: Manifest,
        entry: ArtifactEntry,
    ) -> dict[str, str]:
        """Build expected metadata values for one manifest-tracked artifact."""
        expected_meta = {
            "generator": "vstack",
            "vstack_version": manifest_data.vstack_version,
            "artifact_type": gen.config.type_name,
            "artifact_name": entry.name,
        }
        if entry.version is not None:
            expected_meta["artifact_version"] = entry.version
        return expected_meta

    def _verify_manifest_metadata_entry(
        self,
        gen: GenericArtifactGenerator,
        manifest_data: Manifest,
        entry: ArtifactEntry,
        artifact_path: Path,
    ) -> ValidationResult:
        """Verify manifest-linked metadata for a single artifact file."""
        result = ValidationResult()
        content = artifact_path.read_text(encoding="utf-8")
        metadata = GenericArtifactGenerator.parse_generation_metadata(content)
        rel_path = self._label(artifact_path)

        if metadata is None:
            if "AUTO-GENERATED" not in content:
                result.messages.append(
                    CheckMessage(
                        "fail",
                        f"{rel_path}: missing VSTACK-META and missing AUTO-GENERATED footer",
                    )
                )
                return result

            result.messages.append(
                CheckMessage(
                    "pass",
                    f"{rel_path}: missing VSTACK-META footer; "
                    "treating manifest entry as source of truth",
                )
            )
            result.messages.append(
                CheckMessage(
                    "pass",
                    f"{rel_path}: legacy artifact accepted from manifest tracking",
                )
            )
            return result

        for key, expected_value in self._expected_manifest_metadata(
            gen, manifest_data, entry
        ).items():
            actual_value = metadata.get(key)
            if actual_value == expected_value:
                result.messages.append(CheckMessage("pass", f"{rel_path}: {key} matches manifest"))
            else:
                result.messages.append(
                    CheckMessage(
                        "fail",
                        f"{rel_path}: {key} mismatch "
                        f"(expected '{expected_value}', got '{actual_value}')",
                    )
                )

        return result

    def _verify_manifest_metadata(
        self,
        gen: GenericArtifactGenerator,
        manifest_data: Manifest,
        install_dir: Path,
    ) -> ValidationResult | None:
        """Verify footer metadata for all manifest-tracked artifacts of one type."""
        manifest_entries = manifest_data.entries_for(gen.config.manifest_key)
        if not manifest_entries:
            return None

        result = ValidationResult()
        for entry in manifest_entries:
            artifact_path = install_dir / entry.file
            if not artifact_path.exists():
                continue
            entry_result = self._verify_manifest_metadata_entry(
                gen,
                manifest_data,
                entry,
                artifact_path,
            )
            result.messages.extend(entry_result.messages)

        return result if result.messages else None

    # ── validate ──────────────────────────────────────────────────────────────

    def validate(self, only: list[str] | None = None) -> int:
        """Render all templates in memory; report unresolved tokens. No files written."""
        gens = [g for g in self._generators if only is None or g.config.type_name in only]
        all_artifacts: dict[str, list] = {}
        total_partials = 0
        for gen in gens:
            artifacts = gen.render_all()
            all_artifacts[gen.config.type_name] = artifacts
            total_partials += len(gen.load_partials())

        if not any(all_artifacts.values()):
            print("ERROR: No templates found", file=sys.stderr)
            return 1

        errors: list = []
        for type_name, artifacts in all_artifacts.items():
            type_gen = self._gen_for(type_name)
            if type_gen is None:
                continue
            print(f"\n{type_name.capitalize()} ({len(artifacts)}):")
            for a in artifacts:
                suffix = f"  ⚠ unresolved: {a.unresolved}" if a.unresolved else ""
                print(f"  {type_gen.output_path(a.name)}{suffix}")
            errors.extend(a for a in artifacts if a.unresolved)

        total = sum(len(v) for v in all_artifacts.values())
        if errors:
            print(
                f"\nERROR: {len(errors)} template(s) have unresolved placeholders",
                file=sys.stderr,
            )
            return 1
        print(f"\nOK: {total} artifact(s), {total_partials} partial(s)")
        return 0

    # ── install ───────────────────────────────────────────────────────────────

    def install(
        self,
        install_dir: Path,
        *,
        only: list[str] | None = None,
        force: bool = False,
        update: bool = False,
        dry_run: bool = False,
    ) -> int:
        """Generate and install artifacts into install_dir.

        Args:
            install_dir: Workspace ``.github/`` or VS Code user profile install root.
            only:        Optional list of type names to restrict installation.
            force:       Overwrite existing artifacts unconditionally.
            update:      Install only when a newer version is available.
            dry_run:     Print what would happen without writing any files.
        """
        _C = _Colors

        gens = [g for g in self._generators if only is None or g.config.type_name in only]

        # Read existing manifest once — used to look up installed versions.
        mf = self._manifest(install_dir)
        existing_manifest = mf.read()
        existing_versions: dict[str, str | None] = {}
        selected_manifest_keys = {gen.config.manifest_key for gen in gens}
        if existing_manifest:
            for gen in gens:
                for entry in existing_manifest.entries_for(gen.config.manifest_key):
                    key = f"{gen.config.type_name}/{entry.name}"
                    existing_versions[key] = entry.version

        prefix = f"{_C.DIM}[dry-run]{_C.RESET} " if dry_run else ""
        all_ok = True
        new_entries: dict[str, list[ArtifactEntry]] = {}
        if existing_manifest:
            # Keep manifest entries for artifact families not part of this install run
            # (e.g. install --only instruction should not drop agents/skills entries).
            for manifest_key, entries in existing_manifest.artifacts.items():
                if manifest_key not in selected_manifest_keys:
                    new_entries[manifest_key] = list(entries)

        for gen in gens:
            out_dir = install_dir / gen.config.output_subdir
            artifacts = gen.render_all()

            for artifact in artifacts:
                out_file = out_dir / gen.output_path(artifact.name)
                new_version = (artifact.frontmatter or {}).get("version") or VERSION
                key = f"{gen.config.type_name}/{artifact.name}"
                existing_version = existing_versions.get(key)
                rel = self._label(out_file)

                # Unresolved placeholder warnings always shown.
                if artifact.unresolved:
                    print(
                        f"  {_C.YELLOW}⚠{_C.RESET}  {rel}  unresolved: {artifact.unresolved}",
                        file=sys.stderr,
                    )

                # Decide action.
                action: str  # "install" | "skip" | "update"
                if force:
                    action = "install"
                elif out_file.exists() and existing_version is not None:
                    if update:
                        action = "update" if _version_gt(new_version, existing_version) else "skip"
                    else:
                        action = "skip"
                else:
                    action = "install"

                if action == "skip":
                    print(
                        f"  {_C.YELLOW}↷{_C.RESET}  {rel}"
                        f"  {_C.DIM}skipped — already v{existing_version}{_C.RESET}"
                    )
                elif action == "update":
                    print(
                        f"  {prefix}{_C.CYAN}↑{_C.RESET}  "
                        f"{_C.BOLD}{rel}{_C.RESET}"
                        f"  v{existing_version} → {_C.GREEN}v{new_version}{_C.RESET}"
                    )
                else:
                    tag = "(forced) " if force and out_file.exists() else ""
                    print(
                        f"  {prefix}{_C.GREEN}✓{_C.RESET}  "
                        f"{_C.BOLD}{rel}{_C.RESET}"
                        f"  {_C.DIM}{tag}{_C.RESET}{_C.GREEN}v{new_version}{_C.RESET}"
                    )

                if not dry_run and action != "skip":
                    out_dir.mkdir(parents=True, exist_ok=True)
                    out_file.parent.mkdir(parents=True, exist_ok=True)
                    out_file.write_text(artifact.content, encoding="utf-8")

                new_entries.setdefault(gen.config.manifest_key, []).append(
                    ArtifactEntry(
                        name=artifact.name,
                        file=gen.install_relative_path(artifact.name),
                        version=new_version,
                    )
                )

            # Verify source for unresolvable issues.
            vr = gen.verify_input()
            for msg in vr.messages:
                if msg.level == "fail":
                    print(f"  ERROR [{gen.config.type_name}]: {msg.message}", file=sys.stderr)
                    all_ok = False

        if not dry_run:
            manifest = Manifest(
                vstack_version=VERSION,
                installed_at=datetime.datetime.now(datetime.UTC).isoformat(),
                artifacts=new_entries,
            )
            mf.write(manifest)
            print(f"  {_C.DIM}wrote  {self._label(mf.path)}{_C.RESET}")

        return 0 if all_ok else 1

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
        results: list[ValidationResult] = []
        section_count = sum([source, output])
        step = 0
        gens = [g for g in self._generators if only is None or g.config.type_name in only]

        def _header(label: str) -> None:
            """Print a numbered section header for verify progress output."""
            nonlocal step
            step += 1
            print(f"[{step}/{section_count}] {label}")

        def _print_result(result: ValidationResult) -> None:
            """Render one validation result block and accumulate totals."""
            for msg in result.messages:
                prefix = "✓" if msg.level == "pass" else "✗"
                print(f"  {prefix} {msg.message}")
            if result.failures == 0:
                print(f"  ✓ {result.passes} check(s) passed")
            results.append(result)

        if source:
            _header("checking source templates")
            for gen in gens:
                expected = _EXPECTED_INPUT_NAMES.get(gen.config.type_name)
                vr = gen.verify_input(expected)
                if vr.messages:
                    _print_result(vr)
                else:
                    print(f"  (no {gen.config.type_name} templates found, skipping)")

        if output:
            if install_dir is None:
                print("ERROR: install_dir required for output checks", file=sys.stderr)
                return 1
            manifest_data = self._manifest(install_dir).read()

            for gen in gens:
                out_dir = install_dir / gen.config.output_subdir
                _header(f"checking installed {gen.config.type_name} ({self._label(out_dir)}/)")
                if not out_dir.exists():
                    _print_result(
                        ValidationResult(
                            messages=[
                                CheckMessage(
                                    level="fail",
                                    message=f"{self._label(out_dir)}/ not found — run: vstack install",
                                )
                            ]
                        )
                    )
                else:
                    expected = self._expected_output_names(gen, manifest_data)
                    _print_result(gen.verify_output(out_dir, expected))

                    if manifest_data:
                        metadata_result = self._verify_manifest_metadata(
                            gen, manifest_data, install_dir
                        )
                        if metadata_result:
                            _print_result(metadata_result)

        print()
        total_failures = sum(r.failures for r in results)
        if total_failures:
            print(f"FAILED: {total_failures} check(s) failed")
            return 1
        print("All checks passed.")
        return 0

    # ── uninstall ─────────────────────────────────────────────────────────────

    def uninstall(self, install_dir: Path) -> int:
        """Remove only vstack-managed files.  User files are not touched."""
        removed: list[str] = []
        manifest_data = self._manifest(install_dir).read()

        for gen in self._generators:
            out_dir = install_dir / gen.config.output_subdir
            entries = manifest_data.entries_for(gen.config.type_name) if manifest_data else []

            if not entries:
                # No manifest entries: fall back to known names from templates
                fallback = _EXPECTED_INPUT_NAMES.get(gen.config.type_name)
                if fallback:
                    entries = [
                        ArtifactEntry(
                            name=n,
                            file=gen.config.output_subdir + "/" + gen.output_path(n),
                        )
                        for n in fallback
                    ]

            for entry in entries:
                full_path = install_dir / entry.file
                if gen.config.artifact_is_dir:
                    artifact_dir = full_path.parent
                    if artifact_dir.exists() and artifact_dir != out_dir:
                        shutil.rmtree(artifact_dir)
                        removed.append(self._label(artifact_dir))
                else:
                    if full_path.exists():
                        full_path.unlink()
                        removed.append(self._label(full_path))

            if out_dir.exists() and not any(out_dir.iterdir()):
                out_dir.rmdir()
                removed.append(self._label(out_dir) + "/")

        mf = self._manifest(install_dir)
        if mf.exists():
            mf.path.unlink()
            removed.append(self._label(mf.path))

        if removed:
            for p in removed:
                print(f"  removed  {p}")
        else:
            print("Nothing to remove.")
        return 0
