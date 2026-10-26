---
name: performance
description: 'Performance profiling and regression detection. Establishes baselines, detects regressions, profiles bottlenecks, and recommends optimizations. Use when asked to "profile", "benchmark", "performance test", or "is this faster?".'
license: 'MIT'
compatibility: 'Requires a skills-compatible agent with repository file access and terminal command execution when needed.'
metadata:
  owner: vstack
  maturity: stable
allowed-tools: 'execute read search edit'
argument-hint: '[endpoint or function to profile]'
user-invocable: true
disable-model-invocation: false
---
## Skill Context

This skill is part of **vstack** — a VS Code-native AI engineering workflow system.

### AskUserQuestion Format

When you need clarification, use this exact format — never invent or guess:

> **Question:** [The specific question]
> **Options:** A) … | B) … | C) …
> **Default if no response:** [What you'll do]

Never ask more than one question at a time without waiting for the answer.

### Diagram Convention

When producing hand-authored Markdown outputs, prefer Mermaid for flow,
interaction, lifecycle, state, topology, dependency, and decision diagrams when
the format is supported and improves clarity. Use ASCII as a fallback when
Mermaid is unsupported or would be less readable. Keep ASCII/text trees for
directory structures and other scan-friendly hierarchies.

```bash
# Detect base branch (main / master / develop / trunk)
BASE=$(gh pr view --json baseRefName -q .baseRefName 2>/dev/null) \
  || BASE=$(git remote show origin 2>/dev/null | grep 'HEAD branch' | awk '{print $NF}') \
  || BASE=$(git branch -r 2>/dev/null | grep -E '/(main|master|develop|trunk)' | head -1 | sed 's|.*origin/||') \
  || BASE="main"
echo "Base branch: $BASE"
```

# performance — Profile, Benchmark & Regression Detection

Profile backend services, detect performance regressions, and recommend
optimizations. Measure first; never optimize without evidence.

## Out of scope

- Full code review (use `code-review`)
- Security analysis (use `security`)
- Architecture design (use `architecture`)
- Non-performance bug fixing (use `debug`)

## Deliverable and artifact policy

- Primary deliverable: `docs/reports/performance-baseline.md`
- Baseline-first default: write benchmark outcomes and regression verdicts directly to `docs/reports/performance-baseline.md` on the feature branch.
- Before merge: consolidate thresholds, measurements, and recommendations into the baseline performance report.

## Setup

**Parse the user's request:**

| Parameter | Default                     | Override                                 |
| --------- | --------------------------- | ---------------------------------------- |
| Target    | Whole service / entry point | `Focus on the /search endpoint`          |
| Mode      | Comparison (vs base branch) | `--baseline`, `--profile`, `--load-test` |
| Threshold | 5% regression               | `--threshold 0.10` (10%)                 |

## Phase 1: Establish Baseline

If on a feature branch, record performance metrics before and after the change:

Inspect repository scripts and installed tooling first. Adapt `run_benchmark` to
one existing benchmark runner and the selected interpreter/package manager.
For monorepos, select the component explicitly. Do not install tools or fall back
to another ecosystem when a command fails. Ordinary tests are not benchmarks.

```bash
run_benchmark() {
  if [ -f package.json ]; then
    npm run bench
  elif [ -f pyproject.toml ] || [ -f setup.py ]; then
    python -m pytest --benchmark-only -v
  elif [ -f go.mod ]; then
    go test -bench=. -benchmem ./...
  elif [ -f Cargo.toml ]; then
    cargo bench
  else
    echo "ERROR: no benchmark runner configured for this component"
    return 2
  fi
}
run_benchmark || exit $?
```

Record command, revision, workload, measurements, and exit status.
Unavailable tools or missing benchmark configuration mean `not run`, not a pass;
executed checks with nonzero exit status are `failed`. Keep error output visible.

## Phase 2: Comparison vs Base Branch

```bash
BASE_REF="<base>"
COMPONENT_DIR=$(git rev-parse --show-prefix) || exit $?
BASE_DIR=$(mktemp -d) || exit 1
git worktree add --detach "$BASE_DIR/baseline" "$BASE_REF" || exit 1
(
  cd "$BASE_DIR/baseline/$COMPONENT_DIR" || exit 1
  run_benchmark
)
BASE_STATUS=$?
git worktree remove "$BASE_DIR/baseline" || exit 1
rmdir "$BASE_DIR" || exit 1
if [ "$BASE_STATUS" -ne 0 ]; then
  echo "ERROR: baseline benchmark failed ($BASE_STATUS)"
  exit "$BASE_STATUS"
fi
```

Use an isolated worktree; never stash or switch the user's working tree.
Start Phase 2 in the same component directory as Phase 1; preserve its
repository-relative path and use the same `run_benchmark` command.
If the component does not exist at the base revision, report comparison unavailable;
never substitute a root-level benchmark.
If benchmarks leave files behind, report the worktree path and inspect them
before cleanup. Do not force-remove it or discard user files.

Compare results:

- p50 latency change
- p95/p99 latency change
- Throughput (ops/second) change
- Memory allocation change
- CPU usage change

**Regression threshold:** Flag if any metric degrades by more than 5% (or configured threshold).

## Phase 3: Load Testing (if applicable)

```bash
# Check for load test tools
command -v k6
command -v hey
command -v wrk
command -v ab

# Example k6 run (adapt to your endpoint)
# k6 run --vus 50 --duration 30s script.js
```

For API endpoints, choose one installed load-test tool and an approved target.
Do not generate load against production without explicit permission.

```bash
hey -n 1000 -c 50 "${SERVICE_URL}/health"
```

Or, when `wrk` is the selected installed tool:

```bash
wrk -t4 -c100 -d30s "${SERVICE_URL}/health"
```

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
[NO REGRESSION / REGRESSION FIXED / REGRESSION NEEDS ATTENTION / NOT RUN / CHECK FAILED]
Only measured, comparable results support a regression verdict.
```

<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->
<!-- VSTACK-META: {"artifact_name":"performance","artifact_type":"skill","artifact_version":"20261026004","generator":"vstack","vstack_version":"4.0.0"} -->
