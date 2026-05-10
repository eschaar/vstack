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

| Element          | Path pattern                                   |
| ---------------- | ---------------------------------------------- |
| source template  | `src/vstack/_templates/hooks/<name>/hook.yaml` |
| installed output | `.github/hooks/<name>.json`                    |
| manifest key     | `hooks`                                        |
| singular type    | `hook`                                         |

### 1.2 type behavior

Hook artifacts render from YAML source templates into JSON payloads, so they differ from markdown artifact families:

| Property            | Value       |
| ------------------- | ----------- |
| `add_frontmatter`   | `false`     |
| `auto_gen_footer`   | `false`     |
| `artifact_is_dir`   | `false`     |
| `template_filename` | `hook.yaml` |

Implication: manifest verification must use checksum ownership and skip markdown-footer metadata checks.

Hook templates follow the GitHub Copilot hooks envelope:

```json
{
  "version": 1,
  "hooks": {
    "preToolUse": [
      {
        "type": "command",
        "bash": "...",
        "powershell": "..."
      }
    ]
  }
}
```

______________________________________________________________________

## 2. baseline hook set

vstack ships five default repository hooks:

| Hook name                    | Primary events                                      | Intent                                                      |
| ---------------------------- | --------------------------------------------------- | ----------------------------------------------------------- |
| `session-audit`              | `userPromptSubmitted`, `sessionStart`, `sessionEnd` | Structured JSONL session and prompt audit trail             |
| `pre-tool-safety-gate`       | `preToolUse`, `errorOccurred`                       | Deny destructive shell patterns + error logging             |
| `post-edit-format`           | `postToolUse`                                       | Edit-event logging + optional `make format` run             |
| `post-edit-markdown-quality` | `postToolUse`                                       | vstack markdown/work-item formatting for docs and templates |
| `post-commit-security-scan`  | `postToolUse`, `sessionEnd`                         | Git-mutation checks + optional `gitleaks` run               |

These defaults are safe in audit mode and can be upgraded to enforcement behavior.
For vstack specifically, the markdown-quality hook gives the baseline hook set a direct payoff on ADRs,
design docs, prompts, instructions, and other generated work items.

______________________________________________________________________

## 3. CLI contracts

### 3.1 selection, exclusion, and runtime defaults

- `--only hook` is supported in all type-aware commands.
- `.vstack/config.yaml` supports `exclude.hook` and per-name exclusions under `hook`.
- `.vstack/config.yaml` also supports a `hooks:` block for project-level defaults:

```yaml
hooks:
  enabled: true
  mode: audit
  hooks:
    pre-tool-safety-gate:
      mode: enforce
    post-edit-markdown-quality:
      enabled: false
```

- `hooks.enabled: false` disables the generated baseline hook family.
- `hooks.mode` sets the generated default fallback for `VSTACK_HOOKS_MODE`.
- `hooks.hooks.<name>.enabled: false` disables one named built-in hook.
- `hooks.hooks.<name>.mode` overrides the default mode for one named hook.

### 3.2 command behavior

- `install` / `init`: generate and track `.github/hooks/*.json`
- `status`: show managed/modified/missing state for hook files
- `verify`:
  - source checks: required hook names and source template presence
  - output checks: installed file presence + checksum ownership/drift
  - metadata checks: skipped for hook artifacts
- `uninstall`: remove tracked hook outputs according to checksum protection rules

______________________________________________________________________

## 4. source format and compatibility

Source of truth for built-in hooks is a single `hook.yaml` file per hook directory.
The generator validates YAML structure, then renders the GitHub Copilot JSON envelope.

That gives maintainers:

- readable multiline shell commands,
- descriptive metadata next to behavior,
- project-level mode overrides at generation time,
- the same installed `.github/hooks/*.json` contract expected by Copilot.

## 5. migration and compatibility

Migration is additive.

For existing repositories:

1. run `vstack install` (or `vstack init` in CI),
1. review generated `.github/hooks/*.json`,
1. optionally disable specific defaults using `.vstack/config.yaml` `exclude.hook`.

Per-agent frontmatter field `hooks` remains supported and is intentionally separate
from repository-level hooks artifacts.

## 6. operational modes

Hook templates support two operational modes through `VSTACK_HOOKS_MODE`:

- `audit` (default): record events and alerts without enforcing extra tool runs
- `enforce`: run optional actions such as `make format` and `gitleaks` when conditions match

This keeps first-run installs non-disruptive while allowing stricter policy in CI or hardened repositories.

## 7. execution context and dependencies

### 6.1 where hooks execute

Repository hooks execute in the active Copilot hook runtime context.

- local workspace session: local machine runtime
- remote SSH/devcontainer session: remote runtime

All built-in hooks use `cwd: "."` and therefore run from the workspace root.

### 6.2 dependency strategy

Built-in hooks follow a fail-safe dependency model:

1. `audit` mode must work without optional tools,
1. `enforce` mode may call optional tools,
1. hooks must check tool availability before invoking external commands,
1. missing optional tools should log a structured alert and continue.

This prevents install-time or first-run failures while supporting stricter policy in controlled environments.

### 6.3 security posture

- Keep default behavior non-destructive (`audit` first).
- Restrict deny-response behavior to explicit enforce paths.
- Use short timeouts and deterministic command paths.
- Never log secrets; log only event metadata and detection markers.

## 8. config metadata contract

`src/vstack/_templates/hooks/<name>/hook.yaml` includes a `metadata:` section.
These fields are documentation-oriented, and selected values such as `mode_default` are also
used as generation-time defaults when the project does not override them.

Recommended fields:

| Field                   | Purpose                                         |
| ----------------------- | ----------------------------------------------- |
| `description`           | Human-readable explanation of hook behavior     |
| `purpose`               | Classification (`audit`, `security`, `quality`) |
| `security_level`        | Expected risk posture (`low`, `high`)           |
| `mode_default`          | Declared default operation mode                 |
| `execution_context`     | Runtime location expectation                    |
| `dependencies.required` | Must-exist tools for intended behavior          |
| `dependencies.optional` | Optional tooling used in enforce mode           |

______________________________________________________________________

## 9. extension guidance

When adding new built-in hooks:

1. add template directory under `src/vstack/_templates/hooks/<name>/`
1. include `hook.yaml`
1. add name to expected canonical hook list in CLI constants
1. regenerate artifacts via `python -m vstack install`
1. update this design doc and roadmap status if behavior changes
