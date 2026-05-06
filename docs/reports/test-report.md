# Test Report

**Branch:** `feat/workflow_update`\
**Date:** 2026-05-06\
**Scope:** Full repository — `.vstack/` project-scope directory (ADR-019); `vstack install`/`vstack init` command semantics (ADR-020); manifest relocation from `.github/` to `.vstack/` (ADR-021); selective install with `exclude:` filter (ADR-022); `artifacts.root` config override; `.vstack/.gitignore` seeding; agent `artifacts:` section generation; ADR terminology update (Option A/B → direct execution/orchestrated pipeline); roadmap cleanup (version column, candidate rationalisation); gh-issues skill MCP-first guidance. CLI refactor, manifest backfill, and test suite structure remain in scope as prior context.

______________________________________________________________________

## Verdict

| Dimension     | Result                                     |
| ------------- | ------------------------------------------ |
| Functional    | **PASS** — 428/428 tests green             |
| Lint / Style  | **PASS** — ruff clean                      |
| Type checking | **PASS** — mypy clean (51 files, 0 errors) |
| Coverage      | **PASS** — 100.00% (fail-under=100)        |
| Security      | See `docs/reports/security-report.md`      |
| Performance   | See `docs/reports/performance-baseline.md` |

> **Ship readiness: READY** — all verification gates currently pass.

______________________________________________________________________

## Test Execution

```
platform: linux, Python 3.13.12-final-0
runner: pytest 9.0.3 + pytest-cov 7.1.0
command: pytest -q
428 passed in 5.90s
```

All tests pass. No flaky, skipped, or xfail tests observed.

______________________________________________________________________

## Coverage Summary

Total: 100.00% — 0 missed statements across 2,058 measured

`fail-under=100` is configured in `pyproject.toml`. This gate is **passing**.

All modules are now at 100% statement coverage.

### Resolution summary

Blockage coverage findings were resolved by adding targeted unit tests for:

- per-module test files replacing the `test_commands.py` / `test_coverage_blockers.py` catch-all (test count: 288 → 428)
- manifest subcommand dispatch and missing-action path
- service wrappers and `manifest_upgrade` success/error branches
- parser config guard rails (`scope_help` / `only_help` validation)
- interface scope resolution edge cases
- report YAML/JSON/text rendering branches
- command `run()` wrappers and context forwarding
- manifest-store defensive parsing branches
- install/verify/uninstall error-path behavior
- `manifest upgrade --backfill` branches: missing file, unreadable file, no VSTACK-META footer, existing checksum, unknown algorithm fallback

______________________________________________________________________

## Lint and Type Checking

```
ruff check src tests  →  All checks passed!
python -m mypy src tests  →  Success: no issues found in 51 source files
```

No lint or type findings.

______________________________________________________________________

## Syntax

```
python -m py_compile  →  All checked files compile cleanly
```

______________________________________________________________________

## Blocking Issues

No blocking test findings remain.

______________________________________________________________________

## Handoff

Continue monitoring this area by extending tests whenever new command branches or parser flags are introduced, to preserve the 100% coverage gate.
