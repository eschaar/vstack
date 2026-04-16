"""Utilities and tests for generator."""

from vstack.artifacts.generator import GenericArtifactGenerator
from vstack.constants import TEMPLATES_ROOT
from vstack.instructions.config import INSTRUCTION_TYPE


class InstructionGenerator(GenericArtifactGenerator):
    """Represents InstructionGenerator."""

    def __init__(self) -> None:
        """Initialize instance state."""
        super().__init__(INSTRUCTION_TYPE, TEMPLATES_ROOT)
