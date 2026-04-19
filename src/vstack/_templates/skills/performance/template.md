{{SKILL_CONTEXT}}

{{BASE_BRANCH}}

# performance — Profile, Benchmark & Regression Detection

Profile backend services, detect performance regressions, and recommend
optimizations. Measure first; never optimize without evidence.

## Out of scope

- Full code review (use `code-review`)
- Security analysis (use `security`)
- Architecture design (use `architecture`)
- Non-performance bug fixing (use `debug`)

## Deliverable and artifact policy

- Primary deliverable: `docs/performance-baseline.md`
- Baseline-first default: write benchmark outcomes and regression verdicts directly to `docs/performance-baseline.md` on the feature branch.
- Optional WIP area for complex/uncertain efforts: `docs/delta/{id}/PERFORMANCE_DELTA.md`
- Before merge: consolidate thresholds, measurements, and recommendations into the baseline performance report.

______________________________________________________________________

## Setup

**Parse the user's request:**

| Parameter | Default                     | Override                                 |
| --------- | --------------------------- | ---------------------------------------- |
| Target    | Whole service / entry point | `Focus on the /search endpoint`          |
| Mode      | Comparison (vs base branch) | `--baseline`, `--profile`, `--load-test` |
| Threshold | 5% regression               | `--threshold 0.10` (10%)                 |

______________________________________________________________________

## Phase 1: Establish Baseline

If on a feature branch, record performance metrics before and after the change:

```bash
# Record current branch metrics
CURRENT=$(git branch --show-current)

# Run benchmarks
echo "=== Benchmarks on $CURRENT ==="
{{RUN_TESTS}}

# Language-specific benchmark runners:
# Node/Bun
[ -f package.json ] && npm run bench 2>/dev/null \
  || npx vitest bench 2>/dev/null \
  || npx jest --config jest.bench.config.js 2>/dev/null || true

# Python
[ -f pyproject.toml ] && python -m pytest --benchmark-only -v 2>/dev/null || true

# Go
[ -f go.mod ] && go test -bench=. -benchmem ./... 2>/dev/null || true

# Rust
[ -f Cargo.toml ] && cargo bench 2>/dev/null || true
```

______________________________________________________________________

## Phase 2: Comparison vs Base Branch

```bash
# Stash current changes and benchmark base
git stash
git checkout <base>

echo "=== Benchmarks on <base> ==="
# [run same benchmark commands as Phase 1]

# Restore feature branch
git checkout "$CURRENT"
git stash pop
```

Compare results:

- p50 latency change
- p95/p99 latency change
- Throughput (ops/second) change
- Memory allocation change
- CPU usage change

**Regression threshold:** Flag if any metric degrades by more than 5% (or configured threshold).

______________________________________________________________________

## Phase 3: Load Testing (if applicable)

```bash
# Check for load test tools
which k6 2>/dev/null && echo "k6 available"
which hey 2>/dev/null && echo "hey available"
which wrk 2>/dev/null && echo "wrk available"
which ab 2>/dev/null && echo "ab available"

# Example k6 run (adapt to your endpoint)
# k6 run --vus 50 --duration 30s script.js
```

For API endpoints, run a basic load test:

```bash
# Using hey (install: go install github.com/rakyll/hey@latest)
hey -n 1000 -c 50 "${SERVICE_URL}/health" 2>/dev/null || true

# Using wrk (if available)
wrk -t4 -c100 -d30s "${SERVICE_URL}/health" 2>/dev/null || true
```

______________________________________________________________________

## Phase 4: Profiling (if regression found)

If a regression is detected, profile to identify the bottleneck:

```bash
# Node.js profiling
node --prof app.js &
# ...run workload...
node --prof-process isolate-*.log > profile.txt

# Python profiling
python -m cProfile -o profile.prof app.py
python -m pstats profile.prof

# Go pprof
go tool pprof cpu.prof
```

Common bottleneck categories:

- **N+1 queries:** Multiple DB calls where one would suffice
- **Serialization:** JSON marshal/unmarshal overhead
- **Lock contention:** Mutex/lock held too long
- **Memory allocation:** GC pressure from excessive allocations
- **Missing cache:** Repeated computation of the same result
- **Sync where async:** Blocking I/O on hot path
- **Regex compilation:** Regex compiled inside hot loop

______________________________________________________________________

## Phase 5: Optimization Loop

For each bottleneck identified:

1. Propose the optimization with rationale
1. Implement
1. Re-benchmark
1. Confirm improvement

**Optimization principles:**

- Measure first, optimize second. Never guess what's slow.
- Profile the real workload, not synthetic microbenchmarks.
- Big-O matters more than constant factors.
- Cache invalidation is a correctness problem, not just a performance trick.
- Async I/O > sync I/O for I/O-bound work.
- Batch > N individual calls.

______________________________________________________________________

## Performance Report

```text
## Performance Report — [service/endpoint] — [date]

### Benchmark Results

| Metric | Base | Current | Change | Status |
|--------|------|---------|--------|--------|
| p50 latency | Xms | Xms | +N% | ✓/✗ |
| p95 latency | Xms | Xms | +N% | ✓/✗ |
| p99 latency | Xms | Xms | +N% | ✓/✗ |
| Throughput (rps) | X | X | +N% | ✓/✗ |
| Memory (MB) | X | X | +N% | ✓/✗ |

### Regressions Found
[NONE / List regressions]

### Bottlenecks Identified
1. [Bottleneck] — [Evidence] — [Recommended fix]

### Optimizations Applied
1. [Change] — [Before: Xms → After: Xms] — [Commit SHA]

### Verdict
[NO REGRESSION / REGRESSION FIXED / REGRESSION NEEDS ATTENTION]
```

______________________________________________________________________
