"""Status command wrapper."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from vstack.cli.base import BaseCommand, CommandContext
from vstack.cli.constants import Colors
from vstack.cli.report import StatusReport

if TYPE_CHECKING:
    from vstack.cli.service import CommandService


class StatusCommand(BaseCommand):
    """Report manifest ownership and checksum state."""

    def __init__(self, service: CommandService) -> None:
        self._service = service

    @staticmethod
    def execute(
        service: CommandService,
        *,
        install_dir: Path,
        only: list[str] | None = None,
        output_format: str = "text",
        verbose: bool = False,
        no_color: bool = False,
    ) -> int:
        """Report which installed artifacts still match the manifest and which do not."""
        manifest_file = service.manifest_for(install_dir)
        manifest_data = manifest_file.read()
        gens = [g for g in service.generators if only is None or g.config.type_name in only]
        reports: list[dict[str, object]] = []

        def color(code: str, text: str) -> str:
            """Apply ANSI color to text when enabled."""
            use_color = output_format == "text" and not no_color and sys.stdout.isatty()
            return f"{code}{text}{Colors.RESET}" if use_color else text

        if manifest_data is None:
            if manifest_file.read_error:
                return StatusReport.render_missing_manifest(
                    output_format=output_format,
                    install_dir=install_dir,
                    error=manifest_file.read_error,
                    color=color,
                )

            return StatusReport.render_missing_manifest(
                output_format=output_format,
                install_dir=install_dir,
                error="vstack.json not found; run vstack install before using status",
                color=color,
            )

        for gen in gens:
            reports.append(
                StatusReport.build_type_report(
                    service=service,
                    gen=gen,
                    manifest_data=manifest_data,
                    install_dir=install_dir,
                )
            )

        total_issues, total_warnings = StatusReport.summarize(reports)
        payload = StatusReport.build_payload(
            install_dir=install_dir,
            reports=reports,
            total_issues=total_issues,
            total_warnings=total_warnings,
        )

        if output_format == "json":
            print(json.dumps(payload, indent=2))
            return 0 if total_issues == 0 else 1

        if output_format == "yaml":
            print(StatusReport.to_yaml(payload))
            return 0 if total_issues == 0 else 1

        return StatusReport.render_text_output(
            service=service,
            reports=reports,
            install_dir=install_dir,
            verbose=verbose,
            total_issues=total_issues,
            color=color,
        )

    def run(
        self,
        *,
        context: CommandContext,
    ) -> int:
        install_dir = context.require_install_dir("status")

        return StatusCommand.execute(
            self._service,
            install_dir=install_dir,
            only=context.only,
            output_format=getattr(context.args, "output_format", "text"),
            verbose=getattr(context.args, "verbose", False),
            no_color=getattr(context.args, "no_color", False),
        )
