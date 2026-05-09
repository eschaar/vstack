# vstack migration records

This directory contains machine-readable migration records for `docs/` artifact path
changes across major vstack version boundaries.

Each file covers one major version transition and is named `v{M}_to_v{N}.yaml` where
`M` is the source major version and `N` is the target major version.

These files are read by `vstack migrate` (not yet implemented — see ADR-026) to relocate
agent-owned docs files when their paths change between major versions.

Until `vstack migrate` ships, use the moves listed here as the canonical reference for
manual migration steps. `CHANGELOG.md` for each major release must include a "Migration"
section that restates these moves in prose.

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
