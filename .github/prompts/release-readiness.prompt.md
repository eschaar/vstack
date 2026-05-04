---
description: 'Evaluate release readiness from reports, risks, and unresolved blockers.'
name: release-readiness
argument-hint: '[scope, release date, or branch]'
agent: release
model: GPT-5.3-Codex (copilot)
tools:
  - read
  - search
---
Assess whether this change set is ready to release.

Review product, architecture, design, test, security, and performance evidence.
Prefer evidence-based findings tied to concrete artifacts.

Output exactly in this format:

## Release Gate Verdict

- Verdict: READY | READY-WITH-CONDITIONS | NOT-READY
- Confidence: high | medium | low
- Scope assessed: one sentence

## Blocking Issues

List only release-blocking items.

For each item:

- artifact or file reference
- why this blocks release in one sentence
- concrete unblock action
- owner role (product | architect | designer | engineer | tester | release)

## Conditions Before Release

List non-blocking but mandatory follow-ups to ship safely.

## Evidence Reviewed

List the exact artifacts checked (reports, docs, CI evidence, manifests).
For each expected artifact that is missing, flag it explicitly as: MISSING — [artifact name].

## Recommended Next Action

One clear next step for the team.

<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->
<!-- VSTACK-META: {"artifact_name":"release-readiness","artifact_type":"prompt","artifact_version":"20260502012","generator":"vstack","vstack_version":"2.2.0"} -->
