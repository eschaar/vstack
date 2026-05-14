# Performance Baseline

**Branch:** `chore/split-docs-and-hardening`\
**Date:** 2026-05-14\
**Scope:** CLI hot-path operations baseline for parser build, target resolution, registry build, and cold import.\
**Method:** `timeit.repeat` micro-benchmarks (Python 3.13.12, Linux).

______________________________________________________________________

## Verdict

> **Baseline refreshed.** New measurements were captured after test and security remediation on this branch.

______________________________________________________________________

## Benchmark Results

Latest benchmark capture window (UTC): **2026-05-14T14:23:18+00:00 → 2026-05-14T14:23:38+00:00**.

Command used:

```bash
source .venv/bin/activate
python - <<'PY'
# timeit.repeat for parser build+parse, resolve_targets, build_command_registry,
# plus subprocess-based cold import timing (5 repeats)
PY
```

All times in **milliseconds (ms)** per single call.

| Operation                                      | Mean       | Min        | Max        | Stdev | Iterations |
| ---------------------------------------------- | ---------- | ---------- | ---------- | ----- | ---------- |
| `CommandLineParser().build()` + `parse_args()` | 2.953 ms   | 2.552 ms   | 3.608 ms   | 0.385 | 5 × 1000   |
| `parser.resolve_targets(args)`                 | 0.022 ms   | 0.020 ms   | 0.025 ms   | 0.002 | 5 × 1000   |
| `build_command_registry(svc)`                  | 0.003 ms   | 0.002 ms   | 0.003 ms   | 0.000 | 5 × 1000   |
| Cold `import vstack`                           | 142.279 ms | 134.769 ms | 155.209 ms | 8.994 | 5 × 1      |

______________________________________________________________________

## Notes

### CLI parser build + parse (~2.95 ms)

`CommandLineParser().build()` constructs the full argparse tree and `parse_args(['validate'])` parses a minimal command path. At ~2.95 ms end-to-end, this remains under the configured regression threshold.

No threshold breach detected.

### Target resolution (~0.02 ms)

`resolve_targets` remains effectively free for CLI use.

### Registry build (~0.003 ms)

`build_command_registry` remains negligible.

### Cold import (~142 ms)

The first `import vstack` in a fresh Python process now measures ~142 ms on average. This includes:

- `subprocess` call to `git tag --points-at HEAD` (in `constants.py`) for version detection
- stdlib and package import overhead

This is still the dominant startup cost, but it remains below the 500 ms threshold.

______________________________________________________________________

## Thresholds

These are soft baselines for regression detection, not hard SLAs.

| Operation                     | Regression threshold |
| ----------------------------- | -------------------- |
| `CommandLineParser().build()` | > 5 ms               |
| `resolve_targets`             | > 1 ms               |
| `build_command_registry`      | > 1 ms               |
| Cold import                   | > 500 ms             |

If a future change causes a measured value to exceed these thresholds, investigate before merging.

______________________________________________________________________

## Test Suite Wall Time

```
Final verification run (UTC): 2026-05-14T14:21:41Z → 2026-05-14T14:22:04Z
command: pytest -q
result: 656 passed in 21.51s
```

This is now a green run and can be used as the current wall-time reference for this branch.

______________________________________________________________________

## Profiling Notes

No `pytest-benchmark` is installed in this environment; measurements were taken with `timeit.repeat`. If regression detection becomes a CI requirement, add `pytest-benchmark` to dev dependencies and convert the `timeit` measurements to parametrised benchmark tests.
