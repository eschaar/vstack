# Install and upgrade

Use this guide for operational install and upgrade scenarios.

## Fresh install (recommended)

Use `pipx` so the CLI stays isolated from project dependencies.

```bash
pipx install vstack
cd /path/to/your/project
vstack install
vstack validate
```

Equivalent explicit target form:

```bash
vstack install --target /path/to/your/project
```

For a dedicated step-by-step flow, see [Fresh install](fresh-install.md).

After a fresh repository install, vstack may seed starter stubs in `.vstack/templates/`.
Treat them as project-owned guidance files. Keep and adapt them as needed, but use `vstack init` for `.github/` regeneration.

## Adopt or overwrite existing files

When `.github/` already contains files, run a dry run first:

```bash
cd /path/to/your/project
vstack install --dry-run
```

Resolve preserved-file conflicts with one of these strategies:

```bash
# Overwrite one managed artifact
vstack install --force-name agent/engineer

# Take ownership without overwriting
vstack install --adopt-name agent/engineer

# Overwrite all managed artifacts
vstack install --force
```

Use selectors as `type/name` (for example `agent/engineer`, `skill/verify`).

## Patch or minor upgrade (same major)

For upgrades like `v3.1 -> v3.2`, docs paths stay stable.

```bash
pipx upgrade vstack
cd /path/to/your/project
vstack init
```

For a focused upgrade flow, see [Upgrade](upgrade.md).

`vstack init` is idempotent and safe in CI.

## Major upgrade

For upgrades like `v2 -> v3`, run docs migration before regeneration.

```bash
pipx upgrade vstack
cd /path/to/your/project
vstack migrate
vstack init
```

Preview migration without file changes:

```bash
vstack migrate --dry-run
```

For multi-major jumps, you can force a range:

```bash
vstack migrate --from 1 --to 3
vstack init
```

For incremental regeneration by artifact family, see [Partial upgrade](partial-upgrade.md).

## Manifest schema upgrade

If commands fail with a legacy schema message, upgrade the manifest first.

```bash
cd /path/to/your/project
vstack manifest upgrade
vstack init
```

Typical sequence after a major migration warning:

1. Run `vstack manifest upgrade`.
1. Re-run `vstack init`.
1. Confirm with `vstack manifest status`.

If you need a clean regeneration after migration or config edits, see [Reinitialize](reinitialize.md).

## Common mistakes

- Running from the wrong directory:
  - Symptom: artifacts are generated in an unexpected location.
  - Fix: run from repository root, or pass `--target` explicitly.
- Skipping `vstack init` after upgrade:
  - Symptom: old generated artifacts remain.
  - Fix: run `vstack init` after every CLI upgrade.
- Using `--force` too early:
  - Symptom: local manual edits are overwritten.
  - Fix: prefer `--dry-run`, then `--force-name` or `--adopt-name`.
- Ignoring legacy manifest warnings:
  - Symptom: install/status/verify commands fail.
  - Fix: run `vstack manifest upgrade` once, then retry.
- Trying to control installed output by editing package internals:
  - Symptom: changes do not persist, or commands are run in the wrong repository.
  - Fix: use repository controls instead: update exclusions in `.vstack/config.yaml` or adopt existing files with `--adopt-name`, then run `vstack init` and `vstack manifest verify`.

## Related docs

- [Fresh install](fresh-install.md)
- [Upgrade](upgrade.md)
- [Global install](global-install.md)
- [Uninstall](uninstall.md)
- [What `.vstack/templates` is for](../explanation/vstack-templates.md)
