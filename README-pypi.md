<p align="center">
	<img src="https://raw.githubusercontent.com/eschaar/vstack/main/assets/branding/vstack.png" alt="vstack" width="260">
</p>

[![PyPI version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fpypi.org%2Fpypi%2Fvstack%2Fjson&query=%24.info.version&label=PyPI&color=0B8A6F&cacheSeconds=300)](https://pypi.org/project/vstack/)
[![Python version](https://img.shields.io/badge/python-3.11--3.14-0B8A6F)](https://github.com/eschaar/vstack/blob/main/pyproject.toml)
[![Verify status](https://img.shields.io/github/actions/workflow/status/eschaar/vstack/verify.yml?label=verify&color=1D6FA5)](https://github.com/eschaar/vstack/actions/workflows/verify.yml)
[![Security checks](https://img.shields.io/github/actions/workflow/status/eschaar/vstack/security.yml?label=security&color=B15E00)](https://github.com/eschaar/vstack/actions/workflows/security.yml)
[![Runtime: stdlib only](https://img.shields.io/badge/runtime-stdlib%20only-5B6C8F)](https://github.com/eschaar/vstack/blob/main/pyproject.toml)
[![License: MIT](https://img.shields.io/github/license/eschaar/vstack?color=5F7A1F)](https://github.com/eschaar/vstack/blob/main/LICENSE)
[![GitHub Discussions](https://img.shields.io/badge/discussions-ask%20%26%20share-blueviolet?logo=github)](https://github.com/eschaar/vstack/discussions)

The VS Code-native AI workflow system for backend engineering.

vstack installs structured agents, skills, instructions, and prompts into `.github/` so GitHub Copilot Agent Mode can run repeatable backend workflows with clear role boundaries.

It provides a fixed role model for end-to-end software delivery: `product`, `architect`, `designer`, `engineer`, `tester`, and `release`.

## Best for

- Backend and API teams using GitHub Copilot Agent Mode in VS Code
- Repositories that want consistent planning, implementation, verification, and release flow
- Teams that want reusable AI workflows instead of one-off prompt crafting

## What you get

- Fixed role model: `product`, `architect`, `designer`, `engineer`, `tester`, `release`
- Template-driven install model from `src/vstack/_templates/`
- Backend-first verification, security, and release discipline
- Standard-library-only runtime dependencies

## Quick start

Install with `pipx`, then install vstack artifacts into your repository:

```bash
pipx install vstack
vstack install --target /path/to/your/project
vstack validate
```

Run a first task in Copilot Agent Mode:

```text
@tester /verify Check this repository and summarize findings
```

Expected result:

- `vstack validate` reports no unresolved template tokens
- Agent command returns a concrete verification summary for your repository

## Why this helps

- Consistent role boundaries for planning, implementation, validation, and release
- Reusable skills and instructions instead of ad hoc prompts
- Better release hygiene with documented workflows and CI alignment

## Core commands

```bash
vstack --version
vstack validate
vstack install --target /path/to/your/project
vstack manifest verify --target /path/to/your/project
vstack manifest status --target /path/to/your/project
vstack manifest upgrade --target /path/to/your/project
```

## Common usage patterns

Repository-scoped install (recommended for teams):

```bash
vstack install --target /path/to/your/project
```

Profile-wide install (optional defaults for all projects):

```bash
vstack install --global
```

By default, `vstack install` preserves existing unmanaged files and local edits to tracked files by comparing the current file contents with the SHA-256 checksum recorded in `vstack.json`. Use `--adopt-name <artifact-name>` to start tracking one existing unmanaged file without overwriting it. `vstack uninstall` also preserves locally modified tracked files unless you explicitly pass `--force` or `--force-name <artifact-name>`. Use `vstack manifest status --target ...` (or `vstack status --target ...`) to see what still matches the manifest. If a legacy manifest schema is detected, run `vstack manifest upgrade --target ...` first.

## Fast troubleshooting

- Command not found after install: ensure your `pipx` binary path is in `PATH`
- Validation error: rerun `vstack install --target ...` and then `vstack validate`
- Agent results look generic: explicitly invoke a role (for example `@tester`) before a skill

## Full documentation

For complete documentation (including architecture details, workflow diagrams, and contributor guides), use GitHub:

- [GitHub repository](https://github.com/eschaar/vstack)
- [Full README](https://github.com/eschaar/vstack/blob/main/README.md)
- [Documentation](https://github.com/eschaar/vstack/tree/main/docs)
- [Contributing guide](https://github.com/eschaar/vstack/blob/main/CONTRIBUTING.md)
- [Security policy](https://github.com/eschaar/vstack/blob/main/SECURITY.md)
