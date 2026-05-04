# ADR-009: 6-Role Agent Model

> Maintained by: **architect** role

**date:** 2026-03-28\
**status:** accepted

## context

vstack's original skill model had no concept of "roles" — any skill could be invoked
by anyone at any time. As the skill set grew to 19 skills across planning, verification,
security, release, and observability domains, it became unclear:

- Which skills belong together for a given stage of work?
- Who is responsible for each output artifact?
- How does the pipeline hand off between stages?

A role model answers these questions by defining personas: WHO does what, WHEN, and
which artifacts they own.

## decision

Define **6 fixed agent roles**:

- **`product`** — Initiates pipeline, owns vision + requirements

  - Artifacts: vision, requirements, roadmap

- **`architect`** — Locks in technical plan, writes ADRs

  - Artifacts: architecture overview, ADRs

- **`designer`** — API design + DX; backend-mode skips UI/UX

  - Artifacts: design overview, API specs, UX artifacts (frontend scope only)

- **`engineer`** — Implements code + unit tests

  - Artifacts: source code, unit tests, RCA and post-mortem artifacts

- **`tester`** — Verification, security, and performance audit

  - Artifacts: test report, security report, performance baseline

- **`release`** — Release preparation and PR handoff

  - Artifacts: release document, changelog, release PR

Default artifact paths for each role are defined in ADR-021 and configured per-project
in each agent's `config.yaml`. Paths are overridable; the role ownership above is fixed.

## conceptual model

```
WHO  = role (product, architect, designer, ...)
HOW  = skill (requirements, adr, verify, deploy, ...)
WHAT = user input + artifact files on disk
```

A role is a **persona** with a defined domain of responsibility.
A skill is a **procedure** the persona uses to produce an artifact.
A role may use multiple skills in sequence within one call.

## alternatives considered

1. Keep flat skill list, no roles — rejected because it provides no answer to
   "what should I invoke next?" or "who owns architecture.md?"
1. More than 6 roles (e.g., separate Security + Performance) — rejected because
   vstack keeps the fixed role model intentionally small.
1. Separate tester and guardian roles — rejected because verification, security,
   and performance reviews are tightly coupled in the current workflow.

## rationale

6 roles matches the current vstack operating model: product, architect, designer,
engineer, tester, and release. The mapping is intentionally small and practical.

## impact on future orchestrated pipeline

Each role is one pipeline stage. The 6-role model directly defines the pipeline
order. See `docs/design/workflow.md` and ADR-010.
