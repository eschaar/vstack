{{SKILL_CONTEXT}}

{{BASE_BRANCH}}

# verify - Fix Loop Verification

Run a targeted verification fix loop:

1. choose scope/mode,
1. run checks,
1. fix issues in priority order,
1. re-run only impacted checks,
1. report ship readiness.

Use `inspect` for read-only auditing.

## Out of scope

- Architecture decisions (use `architecture`)
- Full security audit (use `security`)
- Performance benchmarking/profiling (use `performance`)
- New feature implementation outside verification fixes (engineering role)

______________________________________________________________________

## Step 0: Route Mode

Classify first, then run one mode.

> **Question:** Which verify mode should be used?
> **Options:**
> A) quick - critical/high regressions only
> B) standard - default verification + fix loop
> C) exhaustive - broad verification and full fix sweep
> D) report-only - route to `inspect`
> **Default if no response:** B

If D, stop and route to `inspect`.

______________________________________________________________________

## Step 1: Scope and Safety

Parse user scope:

- Target: whole repo or specific component/path
- Tier: quick/standard/exhaustive
- Source: full branch diff or explicit path

Check working tree:

```bash
git status --porcelain
```

If dirty, ask before proceeding because verify may create multiple atomic fix commits.

Bootstrap test command:

{{RUN_TESTS}}

______________________________________________________________________

## Step 2: Baseline Checks (all modes)

Run baseline checks for the selected scope.

### 2.1 Lint and Type

```bash
[ -f package.json ] && (npm run lint 2>/dev/null || true)
[ -f tsconfig.json ] && npx tsc --noEmit 2>/dev/null || true
[ -f pyproject.toml ] && (ruff check . 2>/dev/null || true)
[ -f pyproject.toml ] && (mypy . 2>/dev/null || pyright . 2>/dev/null || true)
[ -f go.mod ] && (go vet ./... 2>/dev/null || true)
```

### 2.2 Unit Tests

{{RUN_TESTS}}

______________________________________________________________________

## Step 3: Conditional Checks by Mode

### quick

- Run only failing or high-risk checks related to changed code
- Skip broad integration/contract/smoke unless directly impacted

### standard

Run these when present:

```bash
# Integration
[ -f package.json ] && npm run test:integration 2>/dev/null || true
[ -f pyproject.toml ] && python -m pytest -m integration -v 2>/dev/null || true
[ -f go.mod ] && go test -run Integration ./... 2>/dev/null || true

# Contract
[ -f openapi.yaml ] && npx @redocly/cli lint openapi.yaml 2>/dev/null || true
[ -n "$(find . -name '*.proto' 2>/dev/null | head -1)" ] && buf lint 2>/dev/null || true
```

### exhaustive

Run standard checks plus:

```bash
# Optional smoke checks if scripts exist
find . -name '*.smoke.*' -o -name '*smoke-test*' -o -name 'smoke.sh' 2>/dev/null | head -5

# Dependency vulnerability gate (lightweight only; full audit belongs to security)
[ -f package.json ] && npm audit --audit-level=high 2>/dev/null || true
[ -f pyproject.toml ] && pip-audit 2>/dev/null || true
[ -f go.mod ] && govulncheck ./... 2>/dev/null || true
```

If deep security/performance concerns appear, stop and route to `security` or `performance`.

______________________________________________________________________

## Step 4: Triage

Classify findings:

| Severity | Examples                                                            |
| -------- | ------------------------------------------------------------------- |
| critical | test crashes, build breaks, data integrity/security regressions     |
| high     | contract violations, broken error handling, missing required checks |
| medium   | flaky tests, non-critical behavior gaps                             |
| low      | style and minor cleanups                                            |

Fix policy:

- quick: critical + high
- standard: critical + high + medium
- exhaustive: all severities

______________________________________________________________________

## Step 5: Fix and Re-verify Loop

For each fixable issue in severity order:

1. Reproduce and confirm root cause.
1. Apply minimal fix.
1. Commit atomically (`fix: ...`).
1. Re-run only impacted checks first.
1. If needed, run the relevant broader check suite.

If an issue implies architecture or design mismatch, stop and escalate.

______________________________________________________________________

## Step 6: Final Report

```text
## Verification Report - [component/repo] - [date]

selected_mode: [quick|standard|exhaustive]
scope: [path/component/full]

### Summary
- tests: [X pass / Y fail / Z skip]
- issues found: [N critical / N high / N medium / N low]
- fixes applied: [N]
- deferred: [N]

### Fixed Issues
1. [issue] - [commit SHA]

### Deferred Issues
1. [issue] - [why deferred] - [owner]

### Routed Follow-ups (if any)
- [security|performance|architecture|design] - [reason]

### Ship Readiness
[READY TO SHIP | NEEDS FIXES | BLOCKED]
```

______________________________________________________________________
