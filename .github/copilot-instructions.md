# vstack Copilot Instructions

You are assisting in the development of **vstack**, a VS Code–native AI engineering workflow system inspired by gstack.

## Identity

vstack provides structured skills for backend/microservice development, executable via GitHub Copilot Agent Mode. It exposes 6 fixed roles — product, architect, designer, engineer, tester, release — each backed by hand-authored agent files that invoke skill templates.

## Core Principles

- **Template-driven install model.** Skills are Markdown templates (`src/vstack/_templates/skills/<name>/template.md` — source of truth). Agent config is in `src/vstack/_templates/agents/<name>/config.yaml` + `template.md`. Generated output is produced at install time. In the vstack source repo, do not treat `.github/` artifacts as source of truth and do not edit them directly. In downstream consumer repos that use vstack, installed `.github/` artifacts are effective project configuration and are usually committed.
- **VS Code native.** Skills run in Copilot Chat / Agent Mode. No assumptions about Claude Code or CLI-only flows.
- **Backend first.** Prioritize API correctness, reliability, observability, CI/CD, contracts, performance, and security. Browser automation is optional and pluggable.

## System Structure

```
src/vstack/      ← Python package (source of truth)
src/vstack/_templates/
├── skills/<name>/
│   ├── template.md             ← skill body (edit these)
│   └── config.yaml
├── skills/_partials/           ← shared partial snippets
├── agents/<name>/
│   ├── template.md             ← agent instructions body
│   └── config.yaml             ← agent frontmatter fields
├── instructions/<name>/
│   ├── template.md             ← instruction file body
│   └── config.yaml
└── prompts/<name>/
    ├── template.md             ← prompt file body
    └── config.yaml
docs/            ← architecture.md, design.md, skills.md, workflow.md, roadmap.md, adr/
.github/         ← generated output (never edit directly*)
├── skills/<name>/SKILL.md
├── agents/<name>.agent.md
├── instructions/<name>.instructions.md
├── prompts/<name>.prompt.md
└── vstack.json                 ← install manifest (generated)
```

*Hand-authored exceptions in `.github/`: `copilot-instructions.md`, `CODEOWNERS`,
`pull_request_template.md`, `ISSUE_TEMPLATE/`, `workflows/`.

Generated files are written to `.github/` at install time:

```bash
python3 -m vstack install
```

## In-repo Installation

When vstack is installed inside its own repo (`.github/agents/` and `.github/skills/` exist):

**Source of truth is always in `src/vstack/_templates/`.** After every change:

| What changed | Command to run |
|---|---|
| `src/vstack/_templates/agents/<name>/config.yaml` or `template.md` | `python3 -m vstack install` |
| `src/vstack/_templates/skills/<name>/template.md` or `_partials/*.md` | `python3 -m vstack install` |
| `src/vstack/_templates/instructions/<name>/template.md` | `python3 -m vstack install` |
| `src/vstack/_templates/prompts/<name>/template.md` | `python3 -m vstack install` |

A single command handles all artifact types:

```bash
python3 -m vstack install
```

Never edit `.github/agents/`, `.github/skills/`, `.github/instructions/`, or `.github/prompts/` directly — changes will be overwritten.

## Execution Model

**Option A (current):** Single Copilot context window. A role agent reads the relevant skill and executes in one call.

**Option B (future):** Sequential multi-agent pipeline — `[vision → architecture → verify → release]`. Each stage is a separate model call; output artifacts feed the next stage. Design all config formats and generators to support this with minimal refactoring.

## Verification (Microservices-First)

`verify` and `verify-lite` must cover:

- Unit, integration, and contract tests (OpenAPI / JSON Schema / Protobuf)
- API smoke tests, migrations, retries/backoff, timeouts, circuit breakers
- Observability (logs, metrics, traces, dashboards)
- Security scanning, semver/API compatibility, linting, typechecking, packaging

Browser/E2E steps are optional.

## Documentation Rules

Update docs whenever a change affects system structure, skill definitions, execution flow, or the Option B path.

| Change | File to update |
|--------|---------------|
| High-level structure | `docs/architecture/architecture.md` |
| Generator, loaders, builders | `docs/design/design.md` |
| Execution flow / pipeline | `docs/design/workflow.md` |
| Skill names and behavior | `docs/design/skills.md` |
| Option B milestones | `docs/product/roadmap.md` |
| Any significant decision | `docs/architecture/adr/NNN-<slug>.md` |

Every ADR must include: context, decision, alternatives considered, rationale, and impact on the Option B pipeline.

## Work Style

- Produce small, reviewable changes.
- Always edit `src/vstack/_templates/skills/<name>/template.md`; generate output at install time with `python3 -m vstack install`.
- Default to microservices and libraries unless UI is explicitly present.
- After each change: summary + files changed + how to test.

## Context Exclusions

When searching or reading repository content, ignore generated and third-party directories by default:

- `.venv/`, `venv/`, `env/`
- `node_modules/`
- `__pycache__/`
- `dist/`, `build/`
- `.git/`

Only include these paths when the user explicitly asks to inspect them.

## Safety

Before executing any destructive command (`rm -rf`, `DROP TABLE`, `git push --force`,
`git reset --hard`, `kubectl delete`, production config changes, database migrations):

1. Stop.
2. Explain exactly what will be permanently lost.
3. Ask for explicit confirmation.
4. Only proceed if the user confirms.
5. Never use workarounds to avoid this confirmation.
