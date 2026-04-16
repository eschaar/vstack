# vstack — workflow

> Maintained by: **designer** role\
> Last updated: 2026-04-01

## overview

This document describes how vstack workflows execute today (single-call execution)
and a possible future orchestrated role pipeline.

______________________________________________________________________

## current execution model — single-call

The user invokes a skill from Copilot Agent Mode. Copilot loads the corresponding
`.agent.md` file and executes the full workflow in a single model call.

```text
User types: @<skill-name> <task>

  → VS Code loads .github/agents/<skill>.agent.md
  → Copilot executes all steps in one context window
  → Artifacts written to disk (docs/architecture/architecture.md, docs/test-report.md, etc.)
  → Done
```

**Characteristics:**

- Fast, low friction
- All context fits in one call
- Limited to skills the user explicitly invokes
- No automatic hand-off between roles

______________________________________________________________________

## possible future model — orchestrated role pipeline

Each role becomes a separate model call. Output artifacts from one role become
the input context for the next.

```text
┌─────────────────────────────────────────────────────────────────┐
│  PIPELINE                                                       │
│                                                                 │
│  product ──→ [vision.md, requirements.md, roadmap.md]          │
│      ↓                                                          │
│  architect ──→ [architecture/architecture.md, architecture/adr/*.md] │
│      ↓                                                          │
│  designer ──→ [design/design.md]  (skip if backend-only)       │
│      ↓                                                          │
│  ┌── USER GATE 1: approve requirements + design ──┐            │
│  └────────────────────────────────────────────────┘            │
│      ↓                                                          │
│  engineer ──→ [code + unit tests]                               │
│      ↓                                                          │
│  tester ──→ [test-report.md, security-report.md, performance-baseline.md]  │
│      ↓                                                          │
│  ┌── USER GATE 2: pre-prod sign-off ──┐                        │
│  └─────────────────────────────────────┘                       │
│      ↓                                                          │
│  ┌── USER GATE 3: final merge approval ──┐                     │
│  └────────────────────────────────────────┘                     │
│      ↓                                                          │
│  release ──→ [releases/{date}.md, CHANGELOG.md, PR]            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Characteristics:**

- Each role is scoped to its domain
- Each role reads its inputs from disk (artifacts from upstream roles)
- User gates are explicit pauses for human review

______________________________________________________________________

## artifact hand-off protocol

Roles communicate through files on disk. Each role:

1. Reads upstream artifacts (defined by its role contract)
1. Executes its workflow
1. Writes its output artifacts

Neither roles nor skills maintain in-memory state between calls.
If an upstream artifact is missing, the role reports what it needs before proceeding.

### required reads per role

| Role      | Must read before starting                                                                                                   |
| --------- | --------------------------------------------------------------------------------------------------------------------------- |
| product   | (none — initiates pipeline)                                                                                                 |
| architect | `docs/product/vision.md`, `docs/product/requirements.md`                                                                    |
| designer  | `docs/product/vision.md`, `docs/product/requirements.md`, `docs/architecture/architecture.md`, `docs/architecture/adr/*.md` |
| engineer  | `docs/product/requirements.md`, `docs/design/design.md`, `docs/architecture/architecture.md`, `docs/architecture/adr/*.md`  |
| tester    | `docs/product/requirements.md`, relevant source files                                                                       |
| release   | `docs/test-report.md`, `docs/security-report.md`, user sign-off                                                             |

______________________________________________________________________

## user gate moments

There are **4 explicit user gate moments** where the pipeline pauses for human input:

| Gate                         | When                                                         | Who signs off |
| ---------------------------- | ------------------------------------------------------------ | ------------- |
| **1. Requirements approval** | After product writes requirements.md                         | User          |
| **2. Design approval**       | After architect writes architecture + designer writes design | User          |
| **3. Pre-prod sign-off**     | After tester reports are ready                               | User          |
| **4. Merge approval**        | Before release creates PR                                    | User          |

Gates prevent automated pipelines from deploying without human review.
In the current model, the user implicitly gates by choosing which skill to invoke next.
In the orchestrated model, the orchestrator pauses and waits for explicit confirmation.

______________________________________________________________________

## skill execution within a role

Skills are the HOW inside a role call.

```text
Role call → loads role persona
          → selects applicable skills
          → executes skill steps sequentially
          → writes output artifacts
```

A role may use multiple skills in sequence within one model call. For example,
the architect role uses the `adr` skill to write decision records and the
`architecture` skill to produce the architecture document.

______________________________________________________________________

## forward compatibility

The move from the current model to an orchestrated role pipeline was designed to require minimal refactoring:

- All artifacts are files — no in-memory state to migrate
- Skill steps are already self-contained and idempotent
- Role boundaries are already defined (see `docs/architecture/adr/009-role-model.md`)
- Pipeline ordering is documented here and in `docs/architecture/adr/010-artifact-flow.md`

See `docs/product/roadmap.md` for the optional orchestration milestone.
