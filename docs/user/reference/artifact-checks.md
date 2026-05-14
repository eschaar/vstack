# Artifact Checks

This page explains how vstack checks generated artifacts and how to read check results.

## Why Checks Exist

Artifact checks protect against drift between:

- generated files in `.github/`,
- manifest ownership in `.vstack/vstack.json`,
- current template output.

## Core Commands

```bash
vstack validate
vstack manifest status --target .
vstack manifest verify --target .
```

What each command does:

- `validate`: checks template/config validity before install output concerns.
- `manifest status`: reports managed, modified, missing, and related ownership states.
- `manifest verify`: verifies installed output and checksum alignment with manifest entries.

## Checksum and Ownership Basics

vstack records checksums for managed artifacts in `.vstack/vstack.json`.

During verification, vstack compares current file content to recorded checksum:

- match: file is managed and unchanged,
- mismatch: file is modified relative to manifest,
- missing file: manifest entry exists but output file does not.

## Managed State and Update Behavior

Unchanged managed files:

- Full regeneration updates them during `vstack init`.
- Type-scoped regeneration updates them during `vstack init --only <type>`.

Modified managed files:

- Normal `vstack init` preserves local manual edits.
- Normal `vstack init --only <type>` also preserves manual edits in scope.
- Overwrite requires explicit force (`vstack init --only <type> --force`, `vstack install --force`, or `vstack install --force-name <type>/<name>`).

Verification outcomes:

- Unchanged managed files verify cleanly.
- Modified managed files appear as modified in status and fail checksum verification.
- After explicit force overwrite, files return to managed and unchanged state.

## Typical Failure Cases

- Manual edits to managed `.github/` artifacts.
- Running commands in the wrong target directory.
- Upgraded CLI without running `vstack init`.
- Legacy manifest schema not upgraded yet.

## Recommended Recovery Flow

1. Run `vstack manifest status --target .`.
1. Inspect modified or missing entries.
1. Re-run `vstack init` (or `vstack init --only <type>`) for non-modified files.
1. For modified managed files, use explicit force overwrite:
   - `vstack install --force-name <type>/<name>`
   - `vstack init --only <type> --force`
   - `vstack install --force`
1. Re-run `vstack manifest verify --target .`.

If schema upgrade is required:

```bash
vstack manifest upgrade
vstack init
```

## Related Docs

- [CLI commands](cli-commands.md)
- [Update managed artifacts](../how-to/update-managed-artifacts.md)
- [Install and upgrade](../how-to/install-and-upgrade.md)
- [Partial upgrade](../how-to/partial-upgrade.md)
- [Reinitialize](../how-to/reinitialize.md)
