# vstack migration records

This directory contains machine-readable migration records for `docs/` artifact path
changes across major vstack version boundaries.

Each file covers one major version transition and is named `v{M}_to_v{N}.yaml` where
`M` is the source major version and `N` is the target major version.

These files are read by `vstack migrate` to relocate agent-owned docs files when their
paths change between major versions.

## Usage

```
vstack migrate [--target <dir>] [--from <major>] [--to <major>] [--dry-run]
```

Run from the project root (or pass `--target`) after upgrading vstack to a new major
version. The command chains all necessary migration steps between the installed major
and the current package major.

| Flag             | Description                                                     |
| ---------------- | --------------------------------------------------------------- |
| `--target <dir>` | Project root to migrate (default: current directory)            |
| `--from <major>` | Source major version (default: read from `.vstack/vstack.json`) |
| `--to <major>`   | Target major version (default: current vstack package major)    |
| `--dry-run`      | Print moves without touching the filesystem                     |

`vstack migrate` only moves files that exist at the old path; absent files are silently
skipped. It reads `items.root` from `.vstack/config.yaml` (with `artifacts.root`
as a legacy fallback) and adjusts destination paths when the project uses a custom
docs root.

## Schema

```yaml
from_version: "3.x"        # semver range for the source version
to_version: "4.0"          # first minor of the target major
moves:
  - old: docs/path/old.md  # path relative to project root
    new: docs/path/new.md  # path relative to project root
    type: docs              # always "docs" for this directory
    notes: >               # optional: human-readable explanation
      Why this path changed and what to do with the old file after migration.
```
