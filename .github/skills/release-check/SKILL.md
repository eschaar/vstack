---
name: release-check
description: 'Evaluate release gate readiness using required reports, artifacts, and sign-off evidence.'
allowed-tools: 'read search'
argument-hint: '[release scope or target branch]'
user-invocable: true
disable-model-invocation: true
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

# release-check - Release Evidence Audit

Evaluate release gate readiness using required reports, artifacts, and sign-off evidence.
Report only; do not create a release, tag, pull request, or sign-off.

Use repository evidence only.

Output exactly in this format:

## Release Gate Status

- overall status: READY | NOT-READY
- scope reviewed
- evidence sources checked

## Missing or Stale Evidence

For each item:

- artifact
- issue: MISSING | STALE | INCOMPLETE
- impact
- owner role

## Sign-off Gaps

For each required role:

- role
- verdict: OK | NOK | NOT-RECORDED
- blocking reason

## Release Actions

Ordered actions to reach READY.

- action
- owner role
- verification step

<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->
<!-- VSTACK-META: {"artifact_name":"release-check","artifact_type":"skill","artifact_version":"20261017001","generator":"vstack","vstack_version":"3.7.8"} -->
