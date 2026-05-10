# Hook YAML Template Format

> Specification for repository hook YAML source templates in vstack.

## Overview

Hook templates are authored in YAML for readability and multiline command support.
The YAML file (`hook.yaml`) contains both metadata and the GitHub Copilot hooks definition.

At install time, vstack:

1. Loads hook template YAML
1. Validates metadata and structure
1. Generates JSON output at `.github/hooks/<name>.json`

This decouples human-friendly source (YAML with long commands) from machine-readable output (JSON).

______________________________________________________________________

## Schema

```yaml
version: <integer>
  # Artifact template version, incremented on semantic changes.
  # Example: 20260510003

metadata:
  name: <string>
    # Hook identifier, used in URLs, file names, and logging.
    # Must be lowercase, alphanumeric + hyphen.
    # Example: "session-audit"

  description: <string>
    # Human-readable explanation of hook behavior and intent.
    # Supports multi-line folded text.
    # Example: "Records session start/end events to JSONL audit logs."

  purpose: <enum: audit | security | quality>
    # Functional classification.
    # - audit: event recording without enforcement
    # - security: threat detection or access control
    # - quality: code style and compliance

  security_level: <enum: low | high>
    # Risk classification.
    # - low: read-only or non-destructive operations
    # - high: may block, modify, or enforce policy

  mode_default: <enum: audit | enforce>
    # Default VSTACK_HOOKS_MODE when environment variable is unset.
    # - audit: non-intrusive logging and detection
    # - enforce: strict policy, optional tool execution
    # Most hooks default to 'audit' for safety.

  execution_context: <enum: copilot-hook-runtime | ci | local>
    # Expected environment where this hook runs.
    # - copilot-hook-runtime: GitHub Copilot hook system (default)
    # - ci: CI/CD pipeline environment
    # - local: developer machine
    # Hints for tool and permission assumptions.

  dependencies:
    required: [<string>, ...]
      # Tools/commands that MUST exist for hook to function.
      # Hook fails or degrades if missing.
      # Example: ["git", "make"]

    optional: [<string>, ...]
      # Tools used conditionally, usually in 'enforce' mode.
      # Hook logs when missing but continues normally.
      # Example: ["gitleaks", "make"]

# GitHub Copilot hooks envelope
hooks:
  <event_name>:
    # Event name: one of:
    # - sessionStart, sessionEnd
    # - userPromptSubmitted
    # - preToolUse, postToolUse
    # - errorOccurred

    - type: command
        # Currently, only type "command" is supported.

      description: <string>
        # Optional: brief explanation of this action's behavior.
        # Supports multi-line text.

      bash: <string>
        # Bash script to execute. Supports multi-line.
        # Input arrives via stdin (JSON payload from Copilot).
        # Output to stdout for responses (JSON for permission decisions).
        # Variables: $VSTACK_HOOKS_MODE (audit|enforce)

      powershell: <string>
        # PowerShell script to execute. Supports multi-line.
        # Read stdin with: $inputText = [Console]::In.ReadToEnd()
        # Use environment variable: $env:VSTACK_HOOKS_MODE

      cwd: <string>
        # Working directory. "." = workspace root.

      timeoutSec: <integer>
        # Maximum execution time in seconds. Default 30.
```

______________________________________________________________________

## Example: Complete Hook Template

```yaml
version: 20260510003

metadata:
  name: session-audit
  description: |
    Records session start and end events to structured JSONL logs
    in .vstack/logs/ for audit trail and compliance verification.
  purpose: audit
  security_level: low
  mode_default: audit
  execution_context: copilot-hook-runtime
  dependencies:
    required: []
    optional: []

hooks:
  sessionStart:
    - type: command
      description: |
        Log session start event with timestamp and context.
      bash: |
        mkdir -p .vstack/logs
        input="$(cat)"
        printf '%s\n' "$input" >> .vstack/logs/hook-session-start.jsonl
      powershell: |
        New-Item -ItemType Directory -Force -Path .vstack/logs | Out-Null
        $inputText = [Console]::In.ReadToEnd()
        Add-Content -Path .vstack/logs/hook-session-start.jsonl -Value $inputText
      cwd: "."
      timeoutSec: 10

  sessionEnd:
    - type: command
      description: |
        Log session end event for correlation with start.
      bash: |
        mkdir -p .vstack/logs
        input="$(cat)"
        printf '%s\n' "$input" >> .vstack/logs/hook-session-end.jsonl
      powershell: |
        New-Item -ItemType Directory -Force -Path .vstack/logs | Out-Null
        $inputText = [Console]::In.ReadToEnd()
        Add-Content -Path .vstack/logs/hook-session-end.jsonl -Value $inputText
      cwd: "."
      timeoutSec: 10
```

______________________________________________________________________

## Authoring Guidance

### Multi-line Scripts

Use YAML literal folded scalars (`|-` or `|`) for scripts:

```yaml
bash: |
  mkdir -p .vstack/logs
  input="$(cat)"
  if [ -z "$input" ]; then
    exit 1
  fi
  printf '%s\n' "$input" >> .vstack/logs/audit.jsonl
```

### Bash Best Practices

- Read stdin early: `input="$(cat)"`
- Check tool availability: `command -v git >/dev/null 2>&1`
- Use early exits: `[ "$VSTACK_HOOKS_MODE" != "enforce" ] && exit 0`
- Log errors to `.vstack/logs/hook-*.log`, not stderr

### PowerShell Best Practices

- Read stdin: `$inputText = [Console]::In.ReadToEnd()`
- Check commands: `Get-Command gitleaks -ErrorAction SilentlyContinue`
- Suppress output: `command *> $null`
- Use `$env:VSTACK_HOOKS_MODE` for mode detection

### Environment Variables

- `VSTACK_HOOKS_MODE` (string: `audit` | `enforce`)
  - Default: `audit` if unset
  - User can override in session
- `.vstack/logs/` for structured JSONL audit output
- `.vstack/config.yaml` available for shared settings

______________________________________________________________________

## Generation and Installation

### Source Workflow

1. User authors hook template: `src/vstack/_templates/hooks/<name>/hook.yaml`
1. HookGenerator loads and validates YAML
1. Generator constructs GitHub Copilot hooks JSON envelope
1. Output written to `.github/hooks/<name>.json`

### Local Project Workflow

1. User copies/modifies hook template to `.vstack/templates/hooks/<name>/hook.yaml`
1. User runs `vstack install`
1. HookGenerator regenerates `.github/hooks/<name>.json` from YAML
1. Manifest updated with checksum

______________________________________________________________________

## vstack Integration

### Seeding

When `vstack init` or `vstack install` runs locally, hook templates are seeded to:

```
.vstack/templates/hooks/<name>/hook.yaml
```

Users can modify these templates directly; `vstack install` will regenerate `.github/hooks/` JSON from them.

### Manifest Tracking

Hooks are tracked in `.vstack/vstack.json`:

```json
{
  "hooks": {
    "session-audit": {
      "source_path": "src/vstack/_templates/hooks/session-audit/hook.yaml",
      "output_path": ".github/hooks/session-audit.json",
      "checksum": "sha256:abc123..."
    }
  }
}
```

### Verification

`vstack verify` checks:

- Source YAML is valid and well-formed
- Metadata fields are correct
- Hook structure complies with envelope spec
- Generated JSON checksums match manifest
