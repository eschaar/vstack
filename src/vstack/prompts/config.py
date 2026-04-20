"""Prompt artifact type configuration."""

from vstack.artifacts.config import PROMPT_SCHEMA, ArtifactTypeConfig
from vstack.prompts.constants import (
    PROMPT_OUTPUT_SUBDIR,
    PROMPT_OUTPUT_SUFFIX,
    PROMPT_TEMPLATES_SUBDIR,
)

PROMPT_TYPE = ArtifactTypeConfig(
    type_name="prompt",
    templates_dir=PROMPT_TEMPLATES_SUBDIR,
    output_subdir=PROMPT_OUTPUT_SUBDIR,
    output_pattern=f"{{name}}{PROMPT_OUTPUT_SUFFIX}",
    add_frontmatter=True,
    artifact_is_dir=False,
    partials_subdir=None,
    auto_gen_footer=True,
    fail_on_unresolved=False,
    frontmatter_schema=PROMPT_SCHEMA,
)
