{{SKILL_CONTEXT}}

# changedoc - Per-Change Planning Document

Create and maintain a changedoc for repository changes before implementation.
Use this for bug fixes, features, refactors, and similar change requests in
existing repositories.

For new greenfield projects, start with vision/roadmap/requirements first.

## File naming convention

Write changedocs to:

`docs/changes/<slug>_<title>_YYYYMMDD.md`

Use lowercase kebab-case for `<slug>` and concise snake_case for `<title>`.

In vstack repositories, initialize the file from:

`.vstack/templates/product/artifacts/changes/changedoc.md`

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
1. Acceptance Criteria
1. Test Scenarios

## Procedure

## Step 1 - Normalize request into scope

Capture:

- requested outcome
- explicit non-goals
- constraints and dependencies

## Step 2 - Build AS-IS from repository evidence

Use concrete file and behavior evidence. Avoid assumptions.

## Step 3 - Define TO-BE

Describe the target behavior and implementation intent clearly enough for
cross-role handoff.

## Step 4 - Record impact

Cover at least:

- architecture and boundaries
- API/data/model implications
- security and privacy implications
- operational implications (logs, metrics, rollout, migration)

## Step 5 - Define acceptance criteria and test scenarios

Make criteria observable and testable.
Include happy path, failure path, and regression scenarios.

## Step 6 - Update status by lifecycle

- `CONCEPT`: initial proposal and discovery
- `BUILD`: approved for implementation
- `IMPLEMENTED`: implementation complete and verified
- `ARCHIVED`: closed and retained for history

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

Escalate before implementation when:

- acceptance criteria are ambiguous
- trust-boundary or security impact is unclear
- migration or rollback implications are unclear
- required stakeholders have not approved transition to `BUILD`
