---
name: release-notes
description: 'Prepare release artifacts: verify all docs are present, write release notes, own CHANGELOG.md updates, and produce docs/releases/{date}.md. Use when asked to "write release notes", "update the changelog", or "prepare release artifacts".'
license: 'MIT'
compatibility: 'Requires a skills-compatible agent with repository file access and terminal command execution when needed.'
metadata:
  owner: vstack
  maturity: stable
argument-hint: '[version or changes to release]'
user-invocable: true
disable-model-invocation: false
---
## Skill Context

This skill is part of **vstack** — a VS Code-native AI engineering workflow system.

### AskUserQuestion Format

When you need clarification, use this exact format — never invent or guess:

> **Question:** [The specific question]
> **Options:** A) … | B) … | C) …
> **Default if no response:** [What you'll do]

Never ask more than one question at a time without waiting for the answer.

### Diagram Convention

When producing hand-authored Markdown outputs, prefer Mermaid for flow,
interaction, lifecycle, state, topology, dependency, and decision diagrams when
the format is supported and improves clarity. Use ASCII as a fallback when
Mermaid is unsupported or would be less readable. Keep ASCII/text trees for
directory structures and other scan-friendly hierarchies.

# release-notes — Release Artifact Preparation

Verify all artifacts are complete, write release notes, and update the changelog.

This skill owns both `docs/releases/{date}.md` and `CHANGELOG.md` updates.

## Out of scope

- Running tests or audits (use `verify`, `security`, `performance`)
- Creating the PR (use `pr`)
- Deployment — CI/CD takes over after merge

## Deliverable and artifact policy

- Primary deliverables: `docs/releases/{date}.md`, `CHANGELOG.md`
- Baseline-first default: write final release artifacts directly to baseline docs on the feature branch.
- Optional WIP area for complex/uncertain efforts: `docs/delta/{id}/RELEASE_DELTA.md`
- Before merge: consolidate final release summary and changelog entries into baseline artifacts.

______________________________________________________________________

## Step 1: Artifact checklist

Verify these files exist and are not empty:

```bash
for f in docs/product/requirements.md docs/architecture/architecture.md docs/design/design.md \
          docs/test-report.md docs/security-report.md CHANGELOG.md; do
  [ -f "$f" ] && echo "✓ $f" || echo "✗ MISSING: $f"
done

# Scope-conditional artifacts
[ -f docs/performance-baseline.md ] && echo "✓ docs/performance-baseline.md" || echo "i docs/performance-baseline.md (optional unless performance validation is in scope)"
[ -f docs/observability-baseline.md ] && echo "✓ docs/observability-baseline.md" || echo "i docs/observability-baseline.md (optional; observability evidence may be in docs/test-report.md)"
```

If any required artifact is missing: **STOP and report**. Do not proceed.
If performance validation is in scope and `docs/performance-baseline.md` is missing: **STOP and report**.

______________________________________________________________________

## Step 2: Summarise changes

Review what changed on this branch vs main:

```bash
git log origin/main..HEAD --oneline
git diff origin/main --stat | head -30
```

Identify:

- New features
- Bug fixes
- Breaking changes (if any)
- Internal/infrastructure changes

______________________________________________________________________

## Step 3: Write `docs/releases/{date}.md`

Date format: `YYYY-MM-DD` (today). Never overwrite an existing file.

```bash
DATE=$(date +%Y-%m-%d)
RELEASE_FILE="docs/releases/${DATE}.md"
[ -f "$RELEASE_FILE" ] && echo "ERROR: $RELEASE_FILE already exists" && exit 1
mkdir -p docs/releases
```

Write the file with this structure:

```markdown
# Release {date}

## summary
[1–3 sentences: what changed and why it matters to users]

## what's new
- [user-visible feature or fix — lead with what the user can now DO]

## fixed
- [bug fixes]

## internal
- [infra, tooling, tests — optional]

## artifacts reviewed
| artifact | status |
|----------|--------|
| docs/product/requirements.md | ✓ |
| docs/architecture/architecture.md | ✓ |
| docs/design/design.md | ✓ |
| docs/test-report.md | ✓ |
| docs/security-report.md | ✓ |
```

Rules:

- Write for users, not contributors
- No internal tracking references
- Every entry should make someone think "oh nice, I want that"

______________________________________________________________________

## Step 4: Update `CHANGELOG.md`

Prepend a new entry at the top of `CHANGELOG.md`:

```markdown
## {date}

### What's new
- [user-visible changes]

### Fixed
- [bug fixes]

### Internal
- [optional]
```

Keep existing entries intact.

______________________________________________________________________

<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->
<!-- VSTACK-META: {"artifact_name":"release-notes","artifact_type":"skill","artifact_version":"1.0.2","generator":"vstack","vstack_version":"1.3.0"} -->
