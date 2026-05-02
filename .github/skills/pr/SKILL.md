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

Push the current branch and open a pull request. This is the final step
before CI/CD takes over.

## Out of scope

- Running tests (use `verify`)
- Writing release notes (use `release-notes`)
- Merging or deploying — CI/CD handles that after merge

## Deliverable

- A pull request open against the target base branch (typically `main`)


## Step 1: Pre-flight

```bash
# Confirm not on the target base branch
BRANCH=$(git branch --show-current)
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
  echo "ERROR: on $BRANCH — create a feature branch first"
  exit 1
fi
echo "Branch: $BRANCH"

# Show what will be included
git status --short
git log origin/main..HEAD --oneline
```


## Step 2: Commit

Stage and commit any uncommitted changes:

```bash
git add -A
git diff --cached --stat

# Only commit if there are staged changes
git diff --cached --quiet || git commit -m "chore: pre-release cleanup"
```


## Step 3: Push

```bash
git push --set-upstream origin "$BRANCH"
```


## Step 4: Open PR

Use the PR title and body provided by the invoking agent or user.
If no body is provided, write a short summary of the changes on this branch.

```bash
gh pr create \
  --base main \
  --title "<title>" \
  --body "<body>"
```

If `gh` is not available:

```bash
echo "Open PR manually:"
echo "  Title: <title>"
echo "  Base:  main"
echo "  Head:  $BRANCH"
echo "  URL:   https://github.com/<org>/<repo>/compare/main...$BRANCH"
```


## Step 5: Report to user

Report the PR URL and confirm what CI/CD will do next:

```text
PR created: <url>

Next steps depend on the repository CI/CD configuration:
- Automated tests and checks will run on the PR.
- Merge when all checks pass and reviewers approve.
```


<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->
<!-- VSTACK-META: {"artifact_name":"pr","artifact_type":"skill","artifact_version":"20260502013","generator":"vstack","vstack_version":"0.0.0.post3.dev0+df3fe6e"} -->
