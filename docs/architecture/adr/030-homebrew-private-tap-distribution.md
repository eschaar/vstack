# ADR-030: Homebrew Distribution via Private Tap

> Maintained by: **architect** role

**date:** 2026-06-02\
**status:** accepted

## context

vstack is currently distributed exclusively via PyPI (`pipx install vstack`). This
requires users to have a working Python environment and awareness of pip or pipx.

macOS and Linux users who prefer to manage installed CLI tools through Homebrew face
unnecessary friction. A second distribution channel eliminates that friction and
broadens the addressable install surface without altering the PyPI release process.

Two Homebrew distribution paths exist: publish to the community-managed
`Homebrew/homebrew-core` repository, or maintain a private tap
(`github.com/eschaar/homebrew-vstack`).

## decision

Distribute vstack via a **private Homebrew tap** now. Evaluate submission to
`Homebrew/homebrew-core` after the project accumulates stable release history and
demonstrable adoption.

The formula uses the **sdist tarball** published to PyPI as its source artifact.
Homebrew's `Language::Python::Virtualenv` mixin installs the sdist into an isolated
virtualenv alongside declared resource blocks for runtime dependencies. The sdist URL
and SHA-256 are sourced from the PyPI JSON API at publish time, not hardcoded.

The Homebrew publish step is a **third, sequential stage** in the existing release
pipeline, triggered only after the PyPI publish job succeeds and only for non-pre-release
tags.

Supply-chain controls are mandatory from day one:

- Dual SHA-256 verification: PyPI JSON metadata is cross-checked against the locally
  downloaded tarball before the formula is updated.
- A dedicated fine-grained PAT with `contents: write` scope limited to the tap repo
  is stored as `HOMEBREW_TAP_TOKEN` in the `pypi` Actions environment.
- The tap repo's `formula-update.yml` is triggered via `repository_dispatch`; direct
  external triggering is not accepted.
- All Actions in both the publish workflow and the tap repo workflows are pinned to
  full commit SHAs.
- Branch protection on the tap repo's `main` branch requires the `test.yml` formula
  check to pass before any commit lands.

## alternatives considered

- **Submit directly to `homebrew-core`** — requires 30-day PyPI history, notable
  adoption, and maintainer-reviewed PRs for every version bump. vstack does not yet
  meet the acceptance bar. Release autonomy would be lost.
- **Use the wheel instead of the sdist** — Homebrew's virtualenv mixin expects a source
  distribution. Using a wheel is non-standard for formula authoring and bypasses the
  compile-from-source path that Homebrew prefers for purity.
- **Maintain no Homebrew distribution** — leaves a friction gap for users who manage
  CLI tools exclusively through Homebrew. The private tap adds minimal ongoing
  maintenance cost given the automated formula update pipeline.

## rationale

A private tap provides immediate installation convenience with full release autonomy.
The formula update is fully automated through the existing `publish.yml` pipeline.
The supply-chain threat surface is narrow: a single sdist tarball with dual-verified
SHA-256, a scoped PAT, and a protected tap branch. The incremental maintenance cost
is low: a single additional CI job and a small tap repository.

Homebrew-core submission is kept as an explicit optional path. When the project meets
the acceptance criteria, the formula is already in shape for submission — the private
tap formula and the homebrew-core formula are structurally identical.

## impact

- **Release pipeline**: `publish.yml` gains a `publish-homebrew` job that runs after
  the `publish` job, conditioned on `github.event.release.prerelease == false`.
- **New repository**: `github.com/eschaar/homebrew-vstack` with `Formula/vstack.rb`,
  `formula-update.yml`, and `test.yml`.
- **Secrets**: `HOMEBREW_TAP_TOKEN` added to the `pypi` Actions environment.
- **NFR**: A new supply-chain NFR (NFR-8) binds the dual-verify requirement and
  pre-release exclusion to the Homebrew publish stage.
- **User-facing**: install instructions in `README.md` after bootstrap is validated.
- **PyPI remains primary**: PyPI is the canonical release artifact; Homebrew wraps it.
  No change to the PyPI publish path.

## impact on future orchestrated pipeline

The Homebrew stage is release-pipeline infrastructure, not part of the vstack agent
workflow. It does not affect the planner-orchestrated role pipeline (ADR-024, ADR-029).
