{{SKILL_CONTEXT}}

{{BASE_BRANCH}}

# inspect - Read-Only Verification Audit

Assess and report; do not edit code, fix issues, or commit. Use `verify` for an
authorized fix loop, `architecture` for decisions, `security` for full audits,
and `performance` for profiling.

## Scope and report placement

Read agreed intent, relevant contracts, project policy, and the reviewed commit
or working-tree scope. Compare actual in-scope behavior with acceptance, including
required behavior absent from the diff. Do not infer completion from checkboxes.

Use `docs/reports/test-report.md` when project policy or cross-change reporting
requires it. Otherwise report in the response, or update an existing changedoc
only when authorized. No duplicate report or mandatory new file.

## Checks

Discover repository commands and run the smallest checks covering acceptance and
regressions. Preserve command failures and missing-tool evidence; never suppress
errors or treat unavailable checks as passes.

| Surface               | Checks when applicable                                                                                   |
| --------------------- | -------------------------------------------------------------------------------------------------------- |
| Baseline              | Lint, types, build/package, unit tests                                                                   |
| Integration/contracts | Service boundaries, OpenAPI/JSON Schema/Protobuf, compatibility                                          |
| Reliability/data      | Smoke, migrations/rollback, timeouts, retries, circuit breakers, concurrency                             |
| Observability         | Structured failure/transition logs, latency/error/saturation metrics, trace propagation, alerts/runbooks |
| Dependencies          | Repository vulnerability gate (for example audit tools); route deeper concerns                           |

Choose by scope and risk, not a universal checklist. Documentation-only work
needs document checks, not runtime tests. Record commands, results, and limits.

## Intent-to-behavior assessment

Separate missing behavior, contradictions, unexplained additions, and evidence
gaps. Ask for scope decisions on unrelated additions; do not delete them.
Necessary helpers need no separate product requirement.

For each applicable criterion record: check/result, evidence reference, reviewed
scope/revision, and `passed`, `failed`, `not run`, or `no longer current`.
Code coverage is not acceptance coverage; requirement wording is not runtime proof.
Reassess only evidence affected by material intent or behavior revisions.

## Verdict

Return scope, checks, severity-ranked findings (source, impact, reproduction),
criterion evidence/gaps, residual risks, and next action:
`SHIP-READY`, `USE VERIFY FIX LOOP`, or `NEEDS ARCH/DESIGN REVIEW`.

Required failed/unrun checks block full verification. Name any policy-approved
exception and approver without marking the criterion passed. Production outcomes
needing observation remain follow-ups. Sanitize evidence; do not copy sensitive logs.
