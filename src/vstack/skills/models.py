"""Backwards-compatible exports for skill artifact models."""

from __future__ import annotations

# The skills layer builds on the shared prompt-artifact types.
from vstack.artifacts.models import ArtifactResult as ArtifactResult
from vstack.artifacts.models import RenderedArtifact as RenderedArtifact

# Re-export shared validation types so existing imports keep working.
from vstack.models import CheckMessage as CheckMessage
from vstack.models import ValidationResult as ValidationResult

# Backwards-compatible aliases — prefer the canonical names above in new code.
RenderedSkill = RenderedArtifact
GenerateResult = ArtifactResult
