# ADR-010: Artifact Hand-off Pipeline

> Maintained by: **agents** role

**date:** 2026-03-28\
**status:** accepted

## context

With 6 defined roles (ADR-009), we need a protocol for how roles communicate.
Options range from in-memory state (fast but transient) to files on disk (slower
but persistent and inspectable) to an external message bus (complex and heavyweight).

## decision

**Roles communicate exclusively through files on disk.**

Each role:

1. Reads its required upstream artifacts (defined below)
1. Executes its workflow
1. Writes its output artifacts

If a required upstream artifact is missing, the role reports what it needs
and stops — it does not proceed with partial context.

### artifact hand-off table

| Role      | Reads                                                                                                                       | Writes                                                                              |
| --------- | --------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| product   | (nothing — initiates)                                                                                                       | `docs/product/vision.md`, `docs/product/requirements.md`, `docs/product/roadmap.md` |
| architect | `docs/product/vision.md`, `docs/product/requirements.md`                                                                    | `docs/architecture/architecture.md`, `docs/architecture/adr/*.md`                   |
| designer  | `docs/product/vision.md`, `docs/product/requirements.md`, `docs/architecture/architecture.md`, `docs/architecture/adr/*.md` | `docs/design/design.md`, API specs                                                  |
| engineer  | `docs/product/requirements.md`, `docs/design/design.md`, `docs/architecture/adr/*.md`                                       | code, unit tests                                                                    |
| tester    | `docs/product/requirements.md`, source files, config                                                                        | `docs/test-report.md`, `docs/security-report.md`, `docs/performance-baseline.md`    |
| release   | `docs/test-report.md`, `docs/security-report.md`, `docs/performance-baseline.md`, user sign-off                             | `docs/releases/{date}.md`, `CHANGELOG.md`, release PR                               |

### user gate moments

There are 3 explicit user gate moments:

| Gate                         | Trigger                                              | Required                              |
| ---------------------------- | ---------------------------------------------------- | ------------------------------------- |
| **1. Requirements approval** | After `product` writes requirements.md               | User approves before architect starts |
| **2. Design approval**       | After `architect` + `designer` write their artifacts | User approves before engineer starts  |
| **3. Pre-prod sign-off**     | After `tester` reports are ready                     | User approves before release starts   |

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

The pipeline runner (`scripts/runner.py`) reads artifact paths from a config and
checks for existence before invoking the next role. This makes the runner
a thin orchestrator, not a data manager.
