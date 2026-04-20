"""Thin prompt generator wrapper over ``GenericArtifactGenerator``."""

from vstack.artifacts.generator import GenericArtifactGenerator
from vstack.constants import TEMPLATES_ROOT
from vstack.prompts.config import PROMPT_TYPE


class PromptGenerator(GenericArtifactGenerator):
    """Generate prompt artifacts using the built-in prompt configuration."""

    def __init__(self) -> None:
        """Create a prompt generator bound to the built-in template root."""
        super().__init__(PROMPT_TYPE, TEMPLATES_ROOT)
