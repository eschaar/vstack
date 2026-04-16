# ADR-002: Artifact Naming and Compatibility Policy

> Maintained by: **agents** role

**date:** 2026-03-27\
**status:** accepted

## context

Artifact names are part of the public surface of vstack. This applies to:

- skills
- agents
- prompts
- instructions

These names appear in generated artifacts, documentation, examples, discovery
surfaces, and team habits.

If naming drifts, several problems follow:

1. Capabilities become harder to discover.
1. Docs and generated artifacts start using different vocabulary.
1. Temporary compatibility names can become permanent accidental API.
1. The system starts to carry naming history instead of a clear current model.

vstack also wants to acknowledge inspiration from earlier systems without carrying
forward literal naming layers or copy-paste compatibility behavior unless there is
a strong product reason to do so.

## decision

vstack adopts the following naming and compatibility policy for artifacts:

1. **Canonical names are the product language.**

   - Directory names and canonical `name` fields are the source of truth.
   - Docs, examples, agents, skills, prompts, and generated artifacts should prefer canonical names.

1. **Aliases are exceptional, not foundational.**

   - Aliases may exist only when they solve a real vstack migration or compatibility need.
   - Aliases should not be kept solely to preserve historical naming lineage.
   - Aliases should be removed once the migration window is no longer useful.

1. **Do not preserve external naming just because it existed elsewhere.**

   - Inspiration may be credited.
   - External names should not be copied forward as a permanent compatibility layer.

1. **Prefer clear backend- and workflow-oriented names over inherited names.**

   - Names should describe the workflow in language that backend and platform teams
     would naturally search for.

1. **A rename is a product decision, not a historical translation table.**

   - If an artifact is renamed, record the reasoning in the relevant ADR.
   - Do not maintain broad rename maps unless they are actively required by the product.

## alternatives considered

### Option A: Keep broad historical alias maps

**Pros:**

- Easier migration for older naming habits.
- Preserves lineage explicitly.

**Cons:**

- Keeps old vocabulary alive in the product surface.
- Encourages docs and generated artifacts to drift between old and new terms.
- Makes vstack feel derivative rather than opinionated.

**Why rejected:**
The long-term clarity cost is higher than the migration benefit.

### Option B: Allow aliases freely whenever they seem convenient

**Pros:**

- Fastest short-term path for experimentation.
- Reduces friction when renaming things.

**Cons:**

- Creates uncontrolled vocabulary growth.
- Makes discovery, docs, and maintenance worse over time.

**Why rejected:**
Unconstrained aliasing turns naming into accidental compatibility debt.

### Option C: Canonical names first, aliases only for narrow migration needs

**Pros:**

- Keeps the product language clean and intentional.
- Still allows pragmatic migration when necessary.
- Matches vstack's goal of reducing ambiguity and token overhead.

**Cons:**

- Requires deliberate cleanup after renames.
- May break stale habits sooner.

**Why chosen:**
This gives vstack a stable vocabulary without carrying unnecessary historical baggage.

## rationale

Names are part of the system design. In an AI-assisted workflow product, naming has
direct impact on:

- discoverability
- prompt and instruction consistency
- token efficiency
- onboarding quality
- perceived product identity

vstack should acknowledge inspiration while still sounding like itself. A clean,
intentional naming model supports that better than preserving literal translation
tables from earlier systems.

## consequences

### Positive

- Vocabulary stays coherent across docs, agents, skills, prompts, and generated artifacts.
- Fewer stale references and less conceptual drift.
- Lower pressure to preserve legacy naming just because it once existed.
- Stronger vstack identity.

### Negative / Tradeoffs

- Renames require active cleanup in docs and examples.
- Users familiar with older names may need a short migration period.

### Risks

- Over-aggressive alias removal can create unnecessary breakage.
- If rename cleanup is incomplete, documentation can temporarily become inconsistent.

## Related ADRs

- ADR-009: 6-Role Agent Model — related
- ADR-011: Skill Restructure (rename, new, retire) — related
