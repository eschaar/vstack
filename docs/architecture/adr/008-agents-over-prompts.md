# ADR-008: VS Code Agent Files Over Prompt Files

> Maintained by: **agents** role

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

The `prompts/` directory had 19 files and was the only VS Code–exposed surface.

## decision

Migrate from `prompts/*.prompt.md` → `.github/agents/*.agent.md`.

- Delete `prompts/` directory entirely.
- Generator (`gen_skill_docs.py`) builds `.github/agents/*.agent.md` when called with `--agents`.
- Agent frontmatter:
  ```yaml
  ---
  name: "<skill-name>"
  description: "<description up to 1024 chars>"
  tools: [read_file, insert_edit_into_file, run_in_terminal, file_search]
  user-invocable: true
  ---
  ```
- `TOOL_MAP` in the generator maps template tool names to VS Code tool IDs.

## alternatives considered

1. Keep `.prompt.md` and add `.agent.md` in parallel — rejected as it duplicates
   19 files and creates synchronisation overhead.
1. Keep `.prompt.md` only — rejected because it lacks subagent capability.

## rationale

The subagent invocation capability is the key enabler for future orchestrated pipeline stages
calling each other. Migrating now keeps the groundwork low-cost.

## impact on future orchestrated pipeline

The `orchestrate` role (and eventually the pipeline runner) can invoke
`@architect`, `@tester`, etc. as named agents. This is the VS Code primitive
for multi-agent orchestration.
