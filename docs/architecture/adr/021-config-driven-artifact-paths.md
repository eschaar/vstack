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
   pipeline stages (ADR-004, Option B) had no structured way to discover which
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
  target: docs/architecture          # directory this agent writes to
  input:                             # paths this agent reads as context
    - docs/product/*.md
  output:                            # files this agent produces within target
    - overview.md
    - adr/*.md
```

Rules:

- `target` is the canonical root directory this agent writes to. Required when
  `output` is present; optional otherwise.
- `input` is a list of glob patterns for files this agent reads. Optional.
- `output` is a list of paths relative to `target`. Optional.
- All paths use forward slashes and are relative to the repository root
  (`target`) or to `target` (`output`).
- The `artifacts:` block is **vstack-internal only** — it is not emitted to
  the generated `.agent.md` frontmatter.

### per-role values

| Agent       | target              | input                                                                      | output                                                            |
| ----------- | ------------------- | -------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| `product`   | `docs/product`      | —                                                                          | `vision.md`, `requirements.md`, `roadmap.md`                      |
| `architect` | `docs/architecture` | `docs/product/**/*.md`                                                     | `overview.md`, `adr/*.md`                                         |
| `designer`  | `docs/design`       | `docs/architecture/**/*.md`                                                | `overview.md`                                                     |
| `engineer`  | `issues`            | `docs/product/**/*.md`, `docs/architecture/**/*.md`, `docs/design/**/*.md` | —                                                                 |
| `tester`    | `docs/reports`      | `docs/architecture/**/*.md`, `docs/design/**/*.md`                         | `test-report.md`, `security-report.md`, `performance-baseline.md` |
| `release`   | `docs/releases`     | `docs/**/*.md`                                                             | `*.md`                                                            |

`engineer` has no `output` entries because it writes code, not documentation
artifacts. Its `input` captures what it reads to perform work.

## alternatives considered

### 1. Encode paths only in template bodies

Paths remain in `template.md` prose. No schema change required.

Rejected: paths stay human-only, untestable, and invisible to any future
automation or Option B pipeline tooling.

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
describes, machine-readable, and immediately useful for future Option B pipeline
validation without requiring a separate registry file.

## impact on Option B pipeline

ADR-004 describes a future sequential multi-agent pipeline where each stage's
output feeds the next. The `artifacts:` schema directly enables this:

- A pipeline orchestrator can read `input` to know what context to inject.
- It can read `output` to know which files to collect and pass to the next stage.
- `target` provides the base path for file resolution without parsing agent prose.

No changes to Option B design are needed; this ADR makes `config.yaml` the
structured input source that Option B pipeline tooling will consume.
