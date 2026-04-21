---
name: pr
description: 'Commit, push, and open a pull request from the current branch to main. Uses the release notes from docs/releases/{date}.md as the PR body. Use when asked to "open a PR", "push and create PR", or "submit for review".'
license: 'MIT'
compatibility: 'Requires a skills-compatible agent with repository file access and terminal command execution when needed.'
metadata:
  owner: vstack
  maturity: stable
argument-hint: '[task]'
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

# pr — Commit, Push & Open Pull Request

Push the current branch and open a PR targeting main. This is the final step
before CI/CD takes over.

## Out of scope

- Running tests (use `verify`)
- Writing release notes (use `release-notes`)
- Merging or deploying — CI/CD handles that after merge

## Deliverable and artifact policy

- Primary deliverable: release pull request targeting main
- Baseline-first default: use existing branch artifacts directly; do not create parallel release records outside baseline docs.
- PR body source: `docs/releases/{date}.md` when present
- Before merge: ensure release artifact references in the PR body reflect final baseline files.

______________________________________________________________________

## Step 1: Pre-flight

```bash
# Confirm not on main
BRANCH=$(git branch --show-current)
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
  echo "ERROR: on $BRANCH — create a feature branch first"
  exit 1
fi
echo "Branch: $BRANCH"

# Check release notes exist
DATE=$(date +%Y-%m-%d)
RELEASE_FILE="docs/releases/${DATE}.md"
[ -f "$RELEASE_FILE" ] || echo "WARN: $RELEASE_FILE not found — PR body will be empty"

# Show what will be included
git status --short
git log origin/main..HEAD --oneline
```

______________________________________________________________________

## Step 2: Commit

Stage and commit any uncommitted changes:

```bash
git add -A
git diff --cached --stat

# Only commit if there are staged changes
git diff --cached --quiet || git commit -m "release: $(date +%Y-%m-%d)"
```

______________________________________________________________________

## Step 3: Push

```bash
git push --set-upstream origin "$BRANCH"
```

______________________________________________________________________

## Step 4: Open PR

```bash
DATE=$(date +%Y-%m-%d)
RELEASE_FILE="docs/releases/${DATE}.md"
BODY=""
[ -f "$RELEASE_FILE" ] && BODY=$(cat "$RELEASE_FILE")

gh pr create \
  --base main \
  --title "release: ${DATE}" \
  --body "$BODY"
```

If `gh` is not available:

```bash
echo "Open PR manually:"
echo "  Title: release: $(date +%Y-%m-%d)"
echo "  Base:  main"
echo "  Head:  $BRANCH"
echo "  URL:   https://github.com/<org>/<repo>/compare/main...$BRANCH"
```

______________________________________________________________________

## Step 5: Report to user

Report the PR URL and next steps:

```text
PR created: <url>

CI/CD will now:
- Run tests and security scan
- Build and publish container image
- Determine version (semantic-release / conventional commits)
- Deploy after approval and merge
```

______________________________________________________________________

<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->
<!-- VSTACK-META: {"artifact_name":"pr","artifact_type":"skill","artifact_version":"1.0.2","generator":"vstack","vstack_version":"1.3.0"} -->
