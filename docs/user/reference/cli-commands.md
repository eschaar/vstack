# CLI commands

This page is the command reference for `vstack`.

## Essential commands

Use these for daily operation:

```bash
vstack --version
vstack validate
vstack install
vstack init
vstack migrate
vstack manifest status --target .
vstack manifest verify --target .
vstack manifest upgrade --target .
```

## Full command reference

| Command                                   | Description                                                                                                                   |
| ----------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `vstack --version`                        | Show vstack version.                                                                                                          |
| `vstack validate`                         | Validate source templates and configuration constraints.                                                                      |
| `vstack verify`                           | Verify source templates and installed output, including checksum drift.                                                       |
| `vstack install`                          | First-run setup in the current directory target. Seeds `.vstack/config.yaml` if missing, then generates `.github/` artifacts. |
| `vstack install --target DIR`             | Same as `install`, but explicit target path.                                                                                  |
| `vstack install --global`                 | Install artifacts into the VS Code user profile scope.                                                                        |
| `vstack install --dry-run`                | Preview install actions without writing files.                                                                                |
| `vstack install --force`                  | Overwrite all managed artifacts in target scope.                                                                              |
| `vstack install --force-name TYPE/NAME`   | Overwrite one managed artifact selector.                                                                                      |
| `vstack install --adopt-name TYPE/NAME`   | Track an existing unmanaged artifact without overwriting it.                                                                  |
| `vstack init`                             | Idempotent regeneration in current directory based on `.vstack/config.yaml`.                                                  |
| `vstack init --target DIR`                | Same as `init`, but explicit target path.                                                                                     |
| `vstack init --prune`                     | Remove safe obsolete tracked artifacts that are no longer generated; default mode only reports and preserves candidates.      |
| `vstack uninstall`                        | Remove tracked artifacts from current directory target when checksums still match manifest.                                   |
| `vstack uninstall --target DIR`           | Same as `uninstall`, but explicit target path.                                                                                |
| `vstack uninstall --global`               | Uninstall profile-scoped artifacts.                                                                                           |
| `vstack uninstall --force`                | Remove tracked artifacts even when locally modified.                                                                          |
| `vstack uninstall --force-name TYPE/NAME` | Force removal for one managed artifact selector.                                                                              |
| `vstack status --target DIR`              | Alias-style status report for installed artifact drift and ownership.                                                         |
| `vstack manifest status --target DIR`     | Manifest-scoped status report for managed, modified, missing, and conflicting files.                                          |
| `vstack manifest verify --target DIR`     | Manifest-scoped verification for installed output and checksums.                                                              |
| `vstack manifest upgrade --target DIR`    | Upgrade legacy `.vstack/vstack.json` schema to current format.                                                                |
| `vstack migrate --target DIR`             | Move docs files to newer paths for major upgrades.                                                                            |
| `vstack migrate --dry-run`                | Preview migration actions only.                                                                                               |
| `vstack migrate --from M --to N`          | Run a specific major-version migration range.                                                                                 |

## Install vs init

| Command          | Primary use                                            | Behavior                                                         |
| ---------------- | ------------------------------------------------------ | ---------------------------------------------------------------- |
| `vstack install` | First setup or onboarding a machine                    | Seeds `.vstack/config.yaml` if missing, then runs generation.    |
| `vstack init`    | Repeatable regeneration after upgrades or config edits | Re-applies generation idempotently from existing project config. |

Both commands default to current working directory when `--target` is omitted.

`vstack init --prune` applies only to obsolete tracked artifacts where the current file content still matches the manifest checksum. Locally modified or untracked files are never removed by this flag.

For manual-edit preservation and force-overwrite flows, see [Update managed artifacts](../how-to/update-managed-artifacts.md).
