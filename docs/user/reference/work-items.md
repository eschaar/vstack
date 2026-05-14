# Work Items

This page explains what work-item documents vstack roles create and what each item is used for.

## What Work Items Are

Work items are role-owned documents (and related outputs) that move work through the delivery flow.

They provide durable handoff context between stages.

## Role Outputs at a Glance

| Role        | Primary Outputs                                                                              | Purpose                                                             |
| ----------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `product`   | `docs/product/vision.md`, `docs/product/requirements.md`, `docs/product/roadmap.md`          | Define product direction, scope, and outcomes.                      |
| `architect` | `docs/architecture/overview.md`, `docs/architecture/adr/*.md`                                | Define system blueprint and major decisions.                        |
| `designer`  | `docs/design/overview.md`, optional additional design docs (for example `docs/design/ux.md`) | Define interfaces, contracts, and interaction-level specifications. |
| `engineer`  | `src/**/*`, `tests/**/*`, optional issue RCA/postmortem docs                                 | Implement approved behavior and tests.                              |
| `tester`    | `docs/reports/**/*.md`, optional test updates in `tests/**/*`                                | Verify correctness, risk, and release readiness evidence.           |
| `release`   | `docs/releases/*.md`                                                                         | Capture release notes and sign-off records.                         |

## Planner Role

`planner` orchestrates stage progression and reads workflow docs across the repository. It does not own a dedicated role-specific output artifact family.

## Typical Flow

1. Product defines what should be built.
1. Architect defines structure and constraints.
1. Designer defines implementation-facing design specs.
1. Engineer writes code and tests.
1. Tester validates behavior and risk.
1. Release assembles release evidence and notes.

## Practical Notes

- Work-item paths are project conventions and can evolve with approved workflow configuration.
- Role ownership matters: each role should write its own output artifacts.
- Use role outputs as handoff baseline instead of ad-hoc chat-only context.

## Related Docs

- [Workflow modes explanation](../explanation/workflow-modes.md)
- [Configure workflow modes](../how-to/configure-workflow-modes.md)
- [Configuration](configuration.md)
- [Prompts overview](prompts-overview.md)
- [Skills overview](skills-overview.md)
