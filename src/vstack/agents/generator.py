"""AgentGenerator — thin wrapper around GenericArtifactGenerator for agents.

Import :class:`AgentGenerator` to get a generator pre-configured for the
``agents`` artifact type.  All behaviour is inherited from
:class:`~vstack.artifacts.generator.GenericArtifactGenerator`.
"""

from __future__ import annotations

from vstack.agents.config import AGENT_TYPE
from vstack.artifacts.generator import GenericArtifactGenerator
from vstack.constants import TEMPLATES_ROOT


class AgentGenerator(GenericArtifactGenerator):
    """Generator for agent artifacts, pre-configured for :data:`~vstack.artifacts.type_config.AGENT_TYPE`."""

    def __init__(self) -> None:
        """Initialize instance state."""
        super().__init__(AGENT_TYPE, TEMPLATES_ROOT)
