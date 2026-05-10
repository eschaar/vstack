"""Artifact type configuration for hook templates and output."""

from __future__ import annotations

from vstack.artifacts.config import ArtifactTypeConfig
from vstack.hooks.constants import (
    HOOK_OUTPUT_SUBDIR,
    HOOK_OUTPUT_SUFFIX,
    HOOK_TEMPLATE_FILENAME,
    HOOK_TEMPLATES_SUBDIR,
)

HOOK_TYPE = ArtifactTypeConfig(
    type_name="hook",
    templates_dir=HOOK_TEMPLATES_SUBDIR,
    output_subdir=HOOK_OUTPUT_SUBDIR,
    output_pattern="{name}" + HOOK_OUTPUT_SUFFIX,
    artifact_is_dir=False,
    add_frontmatter=False,
    auto_gen_footer=False,
    template_filename=HOOK_TEMPLATE_FILENAME,
)
