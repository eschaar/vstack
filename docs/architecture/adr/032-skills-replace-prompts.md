# ADR-032: Skills Replace Prompt Artifacts

**Date:** 2026-10-17
**Status:** accepted

## Context

The VS Code Copilot harness uses skills for reusable workflows and does not load
`*.prompt.md` files. The Local harness still supports them, but vstack should
provide one portable workflow surface rather than duplicate skills and prompts.
Existing installations contain tracked prompts that must not be orphaned.

## Decision

Remove the prompt artifact family in the next major release. Reuse existing
skills where workflows overlap and convert unique prompts to skills with
`disable-model-invocation: true`.

Distribute only workflows useful to consumer projects. Keep the source-specific
`artifact-integrity` audit as a hand-authored repository-only skill under
`.github/skills/`, without a package template, generation footer, or manifest
ownership. Its old prompt maps to the distributed `inspect` skill.

Keep legacy manifest data readable solely for migration. `install` and `init`
automatically retire known prompts when skills are selected, replacement skills
are successfully available, and the old files match their stored checksums.
Preserve and report unmanaged, modified, unknown, or unsafe files.

## Alternatives Considered

- Keep prompts unchanged: compatible with Local sessions but unavailable to the
  Copilot harness. Rejected.
- Generate both prompts and skills: retains compatibility but duplicates command
  discovery and maintenance. Rejected.
- Retire prompts with safe migration: one workflow surface with an explicit
  breaking-change boundary. Selected.
- Distribute repository maintenance skills or add a local-template generator:
  unnecessary consumer coupling and configuration. Rejected in favor of native,
  hand-authored repository skills.

## Rationale

Roles belong to agents and reusable procedures belong to skills. A separate prompt
generator no longer provides sufficient value. Reusing manifest checksums and the
existing conservative install policy prevents loss of local work. Missing or
conflicting replacement skills defer cleanup instead of removing usable workflows.

## Consequences

Prompt selectors, public generator imports, and some old command names disappear.
Users with custom prompt templates must convert those themselves. The migration
guide records replacement commands. Existing skills keep their invocation policy;
converted skills remain opt-in and do not reproduce prompt-specific agent,
model, or tool selection.

For the Option B pipeline, role boundaries and handoff prompt strings remain
unchanged. Stages invoke skills rather than prompt artifacts.
Repository-only maintenance skills are not dependencies of consumer pipeline stages.

## Related ADRs

- [ADR-005](005-vscode-prompt-format.md): superseded prompt-generation direction.
- [ADR-012](012-flat-templates-install-time-generation.md): retains source-first,
  install-time generation for the remaining families.
- [ADR-015](015-conservative-install-by-default.md): preserves local modifications.
- [ADR-020](020-install-init-command-semantics.md): both commands share migration.
