# Hooks

This page explains what repository hooks do in vstack and how to enable or disable them.

## What Hooks Are

vstack manages repository-level hook artifacts under `.github/hooks/*.json`.

Hooks run on Copilot session and tool events. They support safety, audit, and quality checks.

## Version Semantics

Hooks use two different version concepts with different owners:

| Field                       | Example                                                         | Owner                        | Meaning                                                                                                              |
| --------------------------- | --------------------------------------------------------------- | ---------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Hook payload `version`      | `1` in `.github/hooks/<name>.json`                              | GitHub Copilot hook contract | Envelope/schema version for the JSON hook payload (`{"version": 1, "hooks": {...}}`).                                |
| Artifact template `version` | `20260514002` in `src/vstack/_templates/hooks/<name>/hook.yaml` | vstack template lifecycle    | Revision token for the hook template artifact, tracked in `.vstack/vstack.json` and used for drift/ownership checks. |

These fields are intentionally different and should not be forced to match.

- If Copilot changes the hook envelope contract in the future, payload `version` may move from `1` to `2` or higher.
- Hook template revision tokens can still increment independently for normal template updates.

Operational rule: treat payload `version` as contract compatibility, and artifact `version` as vstack-managed template revision.

## Built-in Hooks

vstack ships these baseline hooks:

| Hook                         | Purpose                                                                  |
| ---------------------------- | ------------------------------------------------------------------------ |
| `agent-call-audit`           | Records actor and delegation visibility for agent and subagent flows.    |
| `session-audit`              | Records generic session, prompt, and tool telemetry without actor data.  |
| `log-retention-cleanup`      | Prunes old hook log directories based on retention policy.               |
| `pre-tool-safety-gate`       | Detects risky tool actions before execution and applies policy behavior. |
| `post-edit-format`           | Runs or records formatting-related checks after edit operations.         |
| `post-edit-markdown-quality` | Applies markdown quality checks for docs-oriented changes.               |
| `post-commit-security-scan`  | Runs post-commit safety/security checks when configured.                 |

## Enable or Disable Hooks Globally

In `.vstack/config.yaml`:

```yaml
hooks:
  enabled: true
  mode: audit
```

- `enabled: false` disables generation of baseline hook artifacts.
- `mode` sets default behavior mode for generated hooks.

## Enable or Disable Individual Hooks

```yaml
hooks:
  hooks:
    post-edit-markdown-quality:
      enabled: false
    pre-tool-safety-gate:
      mode: enforce
```

## Log Settings

```yaml
hooks:
  log_level: minimal
  log_retention_days: 7
  log_dir: .vstack/logs
  hooks:
    session-audit:
      log:
        level: verbose
        name: session-audit.log
        retention_days: 14
```

Runtime pruning is enforced for hook logs:

- On each hook event path, vstack prunes old day directories under `log_dir`.
- Pruning only targets directories named `YYYYMMDD`.
- `agent-call-audit` applies the same retention to `hook-agent-call-unknown-events.tsv`, because it is stored in the per-day directory that is pruned.
- Retention defaults to `metadata.log.retention_days` (currently `7`) and can be overridden with `VSTACK_HOOK_RETENTION_DAYS`.
- Invalid override values (non-numeric or non-positive) safely fall back to `7`.

## Audit Boundary Model

- `session-audit` is for generic telemetry only. It tracks payload volume and event metadata for session and tool activity.
- `agent-call-audit` is for actor and delegation telemetry only. It tracks who acted and where control was delegated.

## Session Audit Minimal Logging

When `session-audit` runs in `minimal` mode, logs include compact visibility fields without storing full prompt payload text:

- Every minimal record includes `timestamp`, `event`, `size_bytes`, `estimated_tokens`, and `hook_execution_ms`.
- `preToolUse` and `postToolUse` also include `tool_name` and `tool_call_id`.
- `userPromptSubmitted` also includes `slash_command` when a prompt starts with `/...`; otherwise it records `none`.

Raw event payloads are written only in `verbose` mode.

## Agent Call Audit Minimal Logging

When `agent-call-audit` runs in `minimal` mode, it writes compact JSONL records to `.vstack/logs/YYYYMMDD/hook-agent-call.log`:

- Every minimal record includes `timestamp`, `event`, `size_bytes`, `estimated_tokens`, and `hook_execution_ms`.
- `sessionStart` and `sessionEnd` include `session_id`, `actor_name`, `actor_type`, and `model_used`.
- `preToolUse` and `postToolUse` include `session_id`, `actor_name`, `actor_type`, `tool_name`, `delegated_agent_name`, and `model_used`.
- Delegation calls are explicit:
  - `preToolUse` logs `delegationStart` when `tool_name` is `runSubagent`.
  - `postToolUse` logs `delegationEnd` when `tool_name` is `runSubagent`.
- `delegated_agent_name` is best-effort and extracted when delegation payload fields are present, especially for `runSubagent` calls.
- Unknown suppression in minimal mode is counter-based:
  - Suppressed unknown events persist in `.vstack/logs/YYYYMMDD/hook-agent-call-unknown-events.tsv` as `session_id<TAB>reason<TAB>count`.
  - The hook aggregates counts per `(session_id, reason)` instead of appending duplicate rows.
  - Legacy 2-column rows (`session_id<TAB>reason`) are treated as `count=1` when summarizing and rewriting.
  - `sessionEnd` emits an `unknownSummary` record with aggregated per-session counts before cleanup.

### Why this file exists

`hook-agent-call-unknown-events.tsv` is an internal counter file for minimal-mode unknown suppression.
It preserves per-session unknown reasons so `sessionEnd` can emit an accurate `unknownSummary`, and it helps operators track parser quality and unknown-rate drift over time.

`actor_name`, `actor_type`, `tool_name`, `delegated_agent_name`, and `model_used` are best-effort and may remain `unknown` when payload fields are unavailable.

## Minimal Log Schema

Use this compact reference to see which fields each hook emits per mode and event.

| Hook               | Mode      | Event                 | Emitted fields                                                                                            |
| ------------------ | --------- | --------------------- | --------------------------------------------------------------------------------------------------------- |
| `session-audit`    | `minimal` | any event             | `timestamp`, `event`, `size_bytes`, `estimated_tokens`, `hook_execution_ms`                               |
| `session-audit`    | `minimal` | `preToolUse`          | base fields + `tool_name`, `tool_call_id`                                                                 |
| `session-audit`    | `minimal` | `postToolUse`         | base fields + `tool_name`, `tool_call_id`                                                                 |
| `session-audit`    | `minimal` | `userPromptSubmitted` | base fields + `slash_command`                                                                             |
| `session-audit`    | `verbose` | any event             | raw payload passthrough                                                                                   |
| `agent-call-audit` | `minimal` | any event             | `timestamp`, `event`, `size_bytes`, `estimated_tokens`, `hook_execution_ms`                               |
| `agent-call-audit` | `minimal` | `sessionStart`        | base fields + `session_id`, `actor_name`, `actor_type`, `model_used`                                      |
| `agent-call-audit` | `minimal` | `sessionEnd`          | base fields + `session_id`, `actor_name`, `actor_type`, `model_used`                                      |
| `agent-call-audit` | `minimal` | `preToolUse`          | base fields + `session_id`, `actor_name`, `actor_type`, `tool_name`, `delegated_agent_name`, `model_used` |
| `agent-call-audit` | `minimal` | `postToolUse`         | base fields + `session_id`, `actor_name`, `actor_type`, `tool_name`, `delegated_agent_name`, `model_used` |
| `agent-call-audit` | `verbose` | any event             | raw payload passthrough                                                                                   |

`base fields` in this table means `timestamp`, `event`, `size_bytes`, `estimated_tokens`, and `hook_execution_ms`.

## Apply and Verify Hook Changes

```bash
vstack init --only hook
vstack manifest status --target . --only hook
vstack manifest verify --target . --only hook
```

## Related Docs

- [Configuration](configuration.md)
- [CLI commands](cli-commands.md)
- [Artifact checks](artifact-checks.md)
