"""Utilities and tests for test template config style."""

from __future__ import annotations

import re
from pathlib import Path

LONG_INLINE_LIMIT = 100
BLOCK_SCALAR_MARKERS = {"|", "|-", "|+", ">", ">-", ">+"}


def _strip_inline_yaml_quotes(value: str) -> str:
    """Internal helper to strip inline yaml quotes."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


class TestAgentTemplateConfigStyle:
    """Test cases for AgentTemplateConfigStyle."""

    def test_long_description_and_prompt_use_block_scalars(self) -> None:
        """Test that long description and prompt use block scalars."""
        repo_root = Path(__file__).resolve().parents[3]
        configs = sorted(
            (repo_root / "src" / "vstack" / "_templates" / "agents").glob("*/config.yaml")
        )

        violations: list[str] = []
        pattern = re.compile(r"^(\s*)(description|prompt):\s*(.*)$")

        for path in configs:
            for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                m = pattern.match(line)
                if not m:
                    continue

                value = m.group(3).strip()
                if value in BLOCK_SCALAR_MARKERS or value == "":
                    continue

                inline_value = _strip_inline_yaml_quotes(value)
                if len(inline_value) > LONG_INLINE_LIMIT:
                    rel = path.relative_to(repo_root)
                    violations.append(
                        f"{rel}:{line_no} {m.group(2)} inline length {len(inline_value)} > {LONG_INLINE_LIMIT}; use '>' block scalar"
                    )

        assert not violations, "\n".join(violations)
