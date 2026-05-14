Triage CI failures into root-cause clusters and prioritize the fastest safe recovery path.

Use failing job logs, workflow config, and changed files.

Output exactly in this format:

## Failure Clusters

For each cluster:

- jobs affected
- probable root cause
- confidence: HIGH | MEDIUM | LOW

## Priority Fix Order

Ordered by unblock value.

- fix action
- expected unblocked jobs
- owner role

## Risk Notes

- risky quick fixes to avoid
- possible hidden regressions

## Recovery Checklist

- [ ] apply highest-priority fix
- [ ] rerun targeted jobs
- [ ] rerun full workflow
- [ ] confirm no new failures
