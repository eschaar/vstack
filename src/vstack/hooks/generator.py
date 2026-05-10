"""Thin hook generator wrapper over ``GenericArtifactGenerator``."""

from vstack.artifacts.generator import GenericArtifactGenerator
from vstack.constants import TEMPLATES_ROOT
from vstack.hooks.config import HOOK_TYPE


class HookGenerator(GenericArtifactGenerator):
    """Generate hook artifacts using the built-in hook configuration."""

    def __init__(self) -> None:
        """Create a hook generator bound to the built-in template root."""
        super().__init__(HOOK_TYPE, TEMPLATES_ROOT)
