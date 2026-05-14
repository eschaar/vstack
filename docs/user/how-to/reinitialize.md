# Reinitialize

Use this guide when you need to re-apply vstack generation from current project configuration.

Typical cases:

- after editing `.vstack/config.yaml`,
- after upgrading vstack,
- after resolving conflicts in managed `.github/` artifacts.

## Reinitialize the Project

```bash
vstack init
```

With explicit target:

```bash
vstack init --target /path/to/repo
```

## Reinitialize Specific Artifact Types

Use `--only` when you want a narrower regeneration scope:

```bash
vstack init --only agent
vstack init --only skill prompt
vstack init --only hook
```

## Verify the Reinitialized State

```bash
vstack manifest status --target .
vstack manifest verify --target .
```

## Troubleshooting

- If a file is locally modified and not updated as expected, inspect `manifest status` output.
- If you need explicit overwrite semantics, use install flags such as `--force-name` or `--force`.

## Related Docs

- [Upgrade](upgrade.md)
- [Partial upgrade](partial-upgrade.md)
- [Install and upgrade](install-and-upgrade.md)
- [Artifact checks](../reference/artifact-checks.md)
