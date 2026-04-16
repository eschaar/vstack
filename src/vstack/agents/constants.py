"""Utilities and tests for constants."""

from vstack.constants import TEMPLATES_ROOT

AGENT_TEMPLATE_GLOB = "*/template.md"
AGENT_OUTPUT_SUFFIX = ".agent.md"

#: Subdirectory name under ``templates/`` holding agent source templates.
AGENT_TEMPLATES_SUBDIR = "agents"

#: Subdirectory name under the install root (e.g. ``.github/``) for agent output.
AGENT_OUTPUT_SUBDIR = "agents"

AGENT_TEMPLATES_DIR = TEMPLATES_ROOT / AGENT_TEMPLATES_SUBDIR
