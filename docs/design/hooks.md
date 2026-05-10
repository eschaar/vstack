# vstack - hooks design

> Maintained by: **designer** role\
> Last updated: 2026-05-10

## overview

This document defines the repository-level hooks artifact family in vstack.
It complements:

- `docs/design/overview.md` (global design baseline)
- `docs/design/workflow.md` (workflow progression model)
- `docs/architecture/adr/027-repository-hooks-artifact-type.md` (decision record)

Repository hooks are generated JSON artifacts installed at:

- `.github/hooks/<name>.json`

They are managed by the same install/verify/status/uninstall manifest model used by
other artifact families.

______________________________________________________________________

## 1. artifact model

### 1.1 source and output mapping

| Element          | Path pattern                                     |
| ---------------- | ------------------------------------------------ |
| source config    | `src/vstack/_templates/hooks/<name>/config.yaml` |
| source body      | `src/vstack/_templates/hooks/<name>/hook.json`   |
| installed output | `.github/hooks/<name>.json`                      |
| manifest key     | `hooks`                                          |
| singular type    | `hook`                                           |

### 1.2 type behavior

Hook artifacts use JSON payloads, so they differ from markdown artifact families:

| Property            | Value       |
| ------------------- | ----------- |
| `add_frontmatter`   | `false`     |
| `auto_gen_footer`   | `false`     |
| `artifact_is_dir`   | `false`     |
| `template_filename` | `hook.json` |

Implication: manifest verification must use checksum ownership and skip markdown-footer metadata checks.

______________________________________________________________________

## 2. baseline hook set

vstack ships four default repository hooks:

| Hook name                   | Primary events                | Intent                                          |
| --------------------------- | ----------------------------- | ----------------------------------------------- |
| `session-audit`             | `sessionStart`, `sessionEnd`  | Session boundary visibility                     |
| `pre-tool-safety-gate`      | `preToolUse`, `errorOccurred` | Safety signaling around risky operations        |
| `post-edit-format`          | `postToolUse`                 | Formatting reminder after edit-heavy operations |
| `post-commit-security-scan` | `postToolUse`, `sessionEnd`   | Security hygiene reminder around git mutations  |

These are conservative defaults and should remain safe to install in any repository.

______________________________________________________________________

## 3. CLI contracts

### 3.1 selection and exclusion

- `--only hook` is supported in all type-aware commands.
- `.vstack/config.yaml` supports `exclude.hook` and per-name exclusions under `hook`.

### 3.2 command behavior

- `install` / `init`: generate and track `.github/hooks/*.json`
- `status`: show managed/modified/missing state for hook files
- `verify`:
  - source checks: required hook names and source template presence
  - output checks: installed file presence + checksum ownership/drift
  - metadata checks: skipped for hook artifacts
- `uninstall`: remove tracked hook outputs according to checksum protection rules

______________________________________________________________________

## 4. migration and compatibility

Migration is additive.

For existing repositories:

1. run `vstack install` (or `vstack init` in CI),
1. review generated `.github/hooks/*.json`,
1. optionally disable specific defaults using `.vstack/config.yaml` `exclude.hook`.

Per-agent frontmatter field `hooks` remains supported and is intentionally separate
from repository-level hooks artifacts.

______________________________________________________________________

## 5. extension guidance

When adding new built-in hooks:

1. add template directory under `src/vstack/_templates/hooks/<name>/`
1. include `config.yaml` and `hook.json`
1. add name to expected canonical hook list in CLI constants
1. regenerate artifacts via `python -m vstack install`
1. update this design doc and roadmap status if behavior changes
