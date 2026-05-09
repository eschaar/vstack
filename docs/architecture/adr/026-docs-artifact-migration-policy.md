# ADR-026: Docs Artifact Path Stability and Migration Policy

> Maintained by: **architect** role

**date:** 2026-05-09\
**status:** accepted\
**depends on:** ADR-014 (manifest schema versioning), ADR-019 (vstack project directory), ADR-021 (config-driven artifact paths)

## context

vstack manages two distinct classes of output artifacts:

1. **`.github/` artifacts** — skills, agents, instructions, and prompts generated
   from templates. These paths are constrained by VS Code and GitHub Copilot conventions
   (e.g. `.github/skills/<name>/SKILL.md`). They are tracked in the manifest
   (`.vstack/vstack.json`) with checksums and can be upgraded, reinstalled, or removed
   via CLI commands. Path changes here are infrequent and externally motivated.

1. **`docs/` artifacts** — living documentation produced and maintained by agent roles
   (architect, designer, product, tester, release). Examples: `docs/architecture/overview.md`,
   `docs/product/requirements.md`, `docs/reports/security-report.md`. These are **not**
   tracked in the manifest; they are owned and continuously updated by agents as project
   outputs, not by vstack as generated files.

ADR-021 established that agent `config.yaml` files are the machine-readable source of truth
for which paths each agent writes to (`artifacts.dir`, `artifacts.output`). Skill template
prose duplicates these paths as LLM guidance (e.g. "write to `docs/architecture/overview.md`")
— this is intentional, acceptable duplication. The prose is informational; the config is
authoritative.

### The migration problem

When `docs/` paths change across vstack versions (e.g. a subdirectory is renamed or a file
moves), no automated mechanism exists to relocate the files. Because they are untracked,
`vstack status` does not report them as stale. Because they are agent-owned content, not
generated content, a simple reinstall does not help. The user is left with orphaned files
at old paths and agents writing to new paths, resulting in divergent documentation.

Two related questions arise:

- **When may docs paths change?** What stability commitment do consumers of vstack receive?
- **When they do change, what is the upgrade path?** How does a user migrate their
  existing files?

## decision

### 1. Path stability commitment

Docs artifact paths — the `artifacts.dir` value and the glob patterns in `artifacts.output`
for each agent — are **stable within a minor version** and **may break only on a major version
boundary** (semver major bump, e.g. v2→v3, v3→v4).

This commitment applies to:

- Agent `config.yaml` `artifacts.dir` values
- Agent `config.yaml` `artifacts.output` paths
- Skill template prose references to the same paths (kept in sync as a consequence)

It does **not** apply to:

- `.github/` artifact paths, which follow VS Code / Copilot conventions (covered by ADR-002)
- Project-specific paths the user configures via `artifacts.root` or workflow overrides

### 2. Agent config.yaml is the source of truth; skill prose is informational

Skill templates reference docs paths in their markdown bodies (e.g. "Primary deliverable:
`docs/architecture/overview.md`"). This duplication is accepted as a usability aid for LLM
agents. It is not a second source of truth. When a path changes:

- Update `artifacts.dir` / `artifacts.output` in the relevant agent `config.yaml` — this is
  the authoritative change.
- Update all skill template prose references to the same paths for consistency.
- Never change skill prose without also updating the corresponding agent config.

### 3. Manifest upgrade handles `.github/` relocations; `vstack migrate` handles `docs/`

Two migration mechanisms exist, each scoped to its artifact class:

| Artifact class                                             | Location tracked      | Migration command            |
| ---------------------------------------------------------- | --------------------- | ---------------------------- |
| `.github/` (skills, agents, instructions, prompts)         | `.vstack/vstack.json` | `vstack manifest upgrade`    |
| `docs/` (architecture, design, product, reports, releases) | Not tracked           | `vstack migrate` (see below) |

`vstack manifest upgrade` already handles schema migrations and file relocation for `.github/`
artifacts (ADR-017). Docs artifact migration is a separate concern with a separate command.

### 4. `vstack migrate` — deferred implementation, defined convention now

The `vstack migrate` command is **not implemented** in this decision. The convention for
how it will work is defined here so that migration records can be authored now and executed
when the command ships.

Migration records live in `src/vstack/_migrations/` within the package source. Each file
covers one major version transition:

```
src/vstack/_migrations/
└── v3_to_v4.yaml          # applied when upgrading from any 3.x to 4.x
```

A migration record lists path moves by artifact class:

```yaml
from_version: "3.x"
to_version: "4.0"
moves:
  - old: docs/reports/security-report.md
    new: docs/security/security-report.md
    type: docs
    notes: >
      tester role artifact dir changed from reports/ to security/ to align
      with expanded scope. Files at the old path are safe to remove after
      migration.
```

When `vstack migrate` ships, it will:

1. Read the applicable migration record for the installed-to-installed version range.
1. For each `type: docs` move: check if the old path exists; if so, move it to the
   new path (creating parent directories as needed), and report what was moved.
1. Print a summary and exit non-zero if any move failed.
1. Support `--dry-run` to preview moves without writing.

Until the command ships, the migration record files serve as the canonical reference for
what a user must do manually when upgrading across major versions. `CHANGELOG.md` entries
for major releases must include a "Migration" section that lists the same moves in prose.

### 5. Skill prose references are resolved at LLM runtime, not install time

No variable substitution is applied to skill template prose at install time (e.g.
`{{artifacts_root}}/architecture/overview.md`). The agent config `artifacts.dir` is
the machine-readable source; prose is a human-readable aid for the LLM. If a user
sets a custom `artifacts.root` in `.vstack/config.yaml`, the agent's generated
`.agent.md` body will contain the resolved root because the agent template uses the
config value at generation time. Skill markdown bodies remain as authored.

## alternatives considered

### A — Track `docs/` files in the manifest

Add docs artifacts to `.vstack/vstack.json` so `vstack status` and `vstack manifest upgrade`
can detect and migrate them. Rejected because docs files are agent-owned content that changes
continuously; tracking them like generated files would produce constant checksum drift and
requires agents to update the manifest on every write — which is not feasible in the
current execution model.

### B — Variable substitution in skill template prose

Replace hardcoded paths in skill markdown (e.g. `docs/architecture/overview.md`) with
install-time variables (`{{artifacts_root}}/architecture/overview.md`). Rejected because:
the agent config is already the machine-readable authority; prose is LLM guidance only;
adding a substitution pass increases template complexity for marginal gain. The LLM reads
the agent's own `.agent.md` (which does resolve `artifacts_root`) before executing a skill —
the agent already has the correct context.

### C — Stability promise only, no migration tooling

Commit to path stability without defining a `vstack migrate` command. Rejected because
stability promises are still best-effort — external reasons (tooling integration, naming
mistakes, file reorganisations) can require a path change within a major cycle. A defined
migration convention ensures that when a break does occur, the upgrade path is documented
and eventually automatable.

## impact on the Option B pipeline

The future `planner` orchestrator (ADR-004) resolves agent artifact paths from `config.yaml`
`artifacts.dir` and `artifacts.output` to hand off context between stages. This ADR's
stability commitment means the orchestrator can hard-code path resolution logic against
those config fields for the lifetime of a major version. The `vstack migrate` convention
ensures that when the orchestrator's expected paths change across majors, a machine-readable
migration record is available to update the planner's context without manual intervention.
