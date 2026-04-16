{{SKILL_CONTEXT}}

{{BASE_BRANCH}}

# docs — Post-Release Documentation Update

Update all documentation to match what was just shipped. Report and write; do not
change source code.

## Out of scope

- Code changes or bug fixes (use `verify` or `debug`)
- Creating the PR (use `pr`)
- Generating release notes (use `release-notes`)
- Updating `CHANGELOG.md` (owned by `release-notes`)

______________________________________________________________________

## Step 0: Scope the Release

```bash
# What changed in this release?
git log <base>..HEAD --oneline
git diff <base> --stat | head -30

# Current version
cat VERSION 2>/dev/null \
  || node -p "require('./package.json').version" 2>/dev/null \
  || echo "unknown"
```

______________________________________________________________________

## Step 1: README

Review whether README needs updates:

```bash
cat README.md 2>/dev/null | head -60
```

Check:

- [ ] Installation instructions still accurate?
- [ ] "Getting started" example still works?
- [ ] Feature list reflects new capabilities?
- [ ] Any deprecated features removed from featured examples?
- [ ] Badges (version, CI status) still accurate?

______________________________________________________________________

## Step 2: API Documentation

If there's an OpenAPI / AsyncAPI spec:

```bash
cat openapi.yaml 2>/dev/null | head -40 || true
```

Check:

- [ ] Spec version matches VERSION?
- [ ] New endpoints documented?
- [ ] Changed endpoints updated?
- [ ] Deprecated endpoints marked with `deprecated: true`?
- [ ] Response examples accurate?

If there's generated API documentation (Swagger UI, Redoc, TypeDoc, Sphinx):

```bash
npm run docs 2>/dev/null || make docs 2>/dev/null || true
```

______________________________________________________________________

## Step 3: MIGRATIONS Guide (if applicable)

If this release contains breaking changes or migration steps:

- Create or update `MIGRATIONS.md` or `docs/migrations/vX.md`
- Document: why the change was made, what behavior changed, migration steps, code examples

______________________________________________________________________

## Step 4: Code Comments & ADRs

For significant architectural changes:

- Check if inline code comments reference outdated behavior

- Add an Architecture Decision Record in `docs/architecture/adr/` if a significant decision was made

  (use the `adr` skill for the full ADR writing procedure)

______________________________________________________________________

## Step 5: Commit Documentation Updates

```bash
git add README.md openapi.yaml docs/ 2>/dev/null || true
git commit -m "docs: update documentation for v$(cat VERSION 2>/dev/null || echo 'unknown')"
```

______________________________________________________________________

## Summary

```text
## Documentation Update — v[VERSION] — [date]

Updated:
- [ ] README.md
- [ ] API spec (openapi.yaml)
- [ ] Migration guide (if breaking changes)
- [ ] ADR (if architectural decision)

Skipped (n/a):
- [ ] [reason]
```

______________________________________________________________________
