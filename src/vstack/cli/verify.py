"""Verify command wrapper."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from vstack.cli.base import BaseCommand, CommandContext
from vstack.cli.constants import EXPECTED_INPUT_NAMES, ArtifactState
from vstack.models import CheckMessage, ValidationResult

if TYPE_CHECKING:
    from vstack.cli.service import CommandService


class VerifyCommand(BaseCommand):
    """Run verify checks for source templates and/or installed output."""

    def __init__(self, service: CommandService) -> None:
        self._service = service

    @staticmethod
    def _print_result(result: ValidationResult, results: list[ValidationResult]) -> None:
        """Render one validation result block and accumulate totals."""
        for msg in result.messages:
            prefix = "✓" if msg.level == "pass" else "✗"
            print(f"  {prefix} {msg.message}")
        if result.failures == 0:
            print(f"  ✓ {result.passes} check(s) passed")
        results.append(result)

    @staticmethod
    def _verify_source(
        *,
        gens,
        results: list[ValidationResult],
    ) -> None:
        """Run source template verification for selected generators."""
        for gen in gens:
            expected = EXPECTED_INPUT_NAMES.get(gen.config.type_name)
            verify_result = gen.verify_input(expected)
            if verify_result.messages:
                VerifyCommand._print_result(verify_result, results)
            else:
                print(f"  (no {gen.config.type_name} templates found, skipping)")

    @staticmethod
    def _expected_output_names(gen, manifest_data) -> list[str] | None:
        """Resolve expected output names for verify output checks."""
        if manifest_data:
            return manifest_data.names_for(gen.config.manifest_key)
        return EXPECTED_INPUT_NAMES.get(gen.config.type_name)

    @staticmethod
    def _expected_manifest_metadata(
        service: CommandService, gen, manifest_data, entry
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

    @staticmethod
    def _verify_manifest_metadata_entry(
        service: CommandService, gen, manifest_data, entry, artifact_path: Path
    ) -> ValidationResult:
        """Verify manifest-linked metadata for a single artifact file."""
        from vstack.artifacts.generator import GenericArtifactGenerator

        result = ValidationResult()
        rel_path = service.label(artifact_path)
        try:
            content = artifact_path.read_text(encoding="utf-8")
        except OSError as exc:
            result.messages.append(
                CheckMessage(
                    "fail",
                    f"{rel_path}: could not read file during metadata verify — {exc}",
                )
            )
            return result

        metadata = GenericArtifactGenerator.parse_generation_metadata(content)

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

        for key, expected_value in VerifyCommand._expected_manifest_metadata(
            service, gen, manifest_data, entry
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

    @staticmethod
    def _verify_manifest_metadata(
        service: CommandService, gen, manifest_data, install_dir: Path
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
            entry_result = VerifyCommand._verify_manifest_metadata_entry(
                service,
                gen,
                manifest_data,
                entry,
                artifact_path,
            )
            result.messages.extend(entry_result.messages)

        return result if result.messages else None

    @staticmethod
    def _verify_manifest_checksums(
        service: CommandService, gen, manifest_data, install_dir: Path
    ) -> ValidationResult | None:
        """Verify checksum ownership and drift for manifest-tracked artifacts."""
        manifest_entries = manifest_data.entries_for(gen.config.manifest_key)
        if not manifest_entries:
            return None

        result = ValidationResult()
        for entry in manifest_entries:
            state, message = service.artifact_control_state(
                out_file=install_dir / entry.file,
                existing_entry=entry,
            )
            level = (
                "pass" if state in {ArtifactState.MANAGED, ArtifactState.MANAGED_LEGACY} else "fail"
            )
            result.messages.append(CheckMessage(level, message))

        return result if result.messages else None

    @staticmethod
    def _verify_output(
        *,
        service: CommandService,
        install_dir: Path,
        gens,
        header,
        results: list[ValidationResult],
    ) -> int:
        """Run installed-output verification for selected generators."""
        manifest_file = service.manifest_for(install_dir)
        manifest_data = manifest_file.read()
        if manifest_data is None and manifest_file.read_error:
            print(f"ERROR: {manifest_file.read_error}", file=sys.stderr)
            return 1

        for gen in gens:
            out_dir = install_dir / gen.config.output_subdir
            header(f"checking installed {gen.config.type_name} ({service.label(out_dir)}/)")
            if not out_dir.exists():
                VerifyCommand._print_result(
                    ValidationResult(
                        messages=[
                            CheckMessage(
                                level="fail",
                                message=f"{service.label(out_dir)}/ not found — run: vstack install",
                            )
                        ]
                    ),
                    results,
                )
                continue

            expected = VerifyCommand._expected_output_names(gen, manifest_data)
            VerifyCommand._print_result(gen.verify_output(out_dir, expected), results)

            if not manifest_data:
                continue

            checksum_result = VerifyCommand._verify_manifest_checksums(
                service, gen, manifest_data, install_dir
            )
            if checksum_result:
                VerifyCommand._print_result(checksum_result, results)

            metadata_result = VerifyCommand._verify_manifest_metadata(
                service, gen, manifest_data, install_dir
            )
            if metadata_result:
                VerifyCommand._print_result(metadata_result, results)

        return 0

    @staticmethod
    def execute(
        service: CommandService,
        *,
        install_dir: Path | None = None,
        source: bool = True,
        output: bool = True,
        only: list[str] | None = None,
    ) -> int:
        """Check source templates and/or installed output."""
        results: list[ValidationResult] = []
        section_count = sum([source, output])
        step = 0
        gens = [g for g in service.generators if only is None or g.config.type_name in only]

        def _header(label: str) -> None:
            """Print a numbered section header for verify progress output."""
            nonlocal step
            step += 1
            print(f"[{step}/{section_count}] {label}")

        if source:
            _header("checking source templates")
            VerifyCommand._verify_source(gens=gens, results=results)

        if output:
            if install_dir is None:
                print("ERROR: install_dir required for output checks", file=sys.stderr)
                return 1
            output_exit = VerifyCommand._verify_output(
                service=service,
                install_dir=install_dir,
                gens=gens,
                header=_header,
                results=results,
            )
            if output_exit:
                return output_exit

        print()
        total_failures = sum(r.failures for r in results)
        if total_failures:
            print(f"FAILED: {total_failures} check(s) failed")
            return 1
        print("All checks passed.")
        return 0

    def run(
        self,
        *,
        context: CommandContext,
    ) -> int:
        return VerifyCommand.execute(
            self._service,
            install_dir=context.install_dir,
            source=getattr(context.args, "source", True),
            output=getattr(context.args, "output", True),
            only=context.only,
        )
