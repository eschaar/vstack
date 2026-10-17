---
name: artifact-integrity
description: 'Check source templates against generated artifacts and identify drift or missing regeneration.'
allowed-tools: 'read search'
argument-hint: '[artifact type, path, or full repo]'
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

# artifact-integrity - Generated Artifact Audit

Check source templates against generated artifacts and identify drift.
Report only; do not regenerate, edit, or delete files.

Compare `src/vstack/_templates/` sources with installed artifacts in `.github/`
and the manifest at `.vstack/vstack.json`. Surface mismatches, stale output, or gaps.

Output exactly in this format:

## Drift Findings

List all source-to-artifact mismatches.

For each item:

- source template: path under `src/vstack/_templates/`
- generated artifact: expected path under `.github/`
- drift type: MISSING | STALE | CHECKSUM-MISMATCH | UNTRACKED
- detail: one sentence describing the discrepancy

## Regeneration Actions

List exact commands needed to bring generated artifacts back into sync.

For each action:

- command: the shell command to run (e.g. `python3 -m vstack install`)
- scope: which artifact types or names this command covers
- priority: CRITICAL | HIGH | LOW

## Risk If Unfixed

Describe production risk if drift is left unresolved.

For each drift item from above:

- artifact affected
- risk: what could fail or mislead if the stale artifact ships

## Verification Steps

Provide a checklist to confirm the repository is clean after regeneration.

- [ ] `python3 -m vstack install` completes without errors
- [ ] `vstack validate` reports no unresolved template tokens
- [ ] `make test-local` passes with 100% coverage
- [ ] `make markdown-format` reports no changes
- [ ] All regenerated files match their source checksums in `.vstack/vstack.json`

<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->
<!-- VSTACK-META: {"artifact_name":"artifact-integrity","artifact_type":"skill","artifact_version":"20261017001","generator":"vstack","vstack_version":"3.7.4"} -->
