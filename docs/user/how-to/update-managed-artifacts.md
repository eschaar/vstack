# Update managed artifacts

Use this guide when you want to refresh generated artifacts and control overwrite behavior.

## Update all managed artifacts

Run a full idempotent refresh from project config:

```bash
vstack init
```

## Update one or more artifact types

Use `--only` to refresh a subset:

```bash
vstack init --only hook
vstack init --only hook agent
```

## Remove obsolete tracked artifacts safely

Use prune mode to remove tracked artifacts that are no longer generated:

```bash
vstack init --prune
```

Run a preview first if needed:

```bash
vstack init --prune --dry-run
```

Without `--prune`, obsolete candidates are reported and preserved.

## Force overwrite managed artifacts

Force overwrite for selected type scope:

```bash
vstack init --only hook --force
```

Force overwrite for all managed artifacts:

```bash
vstack install --force
```

Force overwrite one named artifact:

```bash
vstack install --force-name hook/agent-call-audit
vstack install --force-name agent/engineer
```

Use selectors as `type/name`.

## Concrete examples

Refresh hooks and verify hook state:

```bash
vstack init --only hook
vstack manifest status --target . --only hook
vstack manifest verify --target . --only hook
```

Refresh agents and verify agent state:

```bash
vstack init --only agent
vstack manifest status --target . --only agent
vstack manifest verify --target . --only agent
```

## What happens after manual edits

- A normal `vstack init` preserves locally modified managed artifacts.
- `vstack manifest status --target .` shows those files as modified.
- `vstack manifest verify --target .` reports checksum mismatch.
- The file is overwritten only when you use an explicit force command.

## Safe recovery flow

1. Run `vstack manifest status --target .` to list modified managed files.
1. Run `vstack manifest verify --target .` to confirm checksum mismatches.
1. Decide scope:
   - one artifact: `vstack install --force-name <type>/<name>`
   - one type: `vstack init --only <type> --force`
   - all managed artifacts: `vstack install --force`
1. Re-run `vstack manifest status --target .`.
1. Re-run `vstack manifest verify --target .`.

## Related Docs

- [Artifact checks](../reference/artifact-checks.md)
- [CLI commands](../reference/cli-commands.md)
- [Reinitialize](reinitialize.md)
