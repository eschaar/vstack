<p align="center">
	<img src="https://raw.githubusercontent.com/eschaar/vstack/main/assets/branding/vstack.png" alt="vstack" width="260">
</p>

[![PyPI version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fpypi.org%2Fpypi%2Fvstack%2Fjson&query=%24.info.version&label=PyPI&color=0B8A6F&cacheSeconds=300)](https://pypi.org/project/vstack/)
[![Python version](https://img.shields.io/badge/python-3.11--3.14-0B8A6F)](https://github.com/eschaar/vstack/blob/main/pyproject.toml)
[![Verify status](https://img.shields.io/github/actions/workflow/status/eschaar/vstack/verify.yml?label=verify&color=1D6FA5)](https://github.com/eschaar/vstack/actions/workflows/verify.yml)
[![Security checks](https://img.shields.io/github/actions/workflow/status/eschaar/vstack/security.yml?label=security&color=B15E00)](https://github.com/eschaar/vstack/actions/workflows/security.yml)
[![Runtime: PyYAML](https://img.shields.io/badge/runtime-PyYAML-5B6C8F)](https://github.com/eschaar/vstack/blob/main/pyproject.toml)
[![License: MIT](https://img.shields.io/github/license/eschaar/vstack?color=5F7A1F)](https://github.com/eschaar/vstack/blob/main/LICENSE)
[![GitHub Discussions](https://img.shields.io/badge/discussions-ask%20%26%20share-blueviolet?logo=github)](https://github.com/eschaar/vstack/discussions)

The VS Code-native AI workflow system for backend engineering.

vstack installs structured agents, skills, instructions, and prompts into `.github/` so GitHub Copilot Agent Mode can run repeatable backend workflows with clear role boundaries.

It provides six delivery roles for end-to-end software work: `product`, `architect`, `designer`, `engineer`, `tester`, and `release`, coordinated by `planner`.

## Best for

- Backend and API teams using GitHub Copilot Agent Mode in VS Code
- Repositories that want consistent planning, implementation, verification, and release flow
- Teams that want reusable AI workflows instead of one-off prompt crafting

## What you get

- Fixed role model: six delivery roles plus a planner coordinator
- Template-driven install model from `src/vstack/_templates/`
- Backend-first verification, security, and release discipline
- One runtime dependency: PyYAML

## Building blocks

| Artifact type | Purpose                                                    | Typical invocation     |
| ------------- | ---------------------------------------------------------- | ---------------------- |
| Agents        | Main operating interface for role-based work               | `@product`, `@tester`  |
| Skills        | Reusable task procedures                                   | `/verify`, `/security` |
| Instructions  | Baseline policy and repository guardrails                  | auto-loaded by context |
| Prompts       | Reusable prompt artifacts where direct prompting is useful | explicit prompt use    |

## Prompt catalog

Prompts are `.prompt.md` files installed to `.github/prompts/`. Invoke them via the
VS Code command palette (`Chat: Run Prompt File`) or the Copilot Chat attach button.

| Prompt              | Purpose                                                   |
| ------------------- | --------------------------------------------------------- |
| `api-design-review` | Review an API design or OpenAPI spec for correctness      |
| `architecture-risk` | Identify architectural risks and mitigation priorities    |
| `code-review`       | Review a change for bugs, regressions, and missing tests  |
| `dependency-audit`  | Audit dependencies for vulnerabilities and licence risks  |
| `incident-timeline` | Build an evidence-based incident timeline and post-mortem |
| `migration-safety`  | Review DB migration safety, rollback, and zero-downtime   |
| `release-readiness` | Evaluate release readiness from reports and open blockers |

## Quickstart — fresh install

Install with `pipx`, then install vstack artifacts into your repository:

```bash
# Install the CLI once, globally
pipx install vstack

# Move to your repository root and run install — no --target needed
cd /path/to/your/project
vstack install        # seeds .vstack/config.yaml and generates .github/ in the current directory
vstack validate       # confirm no errors
```

When you omit `--target`, vstack uses the current working directory. The equivalent
explicit form is `vstack install --target /path/to/your/project`.

Run a first task in Copilot Agent Mode:

```text
@tester /verify Check this repository and summarize findings
```

Expected result:

- `vstack validate` reports no unresolved template tokens
- Agent command returns a concrete verification summary for your repository

## Quick upgrade

### Patch or minor version (e.g. v3.1 → v3.2, same major)

Docs paths never change within a major version. Only `.github/` artifacts are updated.

```bash
pipx upgrade vstack

cd /path/to/your/project
vstack init           # idempotent — safe to run in CI
```

### Major version (e.g. v2 → v3)

Docs paths may change on a major version bump. Run `vstack migrate` before `vstack init`.

```bash
pipx upgrade vstack

cd /path/to/your/project
vstack migrate        # moves docs files to their new paths (auto-detects installed version)
vstack init           # regenerates .github/ artifacts

# Only if you see "Legacy manifest schema detected" in the output above:
vstack manifest upgrade
vstack init
```

Preview the docs moves without touching any files:

```bash
vstack migrate --dry-run
```

For upgrades spanning multiple major versions (e.g. v1 → v3), `vstack migrate` chains
all intermediate steps automatically. Use `--from` and `--to` to specify the range
explicitly if auto-detection from the manifest fails:

```bash
vstack migrate --from 1 --to 3
vstack init
```

### Force reinstall (overwrite local edits)

```bash
vstack install --force                       # overwrite all managed artifacts
vstack install --force-name agent/engineer   # overwrite one specific artifact
```

## Why this helps

- Consistent role boundaries for planning, implementation, validation, and release
- Reusable skills and instructions instead of ad hoc prompts
- Better release hygiene with documented workflows and CI alignment

## Core commands

```bash
vstack --version
vstack validate

# Run from your repository root (--target defaults to the current directory)
vstack install
vstack init
vstack migrate
vstack manifest verify
vstack manifest status
vstack manifest upgrade

# Or specify a path explicitly
vstack install --target /path/to/your/project
```

## Common usage patterns

Repository-scoped install (recommended for teams):

```bash
# Move to your repository root and install there
cd /path/to/your/project
vstack install

# Or specify a path explicitly from any directory
vstack install --target /path/to/your/project
```

Profile-wide install (optional defaults for all projects):

```bash
vstack install --global
```

`vstack install` is the first-run command: it seeds `.vstack/config.yaml` in your project (never overwrites), then generates `.github/` artifacts from templates. `vstack init` re-runs generation idempotently — safe to use in CI after upgrading vstack.

By default, `vstack install` preserves existing unmanaged files and local edits to tracked files by comparing the current file contents with the SHA-256 checksum recorded in `.vstack/vstack.json`. Use `--adopt-name <name>` to start tracking one existing unmanaged file without overwriting it. `vstack uninstall` also preserves locally modified tracked files unless you explicitly pass `--force` or `--force-name <name>`. Use `vstack manifest status --target ...` (or `vstack status --target ...`) to see what still matches the manifest. If a legacy manifest schema is detected, run `vstack manifest upgrade --target ...` first.

To skip artifact types or individual artifacts you do not need, edit `.vstack/config.yaml`:

```yaml
exclude:
  skills:
    - terraform
    - helm
  instructions: all   # skip the entire type
```

If you already have agents, skills, or other files in `.github/`, run a dry-run first to see what would be preserved before committing:

```bash
# Run from your repository root
vstack install --dry-run
```

The summary lists preserved files as `type/name` selectors (e.g. `agent/engineer`). Resolve each conflict with `--force-name type/name` to overwrite, `--adopt-name type/name` to take ownership without overwriting, or `--force` to overwrite everything.

## Reading `.vstack/config.yaml`

- Lines starting with `#` are comments, explanation, or example configuration and are not active.
- Only uncommented YAML keys are active configuration.
- To enable an example block, remove `#` from that block and keep valid YAML indentation.
- After any config change, run `vstack init` to apply it to generated `.github/` artifacts.

## Workflow modes

vstack supports three workflow modes via `.vstack/config.yaml`:

```yaml
workflow:
  mode: agentic  # default
```

After changing `workflow.mode`, regenerate artifacts:

```bash
vstack init
```

| Mode      | Behavior                                                     | Planner file  | Worker handoff buttons |
| --------- | ------------------------------------------------------------ | ------------- | ---------------------- |
| `agentic` | Planner orchestrates stage progression using subagents       | generated     | omitted                |
| `manual`  | User progresses stage-by-stage manually                      | not generated | shown                  |
| `hybrid`  | Both planner orchestration and manual handoffs are available | generated     | shown                  |

Execution semantics:

- `workflow.stages` order is the canonical progression order.
- `agentic` is stage-sequential by default: planner advances one stage at a time in configured order.
- Parallelization is still possible inside a stage (independent subtasks), but cross-stage progression remains ordered.

Handoff target semantics:

- `handoffs.prompt` is the transition prompt text.
- If `handoffs.agent` is omitted, the target defaults to the next role in `workflow.stages`.
- You can set `handoffs.agent` explicitly to override that default target in `manual`/`hybrid`.
- In `agentic`, worker handoff buttons are hidden; planner controls progression.

Mode quickstart in Copilot Agent Mode:

| Mode      | Start here               | First prompt example                                    |
| --------- | ------------------------ | ------------------------------------------------------- |
| `agentic` | `@planner`               | `@planner Run the workflow for this repository change.` |
| `manual`  | `@product`               | `@product Define requirements for this change.`         |
| `hybrid`  | `@planner` or `@product` | `@planner Run the workflow for this repository change.` |

Usage guidance:

- Use `agentic` when you want one deterministic orchestration path.
- Use `manual` when your team prefers explicit user-controlled stage transitions.
- Use `hybrid` only when your team intentionally wants both options.

Hybrid operating rule:

- Choose one path per session (planner-led or manual handoffs) and stay on it.
- Mixing both paths in one session increases the chance of duplicate stage transitions.

Hybrid warning:

- In `hybrid`, users can click handoff buttons while a planner-led flow is also available.
- This can cause unintended progression jumps or duplicated transitions if your process assumes one strict path.

## Fast troubleshooting

- Command not found after install: ensure your `pipx` binary path is in `PATH`
- Validation error: rerun `vstack install` from your repository root and then `vstack validate`
- Agent results look generic: explicitly invoke a role (for example `@tester`) before a skill

## Full documentation

For complete documentation (including architecture details, workflow diagrams, and contributor guides), use GitHub:

- [GitHub repository](https://github.com/eschaar/vstack)
- [Full README](https://github.com/eschaar/vstack/blob/main/README.md)
- [Documentation](https://github.com/eschaar/vstack/tree/main/docs)
- [Contributing guide](https://github.com/eschaar/vstack/blob/main/CONTRIBUTING.md)
- [Security policy](https://github.com/eschaar/vstack/blob/main/SECURITY.md)
