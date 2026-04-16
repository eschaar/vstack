"""SkillGenerator — thin wrapper around GenericArtifactGenerator for skills.

Import :class:`SkillGenerator` to get a generator pre-configured for the
``skills`` artifact type.  All behaviour is inherited from
:class:`~vstack.artifacts.generator.GenericArtifactGenerator`.
"""

from __future__ import annotations

from vstack.artifacts.generator import GenericArtifactGenerator
from vstack.constants import TEMPLATES_ROOT
from vstack.skills.config import SKILL_TYPE


class SkillGenerator(GenericArtifactGenerator):
    """Generator for skill artifacts, pre-configured for :data:`~vstack.artifacts.type_config.SKILL_TYPE`."""

    def __init__(self) -> None:
        """Initialize instance state."""
        super().__init__(SKILL_TYPE, TEMPLATES_ROOT)
