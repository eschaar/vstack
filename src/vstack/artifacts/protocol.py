"""Structural protocol for prompt-artifact generators.

Any class that implements ``generate``, ``verify_input``, and ``verify_output``
with the signatures below implicitly satisfies :class:`ArtifactGenerator` —
no inheritance required.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from vstack.artifacts.models import ArtifactResult
from vstack.models import ValidationResult


class ArtifactGenerator(Protocol):
    """Structural protocol satisfied by all artifact generators.

    In practice this protocol is satisfied by
    :class:`~vstack.artifacts.generator.GenericArtifactGenerator` and
    specialized subclasses such as
    :class:`~vstack.agents.generator.AgentGenerator` and
    :class:`~vstack.hooks.generator.HookGenerator`.
    """

    def generate(self, output_dir: Path) -> ArtifactResult:
        """Write artifacts to *output_dir* and return a result summary."""
        ...

    def verify_input(
        self,
        expected_names: list[str] | None = None,
    ) -> ValidationResult:
        """Verify source templates / files before generation.

        Args:
            expected_names: Names to check for existence.  When ``None`` the
                            generator validates only the templates it finds.
        """
        ...

    def verify_output(
        self,
        output_dir: Path,
        expected_names: list[str] | None = None,
    ) -> ValidationResult:
        """Verify generated output files in *output_dir*.

        Args:
            expected_names: Names (or filenames) to check for.  When ``None``
                            the generator checks all artifacts it knows about.
        """
        ...
