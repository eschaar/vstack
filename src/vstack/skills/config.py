"""Skill artifact type configuration and frontmatter schema.

Defines the :data:`SKILL_SCHEMA` (which frontmatter fields a ``SKILL.md`` file
uses) and the :data:`SKILL_TYPE` descriptor that configures the generator for
the ``skills`` artifact family.
"""

from __future__ import annotations

from vstack.artifacts.config import ArtifactTypeConfig
from vstack.frontmatter import FieldSpec, FrontmatterSchema
from vstack.skills.constants import (
    SKILL_OUTPUT_SUBDIR,
    SKILL_TEMPLATES_SUBDIR,
    SKILL_TMPL_NAME,
)

#: Fields recognised in VS Code Agent Skill files (``SKILL.md``).
SKILL_SCHEMA = FrontmatterSchema(
    [
        FieldSpec(
            "name",
            required=True,
            quoted=False,
            max_length=64,
            pattern=r"[a-z0-9]+(?:-[a-z0-9]+)*",
        ),
        FieldSpec("description", required=True, max_length=1024, normalize_whitespace=True),
        FieldSpec("license", max_length=256),
        FieldSpec("compatibility", max_length=500, normalize_whitespace=True),
        # Agent Skills spec: arbitrary key/value mapping. We preserve this as raw YAML.
        FieldSpec("metadata", type="raw"),
        FieldSpec("argument-hint"),
        FieldSpec("user-invocable", type="bool"),
        FieldSpec("disable-model-invocation", type="bool"),
    ]
)

#: Type descriptor for the ``skills`` artifact family.
SKILL_TYPE = ArtifactTypeConfig(
    type_name="skill",
    templates_dir=SKILL_TEMPLATES_SUBDIR,
    output_subdir=SKILL_OUTPUT_SUBDIR,
    output_pattern="{name}/SKILL.md",
    add_frontmatter=True,
    artifact_is_dir=True,
    partials_subdir="_partials",
    auto_gen_footer=True,
    placeholders={
        "SKILL_CONTEXT": "skill-context.md",
        "BASE_BRANCH": "base-branch.md",
        "RUN_TESTS": "run-tests.md",
        "OBSERVABILITY_CHECKLIST": "observability-checklist.md",
    },
    fail_on_unresolved=True,
    template_filename=SKILL_TMPL_NAME,
    frontmatter_schema=SKILL_SCHEMA,
)
