{{SKILL_CONTEXT}}

# gh-issues — GitHub Issue Management

Create, update, and manage GitHub issues using the `gh` CLI.

## Out of scope

- Pull requests (use `pr`)
- Release notes (use `release-notes`)
- Project boards — use `gh project` commands or GitHub UI directly

## Step 0: Pre-flight

```bash
# Verify gh CLI is authenticated
gh auth status 2>/dev/null || echo "ERROR: gh CLI not authenticated"

# Identify the repository
gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>/dev/null
```

## Step 1: Determine Action

Classify the request:

- **Create:** new bug report, feature request, or task
- **Update:** edit title, body, labels, assignees, milestone, or state
- **Query:** list, search, or view issues

## Step 2: Query Existing Issues (when relevant)

Before creating, check if a similar issue already exists:

```bash
# List open issues with optional filter
gh issue list --state open --limit 20

# Search for similar issues
gh issue list --search "<keyword>" --state all --limit 10

# View a specific issue
gh issue view <number>
```

## Step 3: Create an Issue

### Bug report

```bash
gh issue create \
  --title "Short imperative description of the bug" \
  --body "## Description
What is broken and what impact does it have?

## Steps to Reproduce
1.
2.
3.

## Expected Behavior
What should happen.

## Actual Behavior
What happens instead.

## Environment
- Version/commit:
- OS/Platform:
- Relevant config:" \
  --label "bug"
```

### Feature request

```bash
gh issue create \
  --title "Add <capability>" \
  --body "## Summary
One-paragraph description of the feature and its value.

## Motivation
Why is this needed? Who benefits?

## Proposed Solution
How it could be implemented at a high level.

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2" \
  --label "enhancement"
```

### Task / chore

```bash
gh issue create \
  --title "Imperative description of the task" \
  --body "## Context
Why this task is needed.

## Definition of Done
- [ ] Step 1
- [ ] Step 2" \
  --label "task"
```

### With assignees and milestone

```bash
gh issue create \
  --title "<title>" \
  --body "<body>" \
  --assignee "<github-username>" \
  --milestone "<milestone-title>"
```

## Step 4: Update an Existing Issue

```bash
# Edit title or body
gh issue edit <number> --title "<new-title>"
gh issue edit <number> --body "<new-body>"

# Add or remove labels
gh issue edit <number> --add-label "bug" --remove-label "needs-triage"

# Change assignees
gh issue edit <number> --add-assignee "<username>"

# Set milestone
gh issue edit <number> --milestone "<milestone-title>"

# Close or reopen
gh issue close <number> --comment "Resolved in <commit/PR>."
gh issue reopen <number>

# Add a comment
gh issue comment <number> --body "Comment text."
```

## Step 5: Sub-issues (if hierarchy is needed)

GitHub supports sub-issues via the REST API:

```bash
# Create sub-issue and link to parent
PARENT=<parent-issue-number>
CHILD=$(gh issue create \
  --title "<sub-task title>" \
  --body "Sub-task for #$PARENT." \
  --json number --jq '.number')

# Link child to parent via REST API
OWNER_REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner')
gh api "repos/$OWNER_REPO/issues/$PARENT/sub_issues" \
  -X POST \
  -f sub_issue_id="$CHILD"
```

## Title guidelines

- Use imperative mood: "Add dark mode", not "Dark mode addition"
- Be specific: "Login fails with SSO enabled" not "SSO broken"
- Keep under 72 characters
- Do not prefix with `[Bug]` or `[Feature]` — use labels instead

## Standard labels

| Label              | Use for                             |
| ------------------ | ----------------------------------- |
| `bug`              | Something is broken                 |
| `enhancement`      | New feature or improvement          |
| `documentation`    | Docs-only change                    |
| `task`             | Internal maintenance or chore       |
| `good first issue` | Suitable for new contributors       |
| `help wanted`      | Extra attention or expertise needed |
| `wontfix`          | Will not be addressed               |
| `duplicate`        | Already tracked elsewhere           |

## Output

Report the URL after creation or update:

```text
https://github.com/<org>/<repo>/issues/<number>
```
