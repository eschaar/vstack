# ADR-029: Multi-agentic execution model — DAG as primary coordination model

> Maintained by: **architect** role

**date:** 2026-05-12
**status:** accepted
**depends on:** ADR-028 (DAG dependency semantics), ADR-009 (role model), ADR-004 (Option A to B pipeline)

## context

vstack models software delivery as a pipeline of role agents: product, architect, designer,
engineer, tester, release. As the system evolves toward multi-agentic execution (Option B),
a coordination model must be chosen that:

1. Expresses dependencies between stages without requiring a runtime scheduler today.
1. Scales from sequential single-agent execution to concurrent multi-agent execution without
   breaking existing configurations.
1. Stays debuggable and transparent to the developer — the developer must be able to reason
   about why an agent was invoked and in what order.
1. Runs inside VS Code Agent Mode, which is chat-turn-based, not event-reactive.

Four coordination models were evaluated:

- **Sequential** — stages run in declared order, no branching or concurrency.
- **DAG** — stages declare explicit dependencies; ready stages execute when all dependencies complete.
- **Event-driven** — agents react to artifact changes (file writes, state transitions) without
  central coordination.
- **Orchestration tree** — a root planner decomposes work into sub-planners, which in turn spawn
  leaf agents.

## decision

**Use the DAG model as the primary coordination contract for vstack workflows.**

The decision follows from two separate concerns kept intentionally separate:

1. **Configuration semantics** (shipped in ADR-028): `depends_on` per stage, validated DAG,
   backward-compatible sequential default.
1. **Runtime scheduling policy** (follow-on work): how the planner executes ready stages,
   handles joins, and manages failure.

The DAG model is adopted because:

1. Dependencies are explicit in `workflow.stages` config — there is no hidden runtime inference.
1. The schema is backward compatible: stages without `depends_on` continue sequential behavior.
1. Validation is strict and fast-fail: cycles, unknown targets, and self-references are caught
   at install time.
1. It is compatible with VS Code Agent Mode's turn-based execution model.
1. Evolution to parallel scheduling does not require configuration changes — the dependency data
   is already present.

## alternatives considered

### A. Sequential ordering (status quo before ADR-028)

Rejected as the long-term model for the following reasons:

- Cannot express that architect and designer can both start once product is done.
- Cannot express that engineer waits for both architect and designer before starting.
- Any parallelism would require duplicating stages or changing the ordering heuristic.

Retained as the backward-compatible default when `depends_on` is omitted.

### B. Event-driven coordination

In an event-driven model, agents react to artifact changes rather than explicit stage
progression. For example, the engineer agent would start when `architecture.md` and
`design.md` appear on disk, and the tester would start when code changes are written.

**Why not adopted:**

1. VS Code Agent Mode is chat-turn-based. Agents are invoked explicitly by the user or the
   planner, not by file-system events. There is no ambient watcher.
1. Without a runtime trigger mechanism, agents have no signal to start. The question
   "how does the engineer know to build?" has no answer in a pure event-driven model
   inside VS Code.
1. Artifact contracts between agents would need to be defined and versioned separately
   from stage configuration. This increases surface area without clear benefit at current scale.
1. Non-determinism: if two agents produce the same artifact type, the event fan-out is
   ambiguous. Cycle prevention requires the same graph analysis as the DAG model, but
   without the explicit declaration.
1. Debugging is harder: "why did the tester not start?" requires inspecting artifact state
   rather than reading a dependency declaration.

Event-driven coordination remains a viable model for external system integrations (triggering
vstack stages from CI artifact uploads, for example), but it is not the right default for the
VS Code-native execution model.

### C. Orchestration tree (hierarchical planner)

In an orchestration tree, the root planner decomposes work into sub-planners, which in turn
spawn leaf agents. This enables recursive decomposition: a `tester-planner` could invoke
`tester(security)`, `tester(performance)`, and `tester(functional)` as independent sub-agents.

**Why not adopted as the primary model:**

1. Requires a runtime planner capable of recursive agent spawning, which is not available in
   the current single-call VS Code Agent Mode execution model.
1. Context propagation through the tree is lossy: each sub-agent receives only a slice of the
   full project context.
1. Cost and latency scale with tree depth: a three-level tree multiplies model calls significantly.
1. Error propagation requires explicit join and failure-handling policy at every tree node.
1. The planner agent already exists in vstack; its evolution toward hierarchical orchestration
   is architecturally possible but is a follow-on milestone.

**Role-variant invocation (e.g. tester(security), tester(performance)):**

The orchestration tree pattern is the correct model when a single role must be invoked
multiple times in different contexts within the same workflow. This applies to any role
whose prompt explicitly permits self-decomposition, including architect, product, designer,
engineer, tester, and release when the work can be merged cleanly. Two strategies are available:

1. **Internal orchestration (recommended now):** The `tester` agent orchestrates its own
   sub-specializations using skill invocations within a single agent turn. No schema change
   required. The `tester` agent reads its context and calls `security`, `performance`, and
   functional verification skills in sequence or passes them as sub-tasks.

1. **Stage variants (future):** Introduce a `variant` or `context` field alongside `role`
   to create distinct stage identities (`tester/security`, `tester/performance`). This
   requires changing the stage identity key from `role` to `role + variant`, updating the
   duplicate-role validation rule, and updating handoff resolution. An ADR must be written
   before implementing this.

The current duplicate-role validation in `_validate_workflow_stages` explicitly rejects
configs with the same role appearing more than once. This is intentional: it prevents
ambiguous dependency edges until stage variants are formally supported.

## rationale

The DAG model provides the right balance of expressiveness and simplicity for vstack's
current execution context:

| Property                                  | Sequential | DAG | Event-driven | Orchestration tree |
| ----------------------------------------- | ---------- | --- | ------------ | ------------------ |
| Explicit dependency declaration           | No         | Yes | No           | Partial            |
| Cycle detection at install time           | N/A        | Yes | No (runtime) | Partial            |
| Compatible with chat-turn execution       | Yes        | Yes | No           | Partial            |
| Backward compatible with existing configs | Yes        | Yes | No           | No                 |
| Enables future parallel scheduling        | No         | Yes | Yes          | Yes                |
| Debuggable by reading config alone        | Yes        | Yes | No           | Partial            |
| Supports role-variant invocation          | No         | No  | Yes          | Yes                |

The DAG model covers all current requirements and does not block future evolution.
Event-driven and orchestration tree remain valid expansion paths for specific use cases:

- **Event-driven:** external trigger integration (CI artifact events → vstack stage start).
- **Orchestration tree:** recursive role decomposition when role-variant stage support is added.

## impact on the Option B pipeline

This ADR establishes the coordination semantics that the Option B planner runtime will
implement. When parallel scheduling is added:

1. The planner reads `depends_on` from workflow config to compute ready stages.
1. Ready stages (all dependencies complete) can be dispatched concurrently.
1. Join behavior (waiting for all incoming edges) is implicit in the dependency graph.
1. No configuration migration is required for existing projects.

This decision also defines the boundary for the next evolution step: if role-variant support
is required, an ADR must extend the stage identity model before code changes are made.
