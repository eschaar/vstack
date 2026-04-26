"""Validate command wrapper."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from vstack.artifacts.models import RenderedArtifact
from vstack.cli.base import BaseCommand, CommandContext

if TYPE_CHECKING:
    from vstack.cli.service import CommandService


class ValidateCommand(BaseCommand):
    """Run source template validation."""

    def __init__(self, service: CommandService) -> None:
        self._service = service

    @staticmethod
    def execute(service: CommandService, only: list[str] | None = None) -> int:
        """Render templates in memory and report unresolved placeholders."""
        gens = [g for g in service.generators if only is None or g.config.type_name in only]
        all_artifacts: dict[str, list[RenderedArtifact]] = {}
        total_partials = 0
        for gen in gens:
            artifacts = gen.render_all()
            all_artifacts[gen.config.type_name] = artifacts
            total_partials += len(gen.load_partials())

        if not any(all_artifacts.values()):
            print("ERROR: No templates found", file=sys.stderr)
            return 1

        errors: list[RenderedArtifact] = []
        for type_name, artifacts in all_artifacts.items():
            type_gen = service.gen_for(type_name)
            if type_gen is None:
                continue
            print(f"\n{type_name.capitalize()} ({len(artifacts)}):")
            for artifact in artifacts:
                suffix = f"  ⚠ unresolved: {artifact.unresolved}" if artifact.unresolved else ""
                print(f"  {type_gen.output_path(artifact.name)}{suffix}")
            errors.extend(artifact for artifact in artifacts if artifact.unresolved)

        total = sum(len(v) for v in all_artifacts.values())
        if errors:
            print(
                f"\nERROR: {len(errors)} template(s) have unresolved placeholders",
                file=sys.stderr,
            )
            return 1
        print(f"\nOK: {total} artifact(s), {total_partials} partial(s)")
        return 0

    def run(
        self,
        *,
        context: CommandContext,
    ) -> int:
        return ValidateCommand.execute(self._service, only=context.only)
