---
name: git
description: 'Git and release hygiene conventions. Use when creating commits, branches, or release-related changes.'
applyTo: '**/*'
---
Use these Git and release hygiene conventions.

## Branch naming

1. Use `type/short-description` branch names.
1. Keep names lowercase and hyphenated.
1. Use one of these branch types when validation is enabled:
   `feature`, `bugfix`, `hotfix`, `release`, `chore`, `feat`, `fix`, `docs`,
   `refactor`, `perf`, `test`, `ci`, `build`, `style`, `opt`, `patch`, `dependabot`.

## Commit messages

1. Use Conventional Commits: `type(optional-scope)!: short summary`.
1. Keep subjects clear, imperative, and within repository limits.
1. Keep commit subjects at 100 characters or fewer when policy CI enforces that limit.
1. Add `!` or a `BREAKING CHANGE:` footer for breaking behavior.
1. Match type and scope to repository policy.

## SemVer alignment

1. Treat commit messages as release inputs when semantic version automation is in use.
1. Reflect major, minor, and patch intent in the commit type and breaking markers.
1. Do not merge release-impacting changes with ambiguous commit messages.

## Security and credentials

1. Never ask users to paste passphrases, tokens, API keys, or private keys into chat.
1. Never echo or log secrets from prompts, command output, or environment variables.
1. Never place credentials in commit messages, source files, workflow files, or documentation.
1. Prefer existing secure auth flows such as SSH agent, OS keychain, or `gh auth`.

## Safe Git operations

1. Avoid force pushes and destructive history rewrites unless explicitly requested and approved.
1. Keep commits focused and reviewable.
1. Prefer local verification before pushing release-impacting changes.

<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->
<!-- VSTACK-META: {"artifact_name":"git","artifact_type":"instruction","artifact_version":"20260421001","generator":"vstack","vstack_version":"3.6.0"} -->
