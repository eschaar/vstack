"""Canonical CLI artifact names."""

from __future__ import annotations

from vstack.agents.config import AGENT_TYPE
from vstack.hooks.config import HOOK_TYPE
from vstack.instructions.config import INSTRUCTION_TYPE
from vstack.skills.config import SKILL_TYPE

EXPECTED_CANONICAL_NAMES = [
    "advise",
    "analyse",
    "architecture",
    "artifact-integrity",
    "ask",
    "adr",
    "aws-cli",
    "changedoc",
    "codeql",
    "code-review",
    "cloudformation",
    "cicd",
    "concise",
    "consult",
    "container",
    "conventional-commit",
    "copilot-ops",
    "debug",
    "dependency",
    "dependabot",
    "design",
    "docs",
    "explore",
    "gdpr",
    "gh-issues",
    "gh-release",
    "guardrails",
    "helm",
    "incident",
    "inspect",
    "k8s",
    "lazy",
    "migrate",
    "migration-plan",
    "onboard",
    "openapi",
    "performance",
    "postmortem",
    "pr",
    "rancher",
    "rca",
    "reasoning",
    "refactor",
    "release-check",
    "release-notes",
    "requirements",
    "secret-scan",
    "security",
    "simplify",
    "space-setup",
    "terraform",
    "terragrunt",
    "threat-model",
    "upgrade-plan",
    "verify",
    "vision",
    "workflow-check",
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


KNOWN_TYPES = [SKILL_TYPE, AGENT_TYPE, HOOK_TYPE, INSTRUCTION_TYPE]
KNOWN_TYPE_NAMES = [type_config.type_name for type_config in KNOWN_TYPES]
GLOBAL_SUPPORTED_TYPE_NAMES = [
    AGENT_TYPE.type_name,
    HOOK_TYPE.type_name,
    INSTRUCTION_TYPE.type_name,
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
    "agent": ["architect", "designer", "engineer", "planner", "product", "release", "tester"],
    "instruction": [
        "git",
        "java",
        "k8s",
        "helm",
        "markdown",
        "python",
        "rancher",
        "security",
        "terraform",
        "terragrunt",
        "testing",
        "typescript",
    ],
    "hook": [
        "agent-call-audit",
        "log-retention-cleanup",
        "post-edit-markdown-quality",
        "post-edit-format",
        "post-commit-security-scan",
        "pre-tool-safety-gate",
        "session-audit",
    ],
}

# Legacy names are retained only to migrate manifest-tracked prompt files.
RETIRED_PROMPT_SKILLS: dict[str, str] = {
    "api-design-review": "openapi",
    "architecture-risk": "architecture",
    "artifact-integrity": "artifact-integrity",
    "ci-triage": "debug",
    "dependency-audit": "dependency",
    "incident-timeline": "postmortem",
    "migration-plan": "migration-plan",
    "migration-safety": "migrate",
    "ops-readiness": "inspect",
    "quick-review": "code-review",
    "reasoning": "reasoning",
    "release-check": "release-check",
    "repo-assessment": "inspect",
    "template-impact": "analyse",
    "test-gaps": "inspect",
    "upgrade-plan": "upgrade-plan",
    "workflow-check": "workflow-check",
}
