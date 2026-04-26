"""Report builders and renderers for CLI commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from vstack.cli.constants import ArtifactState, Colors

if TYPE_CHECKING:
    from vstack.artifacts.generator import GenericArtifactGenerator
    from vstack.cli.service import CommandService
    from vstack.manifest import ArtifactEntry, Manifest


class BaseReport:
    """Shared serialization helpers for CLI report renderers."""

    @staticmethod
    def _yaml_scalar(value: object) -> str:
        """Render a primitive value as a YAML-safe scalar."""
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        text = str(value)
        escaped = text.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'

    @classmethod
    def to_yaml(cls, data: object, indent: int = 0) -> str:
        """Serialize a JSON-like structure to simple YAML."""
        prefix = " " * indent
        if isinstance(data, dict):
            lines: list[str] = []
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{prefix}{key}:")
                    lines.append(cls.to_yaml(value, indent + 2))
                else:
                    lines.append(f"{prefix}{key}: {cls._yaml_scalar(value)}")
            return "\n".join(lines)
        if isinstance(data, list):
            lines = []
            for item in data:
                if isinstance(item, (dict, list)):
                    nested = cls.to_yaml(item, indent + 2)
                    nested_lines = nested.splitlines()
                    if nested_lines:
                        lines.append(f"{prefix}- {nested_lines[0].lstrip()}")
                        lines.extend(nested_lines[1:])
                    else:
                        lines.append(f"{prefix}-")
                else:
                    lines.append(f"{prefix}- {cls._yaml_scalar(item)}")
            return "\n".join(lines)
        return f"{prefix}{cls._yaml_scalar(data)}"


class StatusReport(BaseReport):
    """Status report builders and renderers for status command output."""

    @staticmethod
    def _status_bucket(state: str) -> str:
        """Map an internal artifact state to a status bucket key."""
        mapping = {
            ArtifactState.MANAGED: "managed",
            ArtifactState.MANAGED_LEGACY: "managed_legacy",
            ArtifactState.MODIFIED: "modified",
            ArtifactState.MISSING: "missing",
            ArtifactState.UNKNOWN: "unknown",
            ArtifactState.UNTRACKED: "untracked",
            ArtifactState.ABSENT: "absent",
        }
        return mapping.get(state, "unknown")

    @classmethod
    def build_type_report(
        cls,
        *,
        service: CommandService,
        gen: GenericArtifactGenerator,
        manifest_data: Manifest,
        install_dir: Path,
    ) -> dict[str, object]:
        """Build structured status data for one artifact type."""
        entries: list[dict[str, str]] = []
        counts: dict[str, int] = {
            "managed": 0,
            "managed_legacy": 0,
            "modified": 0,
            "missing": 0,
            "unknown": 0,
            "untracked": 0,
            "absent": 0,
        }
        existing_entries: dict[str, ArtifactEntry] = {}

        for entry in manifest_data.entries_for(gen.config.manifest_key):
            existing_entries[entry.name] = entry
            state, message = service.artifact_control_state(
                out_file=install_dir / entry.file,
                existing_entry=entry,
            )
            bucket = cls._status_bucket(state)
            counts[bucket] += 1
            entries.append(
                {
                    "artifact": entry.name,
                    "path": entry.file,
                    "state": state,
                    "message": message,
                }
            )

        for artifact in gen.render_all():
            if artifact.name in existing_entries:
                continue
            out_file = install_dir / gen.config.output_subdir / gen.output_path(artifact.name)
            state, message = service.artifact_control_state(out_file=out_file, existing_entry=None)
            bucket = cls._status_bucket(state)
            counts[bucket] += 1
            entries.append(
                {
                    "artifact": artifact.name,
                    "path": f"{gen.config.output_subdir}/{gen.output_path(artifact.name)}",
                    "state": state,
                    "message": message,
                }
            )

        warnings = counts["managed_legacy"]
        issues = counts["modified"] + counts["missing"] + counts["unknown"] + counts["untracked"]
        return {
            "type": gen.config.type_name,
            "output_dir": str(install_dir / gen.config.output_subdir),
            "counts": counts,
            "issues": issues,
            "warnings": warnings,
            "entries": entries,
        }

    @staticmethod
    def summarize(reports: list[dict[str, object]]) -> tuple[int, int]:
        """Compute total issue and warning counts across all type reports."""
        total_issues = 0
        total_warnings = 0
        for report in reports:
            issues_value = report.get("issues")
            total_issues += issues_value if isinstance(issues_value, int) else 0
            warnings_value = report.get("warnings")
            total_warnings += warnings_value if isinstance(warnings_value, int) else 0
        return total_issues, total_warnings

    @staticmethod
    def build_payload(
        *,
        install_dir: Path,
        reports: list[dict[str, object]],
        total_issues: int,
        total_warnings: int,
    ) -> dict[str, object]:
        """Build output payload shared by JSON and YAML renderers."""
        return {
            "ok": total_issues == 0,
            "install_dir": str(install_dir),
            "types": reports,
            "summary": {
                "issues": total_issues,
                "warnings": total_warnings,
                "types_checked": len(reports),
            },
        }

    @staticmethod
    def _missing_manifest_payload(install_dir: Path, error: str) -> dict[str, object]:
        """Build the structured error payload for missing or invalid manifest state."""
        return {
            "ok": False,
            "error": error,
            "install_dir": str(install_dir),
            "types": [],
            "summary": {"issues": 0},
        }

    @classmethod
    def render_missing_manifest(
        cls,
        *,
        output_format: str,
        install_dir: Path,
        error: str,
        color,
    ) -> int:
        """Render an error response when status cannot read a usable manifest."""
        payload = cls._missing_manifest_payload(install_dir, error)
        if output_format == "json":
            print(json.dumps(payload, indent=2))
            return 1
        if output_format == "yaml":
            print(cls.to_yaml(payload))
            return 1

        print(color(Colors.RED, "FAILED") + f": {error}")
        return 1

    @staticmethod
    def render_text_output(
        *,
        service: CommandService,
        reports: list[dict[str, object]],
        install_dir: Path,
        verbose: bool,
        total_issues: int,
        color,
    ) -> int:
        """Render text status output and return process-style exit code."""
        print(f"{color(Colors.BOLD, 'STATUS')} {color(Colors.DIM, service.label(install_dir))}")
        for report in reports:
            counts = report["counts"]
            if not isinstance(counts, dict):
                raise TypeError(f"expected dict for 'counts', got {type(counts).__name__}")
            issues_value = report.get("issues")
            issues = issues_value if isinstance(issues_value, int) else 0
            warnings_value = report.get("warnings")
            warnings = warnings_value if isinstance(warnings_value, int) else 0
            state_label = color(Colors.GREEN, "OK") if issues == 0 else color(Colors.RED, "ISSUES")
            summary_line = (
                f"[{report['type']}] {state_label} "
                f"ok={counts['managed']} mod={counts['modified']} "
                f"miss={counts['missing']} untracked={counts['untracked']} "
                f"unknown={counts['unknown']} legacy={counts['managed_legacy']}"
            )
            print(summary_line)
            if warnings:
                print(color(Colors.YELLOW, f"  ! {warnings} legacy warning(s)"))

            entries = report["entries"]
            if not isinstance(entries, list):
                raise TypeError(f"expected list for 'entries', got {type(entries).__name__}")
            for entry in entries:
                if not isinstance(entry, dict):
                    raise TypeError(f"expected dict for entry, got {type(entry).__name__}")
                state = str(entry["state"])
                if not verbose and state == ArtifactState.MANAGED:
                    continue

                if state == ArtifactState.MANAGED:
                    marker = color(Colors.GREEN, "  ✓")
                elif state in {
                    ArtifactState.MODIFIED,
                    ArtifactState.MISSING,
                    ArtifactState.UNKNOWN,
                    ArtifactState.UNTRACKED,
                    ArtifactState.MANAGED_LEGACY,
                }:
                    marker = color(Colors.YELLOW, "  !")
                else:
                    marker = color(Colors.DIM, "  ·")

                print(f"{marker} {entry['message']}")

        print()
        if total_issues:
            print(color(Colors.RED, "FAILED") + f": {total_issues} artifact status issue(s) found")
            return 1
        print(color(Colors.GREEN, "OK") + ": all tracked artifacts match the manifest")
        return 0
