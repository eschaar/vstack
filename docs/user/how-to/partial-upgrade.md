# Partial Upgrade

Use this guide when you want to upgrade only selected artifact families instead of regenerating everything.

## When to Use Partial Upgrade

Common scenarios:

- you only changed one artifact family in templates,
- you want lower-risk incremental rollout,
- you want faster local verification during migration.

## Upgrade Selected Artifact Types

```bash
pipx upgrade vstack
vstack init --only agent
```

Multiple types:

```bash
vstack init --only skill prompt instruction
```

Hooks only:

```bash
vstack init --only hook
```

## Verify Selected Types

```bash
vstack manifest status --target . --only agent
vstack manifest verify --target . --only agent
```

## Recommended Rollout Pattern

1. Upgrade one type with `vstack init --only <type>`.
1. Run `manifest status` and `manifest verify` for the same type.
1. Repeat for the next type.
1. Finish with a full verification pass.

## Risks and Limits

- Partial upgrade can leave other artifact types on older generated output.
- For broad CLI upgrades, a full `vstack init` is still the safest final step.

## Related Docs

- [Upgrade](upgrade.md)
- [Reinitialize](reinitialize.md)
- [CLI commands](../reference/cli-commands.md)
