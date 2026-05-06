# ADR-022: Selective exclude filter in `.vstack/config.yaml`

> Maintained by: **architect** role

**date:** 2026-05-06\
**status:** accepted

## context

vstack installs Copilot artifacts — agents, skills, instructions, and prompts — into `.github/`
at install or init time. Before this change, every run regenerated all artifact types
unconditionally. Teams adopting vstack in an existing repo often want only a subset of artifact
types: a platform team may need agents and instructions but has no use for skills or prompts; a
team that already maintains its own prompt library does not want vstack's prompts landing in their
repository.

The existing `--only` CLI flag allows callers to restrict a single run to specific artifact types,
but it is transient. A team running `vstack init` in CI must repeat the flag on every invocation.
There was no mechanism for a project to encode its artifact preferences once and have them honored
automatically on every subsequent install.

## decision

An `exclude:` block is added to `.vstack/config.yaml`. It supports two modes per artifact type:

- **Full-type exclusion** — setting a type's value to `all` (e.g. `skills: all`) removes every
  artifact of that type from the effective install set.
- **Name-level exclusion** — setting a type's value to a list (e.g. `instructions: [security, testing]`)
  installs all artifacts of that type except the named ones.

Example configuration:

```yaml
exclude:
  skills: all
  prompts: all
  instructions: [security, testing]
```

Agents cannot be excluded. The six-role agent chain is treated as an atomic unit; vstack's
execution model depends on all six roles being present, and allowing partial agent installs would
produce a broken workflow for the consumer.

Config keys use plural forms (`skills`, `agents`, `instructions`, `prompts`) for readability and
are mapped to singular internal type names at parse time via a `_CONFIG_TYPE_ALIAS` table in
`interface.py`. The implementation is split across two layers: full-type exclusions are resolved
at the `CommandLineInterface` level by filtering `effective_only` before dispatch, while
name-level exclusions are carried in `CommandContext.excluded_names` and applied per-artifact
inside the `init` command's generate loop. This keeps the type-routing logic central and the
per-artifact skip logic local to generation.

When the config file is absent or the `exclude:` key is not present, the filter is a no-op and
all artifacts are installed, preserving full backward compatibility. When `--only` is also
supplied, type exclusions subtract from the explicit `--only` set; they narrow the effective set
but never override an explicit inclusion.

## alternatives considered

**`--only` CLI flag alone.** The flag already exists and handles ad-hoc type filtering. It was
not sufficient here because project-level preferences must survive across all invocations — in CI,
in local onboarding, and in automated upgrade flows — without requiring every caller to repeat the
flag. Encoding the preference in config is the correct level of abstraction.

**Per-type boolean flags in config** (`install_skills: false`). This approach is more verbose,
requires a separate key per type, and does not compose naturally with name-level exclusions
without additional design. The `exclude:` block with `all`/list values is more compact, expresses
both modes under a single key, and leaves room for future glob-based partial exclusion without a
config format change.

**Allowlist instead of denylist** (`include: [agents, instructions]`). An allowlist requires
teams to update their config whenever vstack adds a new artifact type. A denylist is
forward-compatible by default: new types are installed unless explicitly excluded, which matches
the expected behavior for most consumers upgrading vstack.

## rationale

The `exclude:` filter is the minimal solution for the two most common adoption patterns: teams
that want agents and instructions only, and teams that already have their own skills or prompts
and do not want vstack's versions to land in their repository. It introduces no new concepts
beyond what is already present in the config schema and composes cleanly with `--only` without
changing install semantics for teams that do not configure it.

Keeping agents non-excludable is a deliberate constraint rather than an oversight. The six-role
model (ADR-009) is the structural unit of vstack; partially removing roles would leave consumers
with a workflow that references agents that do not exist. If a team genuinely does not need all
six roles, the correct solution is a future scoped-install mode, not silent omission of individual
agents.

Splitting the implementation between `CommandLineInterface` (type filtering) and the generate
loop (name filtering) reflects the natural ownership boundary: the CLI layer owns which types
enter the pipeline, and the generator layer owns which named artifacts within a type are emitted.
This avoids coupling artifact-level skip logic to the routing layer and keeps each layer testable
in isolation.

## impact on orchestrated pipeline

Low. The filter operates entirely before artifact generation, at context construction time. In a
multi-agent sequential pipeline (ADR-004), each stage receives `CommandContext` as its
input; `excluded_names` and `effective_only` travel with the context unchanged. No stage-level
changes are required to honor the filter. The constraint that agents cannot be excluded aligns
naturally with the orchestrated pipeline's dependency on all six roles being available as pipeline stages.
