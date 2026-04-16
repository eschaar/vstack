# ADR-005: VS Code Prompt File Format

> Maintained by: **agents** role

**date:** 2026-03-27\
**status:** superseded by ADR-009

## context

VS Code GitHub Copilot supported `.prompt.md` files with YAML frontmatter defining
agent mode prompts. These were placed in `.github/prompts/` and invocable from
Copilot Chat.

## decision

Generate `prompts/*.prompt.md` files for each skill with:

```yaml
---
name: "vstack: {skill-name}"
description: "{description}"
mode: "agent"
tools: [...]
---
```

## superseded

This ADR is superseded by **ADR-009**. The format migrated from `.prompt.md` in
`prompts/` to `.agent.md` in `.github/agents/`, which provides subagent invocation
capability and better VS Code Agent Mode integration.

The `prompts/` directory has been deleted. See ADR-009 for the replacement decision.
