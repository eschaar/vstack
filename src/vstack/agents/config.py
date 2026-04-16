"""Agent artifact type configuration and frontmatter schema.

Defines the :data:`AGENT_SCHEMA` (which frontmatter fields a ``.agent.md`` file
uses) and the :data:`AGENT_TYPE` descriptor that configures the generator for
the ``agents`` artifact family.
"""

from __future__ import annotations

from vstack.agents.constants import AGENT_OUTPUT_SUBDIR, AGENT_OUTPUT_SUFFIX, AGENT_TEMPLATES_SUBDIR
from vstack.artifacts.config import ArtifactTypeConfig
from vstack.frontmatter import FieldSpec, FrontmatterSchema

# ── Nested schemas ────────────────────────────────────────────────────────────

#: Schema for a single ``handoffs`` entry.
HANDOFF_ITEM_SCHEMA = FrontmatterSchema(
    [
        FieldSpec("label", required=True),
        FieldSpec("agent", required=True, quoted=False),
        FieldSpec("prompt", required=True),
        FieldSpec("send", type="bool"),
        FieldSpec("model"),
    ]
)

#: Fields recognised in VS Code custom agent files (``.agent.md``).
AGENT_SCHEMA = FrontmatterSchema(
    [
        FieldSpec("description"),
        FieldSpec("name", quoted=False),
        FieldSpec("argument-hint"),
        FieldSpec("tools", type="list"),
        FieldSpec("agents", type="list"),
        # Allow model fallback lists (first available model is used).
        FieldSpec("model", type="list"),
        FieldSpec("user-invocable", type="bool"),
        FieldSpec("disable-model-invocation", type="bool"),
        FieldSpec("target", quoted=False),
        # Handoff buttons shown after a response completes.
        # Each entry: label (str), agent (str), prompt (str), send (bool), model (str).
        FieldSpec("handoffs", type="object-list", item_schema=HANDOFF_ITEM_SCHEMA),
        # MCP server config (github-copilot target only). Value is a raw YAML mapping
        # where each key is a server name: type, command, args, tools, env.
        FieldSpec("mcp-servers", type="raw"),
        # Per-agent hook commands scoped to this agent (Preview, requires chat.useCustomAgentHooks).
        # Uses the same nested format as hook config files.
        FieldSpec("hooks", type="raw"),
        # Arbitrary string key/value annotations (github-copilot target only).
        FieldSpec("metadata", type="raw"),
    ]
)

#: Type descriptor for the ``agents`` artifact family.
AGENT_TYPE = ArtifactTypeConfig(
    type_name="agent",
    templates_dir=AGENT_TEMPLATES_SUBDIR,
    output_subdir=AGENT_OUTPUT_SUBDIR,
    output_pattern=f"{{name}}{AGENT_OUTPUT_SUFFIX}",
    add_frontmatter=True,
    artifact_is_dir=False,
    partials_subdir="_partials",
    auto_gen_footer=True,
    fail_on_unresolved=False,
    frontmatter_schema=AGENT_SCHEMA,
    preserve_multiline_frontmatter=True,
)
