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

## Step 1: Pre-flight

Resolve the configured remote's **push** URL to its GitHub owner/repository
(including SSH aliases), then set `PUSH_REPO` below. Set `BASE_REPO` to the target
repository, which may differ for forks. Confirm both are on the same GitHub host.
Stop on ambiguous or multiple push destinations; never infer push identity from
the fetch URL or branch name alone. Requires `gh` and `jq`.

```bash
PUSH_REMOTE="origin"
PUSH_REPO="<push-owner>/<push-repo>"
BASE_REPO="<base-owner>/<base-repo>"
PUSH_OWNER=${PUSH_REPO%/*}
git remote get-url --push --all "$PUSH_REMOTE" || exit $?

# Confirm gh CLI is authenticated
gh auth status || exit $?

# Confirm not on the target base branch
BRANCH=$(git branch --show-current)
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
  echo "ERROR: on $BRANCH — create a feature branch first"
  exit 1
fi
echo "Branch: $BRANCH"

# Check if a PR already exists for this branch
PR_CANDIDATES=$(gh pr list --repo "$BASE_REPO" --head "$BRANCH" --state open \
  --json url,headRepositoryOwner,headRepository,headRefName) || exit $?
EXISTING_PR=$(printf '%s' "$PR_CANDIDATES" | jq -r \
  --arg repo "$PUSH_REPO" --arg branch "$BRANCH" \
  '[.[] | select(
    (.headRepositoryOwner.login + "/" + .headRepository.name) == $repo
    and .headRefName == $branch
  )] | .[0].url // empty') || exit $?
if [ -n "$EXISTING_PR" ]; then
  echo "Existing PR will be updated after push: $EXISTING_PR"
fi

# Show what will be included
git status --short
git log origin/main..HEAD --oneline

# Detect PR template for body structure
PR_TEMPLATE=$(cat .github/PULL_REQUEST_TEMPLATE.md \
  .github/PULL_REQUEST_TEMPLATE/pull_request_template.md \
  .github/pull_request_template.md 2>/dev/null | head -5)
[ -n "$PR_TEMPLATE" ] && echo "PR template found — use its structure for the body"
```

## Step 2: Commit

Review changed and already-staged files. Commit only approved task changes using
`@#conventional-commit` and an intent-specific message. Stage explicit paths;
never use `git add -A` or a generic cleanup commit. Leave unrelated work untouched.
If scope is unclear, ask before staging or committing.

```bash
git diff --cached --stat
```

## Step 3: Push

```bash
git push --set-upstream "$PUSH_REMOTE" "$BRANCH" || exit $?
```

## Step 4: Reuse or Open PR

Only after a successful push, reuse an existing PR:

```bash
if [ -n "$EXISTING_PR" ]; then
  echo "PR updated: $EXISTING_PR"
  exit 0
fi
```

Use the PR title and body provided by the invoking agent or user.
If no body is provided, write a short summary of the changes on this branch.
Use `--draft` when the work is not yet ready for review.

```bash
# Short body (inline):
gh pr create \
  --repo "$BASE_REPO" --head "$PUSH_OWNER:$BRANCH" \
  --base main \
  --title "<title>" \
  --body "<body>"

# Long body (write to file first):
cat > /tmp/pr-body.md <<'EOF'
<body>
EOF
gh pr create \
  --repo "$BASE_REPO" --head "$PUSH_OWNER:$BRANCH" \
  --base main \
  --title "<title>" \
  --body-file /tmp/pr-body.md

# Draft PR (not ready for review):
gh pr create \
  --repo "$BASE_REPO" --head "$PUSH_OWNER:$BRANCH" \
  --base main \
  --title "<title>" \
  --body "<body>" \
  --draft
```

If `gh` is not available or not authenticated:

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
