{{SKILL_CONTEXT}}

# pr — Commit, Push & Open Pull Request

Push the current branch and open a PR targeting main. This is the final step
before CI/CD takes over.

## Out of scope

- Running tests (use `verify`)
- Writing release notes (use `release-notes`)
- Merging or deploying — CI/CD handles that after merge

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
