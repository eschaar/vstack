{{SKILL_CONTEXT}}

{{BASE_BRANCH}}

# verify - Fix Loop Verification

Check agreed behavior, fix authorized gaps, and rerun affected checks. Use
`inspect` for report-only work, `architecture` for decisions, `security` for deep
audits, and `performance` for profiling. Do not add features outside agreed scope.

## 1. Select mode and scope

Use the requested mode, otherwise `standard`:

| Mode        | Depth and fix policy                                                                       |
| ----------- | ------------------------------------------------------------------------------------------ |
| quick       | Focused critical/high regressions; broaden if acceptance needs it                          |
| standard    | Relevant baseline, integration, contract, and reliability checks; fix critical/high/medium |
| exhaustive  | Standard plus relevant smoke, dependency, and operational checks; all severities           |
| report-only | Route to `inspect`; no fixes                                                               |

Read intent, criteria, relevant contracts, project policy, and working-tree
changes. Establish reviewed commit or working-tree scope. Preserve unrelated
edits; ask before conflicting changes. Commit only when authorized.
Small low-risk tasks may use an existing issue/conversation; no mandatory document.

Readiness requires understood scope, observable acceptance, resolved blockers,
and policy approval. Safety gates apply regardless of mode or task size.

## 2. Check behavior

Compare actual in-scope behavior with acceptance, including required behavior
absent from the diff. Discover existing repository commands and run the smallest
checks covering changed behavior and regressions. Broaden only as needed.

| Surface          | Checks when applicable                                                                        |
| ---------------- | --------------------------------------------------------------------------------------------- |
| Baseline         | Lint, types, build/package, unit tests                                                        |
| Boundaries       | Integration, OpenAPI/JSON Schema/Protobuf, API compatibility                                  |
| Reliability/data | Smoke, migrations/rollback, retries/backoff, timeouts, circuit breakers, concurrency          |
| Operations       | Failure/transition logs, latency/error/saturation metrics, trace propagation, alerts/runbooks |
| Dependencies     | Existing vulnerability gate; route deeper security/performance concerns                       |

Use measurable operational evidence when relevant, not runtime tests for prose.
Preserve failures and missing-tool details; never suppress errors or substitute
an available check for a different required one.

## 3. Triage and fix

Separate behavioral gaps, contradictions, unexplained additions, and unavailable
evidence. Severity: critical (build/data/security failure), high (broken contract
or required check), medium (other behavior/flakiness), low (minor cleanup).

Within the mode's fix policy:

1. Reproduce and confirm root cause.
1. Apply the smallest authorized fix; preserve acceptance and role ownership.
1. Rerun affected checks, then broader checks if needed.
1. Update useful existing tasks, not an append-only remediation history.

Unexplained additions require a scope decision, not automatic deletion; necessary
helpers need no separate requirement. Escalate changed intent/contracts to their
owner. After material revisions, preserve criterion references and reassess only
affected tasks/evidence. Renew approval only for scope, risk, or policy changes.

Stop and report blockers when required evidence cannot be obtained, scope/policy
decisions are needed, or attempts repeat without new evidence. Honor existing
iteration budgets; do not loop indefinitely or weaken criteria to claim success.

## 4. Record evidence and verdict

Use `docs/reports/test-report.md` (and scoped security/performance reports) when
policy or cross-change reporting requires it. Otherwise keep evidence in the
existing changedoc or response; no duplicate reports.

Report mode/scope, checks/results, fixes, deferred findings with owners, and
residual risks. Map applicable criteria to check/result, evidence reference,
reviewed scope/revision, and `passed`, `failed`, `not run`, or `no longer current`.
Code coverage and task checkboxes are not acceptance evidence.

Verdict: `READY TO SHIP`, `NEEDS FIXES`, or `BLOCKED`. Required failed/unrun checks
prevent full verification; name policy-approved exceptions and approvers without
reporting a pass. Production outcomes needing observation remain follow-ups.
Sanitize evidence references; do not persist secrets or sensitive logs.
