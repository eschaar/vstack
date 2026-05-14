# vstack - hooks design

> Maintained by: **designer** role\
> Last updated: 2026-05-14

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

### 1.3 version fields and ownership

Hook artifacts intentionally carry two independent version concepts:

| Field              | Location                                                          | Example       | Purpose                                                                                         |
| ------------------ | ----------------------------------------------------------------- | ------------- | ----------------------------------------------------------------------------------------------- |
| Payload `version`  | Generated `.github/hooks/<name>.json`                             | `1`           | Copilot hook envelope/contract version.                                                         |
| Artifact `version` | Source `src/vstack/_templates/hooks/<name>/hook.yaml` (top-level) | `20260514002` | vstack template revision token used in manifest and footer metadata for ownership/drift checks. |

Design implication:

- Do not couple payload contract versioning to template revision versioning.
- A future Copilot contract bump (`version: 2`) should be handled in hook generator render logic.
- Routine template changes should continue to bump only the artifact revision token.

______________________________________________________________________

## 2. baseline hook set

vstack ships seven default repository hooks:

| Hook name                    | Primary events                                                                   | Intent                                                                                                               |
| ---------------------------- | -------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `agent-call-audit`           | `sessionStart`, `sessionEnd`, `preToolUse`, `postToolUse`                        | Actor and delegation visibility with per-session unknown counters, `unknownSummary`, and delegation start/end events |
| `session-audit`              | `userPromptSubmitted`, `sessionStart`, `sessionEnd`, `preToolUse`, `postToolUse` | Generic session, prompt, and tool telemetry without actor fields                                                     |
| `log-retention-cleanup`      | `sessionStart`                                                                   | Prune dated log directories by retention policy                                                                      |
| `pre-tool-safety-gate`       | `preToolUse`, `errorOccurred`                                                    | Deny destructive shell patterns + error logging                                                                      |
| `post-edit-format`           | `postToolUse`                                                                    | Edit-event logging + optional `make format` run                                                                      |
| `post-edit-markdown-quality` | `postToolUse`                                                                    | vstack markdown/work-item formatting for docs and templates                                                          |
| `post-commit-security-scan`  | `postToolUse`, `sessionEnd`                                                      | Git-mutation checks + optional `gitleaks` run                                                                        |

These defaults are safe in audit mode and can be upgraded to enforcement behavior.
For vstack specifically, the markdown-quality hook gives the baseline hook set a direct payoff on ADRs,
design docs, prompts, instructions, and other generated work items.

### 2.1 agent-call-audit unknown-events sidecar

`agent-call-audit` keeps `.vstack/logs/YYYYMMDD/hook-agent-call-unknown-events.tsv` as a per-day sidecar.

- Why it exists: minimal-mode logging suppresses repeated unknown rows, so the sidecar accumulates unknown reasons per session instead of writing noisy duplicates.
- Operational value: it exposes parser quality and unknown-rate trends, and powers reliable `unknownSummary` emission at `sessionEnd`.
- When it is not needed: verbose mode (raw payload logs), disabled/off hook logging, or sessions with no unknown actor/tool extraction outcomes.

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
  log_level: minimal
  log_retention_days: 7
  log_dir: .vstack/logs
  hooks:
    pre-tool-safety-gate:
      mode: enforce
      log:
        level: verbose
        name: hook-security-alerts.log
        retention_days: 14
    post-edit-markdown-quality:
      enabled: false
```

- `hooks.enabled: false` disables the generated baseline hook family.
- `hooks.mode` sets the generated default fallback for `VSTACK_HOOKS_MODE`.
- `hooks.log_level` sets the generated default fallback for `VSTACK_HOOKS_LOG_LEVEL` (`off`, `minimal`, `verbose`).
- `hooks.log_retention_days` sets the generated default fallback for `VSTACK_HOOKS_LOG_RETENTION_DAYS`.
- `hooks.log_dir` sets the generated default fallback for `VSTACK_HOOK_LOG_DIR`.
- `hooks.hooks.<name>.enabled: false` disables one named built-in hook.
- `hooks.hooks.<name>.mode` overrides the default mode for one named hook.
- `hooks.hooks.<name>.log.level` overrides `VSTACK_HOOKS_LOG_LEVEL` for one hook.
- `hooks.hooks.<name>.log.name` overrides `VSTACK_HOOK_LOG_NAME` for one hook.
- `hooks.hooks.<name>.log.retention_days` overrides retention for one hook.

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

### 6.4 audit-hook runtime budget

`session-audit` and `agent-call-audit` are intentionally bounded to `timeoutSec: 5`.
They do not depend on external tools and only perform local payload parsing and append-only log writes.
The shorter timeout reduces tail latency and keeps hook execution atomic and fast.

### 6.5 minimal log schema baseline

The internal logging contract keeps minimal mode compact and deterministic across both audit hooks:

| Hook                                   | Event scope                 | Minimal schema baseline                                                                                                       |
| -------------------------------------- | --------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `session-audit`                        | any event                   | `timestamp`, `event`, `size_bytes`, `estimated_tokens`, `hook_execution_ms`                                                   |
| `session-audit`                        | `preToolUse`, `postToolUse` | base fields + `tool_name`, `tool_call_id`                                                                                     |
| `agent-call-audit`                     | any event                   | `timestamp`, `event`, `size_bytes`, `estimated_tokens`, `hook_execution_ms`                                                   |
| `agent-call-audit`                     | `preToolUse`, `postToolUse` | base fields + `session_id`, `actor_name`, `actor_type`, `tool_name`, `delegated_agent_name`, `model_used` (no `tool_call_id`) |
| `session-audit` and `agent-call-audit` | `verbose` mode              | raw payload passthrough                                                                                                       |

`base fields` means `timestamp`, `event`, `size_bytes`, `estimated_tokens`, and `hook_execution_ms`.

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
