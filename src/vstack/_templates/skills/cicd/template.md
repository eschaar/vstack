{{SKILL_CONTEXT}}

# cicd — GitHub Actions Workflows

Write CI/CD pipeline configuration as `.github/workflows/*.yml` files.
These files live in the PR — the pipeline runs after merge.

## Out of scope

- Application code changes (engineering role)
- Container image authoring (use `container`)
- Post-deploy monitoring (CI/CD's responsibility after merge)

______________________________________________________________________

## Step 1: Detect context

```bash
# Detect runtime and tooling
ls pyproject.toml requirements.txt package.json go.mod Cargo.toml 2>/dev/null | head -5

# Detect existing workflows
ls .github/workflows/ 2>/dev/null || echo "No workflows found"

# Detect container config
ls Dockerfile 2>/dev/null && echo "Dockerfile present"
```

______________________________________________________________________

## Step 2: CI workflow — `.github/workflows/ci.yml`

Runs on every push and PR. Must pass before merge.

```yaml
name: CI

on:
  push:
    branches: ["**"]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Language-specific setup — pick the applicable block:

      # Python
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: ruff check .
      - run: mypy .
      - run: pytest --tb=short

      # Node
      # - uses: actions/setup-node@v4
      #   with: { node-version: "22" }
      # - run: npm ci
      # - run: npm run lint
      # - run: npm test

      # Go
      # - uses: actions/setup-go@v5
      #   with: { go-version: "1.22" }
      # - run: go vet ./...
      # - run: go test ./...
```

______________________________________________________________________

## Step 3: Security scan — add to CI or separate workflow

Add dependency and secret scanning:

```yaml
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Dependency scan (pick one):
      # Python
      - run: pip install pip-audit && pip-audit

      # Node
      # - run: npm audit --audit-level=high

      # Secret scan
      - uses: trufflesecurity/trufflehog-actions-scan@main
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}
```

______________________________________________________________________

## Step 4: CD workflow — `.github/workflows/cd.yml`

Runs on merge to main. Builds and publishes the container image, then triggers deployment.

```yaml
name: CD

on:
  push:
    branches: [main]

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          push: true
          tags: |
            ghcr.io/${{ github.repository }}:latest
            ghcr.io/${{ github.repository }}:${{ github.sha }}
```

Adapt the deploy trigger to match the target platform (Fly.io, Render, Railway, K8s, etc.).

______________________________________________________________________

## Step 5: Branch protection (document, don't automate)

Record in `docs/architecture/architecture.md` or a README section:

```text
Branch protection rules for `main`:
- Require PR before merging
- Require status checks: CI / test, CI / security
- Require at least 1 approval
- No force pushes
```

Configure these in GitHub → Settings → Branches.

______________________________________________________________________

## Step 6: Review checklist

- [ ] CI workflow triggers on push + PR
- [ ] Lint, type-check, and tests all run in CI
- [ ] Security scan included
- [ ] CD triggers only on merge to main
- [ ] No secrets hardcoded in workflow files — use `secrets.*`
- [ ] Container image tagged with both `latest` and `${{ github.sha }}`
- [ ] Workflows validate locally: `act` (optional, for local testing)

______________________________________________________________________
