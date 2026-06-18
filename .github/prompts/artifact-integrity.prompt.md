---
description: 'Check source templates against generated artifacts and identify drift or missing regeneration.'
name: artifact-integrity
argument-hint: '[artifact type, path, or full repo]'
agent: tester
tools:
  - read
  - search
---
Check source templates against generated artifacts and identify drift.

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
<!-- VSTACK-META: {"artifact_name":"artifact-integrity","artifact_type":"prompt","artifact_version":"20260513002","generator":"vstack","vstack_version":"3.5.2"} -->
