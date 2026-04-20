"""Thin instruction generator wrapper over ``GenericArtifactGenerator``."""

from vstack.artifacts.generator import GenericArtifactGenerator
from vstack.constants import TEMPLATES_ROOT
from vstack.instructions.config import INSTRUCTION_TYPE


class InstructionGenerator(GenericArtifactGenerator):
    """Generate instruction artifacts using the built-in instruction configuration."""

    def __init__(self) -> None:
        """Create an instruction generator bound to the built-in template root."""
        super().__init__(INSTRUCTION_TYPE, TEMPLATES_ROOT)
