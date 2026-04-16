# vstack — agents

> Maintained by: **designer** role\
> Last updated: 2026-04-01\
> VS Code docs: [custom agents](https://code.visualstudio.com/docs/copilot/customization/custom-agents) · [agents overview](https://code.visualstudio.com/docs/copilot/agents/overview)

## what are agents?

Agents are VS Code custom agents (`.agent.md`) that adopt a specific role or persona in GitHub Copilot Chat. Each agent has:

- A **set of tools** it may use (read, edit, execute, …)
- **Instructions** in the file body (role, responsibilities, how to work)
- Optional **handoffs** to transition the user to the next agent in a workflow

In vstack, agents map to the 6 engineering roles: `product`, `architect`, `designer`, `engineer`, `tester`, `release`.

Canonical names are the source of truth. Historical or compatibility aliases should
remain exceptional and temporary. See `docs/architecture/adr/002-artifact-naming-and-compatibility-policy.md`.

______________________________________________________________________

## file locations

| Path                                              | Purpose                                           |
| ------------------------------------------------- | ------------------------------------------------- |
| `src/vstack/_templates/agents/<name>/config.yaml` | Source of truth — metadata and frontmatter fields |
| `src/vstack/_templates/agents/<name>/template.md` | Agent instructions (body only, no frontmatter)    |
| `.github/agents/<name>.agent.md`                  | Generated output — what VS Code loads             |

**Never edit `.github/agents/` directly.** Regenerate after every change:

```bash
vstack install
```

______________________________________________________________________

## config.yaml fields

`config.yaml` is plain YAML (no `---` markers). vstack reads it at generation time and emits only recognised schema fields to the `.agent.md` frontmatter. Unknown fields (`version`, `handoffs`, …) are silently dropped from output.

Style rule: long `description` and `handoffs.prompt` values should use YAML block scalars (`>`). A test enforces this when inline text exceeds 100 characters.

### emitted to frontmatter

| Field                      | Type           | Required | Notes                                                                                                                                                                            |
| -------------------------- | -------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`                     | string         | no       | Overrides filename as picker label                                                                                                                                               |
| `description`              | string         | no       | Shown as placeholder text in chat input                                                                                                                                          |
| `argument-hint`            | string         | no       | Hint text shown after `@agent` in chat                                                                                                                                           |
| `tools`                    | list           | no       | Tools available to this agent (see below)                                                                                                                                        |
| `agents`                   | list           | no       | Subagents this agent may invoke; `["*"]` = all                                                                                                                                   |
| `model`                    | string or list | no       | Force one or more model IDs. In this repo, model values are pinned in templates and validated by tests; change only after verifying support in your VS Code/Copilot environment. |
| `user-invocable`           | bool           | no       | `true` = show in agents dropdown (default)                                                                                                                                       |
| `disable-model-invocation` | bool           | no       | `true` = prevent other agents from calling this one                                                                                                                              |
| `target`                   | string         | no       | `vscode` (default) or `github-copilot`                                                                                                                                           |
| `handoffs`                 | object-list    | no       | Sequential workflow handoffs — see [handoffs](#handoffs) below                                                                                                                   |
| `mcp-servers`              | raw YAML       | no       | MCP server config (`github-copilot` target only)                                                                                                                                 |
| `hooks`                    | raw YAML       | no       | Chat hooks (Preview — requires `chat.useCustomAgentHooks` setting)                                                                                                               |
| `metadata`                 | raw YAML       | no       | String key/value annotations (`github-copilot` target only)                                                                                                                      |

### vstack-internal only (not emitted)

| Field     | Notes                                                                          |
| --------- | ------------------------------------------------------------------------------ |
| `version` | Semantic version for vstack change tracking — never reaches the generated file |

Frontmatter multiline rendering is configured in generator code (`ArtifactTypeConfig.preserve_multiline_frontmatter`), not per-agent `config.yaml`.

______________________________________________________________________

## tools

Use the following tool names in the `tools` list:

| Tool      | Access                                        |
| --------- | --------------------------------------------- |
| `read`    | Read files, search workspace, terminal output |
| `search`  | Semantic and text search                      |
| `edit`    | Create and modify files                       |
| `execute` | Run terminal commands                         |
| `web`     | Fetch web pages                               |
| `vscode`  | Open editors, run commands, access UI         |
| `todo`    | Create and manage todo lists                  |
| `agent`   | Invoke subagents (requires `agents` field)    |

Include `agent` in `tools` when you set `agents`. Omit `execute` for read-only roles (e.g. `product`).

______________________________________________________________________

## handoffs

Handoffs create guided sequential workflows. After a response completes, VS Code shows a button that switches to the target agent with a pre-filled prompt.

`handoffs` is fully supported in `AGENT_SCHEMA` and is emitted by the generator. Define handoffs in `config.yaml` and they will appear in the generated `.agent.md` frontmatter.

Structure:

```yaml
handoffs:
  - label: Start implementation
    agent: engineer
    prompt: Design is complete in docs/design/design.md. Please implement.
    send: false        # true = auto-submit the prompt
    model: ""          # optional override; use only a verified model ID
```

______________________________________________________________________

## template body

`template.md` contains only the agent instructions — no frontmatter. The generator adds frontmatter from `config.yaml` at build time.

## canonical template structure (required)

All role templates in `src/vstack/_templates/agents/<name>/template.md` must follow this high-level section order:

1. `# <role>`
1. `## identity and purpose`
1. `## responsibilities`
1. `## scope and boundaries`
1. `## limitations and do not do`
1. `## working principles`
1. `## decision guidelines`
1. `## communication style`
1. `## workflow and handoffs`
1. Role-specific deep-dive sections (e.g. `how you work`, `scope detection`, `artifact checklist`, `verification tracks`)
1. `## baseline and optional delta` (if applicable)
1. `## success criteria`
1. `## failure and escalation rules`
1. `## artifacts you own` or `## artifacts you touch`
1. `## completion checklist`
1. `## skills you use`

Rules:

- Keep the canonical sections present and in this order for every role.
- Role-specific sections are allowed, but they must not replace canonical sections.
- Keep role boundaries explicit; do not let one role absorb another role's ownership.
- Prefer baseline-first language and treat `docs/delta/{id}/` as temporary.

Minimal shape:

```markdown
# <role>

## identity and purpose

You are a **<title>** acting as the **<role> role**. <one-line purpose>.

## responsibilities

- …

## scope and boundaries

- …

## limitations and do not do

- …

## working principles

- …

## decision guidelines

- …

## communication style

- …

## workflow and handoffs

- …

## success criteria

- …

## failure and escalation rules

- …

## artifacts you own

| artifact | purpose |
|----------|---------|
| ... | ... |

## completion checklist

- …

## skills you use

- …
```

To reference a tool in body text, use `#tool:<name>`, e.g. `#tool:web/fetch`.\
To reference other files (e.g. instruction files), use Markdown links.

______________________________________________________________________

## adding a new agent

1. Create `src/vstack/_templates/agents/<name>/config.yaml` with at minimum `name` and `description`.
1. Create `src/vstack/_templates/agents/<name>/template.md` with the agent instructions.
1. Regenerate: `vstack install`
1. Verify: `vstack verify` or `python3 -m pytest test/ -q`

______________________________________________________________________

## example config.yaml

```yaml
name: architect
version: 1.0.1
description: "Senior software architect. Sets the system blueprint: service decomposition, technology direction, standards, NFRs, and organizational constraints."
argument-hint: "[design architecture | write ADR | review architecture | check implementation alignment]"
tools:
  - read
  - search
  - edit
  - web
  - vscode
  - todo
  - agent
agents: ["*"]
target: vscode
user-invocable: true
```
