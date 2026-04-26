"""Canonical CLI artifact names."""

from __future__ import annotations

from vstack.agents.config import AGENT_TYPE
from vstack.instructions.config import INSTRUCTION_TYPE
from vstack.prompts.config import PROMPT_TYPE
from vstack.skills.config import SKILL_TYPE

EXPECTED_CANONICAL_NAMES = [
    "vision",
    "architecture",
    "requirements",
    "adr",
    "design",
    "consult",
    "concise",
    "code-review",
    "release-notes",
    "pr",
    "verify",
    "inspect",
    "security",
    "debug",
    "performance",
    "analyse",
    "explore",
    "docs",
    "guardrails",
    "container",
    "cicd",
    "migrate",
    "openapi",
    "refactor",
    "onboard",
    "dependency",
    "incident",
]


class Colors:
    """ANSI colour codes used in CLI output."""

    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    BLUE = "\033[34m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


KNOWN_TYPES = [SKILL_TYPE, AGENT_TYPE, INSTRUCTION_TYPE, PROMPT_TYPE]
KNOWN_TYPE_NAMES = [type_config.type_name for type_config in KNOWN_TYPES]
GLOBAL_SUPPORTED_TYPE_NAMES = [
    AGENT_TYPE.type_name,
    INSTRUCTION_TYPE.type_name,
    PROMPT_TYPE.type_name,
    SKILL_TYPE.type_name,
]


class ArtifactState:
    """Canonical artifact control states returned by CLI state checks."""

    MANAGED = "managed"
    MANAGED_LEGACY = "managed-legacy"
    MODIFIED = "modified"
    MISSING = "missing"
    UNTRACKED = "untracked"
    ABSENT = "absent"
    UNKNOWN = "unknown"


# Names that must exist for each artifact type (used in verify --source).
EXPECTED_INPUT_NAMES: dict[str, list[str]] = {
    "skill": EXPECTED_CANONICAL_NAMES,
    "agent": ["architect", "designer", "engineer", "product", "release", "tester"],
    "instruction": ["git", "python"],
    "prompt": ["code-review"],
}
