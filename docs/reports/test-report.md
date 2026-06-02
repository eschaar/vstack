# Test Report

**Branch:** `feature/publish_in_homebrew`\
**Date:** 2026-06-02\
**Scope:** Full repository verification snapshot including Homebrew publish workflow contract tests.

______________________________________________________________________

## Verdict

| Dimension     | Result                                     |
| ------------- | ------------------------------------------ |
| Functional    | **PASS** — 658 passed                      |
| Lint / Style  | **PASS** — ruff clean                      |
| Type checking | **PASS** — mypy clean (120 source files)   |
| Coverage      | **PASS** — 100.00%                         |
| Security      | See `docs/reports/security-report.md`      |
| Performance   | See `docs/reports/performance-baseline.md` |

> **Ship readiness: READY** — test gate is green.

______________________________________________________________________

## Changes Since Previous Baseline (2026-05-14)

### Engineer changes

- Added `publish-homebrew` job to `.github/workflows/publish.yml`.
- Added `tests/vstack/test_publish_workflow.py` — two contract tests for the new job.
- Updated `docs/design/workflow.md` with Homebrew distribution flow.

### Tester findings and fixes

- **T-001 (test bug — fixed):** `test_homebrew_job_verifies_sdist_and_dispatches_update` raised
  `KeyError: 'id'` because the generator iterated steps that have no `id` key before reaching the
  target step. Fixed by changing `step["id"]` to `step.get("id")` in
  `tests/vstack/test_publish_workflow.py`.

## Final Verification Run

```bash
.venv/bin/pytest -q
```

Run window (UTC):

- started: `2026-06-02T00:00:00Z` (approximate)
- platform: darwin, Python 3.13.2

Result:

- 658 passed in 12.36s
- Coverage: 100.00% (fail-under=100 satisfied)

______________________________________________________________________

## Lint and Type Checks

```
ruff check src tests                 -> All checks passed
python -m mypy src tests             -> Success: no issues found in 120 source files
```

No lint or type issues were introduced by the test fix.

______________________________________________________________________

## Handoff

All publish workflow contract tests pass. Use this report as the new green baseline for the `feature/publish_in_homebrew` branch.
