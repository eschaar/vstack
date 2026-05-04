# ADR-010: Artifact Hand-off Pipeline

> Maintained by: **architect** role

**date:** 2026-03-28\
**status:** accepted

## context

With 6 defined roles (ADR-009), we need a protocol for how roles communicate.
Options range from in-memory state (fast but transient) to files on disk (slower
but persistent and inspectable) to an external message bus (complex and heavyweight).

## decision

**Roles communicate exclusively through files on disk.**

**Pipeline progression is stage-gated by explicit user approval.**

**Handoff controls are reserved for happy-path continuation only.**

**Release is the sign-off orchestrator and consolidates cross-role review outcomes.**

Each role:

1. Reads its required upstream artifacts (defined below)
1. Executes its workflow
1. Writes its output artifacts

If a required upstream artifact is missing, the role reports what it needs
and stops — it does not proceed with partial context.

### artifact hand-off table

This table describes the conceptual read/write relationships between roles.
Default artifact paths are defined in ADR-021 and configured per-project in each
agent's `config.yaml`. Paths are overridable; the hand-off relationships below are fixed.

- **`product`**

  - Reads: *(nothing — initiates)*
  - Writes: vision, requirements, roadmap

- **`architect`**

  - Reads: product artifacts
  - Writes: architecture overview, ADRs

- **`designer`**

  - Reads: product artifacts, architecture artifacts
  - Writes: design overview, API specs, UX artifacts (frontend scope only)

- **`engineer`**

  - Reads: product artifacts, architecture artifacts, design artifacts
  - Writes: source code, unit tests, RCA and post-mortem artifacts

- **`tester`**

  - Reads: architecture artifacts, design artifacts, source files
  - Writes: test report, security report, performance baseline

- **`release`**

  - Reads: product artifacts, architecture artifacts, design artifacts, tester reports, user sign-off
  - Writes: release document, changelog, release PR

### user gate moments

There are explicit user gate moments after each stage output and before merge:

| Gate                             | Trigger                                 | Required                              |
| -------------------------------- | --------------------------------------- | ------------------------------------- |
| **1. Product approval**          | After `product` updates scope artifacts | User approves before architect starts |
| **2. Architecture approval**     | After `architect` updates artifacts     | User approves before designer starts  |
| **3. Design approval**           | After `designer` updates artifacts      | User approves before engineer starts  |
| **4. Implementation checkpoint** | After `engineer` updates code/tests     | User approves before tester starts    |
| **5. Verification approval**     | After `tester` reports are ready        | User approves before release starts   |
| **6. Merge approval**            | Before `release` creates PR             | User approves final merge             |

### handoff policy

Handoffs are UI accelerators for the happy path, not orchestration logic.

- Allowed pattern: `Go to next stage: <stage>` (single forward continuation)
- Disallowed: back/side/escalation handoff buttons
- For `NOK` or blockers, user explicitly chooses the recovery path

### release sign-off consolidation

Release gathers explicit `OK`/`NOK` reviews from upstream role perspectives
(typically tester, architect, designer, and product) and records a unified
decision matrix before PR creation.

The sign-off payload is standardized:

1. Verdict (`OK` or `NOK`)
1. Reviewed scope
1. Gaps or deviations
1. Impact/risk summary
1. Required next action and owner

## alternatives considered

1. In-memory state (pass objects between calls) — rejected: not persistent, hard to inspect,
   lost on interruption.
1. External database/message bus — rejected: heavyweight, introduces new dependency.
1. Files in a temp directory — rejected: not inspectable by the developer, not git-tracked.

## rationale

Files on disk:

- Are inspectable and editable by the developer
- Can be committed to git (traceability)
- Survive interruptions (resume-able pipeline)
- Require no new infrastructure
- Are already the natural output format for AI agents in VS Code

## impact on future orchestrated pipeline

The pipeline runner reads artifact paths from a config and
checks for existence before invoking the next role. This makes the runner
a thin orchestrator, not a data manager.
