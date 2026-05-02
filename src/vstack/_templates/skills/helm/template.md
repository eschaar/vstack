{{SKILL_CONTEXT}}

# helm - Helm Chart and Release Workflows

Write, review, and operate Helm charts and release lifecycles.

## Out of scope

- Raw Kubernetes manifest-only workflows (use `k8s`)
- Rancher/Fleet governance workflows (use `rancher`)

## Step 0: Detect Context

```bash
helm version 2>/dev/null || echo "helm not installed"

# Detect charts
find . -name Chart.yaml -o -path "*/charts/*" | head -40
```

## Step 1: Chart Structure Review

Expected chart layout:

- `Chart.yaml` for metadata and dependencies
- `values.yaml` for defaults
- `templates/` for rendered resources
- `templates/_helpers.tpl` for naming/labels helpers

```bash
helm show chart <chart-path>
helm show values <chart-path>
```

## Step 2: Static Validation Before Deploy

```bash
# Lint chart and values
helm lint <chart-path> -f values.yaml

# Render to inspect final manifests
helm template <release> <chart-path> -n <namespace> -f values.yaml > rendered.yaml

# Optional Kubernetes dry-run check
kubectl apply --dry-run=server -f rendered.yaml
```

Validation checklist:

- Workload resources define `requests`/`limits`
- Probes exist for long-running services
- Service selectors match deployment labels
- Secrets are referenced, not hardcoded in values

## Step 3: Install and Upgrade Safely

```bash
# Install
helm install <release> <chart-path> -n <namespace> --create-namespace -f values.yaml

# Upgrade with safety flags
helm upgrade <release> <chart-path> -n <namespace> -f values.yaml \
  --atomic --timeout 10m --history-max 10

# Check release state
helm list -n <namespace>
helm status <release> -n <namespace>
```

Use environment-specific values files (`values-dev.yaml`, `values-prod.yaml`) and keep overrides minimal.

## Step 4: Rollback and Incident Recovery

```bash
helm history <release> -n <namespace>
helm rollback <release> <revision> -n <namespace>
```

Rollback policy:

- Identify the last known healthy revision
- Roll back first, then investigate forward fix
- Capture failing diff for follow-up hardening

## Step 5: Dependencies and Supply Chain

```bash
# Resolve chart dependencies
helm dependency update <chart-path>

# Inspect rendered manifests for dependency side effects
helm template <release> <chart-path> -f values.yaml | head -80
```

Practices:

- Pin dependency versions in `Chart.yaml`
- Review transitive chart defaults before promotion
- Avoid unverified third-party repositories in production

## References

> Always use the official documentation for the exact Helm and Kubernetes versions in use - chart schema, flags, and behavior evolve between releases.

- [Helm documentation](https://helm.sh/docs/)
- [Helm command reference](https://helm.sh/docs/helm/)
- [Chart best practices](https://helm.sh/docs/chart_best_practices/)
