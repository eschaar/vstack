# Troubleshooting

Use this guide when install or day-to-day usage does not behave as expected.

## Install and environment

### `vstack` command not found

Cause: `pipx` binary path is not on `PATH`.

Checks:

```bash
pipx --version
pipx ensurepath
```

Then restart your shell and verify:

```bash
vstack --version
```

### Validation fails right after install

Run from repository root:

```bash
cd /path/to/your/project
vstack install
vstack validate
```

If manifest-related errors mention a legacy schema:

```bash
vstack manifest upgrade
vstack init
```

### Install appears to skip files

vstack defaults to conservative behavior and preserves unmanaged files.

```bash
vstack install --dry-run
```

Then resolve preserved entries with `--adopt-name`, `--force-name`, or `--force`.

## Copilot visibility and behavior

### Agents are not visible in Copilot Chat

1. Confirm artifacts exist in `.github/` for your repository.
1. Run VS Code command `Developer: Reload Window`.
1. Re-open Copilot Chat and pick an agent.

### Results look generic

Cause: no explicit role context.

Fix: choose a role in the agent picker first (for example `planner` or `tester`), then run your prompt or skill.

## CI parity and local parity

### CI behavior differs from local generation

Most common cause: local changes were not regenerated with current templates.

Local parity checklist:

1. Run `vstack init` in the repository root.
1. Run `vstack validate`.
1. Run `vstack manifest status --target .`.
1. Commit generated `.github/` changes when expected.

For upgrades, ensure CI and local both use the same installed CLI major version.

## Search noise in large repositories

When searching generated artifacts or docs, results can be noisy.

Practical approaches:

- Narrow search scope to source directories first (for example `src/`, `tests/`).
- Exclude generated or dependency folders in search UI:
  - `.github/` (when not reviewing generated output)
  - `.venv/`, `node_modules/`, `dist/`, `build/`
- Use `vstack manifest status` to inspect managed artifact drift instead of raw text search.

## Useful diagnostics commands

```bash
vstack --version
vstack validate
vstack manifest status --target .
vstack manifest verify --target .
```

If the issue persists, open a discussion with command output and repository context:

- <https://github.com/eschaar/vstack/discussions>
