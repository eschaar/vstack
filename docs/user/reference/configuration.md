# Configuration

Project configuration is read from `.vstack/config.yaml`.

## How to read `.vstack/config.yaml`

- Lines starting with `#` are comments or examples and are not active.
- Only uncommented YAML keys are active configuration.
- Keep indentation valid when enabling example blocks.
- After changing configuration, run `vstack init` to apply it.

## Exclude configuration

Use `exclude` to skip artifact types or specific artifacts.

```yaml
exclude:
  skills:
    - terraform
    - helm
    - k8s
  instructions: all
  prompts: all
  hook: all
```

Rules:

- `type: all` skips an entire artifact type.
- `type: [name, ...]` skips only listed artifacts.
- Use exclusions to reduce generated surface for team needs.

## Workflow mode

Set workflow execution style in config:

```yaml
workflow:
  mode: agentic
```

Supported values:

| Mode      | Meaning                                                       |
| --------- | ------------------------------------------------------------- |
| `agentic` | Planner orchestrates stage progression automatically.         |
| `manual`  | User advances stages manually with handoffs.                  |
| `hybrid`  | Both planner orchestration and manual handoffs are available. |

Run `vstack init` after changing mode.

## Workflow version

`workflow.version` is the schema version for the `workflow` block in `.vstack/config.yaml`.

```yaml
workflow:
  mode: agentic
  version: 1
```

Guidance:

- Current supported value is `1`.
- `vstack install` seeds `version: 1` in new project config.
- Keep the existing value unless release notes explicitly require a change.
- Preserve this field when editing `workflow.stages` so tooling can validate semantics correctly.

Task-focused setup steps:

- [Configure workflow modes](../how-to/configure-workflow-modes.md)
- [Workflow modes](../explanation/workflow-modes.md)

## Hooks configuration

Use `hooks` to control repository hook generation and defaults.

```yaml
hooks:
  enabled: true
  mode: audit
  log_level: minimal
  log_retention_days: 7
  log_dir: .vstack/logs
  hooks:
    post-edit-markdown-quality:
      enabled: false
    pre-tool-safety-gate:
      mode: enforce
```

Common controls:

- `hooks.enabled`: globally enable or disable baseline hooks.
- `hooks.mode`: set default hook mode (`audit` or `enforce`).
- `hooks.hooks.<name>.enabled`: disable one named hook.
- `hooks.hooks.<name>.mode`: override mode for one named hook.

Run `vstack init --only hook` (or `vstack init`) after changing hooks config.

## `depends_on` semantics

`workflow.stages` order is canonical. Without `depends_on`, each stage implicitly depends on the previous stage (sequential flow).

Add `depends_on` to create explicit graph dependencies and parallel-ready branches:

```yaml
workflow:
  mode: agentic
  version: 1
  stages:
    - role: product
      gate: required
      hitl: always
    - role: architect
      gate: required
      hitl: always
      depends_on: [product]
    - role: designer
      gate: optional
      hitl: on-change
      depends_on: [product]
    - role: engineer
      gate: required
      hitl: always
      depends_on: [architect, designer]
```

Semantics:

- `depends_on: []` marks a root stage.
- Omitted `depends_on` falls back to sequential predecessor.
- A stage becomes ready only when all dependencies are ready or skipped.
- Cycles and invalid dependencies are rejected during validation/install.

## Related docs

- [Workflow modes](../explanation/workflow-modes.md)
- [Configure workflow modes](../how-to/configure-workflow-modes.md)
- [Hooks](./hooks.md)
- [Install and upgrade](../how-to/install-and-upgrade.md)
- [CLI commands](./cli-commands.md)
