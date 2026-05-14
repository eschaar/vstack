# Upgrade with checks

This tutorial shows a safe upgrade flow with explicit checkpoints for both same-major and major upgrades.

## Goal

By the end, you can upgrade vstack and confirm generated artifacts are healthy.

## Prerequisites

1. `vstack` is already installed in your repository.
1. You can run commands from repository root.

All commands below assume you are in repository root, so `--target` is omitted.

## Path A: patch or minor upgrade

Use this path for upgrades like `v3.1 -> v3.2`.

1. Upgrade the CLI:

```bash
pipx upgrade vstack
vstack --version
```

1. Re-generate artifacts:

```bash
vstack init
```

1. Verify results:

```bash
vstack validate
vstack manifest status
vstack manifest verify
```

## Path B: major upgrade

Use this path for upgrades like `v2 -> v3`.

1. Upgrade the CLI:

```bash
pipx upgrade vstack
vstack --version
```

1. Run migration, then regeneration:

```bash
vstack migrate
vstack init
```

1. Verify results:

```bash
vstack validate
vstack manifest status
vstack manifest verify
```

## Optional migration checks

Preview migration before writing files:

```bash
vstack migrate --dry-run
```

For multi-major jumps, run an explicit range:

```bash
vstack migrate --from 1 --to 3
vstack init
```

If you see a legacy manifest warning:

```bash
vstack manifest upgrade
vstack init
vstack manifest status
```

## Expected checkpoints

- `vstack validate` passes.
- `vstack manifest status` reports expected managed state.
- `vstack manifest verify` confirms checksum integrity.

## Next steps

1. Use [Upgrade](../how-to/upgrade.md) for a compact operational version.
1. Use [Reinitialize](../how-to/reinitialize.md) when you need targeted regeneration.
1. Use [Artifact checks](../reference/artifact-checks.md) for drift triage.
