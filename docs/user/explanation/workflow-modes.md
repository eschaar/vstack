# Workflow modes

Workflow modes define how teams move through vstack stages.

Use this page to choose the right mode for team maturity, review style, and release risk.

## Why modes exist

Different teams need different execution control:

- some want strict orchestration,
- some want explicit manual checkpoints,
- some need both depending on change type.

A single mode cannot optimize all of those goals.

## Agentic mode

In `agentic`, planner orchestrates stage progression using configured workflow rules.

Choose `agentic` when you want:

- consistent stage ordering,
- centralized orchestration,
- less manual transition overhead,
- easier repeatability for routine delivery flows.

Trade-off: less interactive control per transition.

## Manual mode

In `manual`, users move stage-by-stage using explicit handoffs.

Choose `manual` when you want:

- explicit human control for each transition,
- tighter compliance or review sign-off points,
- training workflows where teams learn each stage boundary.

Trade-off: slower throughput and more operator effort.

## Hybrid mode

In `hybrid`, both planner orchestration and manual handoffs are available.

Choose `hybrid` when:

- teams are transitioning from manual to planner-led execution,
- different work streams need different control styles,
- you want fallback manual control without disabling planner paths.

Trade-off: mixed use in one session can cause duplicated transitions or confusion.

## How to choose

A practical default policy:

1. Start with `agentic` for standard delivery work.
1. Use `manual` for high-governance or training contexts.
1. Use `hybrid` only when both patterns are intentionally required.

In `hybrid`, pick one execution path per session and stay on it.

## Planner vs. direct agent invocation

Choosing a workflow mode is separate from deciding whether to use the planner at all.
The planner is built for coordinating a full multi-role delivery pipeline.
It adds overhead — multiple model calls, orchestration logic, gate pauses — that is only
worthwhile when multiple roles genuinely need to collaborate in sequence.

**Use the planner when:**

- Delivering a feature, fix, or change that spans multiple roles (product → architect → designer → engineer → tester → release).
- You want explicit gate approvals at each stage boundary.
- The work is large enough that cross-role coordination matters.

**Use a specialist agent directly when:**

- The task clearly belongs to one role: update architecture docs → `@architect`, write release notes → `@release`, fix a test → `@engineer`, review an API contract → `@designer`.
- You are doing focused day-to-day maintenance: refreshing a report, writing an ADR, bumping a dependency.
- You want the fastest path to a result.

**Why the planner cannot automatically do this better:**
The planner works from a stage-based pipeline, not from artifact ownership. It cannot
infer that "update the architecture docs" should skip product, designer, engineer, tester,
and release and route only to architect. Per-task stage qualification does not scale —
there is no finite list of task types that maps cleanly onto pipeline subsets.

The effective pattern is: you make the routing decision. The planner handles orchestration
when the full pipeline is genuinely needed. Direct invocation handles everything else.

| Situation                       | Best approach                                        |
| ------------------------------- | ---------------------------------------------------- |
| Full feature delivery           | `@planner` — run the pipeline                        |
| Update a specific doc           | `@architect`, `@designer`, `@release`, etc. directly |
| Fix a bug                       | `@engineer` directly                                 |
| Run verification                | `@tester` directly                                   |
| Prepare a release               | `@release` directly                                  |
| Unsure which role owns the work | `@planner` — it will route to the right specialist   |

## Related docs

- [Configure workflow modes](../how-to/configure-workflow-modes.md)
- [Configuration](../reference/configuration.md)
- [CLI commands](../reference/cli-commands.md)
