{{SKILL_CONTEXT}}

# release-notes — Release Artifact Preparation

Write release notes and update the changelog so that the release is documented
before the PR is opened.

## Out of scope

- Running tests or audits (use `verify`, `security`, `performance`)
- Creating the PR (use `pr`)
- Deployment — CI/CD takes over after merge

## Deliverable

- A release notes document summarising what changed
- An updated `CHANGELOG.md` entry

The invoking agent determines which files to read as evidence and where to write
the release notes. This skill describes the procedure, not the file paths.

______________________________________________________________________

## Step 1: Evidence review

Verify that the evidence the invoking agent has designated as required is present
and not empty. Report any missing items and stop if blockers exist.

Typical evidence to check (agent-defined):

- Test results or verification report
- Security findings or sign-off
- Change summary (git log, diff stat, or agent-provided summary)
- Acceptance criteria from requirements

If any required evidence is missing: **STOP and report to the invoking agent**.

______________________________________________________________________

## Step 2: Summarise changes

Review what changed on this branch vs the base branch:

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

## Step 3: Write release notes

Write a release notes document to the location designated by the invoking agent.
Date format: `YYYY-MM-DD` (today). Never overwrite an existing file.

Use this structure:

```markdown
# Release {date}

## Summary
[1–3 sentences: what changed and why it matters to users]

## What's new
- [user-visible feature or fix — lead with what the user can now DO]

## Fixed
- [bug fixes]

## Internal
- [infra, tooling, tests — optional]

## Evidence reviewed
| evidence | status |
|----------|--------|
| [evidence item] | ✓ / ✗ MISSING |
```

Rules:

- Write for users, not contributors
- No internal tracking references
- Every entry should make someone think "oh nice, I want that"

______________________________________________________________________

## Step 4: Update `CHANGELOG.md`

Prepend a new entry at the top of `CHANGELOG.md`:

```markdown
## {version or date}

### What's new
- [user-visible changes]

### Fixed
- [bug fixes]

### Internal
- [optional]
```

Keep existing entries intact.

______________________________________________________________________
