# Prompt Migration

The next major version removes vstack's prompt artifact family. The VS Code Copilot
harness does not load `*.prompt.md` files; Local harness sessions still support
them. vstack now supplies reusable workflows as skills in
`.github/skills/<name>/SKILL.md`.

## Replacement Commands

| Retired prompt       | Replacement skill | Change                                                                   |
| -------------------- | ----------------- | ------------------------------------------------------------------------ |
| `api-design-review`  | `openapi`         | Reuse API contract writing and review.                                   |
| `architecture-risk`  | `architecture`    | Reuse architecture and execution-plan review.                            |
| `artifact-integrity` | `inspect`         | Reuse repository auditing; the source-specific skill is repository-only. |
| `ci-triage`          | `debug`           | Reuse root-cause investigation for CI failures.                          |
| `dependency-audit`   | `dependency`      | Reuse dependency health auditing.                                        |
| `incident-timeline`  | `postmortem`      | Reuse incident timeline and postmortem workflow.                         |
| `migration-plan`     | `migration-plan`  | New explicit-only cross-component planning skill.                        |
| `migration-safety`   | `migrate`         | Reuse database migration review.                                         |
| `ops-readiness`      | `inspect`         | Reuse reliability and observability auditing.                            |
| `quick-review`       | `code-review`     | Reuse pre-landing review.                                                |
| `reasoning`          | `reasoning`       | New explicit-only reasoning framework.                                   |
| `release-check`      | `release-check`   | New explicit-only release evidence audit, not release publication.       |
| `repo-assessment`    | `inspect`         | Reuse repository verification audit.                                     |
| `template-impact`    | `analyse`         | Reuse impact analysis.                                                   |
| `test-gaps`          | `inspect`         | Reuse test and verification auditing.                                    |
| `upgrade-plan`       | `upgrade-plan`    | New explicit-only upgrade planning skill.                                |
| `workflow-check`     | `workflow-check`  | New explicit-only stage, gate, and handoff audit.                        |

Invoke skills with `/name`, for example `/code-review`. References such as
`prompt/reasoning` become `skill/reasoning`. Existing replacement skills keep their
own procedure and output format; the old prompt output contracts are not aliases.
For example, `debug` may proceed to a fix and `inspect` can run checks; request a
report-only scope when that is what you need.

Converted skills have `user-invocable: true` and `disable-model-invocation: true`.
Their bodies and output sections are preserved, but prompt-specific `agent`,
`model`, and `tools` selection is not. Select a role agent separately when needed.
The skills' `allowed-tools` metadata is not a replacement for runtime permissions.

## Upgrade Safely

After upgrading the CLI, preview and apply the artifact migration:

```bash
vstack init --dry-run
vstack init
vstack manifest verify
```

`vstack install` performs the same artifact migration. `vstack migrate` handles
role-document paths, not prompt conversion. Installing the Python package alone
does not change repository files.

During an install with skills selected:

1. Generate and install replacement skills using conservative install rules.
1. Inspect legacy `prompts` entries in the install manifest.
1. Remove only known, canonical, non-symlinked prompt files matching their stored
   checksum and whose replacement skill was installed or verified unchanged.
1. Remove their manifest entries and empty prompt directories.

No `--prune` flag is needed for this targeted retirement. Other obsolete artifact
cleanup still requires `init --prune`.

`artifact-integrity` is maintained only in the vstack source repository as a
hand-authored skill. Fresh installations do not receive it. If an earlier build
installed a managed copy, `init` reports it as obsolete; `init --prune` removes
it only when its stored checksum still matches. Locally modified copies are
preserved. Untracked repository-only skills remain untouched, including with
`--force` and `--prune`.

Untracked files are never touched. Modified, unreadable, checksum-less, unknown,
or unsafe-path prompts are preserved, reported, and kept in the manifest for
retry. Missing old files can be cleared from tracking after the replacement is
available. `--force` does not bypass prompt deletion safeguards.

If skills are not selected, or a replacement skill is excluded, locally modified,
untracked, or merely adopted, migration is deferred. Resolve the reported conflict
and rerun `vstack init`. Review and migrate preserved custom workflows manually;
vstack does not delete unknown custom prompts or scan directories for ownership.

Deletion errors are reported with a nonzero exit code. The prompt's manifest entry
is retained, so you can resolve the filesystem error and retry without losing
ownership information.

## Breaking Interfaces

- `--only prompt` is no longer a valid CLI filter.
- `prompt/<name>` is no longer an install, force, or adoption selector.
- `vstack.prompts`, `PromptGenerator`, and `PROMPT_SCHEMA` are removed.
- Custom template packs must replace their prompt templates with skill templates.
- `exclude.prompts` is retired and warns when read. Replace it with appropriate
  `exclude.skills` entries; it no longer disables the replacement workflows.
- Legacy manifest `prompts` entries remain readable for safe migration. Do not
  hand-edit the manifest to claim ownership of files.

See [ADR-032](../../architecture/adr/032-skills-replace-prompts.md) and the
[VS Code migration guide](https://code.visualstudio.com/docs/agent-customization/migrate-customizations#_convert-prompt-files-to-skills).

## Related Docs

- [Skills overview](skills-overview.md)
- [Instructions overview](instructions-overview.md)
- [Work items](work-items.md)
