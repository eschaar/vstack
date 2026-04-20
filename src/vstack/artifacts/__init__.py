"""vstack.artifacts — shared prompt-artifact models, generator, and protocol."""

from vstack.artifacts.config import INSTRUCTION_SCHEMA as INSTRUCTION_SCHEMA
from vstack.artifacts.config import PROMPT_SCHEMA as PROMPT_SCHEMA
from vstack.artifacts.config import ArtifactTypeConfig as ArtifactTypeConfig
from vstack.artifacts.generator import (
    GenericArtifactGenerator as GenericArtifactGenerator,
)
from vstack.artifacts.models import ArtifactResult as ArtifactResult
from vstack.artifacts.models import RenderedArtifact as RenderedArtifact
from vstack.artifacts.protocol import ArtifactGenerator as ArtifactGenerator
from vstack.frontmatter import FieldSpec as FieldSpec
from vstack.frontmatter import FieldType as FieldType
from vstack.frontmatter import FrontmatterContent as FrontmatterContent
from vstack.frontmatter import FrontmatterParser as FrontmatterParser
from vstack.frontmatter import FrontmatterSchema as FrontmatterSchema
from vstack.frontmatter import FrontmatterSerializer as FrontmatterSerializer
