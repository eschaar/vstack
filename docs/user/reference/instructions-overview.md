# Instructions Overview

This page lists instruction sets built into the installed vstack package and explains where they apply.

## What Instructions Are

Instructions define repository conventions that apply automatically by file pattern.

In vstack, instructions are generated into `.github/instructions/*.instructions.md`.

## Built-in Instructions

| Instruction  | What It Helps With                                                                |
| ------------ | --------------------------------------------------------------------------------- |
| `git`        | Git and release hygiene conventions for branches, commits, and release workflows. |
| `helm`       | Helm chart conventions for chart templates and values files.                      |
| `java`       | Java coding conventions for source, tests, and build configuration.               |
| `k8s`        | Kubernetes manifest conventions for workloads and services.                       |
| `markdown`   | Markdown authoring standards for docs, READMEs, and ADRs.                         |
| `python`     | Python coding conventions for modules, tests, and CLI code.                       |
| `rancher`    | Rancher and Fleet conventions for governance and cluster config.                  |
| `security`   | Security policy for code, configuration, and infrastructure.                      |
| `terraform`  | Terraform coding conventions for modules and root configs.                        |
| `terragrunt` | Terragrunt conventions for DRY multi-environment setups.                          |
| `testing`    | Test authoring conventions for behavior-focused coverage.                         |
| `typescript` | TypeScript and JavaScript coding conventions.                                     |

## How Instructions Are Applied

- Each instruction has an `applyTo` pattern.
- Matching files inherit the instruction constraints.
- Multiple matching instructions can apply together.

## Related Docs

- [Configuration](configuration.md)
- [Skills overview](skills-overview.md)
- [Prompts overview](prompts-overview.md)
