{{SKILL_CONTEXT}}

{{BASE_BRANCH}}

# inspect - Read-Only Verification Audit

Run verification checks and report findings. Do not edit code, do not commit,
and do not fix anything.

Use `verify` when a fix loop is required.

## Out of scope

- Fixing issues (use `verify`)
- Architecture decisions (use `architecture`)
- Full security audit (use `security`)
- Performance profiling (use `performance`)

## Step 0: Scope

```text
Report only. No edits. No commits.
If critical issues are found, recommend `verify`.
```

______________________________________________________________________

## Step 1: Baseline Checks

```bash
[ -f package.json ] && (npm run lint 2>/dev/null || true)
[ -f tsconfig.json ] && npx tsc --noEmit 2>/dev/null || true
[ -f pyproject.toml ] && (ruff check . 2>/dev/null || true)
[ -f pyproject.toml ] && (mypy . 2>/dev/null || pyright . 2>/dev/null || true)
[ -f go.mod ] && (go vet ./... 2>/dev/null || true)
```

{{RUN_TESTS}}

______________________________________________________________________

## Step 2: Extended Checks (when present)

```bash
# Integration
[ -f package.json ] && npm run test:integration 2>/dev/null || true
[ -f pyproject.toml ] && python -m pytest -m integration -v 2>/dev/null || true
[ -f go.mod ] && go test -run Integration ./... 2>/dev/null || true

# Contract
[ -f openapi.yaml ] && npx @redocly/cli lint openapi.yaml 2>/dev/null || true
[ -n "$(find . -name '*.proto' 2>/dev/null | head -1)" ] && buf lint 2>/dev/null || true

# Lightweight vulnerability gate
[ -f package.json ] && npm audit --audit-level=high 2>/dev/null || true
[ -f pyproject.toml ] && pip-audit 2>/dev/null || true
[ -f go.mod ] && govulncheck ./... 2>/dev/null || true
```

______________________________________________________________________

## Step 3: Report

```text
## Inspection Report - [component/repo] - [date]

### Summary
- tests: [X pass / Y fail / Z skip]
- issues: [N critical / N high / N medium / N low]

### Critical
1. [issue] - [file:line] - [evidence]

### High
1. [issue] - [file:line] - [recommended fix]

### Medium
1. [issue] - [file:line] - [recommended fix]

### Low
1. [issue] - [notes]

### Recommendation
[SHIP-READY | USE VERIFY FIX LOOP | NEEDS ARCH/DESIGN REVIEW]
```

______________________________________________________________________
