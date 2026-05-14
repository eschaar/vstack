# Fresh Install

Use this guide when installing vstack in a repository that does not have a previous vstack setup.

## Before You Start

- Install the CLI with `pipx` (recommended).
- Open your repository root in VS Code.
- Confirm the repository does not already contain `.vstack/vstack.json`.

## Install vstack

```bash
pipx install vstack
vstack --version
```

## Initialize the Repository

Run install from the repository root:

```bash
vstack install
```

What this does:

- creates `.vstack/` when missing,
- seeds project config when needed,
- seeds starter files under `.vstack/templates/` when available,
- generates managed artifacts under `.github/`.

About `.vstack/templates/`:

- These files are project-owned stubs and are safe to customize.
- New files can be added by future versions, but existing files are not overwritten.
- They are not the source for `.github/` regeneration.

## Validate the Result

Run the standard checks:

```bash
vstack validate
vstack manifest status --target .
vstack manifest verify --target .
```

Expected outcome:

- `validate` passes template/config checks,
- `manifest status` reports managed artifact state,
- `manifest verify` confirms checksum ownership and output consistency.

## Resolve Existing File Conflicts

If your repository already has overlapping `.github/` files, preview first:

```bash
vstack install --dry-run
```

Then choose one strategy:

```bash
# Overwrite one managed artifact
vstack install --force-name agent/engineer

# Adopt one existing artifact without overwrite
vstack install --adopt-name agent/engineer

# Overwrite all managed artifacts
vstack install --force
```

## Related Docs

- [Install and upgrade](install-and-upgrade.md)
- [CLI commands](../reference/cli-commands.md)
- [Configuration](../reference/configuration.md)
- [Artifact checks](../reference/artifact-checks.md)
- [What `.vstack/templates` is for](../explanation/vstack-templates.md)
