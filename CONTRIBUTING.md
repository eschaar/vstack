# Contributing

Thanks for your interest in contributing to vstack.

## Prerequisites

- Python 3.11-3.14
- Virtual environment enabled

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
```

## Development Workflow

1. Create a branch from `main`.
1. Make focused, reviewable changes.
1. Run checks locally:

```bash
make test
```

1. Open a pull request with clear context.

## Commit Message Guidance

This repository uses a Conventional Commits baseline for release automation.

### 1) Message format

```text
type(optional-scope)!: short summary
```

- `type`: what kind of change you made.
- `scope` (optional): where the change happened.
- `!`: marks a breaking change.

### 2) Version bump rules

- `major`: any commit with `!` in the header or a `BREAKING CHANGE:` footer.
- `minor`: `feat`, `feature`.
- `patch`: `fix`, `bugfix`, `hotfix`, `opt`, `patch`, `perf`, `refactor`, `chore`, `revert`.

### 3) Allowed types

- `feat`, `feature`: new behavior or capabilities.
- `fix`, `bugfix`: bug correction.
- `hotfix`: urgent production fix.
- `opt`: small, practical optimization.
- `patch`: small maintenance fix that should still trigger a patch release.
- `perf`: measurable performance improvement.
- `refactor`: structural cleanup without intended behavior change.
- `chore`: repository maintenance and non-feature housekeeping.
- `revert`: rollback of a previous commit.

### 4) Suggested scopes (optional)

- Domain and backend areas: `api`, `auth`, `permissions`, `serializer`, `viewset`, `orm`, `migrations`, `admin`, `settings`.
- Tooling and workflow areas: `deps`, `ci`, `docs`, `build`, `style`, `release`, `workflow`.
- Quality and test areas: `test`, `tests`.
- Project modules: `cli`, `agents`, `skills`, `instructions`, `prompts`, `frontmatter`, `artifacts`.

### 5) Examples

- `feat(cli): add --global verify mode`
- `fix(auth): handle missing token header`
- `hotfix(ci): handle broken tag push race`
- `opt(serializer): simplify optional-field validation path`
- `patch(docs): clarify release gating`
- `perf(orm): reduce query count in list endpoint`
- `refactor(artifacts)!: drop legacy manifest key`

### 6) Subject length

- Commit subject lines are limited to 100 characters by CI.

### 7) Branch naming

Branch names are validated in CI using Conventional Branch format:

```text
type/short-description
```

Allowed branch types:

- `feature`, `bugfix`, `hotfix`, `release`, `chore`, `feat`, `fix`
- `docs`, `refactor`, `perf`, `test`, `ci`, `build`, `style`
- `opt`, `patch`, `dependabot`

A dedicated CI workflow validates commit messages on branch pushes and PRs using commit-check with policy from `cchk.toml`.
Scope names are guidance-level in this document and are not currently hard-enforced by CI.

## Pull Request Expectations

- Keep PRs small when possible.
- Include tests for behavior changes.
- Update docs when behavior changes.
- Link related issues.

## Security

Please do not report security issues in public issues.
Use the process in `SECURITY.md`.

## Repository Settings Checklist (Maintainers)

Keep these GitHub settings aligned with the CI/CD design in `docs/design/cicd.md`.

1. Ruleset on `main` (Settings → Rules → Rulesets):
   - require pull request before merging
   - required approvals: at least 1
   - require status checks: `Commit`, `Check`, `Verify`, and `Security`
   - allowed merge methods: include **Squash** (required by `automerge.yml`)
   - restrict force pushes
1. Actions permissions (Settings → Actions → General):
   - allow GitHub Actions to create pull requests
   - allow GitHub Actions to approve pull requests
1. Auto-merge (Settings → General):
   - enabled at repository level (required for Dependabot auto-merge path)
1. PyPI environment (Settings → Environments):
   - `pypi` environment exists
   - OIDC trusted publishing configured
   - any required reviewer policy matches release expectations
