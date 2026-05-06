# ADR-021: Config-Driven Artifact Paths in Agent Config

> Maintained by: **architect** role

**date:** 2026-05-03\
**status:** accepted

## context

Each vstack agent role owns a well-defined set of documentation artifacts. These
paths — `docs/architecture/overview.md`, `docs/product/vision.md`, and so on —
were previously documented only in agent `template.md` bodies and in
`docs/design/agents.md`. They existed in two places in prose form: the agent
instructions and the design documentation.

This created two problems:

1. **No machine-readable source of truth.** Tooling, validators, and future
   orchestrated pipeline stages (ADR-004) had no structured way to discover which
   agent produces or consumes which paths without parsing Markdown.

1. **Drift risk.** When an artifact path changes, the update had to be applied
   independently to the template body, the design docs, and any tooling that
   relied on the path. There was no single authoritative record.

The manifest schema (ADR-014) tracks which files were installed; it does not
describe which files an agent conceptually owns. A separate schema field is
needed to capture ownership at the agent config level.

## decision

Agent `config.yaml` files gain an optional `artifacts:` block:

```yaml
artifacts:
  dir: architecture              # subdirectory within the global docs root (no root prefix)
  input:                         # paths this agent reads as context
    - product/**/*.md
  output:                        # files this agent produces
    - overview.md                # string: resolved as <docs_root>/<dir>/<path>
    - path: ux.md                # dict: allows an optional notes annotation
      notes: frontend/fullstack scope only
    - path: ./src/**/*           # ./ prefix: verbatim path, dir prefix not applied
```

Rules:

- `dir` is the subdirectory within the global `ARTIFACTS_DOCS_ROOT` (`docs`) that
  this agent writes to. It is a subdirectory name only — no root prefix. Required
  when `output` items are relative paths without a `./` prefix; optional otherwise.
- `input` is a list of glob patterns for files this agent reads. Paths are resolved
  as `<ARTIFACTS_DOCS_ROOT>/<item>` (e.g. `product/**/*.md` → `docs/product/**/*.md`).
- `output` is a list of items, each either a plain string or a dict with `path` and
  an optional `notes` field. Path resolution:
  - No `./` prefix, `dir` set → `<ARTIFACTS_DOCS_ROOT>/<dir>/<path>`
  - No `./` prefix, no `dir` → `<path>` verbatim
  - `./` prefix → strip `./`, use remainder verbatim (`./src/**/*` → `src/**/*`)
- `ARTIFACTS_DOCS_ROOT` is a global constant (`src/vstack/constants.py`, default
  `docs`). It is applied at render time. Individual agents must not embed the root
  prefix; only the subdirectory is set in `dir`.
- The `artifacts:` block is **vstack-internal only** — it is not emitted to the
  generated `.agent.md` frontmatter.
- At install time, `AgentGenerator` resolves the block into four placeholder tokens
  (`{{AGENT_ARTIFACTS_INPUT}}`, `{{AGENT_ARTIFACTS_OUTPUT}}`,
  `{{AGENT_ARTIFACTS_INPUT_COMMENTS}}`, `{{AGENT_ARTIFACTS_OUTPUT_COMMENTS}}`)
  that are substituted into the template body.

### per-role values

| Agent       | dir            | input                                                       | output                                                                                            |
| ----------- | -------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `product`   | `product`      | —                                                           | `vision.md`, `requirements.md`, `roadmap.md`, `changes/*.md`, `issues/*.md`                       |
| `architect` | `architecture` | `product/**/*.md`                                           | `overview.md`, `adr/*.md`                                                                         |
| `designer`  | `design`       | `architecture/**/*.md`                                      | `overview.md`, `ux.md` *(frontend/fullstack)*, `**/*.md` *(when scope warrants)*                  |
| `engineer`  | —              | `product/**/*.md`, `architecture/**/*.md`, `design/**/*.md` | `./src/**/*`, `./tests/**/*`, `./issues/{id}-{slug}-rca.md`, `./issues/{id}-{slug}-postmortem.md` |
| `tester`    | `reports`      | `architecture/**/*.md`, `design/**/*.md`                    | `**/*.md`, `./tests/**/*`                                                                         |
| `release`   | `releases`     | `**/*.md`                                                   | `*.md` *(release notes and sign-off record)*                                                      |

`engineer` has no `dir` because its outputs are code files under `src/` and
`tests/`, addressed with `./` verbatim paths rather than documentation
subdirectories.

## alternatives considered

### 1. Encode paths only in template bodies

Paths remain in `template.md` prose. No schema change required.

Rejected: paths stay human-only, untestable, and invisible to any future
automation or orchestrated pipeline tooling.

### 2. Separate paths manifest file

A standalone `paths.yaml` or `artifact-registry.yaml` at the repo root lists all
role-to-path mappings.

Rejected: splits ownership away from the agent config. A single `config.yaml`
per agent keeps all agent-level facts co-located.

### 3. Embed paths in the generated `.agent.md` frontmatter

Emit `artifacts:` into the VS Code agent file.

Rejected: VS Code does not define `artifacts:` as a supported frontmatter field.
Emitting unknown fields risks warnings or future parse errors. This schema is
vstack-internal.

## rationale

Placing `artifacts:` in `config.yaml` is consistent with the existing pattern:
`version`, `handoffs`, and other vstack-internal fields already live in
`config.yaml` without being emitted. The field is co-located with the agent it
describes, machine-readable, and immediately useful for orchestrated pipeline validation without requiring a separate registry file.

## impact on orchestrated pipeline

ADR-004 describes a future sequential multi-agent pipeline where each stage's
output feeds the next. The `artifacts:` schema directly enables this:

- A pipeline orchestrator can read `input` to know what context to inject.
- It can read `output` to know which files to collect and pass to the next stage.
- `dir` and `ARTIFACTS_DOCS_ROOT` together provide the base path for file
  resolution without parsing agent prose.

No changes to the orchestrated pipeline design are needed; this ADR makes `config.yaml` the
structured input source that orchestrated pipeline tooling will consume.
