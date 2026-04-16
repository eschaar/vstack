"""Utilities and tests for config."""

from vstack.artifacts.config import INSTRUCTION_SCHEMA, ArtifactTypeConfig
from vstack.instructions.constants import (
    INSTRUCTION_OUTPUT_SUBDIR,
    INSTRUCTION_OUTPUT_SUFFIX,
    INSTRUCTION_TEMPLATES_SUBDIR,
)

INSTRUCTION_TYPE = ArtifactTypeConfig(
    type_name="instruction",
    templates_dir=INSTRUCTION_TEMPLATES_SUBDIR,
    output_subdir=INSTRUCTION_OUTPUT_SUBDIR,
    output_pattern=f"{{name}}{INSTRUCTION_OUTPUT_SUFFIX}",
    add_frontmatter=True,
    artifact_is_dir=False,
    partials_subdir=None,
    auto_gen_footer=True,
    fail_on_unresolved=False,
    frontmatter_schema=INSTRUCTION_SCHEMA,
)
