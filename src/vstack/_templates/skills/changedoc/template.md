{{SKILL_CONTEXT}}

# changedoc - Per-Change Planning Document

Use one changedoc when scope needs durable agreement or handoff, or when requested.
Small, clear, low-risk work may use an existing issue or conversation with outcome
and verification instead. Risk, ambiguity, and project policy determine escalation,
not change size. For greenfield projects, start with vision/requirements/roadmap.

## File naming convention

Write changedocs to:

`docs/changes/<slug>_<title>_YYYYMMDD.md`

Use lowercase kebab-case for `<slug>` and concise snake_case for `<title>`.

Initialize from `.vstack/templates/product/artifacts/changes/changedoc.md`.
Older customized templates remain valid: supplement the new document, never
overwrite the local template or backfill historical changedocs.

## Required metadata

Use this exact metadata block:

```yaml
status: CONCEPT | BUILD | IMPLEMENTED | ARCHIVED
type: bug | feature | refactor | chore | security | performance | docs | migration
reference: <single external reference, for example JIRA-123>
last_modified: YYYY-MM-DD
```

Rules:

- `reference` is singular.
- Do not add a separate `id` field.
- Do not use `created_at` or `updated_at`.
- Keep `last_modified` current on every substantive edit.

## Required sections

1. Goal and Context
1. AS-IS
1. TO-BE
1. Impact (high level)
1. Requirements (change-local obligations, not duplicated system baselines)
1. Acceptance Criteria (observable completion)
1. Test Scenarios (how to check)
1. Verification (actual evidence and gaps)

Add Execution Tasks only when useful; list real prerequisites, not dependencies
inferred from list order or role names. Multiple changes may share a branch.
Use local references when useful; preserve established references during revisions.

## Procedure

1. Read relevant code and decisions; record scope, constraints, non-goals, and AS-IS evidence.
1. Resolve material ambiguity one question at a time after checking known answers.
   Record accepted answers here; distinguish user outcomes from technical choices.
1. Define TO-BE, obligations, acceptance, and relevant happy/failure/regression
   scenarios without repeating prose. Use verifiable delivery slices when useful.
1. Record architecture, contract/data, security/privacy, and operational impact;
   link supporting material only when needed. Update affected shared baselines,
   not a parallel specification tree.
1. Before implementation, confirm understood scope, observable acceptance, no
   blocking questions, and required approval. Product owns intent; contributors
   may maintain tasks/evidence but escalate scope deviations.
1. Record criterion, check/result, reviewed commit or working-tree scope, and
   limitation. Use `passed`, `failed`, `not run`, or `no longer current`.
   Required failed/unrun checks prevent full verification; approved exceptions
   name the limitation and approver, never turn it into a pass. Production
   outcomes needing observation remain follow-ups.
1. After material intent/behavior changes, preserve references and reassess only
   affected tasks/evidence. Renew approval only for changed scope, risk, or policy.

Lifecycle states are not ordered thresholds:

- `CONCEPT`: discovery; implementation not authorized.
- `BUILD`: implementation authorized under project policy.
- `IMPLEMENTED`: agreed scope completed and verified.
- `ARCHIVED`: closed history; never authorizes new implementation.

## Output contract

Return:

```text
changedoc_path: docs/changes/<slug>_<title>_YYYYMMDD.md
status: CONCEPT|BUILD|IMPLEMENTED|ARCHIVED
reference: <single value>
summary: <one short paragraph>
open_questions: none | <bullet list>
```

## Escalation

Pause affected implementation for unclear acceptance, trust-boundary risk,
migration/rollback decisions, or missing required approval. Lightweight routing
never bypasses safety gates. Keep text concrete and compact; link rather than copy.
