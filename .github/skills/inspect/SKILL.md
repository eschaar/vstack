---
name: inspect
description: 'Read-only verification audit against agreed behavior, including missing work and evidence gaps. Use for "inspect", "assess", or "check without fixing". Report findings without code edits, commits, or mandatory duplicate reports.'
license: 'MIT'
compatibility: 'Requires a skills-compatible agent with repository file access and terminal command execution when needed.'
metadata:
  owner: vstack
  maturity: stable
allowed-tools: 'execute read search'
argument-hint: '[component or service to inspect]'
user-invocable: true
disable-model-invocation: false
---
## Skill Context

This skill is part of **vstack** — a VS Code-native AI engineering workflow system.

### AskUserQuestion Format

When you need clarification, use this exact format — never invent or guess:

> **Question:** [The specific question]
> **Options:** A) … | B) … | C) …
> **Default if no response:** [What you'll do]

Never ask more than one question at a time without waiting for the answer.

### Diagram Convention

When producing hand-authored Markdown outputs, prefer Mermaid for flow,
interaction, lifecycle, state, topology, dependency, and decision diagrams when
the format is supported and improves clarity. Use ASCII as a fallback when
Mermaid is unsupported or would be less readable. Keep ASCII/text trees for
directory structures and other scan-friendly hierarchies.

```bash
# Detect base branch (main / master / develop / trunk)
BASE=$(gh pr view --json baseRefName -q .baseRefName 2>/dev/null) \
  || BASE=$(git remote show origin 2>/dev/null | grep 'HEAD branch' | awk '{print $NF}') \
  || BASE=$(git branch -r 2>/dev/null | grep -E '/(main|master|develop|trunk)' | head -1 | sed 's|.*origin/||') \
  || BASE="main"
echo "Base branch: $BASE"
```

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

<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->
<!-- VSTACK-META: {"artifact_name":"inspect","artifact_type":"skill","artifact_version":"20261026001","generator":"vstack","vstack_version":"4.0.0"} -->
