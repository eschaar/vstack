{{SKILL_CONTEXT}}

# pr — Commit, Push & Open Pull Request

Push the current branch and open a pull request. This is the final step
before CI/CD takes over.

## Out of scope

- Running tests (use `verify`)
- Writing release notes (use `release-notes`)
- Merging or deploying — CI/CD handles that after merge

## Deliverable

- A pull request open against the target base branch (typically `main`)

______________________________________________________________________

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

______________________________________________________________________

## Step 2: Commit

Stage and commit any uncommitted changes:

```bash
git add -A
git diff --cached --stat

# Only commit if there are staged changes
git diff --cached --quiet || git commit -m "chore: pre-release cleanup"
```

______________________________________________________________________

## Step 3: Push

```bash
git push --set-upstream origin "$BRANCH"
```

______________________________________________________________________

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

______________________________________________________________________

## Step 5: Report to user

Report the PR URL and confirm what CI/CD will do next:

```text
PR created: <url>

Next steps depend on the repository CI/CD configuration:
- Automated tests and checks will run on the PR.
- Merge when all checks pass and reviewers approve.
```

______________________________________________________________________
