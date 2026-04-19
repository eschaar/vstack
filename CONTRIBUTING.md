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

This repository uses semantic commit prefixes for releases.

- `feat:` for new functionality
- `fix:` for bug fixes
- `chore:` for maintenance
- `docs:` for documentation only changes

Use `BREAKING CHANGE` in the commit body when applicable.

## Pull Request Expectations

- Keep PRs small when possible.
- Include tests for behavior changes.
- Update docs when behavior changes.
- Link related issues.

## Security

Please do not report security issues in public issues.
Use the process in `SECURITY.md`.
