# Retire Prompts in Favor of Skills

## Metadata

```yaml
status: IMPLEMENTED
type: migration
reference: user-request-20261017
last_modified: 2026-10-17
```

## Goal and Context

Retire the prompt artifact family because the Copilot harness does not load
prompt files. Preserve reusable workflows as skills without maintaining duplicate
procedures. This is a breaking change intended for the next major release.

## AS-IS

vstack generates 17 built-in prompts alongside skills, agents, instructions, and
hooks. `init --prune` can remove obsolete artifacts only for selected, registered
families. Removing the prompt generator alone would leave installed prompts and
their manifest entries behind.

## TO-BE

- Remove the prompt generator, schema, CLI type, and source templates.
- Reuse existing skills for overlapping workflows.
- Convert unique workflows to manually invoked skills.
- During `install` and `init` with skills selected, remove unchanged legacy prompts
  only after their replacement skills are successfully available with no unresolved
  template placeholders.
- Preserve unmanaged, modified, checksum-less, unsafe-path, and unknown prompts.
  Report why migration was deferred and retain manifest tracking for retry.
- Keep legacy manifest parsing, dry-run behavior, and scoped installs intact.
- Do not change agent handoff prompt strings or release/tag automation.

## Impact (High Level)

- Architecture: four active artifact families; legacy prompt data is migration-only.
- API/data/model: remove `prompt` selectors and public prompt generator imports.
- Security/privacy: require manifest ownership, checksums, canonical paths, and
  non-symlink destinations before deleting a legacy file.
- Operations: upgrade with `vstack install` or `vstack init`; repeated runs are
  idempotent. Custom prompt workflows require manual conversion.
- Option B: roles and handoffs remain unchanged; reusable procedures use skills.

## Acceptance Criteria

1. Fresh installs produce no prompt files and expose no prompt artifact type.
1. Each retired built-in has a documented replacement skill.
1. Unique workflows retain their instructions and explicit invocation behavior.
1. Upgrades install replacements before removing safe legacy prompts.
1. Unsafe or modified files remain untouched, tracked, and explicitly reported.
1. Dry runs and non-skill installs do not remove prompts.
1. Tests cover fresh installs, upgrades, collisions, exclusions, and repeat runs.

## Test Scenarios

- Upgrade an old manifest containing all built-in prompts.
- Preserve a modified, untracked, checksum-less, unknown, or symlinked prompt.
- Preserve prompts when replacement skills are excluded or collide with local files.
- Reject unsafe manifest paths without accessing files outside the install root.
- Retry a partially completed migration and clear entries for already missing files.
- Confirm dry-run leaves files and manifest bytes unchanged.
- Preserve prompts when a replacement partial is missing, including install,
  update, unchanged, and dry-run paths; retry retirement after repairing the partial.
- Confirm CLI rejection of removed selectors and valid output for all four families.
- Run lint, type checking, tests with 100% coverage, and source validation.

## Verification

- Full suite: 698 tests passed with 100% coverage on Python 3.14.
- Ruff lint, Python formatting, and mypy passed.
- Shipped templates validate; installed artifact checksums and metadata verify.
- Repository migration removed all 17 tracked prompts and installed six explicit-only skills.
- A repeat update dry-run reports no installations, updates, or preserved conflicts.
- Changed Markdown passes mdformat with the repository's GFM plugin; local links resolve.
- The pre-commit wrapper could not initialize its remote hook environments because
  GitHub SSH authentication is unavailable. Markdownlint was not run. The full
  Ruff formatting command also reports an unrelated pre-existing formatting issue
  in the `refactor` skill's Python examples; those examples were left unchanged.
