# Performance Baseline

**Branch:** `feat/improved_cli`
**Date:** 2026-04-26
**Scope:** CLI hot-path operations — parser build, target resolution, registry build; post-backfill feature addition
**Method:** `timeit.repeat` micro-benchmarks (Python 3.13.12, Linux)

______________________________________________________________________

## Verdict

> **No regressions detected.** All measured operations are sub-2ms. The CLI is a local dev tool with no throughput or latency SLAs — these baselines exist to catch accidental regressions from future changes.

______________________________________________________________________

## Benchmark Results

All times in **milliseconds (ms)** per single call.

| Operation                                      | Mean     | Min      | Max      | Stdev | Iterations |
| ---------------------------------------------- | -------- | -------- | -------- | ----- | ---------- |
| `CommandLineParser().build()` + `parse_args()` | 1.852 ms | 1.783 ms | 2.018 ms | —     | 5 × 1000   |
| `parser.resolve_targets(args)`                 | 0.009 ms | 0.008 ms | 0.012 ms | —     | 5 × 1000   |
| `build_command_registry(svc)`                  | 0.002 ms | 0.002 ms | 0.002 ms | —     | 5 × 1000   |
| Cold `import vstack`                           | 69.6 ms  | 66.0 ms  | 75.9 ms  | —     | 5 × 1      |

______________________________________________________________________

## Notes

### CLI parser build + parse (~1.85 ms)

`CommandLineParser().build()` constructs the full argparse tree — 6 top-level commands and all manifest subcommands — followed by `parse_args()`. The `CommandLineParser()` constructor itself is essentially a no-op (\<0.001 ms); the build step is what dominates. At ~1.85 ms end-to-end, this remains well within acceptable startup overhead for an interactive CLI.

No regression from the backfill feature addition: the new `--backfill` flag on the `manifest upgrade` subcommand adds one `add_argument` call, which is negligible at this scale.

### Target resolution (\<0.01 ms)

`resolve_targets` is essentially free — filesystem path manipulation with a single `Path.exists()` check in the `--global` path. No blocking I/O in the default (CWD) path.

### Registry build (\<0.01 ms)

`build_command_registry` constructs the command map from the catalog. The catalog-driven approach (dict comprehension over ~8 entries) is negligible.

### Cold import (~70 ms)

The first `import vstack` in a fresh Python process takes ~70 ms on average (59–80 ms observed across 5 runs). This includes:

- `subprocess` call to `git tag --points-at HEAD` (in `constants.py`) for version detection
- Stdlib imports (`pathlib`, `argparse`, `importlib.metadata`, `re`, `subprocess`, `yaml`)

This is the dominant startup cost. The git subprocess call is the likely bottleneck. For a CLI tool this is acceptable — it runs once at startup.

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
342 tests passed in 4.24s (pytest, with coverage)
```

Acceptable. No slow test outliers observed.

______________________________________________________________________

## Profiling Notes

No `pytest-benchmark` is installed in this environment; measurements were taken with `timeit.repeat`. If regression detection becomes a CI requirement, add `pytest-benchmark` to dev dependencies and convert the `timeit` measurements to parametrised benchmark tests.
