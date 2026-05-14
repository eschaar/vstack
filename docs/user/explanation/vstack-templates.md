# What `.vstack/templates` is for

This page explains the role of `.vstack/templates/` in a repository installation.

## What it is

When you run `vstack install` in a repository, vstack can seed starter files under `.vstack/templates/`.

These files are project-owned guidance stubs. They help teams document local role workflows and artifact patterns.

## Ownership and update model

- Existing files in `.vstack/templates/` are not overwritten by later `vstack init` runs.
- New files may be added by newer vstack versions.
- Files in this directory are outside manifest-managed `.github/` artifact checks.

## What to do with these stubs

- Keep useful stubs and adapt them to your team conventions.
- Commit your local edits if they are part of your repository workflow.
- Use them as project-local guidance, not as generated output.

## What not to expect

Editing `.vstack/templates/` does not regenerate `.github/` artifacts.

Use `vstack init` to regenerate managed artifacts under `.github/` from installed vstack templates and your `.vstack/config.yaml` settings.

## Related docs

- [Fresh install](../how-to/fresh-install.md)
- [Install and upgrade](../how-to/install-and-upgrade.md)
- [Configuration](../reference/configuration.md)
