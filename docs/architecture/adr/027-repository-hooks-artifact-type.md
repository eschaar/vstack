# ADR-027: Repository Hooks as a First-Class Artifact Type

> Maintained by: **architect** role

**date:** 2026-05-10\
**status:** accepted\
**depends on:** ADR-014 (manifest schema versioning), ADR-019 (vstack project directory), ADR-022 (selective exclude filter), ADR-023 (workflow contract)

## context

vstack already manages four generated artifact families under `.github/`:
`skills`, `agents`, `instructions`, and `prompts`.

Repository-level agent hooks in GitHub Copilot use `.github/hooks/<name>.json` and are
an operational control surface for safety and quality checks at session boundaries.
Until now, hooks were only represented as a raw per-agent frontmatter field (`hooks`)
and not as installable, manifest-tracked artifacts.

That gap created three practical issues:

1. No standard hook baseline shipped with `vstack install`
1. No checksum ownership or drift visibility for hook files
1. No consistent migration and exclusion behavior aligned with other artifact families

## decision

Hooks are promoted to a first-class artifact type in vstack.

### 1) New artifact type

A new singular type `hook` is added to the generator and CLI type registry.

- Source template: `src/vstack/_templates/hooks/<name>/hook.yaml`
- Install output: `.github/hooks/<name>.json`

### 2) Manifest tracking and verify behavior

Hook artifacts are tracked in `.vstack/vstack.json` under the `hooks` manifest key,
including checksum metadata, identical to other managed artifact types.

Because hook output is JSON, hooks do not emit markdown auto-generated footers.
`verify` must therefore:

- validate file presence and expected names,
- validate checksum ownership/drift,
- skip VSTACK-META/footer checks for artifact types with `auto_gen_footer = false`.

### 3) Baseline hook templates

vstack ships multiple default hooks, not just one sample:

- `session-audit`
- `pre-tool-safety-gate`
- `post-edit-format`
- `post-edit-markdown-quality`
- `post-commit-security-scan`

These templates are conservative defaults that provide immediate, low-risk guidance.
Teams can replace or extend them via normal template customization patterns.

For vstack itself, the markdown-quality hook is part of the default baseline because
the repository's primary outputs include ADRs, docs, prompts, instructions, and other
Markdown-heavy work items.

### 4) Separation from per-agent frontmatter hooks

Per-agent frontmatter `hooks` remains supported and unchanged.
That field configures agent-scoped behavior.
Repository hook artifacts configure repository-scoped behavior.
Both are valid and intentionally separate concerns.

### 5) Migration path

No destructive migration is required.

For existing repositories:

1. upgrade to a vstack version that includes this ADR implementation,
1. run `vstack install` (or `vstack init` in CI),
1. optional: disable repository hooks using `.vstack/config.yaml` with `exclude.hook`
   or the `hooks:` configuration block.

No existing agent configuration must be rewritten.

### 6) Execution model and dependency policy

Repository hooks execute in the active Copilot hook runtime context for the current
workspace session.

- local session: hooks run on the local machine,
- remote/devcontainer/SSH session: hooks run in that remote runtime.

Hook defaults must remain operational in `audit` mode without hard external-tool
dependencies. Optional integrations (for example `make` or `gitleaks`) may run only
when explicitly enabled, and implementations must degrade safely when those tools are
not available.

### 7) Project-level hook controls and template metadata semantics

Projects may control the default generated hook baseline from `.vstack/config.yaml`.

Supported controls:

- `hooks.enabled`: disable the baseline hook family for the project,
- `hooks.mode`: set the generated default runtime mode (`audit` or `enforce`),
- `hooks.hooks.<name>.enabled`: disable one named hook,
- `hooks.hooks.<name>.mode`: override mode for one named hook.

Hook `hook.yaml` files include descriptive metadata beyond versioning. This metadata
improves maintainability and reviewability while preserving the runtime JSON contract.

Examples include:

- `description` and `purpose` to state intent,
- `security_level` and `mode_default` to communicate expected operating posture,
- dependency hints for optional enforce-mode tooling.

## alternatives considered

### A) Keep hooks only as per-agent raw frontmatter

Rejected. This keeps hooks outside the managed artifact model and prevents
checksum governance, deterministic install output, and selective-type operations.

### B) Treat hooks as prompts or instructions

Rejected. Hook JSON has distinct schema/behavior and should not be forced into
markdown-oriented families with frontmatter/footer semantics.

### C) Add hooks only in docs, no generator support

Rejected. Documentation-only support does not provide enforceable defaults,
manifest state, or verifiable install behavior.

## rationale

Promoting hooks to a first-class type keeps vstack's artifact model coherent:
all generated repository artifacts are discoverable, installable, verifiable,
and checksum-tracked via one mechanism.

It also enables consistent CLI ergonomics (`--only hook`, `exclude.hook`) and
reduces drift between declared policy and repository state.

## impact on the Option B pipeline

The planner-oriented orchestrated pipeline depends on predictable repository
controls during multi-stage execution.

Repository hooks provide a stage-independent guardrail layer around session and
tool events. This improves baseline safety and quality enforcement regardless of
which role stage is active, while preserving stage-level workflow contracts from
ADR-023.
