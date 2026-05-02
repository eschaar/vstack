# ADR-008: VS Code Agent Files Over Prompt Files

> Maintained by: **architect** role

**date:** 2026-03-28\
**status:** accepted

## context

vstack originally generated `.prompt.md` files in `prompts/` (see ADR-005).
VS Code Copilot has since introduced `.agent.md` files in `.github/agents/`, which
provide two significant advantages:

1. **Subagent invocation**: Agents can call other agents (`@agent-name`), enabling
   role-to-role hand-offs without a custom pipeline runner.
1. **Better tool control**: Agent files support an explicit `tools:` list that is
   enforced by VS Code, not just advisory.
1. **User-invocable flag**: `user-invocable: true` makes agents appear in the
   Copilot agent picker.

The `prompts/` directory was the only VS Code–exposed surface.

## decision

Migrate from `prompts/*.prompt.md` → `.github/agents/*.agent.md`.

- Delete `prompts/` directory entirely.
- Generator produces `.github/agents/*.agent.md` from templates under `src/vstack/_templates/agents/`.
- Agent frontmatter:
  ```yaml
  ---
  name: "<agent-name>"
  description: "<description up to 1024 chars>"
  tools: [read, search, edit, execute, web, vscode, todo, agent]
  user-invocable: true
  ---
  ```

## alternatives considered

1. Keep `.prompt.md` and add `.agent.md` in parallel — rejected as it duplicates
   files and creates synchronisation overhead.
1. Keep `.prompt.md` only — rejected because it lacks subagent capability.

## rationale

The subagent invocation capability is the key enabler for future orchestrated pipeline stages
calling each other. Migrating now keeps the groundwork low-cost.

## impact on future orchestrated pipeline

The pipeline can invoke `@architect`, `@tester`, etc. as named agents.
This is the VS Code primitive for multi-agent orchestration.
