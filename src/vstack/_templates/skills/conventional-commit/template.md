{{SKILL_CONTEXT}}

# conventional-commit — Prepare Conventional Commits

Create clear, policy-aligned commits with a Conventional Commit header:

`type(optional-scope)!: short summary`

## Out of scope

- Pushing branches or opening PRs (use `pr`)
- Writing release notes (use `release-notes`)
- Rewriting repository history unless explicitly requested

## Deliverable

- One or more commits with compliant Conventional Commit messages

## Step 1: Inspect changes and choose commit boundaries

Review current changes first:

```bash
git status --short
git diff --stat
git diff --cached --stat
```

Split unrelated changes into separate commits.

Boundary rules:

- One commit per cohesive intent
- Avoid mixing refactor + feature + tests unless tightly coupled
- Keep commits reviewable and reversible

## Step 2: Select commit type and scope

Choose the best type from change intent:

- `feat` for new behavior
- `fix` for bug fixes
- `refactor` for structure-only changes without behavior change
- `docs` for documentation-only changes
- `test` for test-only changes
- `chore` for maintenance/tooling/meta updates
- `ci` for CI/CD workflow changes
- `perf` for performance-focused improvements

Scope guidance:

- Use optional scope when it improves clarity: `feat(auth): ...`
- Keep scope short, stable, and system-oriented
- Omit scope if it adds noise

## Step 3: Draft header and body

Header format:

```text
type(optional-scope)!: short summary
```

Quality rules:

- imperative mood (`add`, `fix`, `remove`)
- summary \<= 100 characters
- no trailing period
- no vague text like `update stuff`

Use breaking marker `!` only when behavior or contract is breaking.

Optional body should explain why, risk, and migration notes when relevant.

## Step 4: Validate against staged content

Before committing, verify message-content alignment:

```bash
git diff --cached --name-only
git diff --cached --stat
```

Validation checks:

- `docs` commit does not include source code changes (unless explicitly intended)
- `test` commit does not include product logic changes (unless fixing test harness)
- `refactor` commit does not change observable behavior
- breaking marker appears only with actual breaking impact

If alignment fails, revise scope/type or split commits.

## Step 5: Commit safely

Commit staged changes with validated header:

```bash
git commit -m "<type(optional-scope): summary>"
```

For non-trivial changes, include body:

```bash
git commit \
  -m "<type(optional-scope): summary>" \
  -m "Why: <reason>" \
  -m "Risk: <risk and mitigation>"
```

## Step 6: Report result

Return concise result:

```text
Committed:
- <sha> <header>

Remaining changes:
- <summary or none>
```

If commit is blocked, report exact reason and proposed fix.
