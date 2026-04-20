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
    """Generate agent artifacts using the built-in agent type configuration."""

    def __init__(self) -> None:
        """Create an agent generator bound to the built-in template root."""
        super().__init__(AGENT_TYPE, TEMPLATES_ROOT)
