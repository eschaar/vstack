# Skills Overview

This page lists skills built into the installed vstack package and explains what each skill is used for.

## What Skills Are

Skills provide domain-specific execution playbooks. Agents use them to perform focused technical work.

In vstack, skills are generated into `.github/skills/<name>/SKILL.md`.

## Built-in Skills

| Skill                 | What It Helps With                                                        |
| --------------------- | ------------------------------------------------------------------------- |
| `adr`                 | Architecture Decision Record writing for significant technical decisions. |
| `analyse`             | Cross-cutting impact, tradeoff, and feasibility analysis.                 |
| `architecture`        | Engineering-lead architecture and execution-plan review.                  |
| `aws-cli`             | AWS CLI operations across core AWS services.                              |
| `cicd`                | GitHub Actions CI/CD workflow authoring and hardening.                    |
| `cloudformation`      | CloudFormation template authoring and review.                             |
| `code-review`         | Pre-merge review for bugs, regressions, and risk gaps.                    |
| `codeql`              | CodeQL scanning setup and workflow configuration.                         |
| `concise`             | Runtime response-density control (normal/compact/ultra).                  |
| `consult`             | DX-focused review with prioritized usability improvements.                |
| `container`           | Dockerfile and container runtime setup and hardening.                     |
| `conventional-commit` | Conventional Commit message preparation and validation.                   |
| `copilot-ops`         | Copilot policy/configuration operations and governance.                   |
| `debug`               | Root-cause-first debugging using scientific investigation flow.           |
| `dependabot`          | Dependabot configuration strategy for update hygiene.                     |
| `dependency`          | Dependency health audit, upgrade strategy, and supply-chain checks.       |
| `design`              | API and service interface design standards and contracts.                 |
| `docs`                | Post-release documentation alignment with shipped behavior.               |
| `explore`             | Repository architecture discovery and onboarding analysis.                |
| `gdpr`                | GDPR-compliant engineering review for data handling and flows.            |
| `gh-issues`           | GitHub issue lifecycle management via `gh`.                               |
| `gh-release`          | GitHub Release drafting and publication flow via `gh`.                    |
| `guardrails`          | Session safety controls for destructive-command confirmation.             |
| `helm`                | Helm chart authoring, upgrade, and release troubleshooting.               |
| `incident`            | Incident coordination, sequencing, and action definition.                 |
| `inspect`             | Read-only verification audit with severity-ranked findings.               |
| `k8s`                 | Kubernetes manifest authoring and operational troubleshooting.            |
| `migrate`             | Safe database migration planning and review.                              |
| `onboard`             | Contributor onboarding guide creation.                                    |
| `openapi`             | OpenAPI 3.1 specification writing and review.                             |
| `performance`         | Benchmarking, profiling, and performance regression analysis.             |
| `postmortem`          | Blameless stakeholder-facing incident postmortem writing.                 |
| `pr`                  | Commit/push and pull-request creation workflow support.                   |
| `rancher`             | Rancher and Fleet workload/governance operations.                         |
| `rca`                 | Technical root cause analysis for incidents and defects.                  |
| `refactor`            | Behavior-preserving structural refactoring.                               |
| `release-notes`       | Release note artifact and changelog preparation.                          |
| `requirements`        | Structured requirements gathering and documentation.                      |
| `secret-scan`         | Secret scanning and push-protection setup and triage.                     |
| `security`            | OWASP/STRIDE security audit across code and config.                       |
| `space-setup`         | Copilot Space setup and context quality management.                       |
| `terraform`           | Terraform IaC authoring and review.                                       |
| `terragrunt`          | Terragrunt DRY multi-environment configuration design.                    |
| `threat-model`        | Threat modeling with STRIDE-first prioritization.                         |
| `verify`              | Verification fix-loop with targeted re-checking.                          |
| `vision`              | Scope and strategy review from first principles.                          |

## Related Docs

- [Prompts overview](prompts-overview.md)
- [Instructions overview](instructions-overview.md)
- [Work items](work-items.md)
