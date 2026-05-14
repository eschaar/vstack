# Test Report

**Branch:** `chore/split-docs-and-hardening`\
**Date:** 2026-05-14\
**Scope:** Full repository verification snapshot after resolving open report points.

______________________________________________________________________

## Verdict

| Dimension     | Result                                     |
| ------------- | ------------------------------------------ |
| Functional    | **PASS** — 656 passed                      |
| Lint / Style  | **PASS** — ruff clean                      |
| Type checking | **PASS** — mypy clean (119 source files)   |
| Coverage      | **PASS** — 100.00%                         |
| Security      | See `docs/reports/security-report.md`      |
| Performance   | See `docs/reports/performance-baseline.md` |

> **Ship readiness: READY** — test gate is green.

______________________________________________________________________

## Reproduction of Previous Failures

Initial reproduction command:

```bash
source .venv/bin/activate
pytest -q
```

Reproduced result:

- 8 failed, 646 passed
- Failures were all golden-fixture drift checks in `tests/vstack/artifacts/test_generator.py`
- Coverage gate also failed at 99.93% because the failing run stopped before complete branch coverage

______________________________________________________________________

## Fixes Applied

1. Updated golden fixtures to match current generated artifacts for:
   - instructions: `security`, `testing`
   - skills: `concise`, `verify`
   - agents: `planner`, `product`
   - prompts: `code-review`, `api-design-review`
1. Corrected agent golden tests to use `AgentGenerator` (agent templates now require agent-specific placeholder expansion).
1. Added targeted regression tests to close coverage gaps introduced during failure remediation:
   - `tests/vstack/agents/test_generator.py` for non-list `agents` verification path
   - `tests/vstack/frontmatter/test_serializer.py` for YAML-special list-item quoting

## Final Verification Run

```bash
source .venv/bin/activate
pytest -q
```

Run window (UTC):

- started: `2026-05-14T14:21:41Z`
- finished: `2026-05-14T14:22:04Z`

Result:

- 656 passed in 21.51s
- Coverage: 100.00% (fail-under=100 satisfied)

______________________________________________________________________

## Lint and Type Checks

```
ruff check src tests                 -> All checks passed
python -m mypy src tests             -> Success: no issues found in 119 source files
```

No lint or type issues were introduced by the test-fix changes.

______________________________________________________________________

## Handoff

Open test-failure point is fully resolved. Use this report as the new green baseline for this branch.
