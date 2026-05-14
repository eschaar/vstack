# Configure Workflow Modes

Use this guide to set and use workflow modes in `.vstack/config.yaml`.

## Supported Modes

- `agentic`: planner orchestrates stage progression.
- `manual`: you move stages with explicit handoffs.
- `hybrid`: both planner orchestration and manual handoffs are available.

For conceptual guidance, see [Workflow modes](../explanation/workflow-modes.md).

## Set a Mode

Edit `.vstack/config.yaml`:

```yaml
workflow:
  mode: agentic
```

Then apply changes:

```bash
vstack init
```

## Verify Configuration

```bash
vstack validate
vstack manifest status --target .
```

## How to Use Each Mode

### Agentic

- Start your workflow with planner-led orchestration.
- Let stage progression follow configured workflow rules.
- Use this as default for routine delivery.

### Manual

- Run each stage explicitly and review handoff results.
- Use this for high-governance changes or onboarding.
- Expect slower throughput but tighter control.

### Hybrid

- Choose one execution path per session.
- Do not mix planner and manual transitions in the same flow.
- Use this when teams are transitioning process style.

## Team Policy Example

A practical policy:

1. Default to `agentic`.
1. Switch to `manual` for high-risk changes.
1. Use `hybrid` only for controlled transition periods.

## Related Docs

- [Workflow modes](../explanation/workflow-modes.md)
- [Configuration](../reference/configuration.md)
- [CLI commands](../reference/cli-commands.md)
