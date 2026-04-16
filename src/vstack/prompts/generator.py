"""Utilities and tests for generator."""

from vstack.artifacts.generator import GenericArtifactGenerator
from vstack.constants import TEMPLATES_ROOT
from vstack.prompts.config import PROMPT_TYPE


class PromptGenerator(GenericArtifactGenerator):
    """Represents PromptGenerator."""

    def __init__(self) -> None:
        """Initialize instance state."""
        super().__init__(PROMPT_TYPE, TEMPLATES_ROOT)
