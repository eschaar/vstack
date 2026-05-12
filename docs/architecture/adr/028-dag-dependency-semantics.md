# ADR-028: DAG dependency semantics for multi-agentic workflow stages

> Maintained by: **architect** role

**date:** 2026-05-12
**status:** accepted
**depends on:** ADR-023 (workflow contract), ADR-024 (subagent orchestration)

## context

ADR-023 introduced `workflow.stages` as the project source of truth for stage order,
gates, and handoffs. The initial behavior remained sequential: each stage progressed to
the next stage in declared order.

That model is deterministic and simple, but it cannot represent branching workflows where
multiple stages can start after a shared prerequisite. It also cannot represent explicit
joins where a downstream stage waits for several upstream stages.

The roadmap already identified a DAG model as the next step. We now need to make DAG
semantics first-class in workflow configuration while preserving compatibility for existing
projects that rely on sequential behavior.

## decision

### 1. Add optional `depends_on` to `workflow.stages`

Each stage may define `depends_on: [role, ...]` in `.vstack/config.yaml`.

Rules:

1. Dependency names must reference existing stage roles.
1. A stage cannot depend on itself.
1. Duplicate dependency entries are normalized to one entry.
1. Blank dependency entries are ignored.

### 2. Keep sequential compatibility as default

If a stage omits `depends_on`, vstack applies an implicit dependency on the previous
stage in `workflow.stages` order.

This preserves legacy behavior without requiring migration for existing repositories.

### 3. Validate the full workflow graph before generation

Workflow parsing now validates:

1. Stage roles are non-empty.
1. Stage roles are unique.
1. `handoffs[].agent` targets refer to existing stage roles.
1. `depends_on` references are valid and non-self.
1. The full stage graph is acyclic.

Invalid configuration fails fast with actionable error messages.

### 4. Make handoff resolution DAG-aware

Worker handoff target resolution now derives downstream roles from dependency edges,
not only from linear next-stage indexing.

Behavior:

1. If a stage has no explicit handoffs and has multiple downstream dependents, fallback
   handoffs are generated for each dependent in configured stage order.
1. If explicit handoffs omit `agent`, target resolution defaults to the first downstream
   dependent in configured stage order.
1. Existing manual/agentic/hybrid mode semantics are unchanged.

## alternatives considered

### A. Keep strictly sequential stage semantics

Rejected. This cannot model branching and join dependencies and blocks DAG progression.

### B. Introduce a separate `workflow.dependencies` top-level map

Rejected. It duplicates role declarations and increases drift risk between stage and
dependency definitions.

### C. Treat DAG as planner-only runtime logic without schema support

Rejected. Without schema-level dependency data, planner behavior would be implicit,
non-portable, and hard to validate.

## rationale

This decision gives vstack a minimal but robust DAG contract:

1. Configuration remains backward compatible.
1. Validation is strict enough to prevent ambiguous or unsafe orchestration graphs.
1. Worker artifact generation can express dependency-aware transitions.
1. Planner evolution toward parallel stage scheduling is unblocked.

The design intentionally separates two concerns:

1. **Configuration semantics** (this ADR): dependency graph, validation, and handoff target rules.
1. **Runtime scheduling policy** (follow-on work): how planner executes ready stages in parallel
   and how join/failure behavior is handled.

## impact on the Option B pipeline

This ADR upgrades the workflow contract from linear progression to a validated DAG model.
It enables planner implementations to compute ready stages from dependency completion and
support multi-agentic execution patterns while keeping deterministic compatibility behavior
for existing projects.

Planner runtime layer scheduling and explicit join policy controls remain follow-on work,
not part of this ADR's shipped scope.
