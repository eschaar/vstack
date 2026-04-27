# GitHub Workflows

This folder contains repository automation workflows.

For the full CI/CD design and release model, see `docs/design/cicd.md`.

## Quick Map

| Workflow | Trigger | Purpose |
| --- | --- | --- |
| `commit.yml` | push to non-main branches and PRs to `main` | Commit policy and lint/typecheck (branch-name policy on push) |
| `check.yml` | push to non-main branches and PRs to `main` | Single-version unit test feedback (py3.11) |
| `verify.yml` | pull_request to `main` | Required verification checks: cross-version test matrix + artifact verify |
| `security.yml` | pull_request to `main` | Required security checks |
| `automerge.yml` | pull_request_target to `main` | Dependabot safe auto-merge policy |
| `release.yml` | push to `main` | Release Please orchestration |
| `publish.yml` | release published | Build and publish to PyPI |

## Operational Notes

1. `commit.yml` handles commit policy and lint/typecheck on branch pushes and PRs.
2. `check.yml` provides single-version test feedback on branch pushes and PRs.
3. `verify.yml` and `security.yml` are the required PR gates.
4. `release.yml` is the only release orchestrator.
5. `publish.yml` is publish-only and never computes versions.
6. Ruleset on `main` should require `Commit`, `Check`, `Verify` (all jobs), and `Security` before merge.
