"""Artifact configuration types and built-in frontmatter schema registrations.

This module provides:

* :class:`ArtifactTypeConfig` — fully describes one family of prompt artifacts:
  where to find source templates, how to derive output paths, which frontmatter
  schema applies, and what to verify.
* Shared schemas for **prompts** and **instructions**.

Frontmatter field types (:class:`~vstack.frontmatter.FieldSpec`,
:class:`~vstack.frontmatter.FrontmatterSchema`, :data:`~vstack.frontmatter.FieldType`)
live in :mod:`vstack.frontmatter`.

Type-specific schemas and descriptors live in their own packages:

* :mod:`vstack.skills.config` — :data:`~vstack.skills.config.SKILL_SCHEMA`, :data:`~vstack.skills.config.SKILL_TYPE`
* :mod:`vstack.agents.config` — :data:`~vstack.agents.config.AGENT_SCHEMA`, :data:`~vstack.agents.config.AGENT_TYPE`
"""

from __future__ import annotations

from dataclasses import dataclass, field

from vstack.frontmatter import FieldSpec, FrontmatterSchema

# ── ArtifactTypeConfig ────────────────────────────────────────────────────────


@dataclass
class ArtifactTypeConfig:
    """Describes a family of prompt artifacts and how to process them.

    Attributes:
        type_name:         Singular identifier used in log output and internal lookups
                           (e.g. ``"skill"``).  Not used as a manifest key — see
                           :attr:`manifest_key` for that.
        manifest_key:      Key used in the manifest JSON ``artifacts`` dict
                           (e.g. ``"skills"``).  Defaults to :attr:`output_subdir`
                           when left empty.
        templates_dir:     Subdirectory name under ``templates/`` that holds source templates.
        output_subdir:     Subdirectory under the install root (``.github/``) for output.
        output_pattern:    Output filename relative to *output_subdir*, with a ``{name}``
                           placeholder.  Examples: ``"{name}/SKILL.md"``,
                           ``"{name}.agent.md"``.
        add_frontmatter:   When ``True`` the generator validates that every artifact has
                           frontmatter (from the template or from ``config.yaml``).
        artifact_is_dir:   When ``True`` each artifact occupies its own subdirectory
                           (like ``skills/<name>/``).  Used by uninstall to remove the
                           whole directory rather than a single file.
        partials_subdir:   Subdirectory relative to *templates_dir* that contains
                           partial snippets.  ``None`` disables partial loading.
        template_filename: Filename of the source template inside each ``<name>/`` dir.
        config_filename:   Optional per-artifact YAML metadata file.
        auto_gen_footer:   When ``True``, appends the shared AUTO-GENERATED footer comment
                           after the body. ``False`` means no footer is injected or verified.
        placeholders:      Registry of supported placeholders for this artifact type,
                   mapping ``TOKEN`` to the template file that defines it
                   (e.g. ``{"SKILL_CONTEXT": "skill-context.md"}``).
        fail_on_unresolved:   When ``True``, ``verify_output`` flags any remaining
                           ``{{TOKEN}}`` occurrences in output files as errors.
        frontmatter_schema: Schema controlling which fields are emitted and how.
                           Required when *add_frontmatter* is ``True``.
        preserve_multiline_frontmatter:
                   When ``True``, long string fields are emitted as folded
                   YAML scalars (``>-``) in generated frontmatter.
    """

    type_name: str
    templates_dir: str
    output_subdir: str
    output_pattern: str
    add_frontmatter: bool
    artifact_is_dir: bool = False
    partials_subdir: str | None = "_partials"
    template_filename: str = "template.md"
    config_filename: str = "config.yaml"
    auto_gen_footer: bool = False
    placeholders: dict[str, str] = field(default_factory=dict)
    fail_on_unresolved: bool = False
    frontmatter_schema: FrontmatterSchema | None = None
    preserve_multiline_frontmatter: bool = False
    manifest_key: str = ""

    def __post_init__(self) -> None:
        """Internal helper to post init."""
        if not self.manifest_key:
            self.manifest_key = self.output_subdir


# ── Frontmatter schemas ───────────────────────────────────────────────────────

#: Fields recognised in VS Code prompt files (``.prompt.md``).
PROMPT_SCHEMA = FrontmatterSchema(
    [
        FieldSpec("description"),
        FieldSpec("name", quoted=False),
        FieldSpec("argument-hint"),
        FieldSpec("agent", quoted=False),
        FieldSpec("model", quoted=False),
        FieldSpec("tools", type="list"),
    ]
)

#: Fields recognised in VS Code instruction files (``.instructions.md``).
INSTRUCTION_SCHEMA = FrontmatterSchema(
    [
        FieldSpec("name", quoted=False),
        FieldSpec("description"),
        FieldSpec("applyTo", quoted=False),
    ]
)
