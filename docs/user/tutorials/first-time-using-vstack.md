# First time using vstack

This tutorial introduces the minimal happy path for running vstack in a repository.

## Goal

By the end, you can install vstack artifacts and understand where generated files live.

## Prerequisites

1. `pipx` is installed.
1. You are in a repository where vstack should be installed.

## Steps

1. Install vstack:

```bash
pipx install vstack
vstack --version
```

1. From repository root, install managed artifacts:

```bash
vstack install
```

1. Validate the baseline setup:

```bash
vstack validate
```

1. Review generated output under `.github/`.
1. Review project-scoped state under `.vstack/`.

## What to do with `.vstack/templates`

After `vstack install`, you may see starter templates under `.vstack/templates/`.

- Treat these as project-owned stubs you can adapt for your team.
- Keep useful edits there for local project guidance.
- Do not expect edits in `.vstack/templates/` to regenerate `.github/` artifacts.

Use `vstack init` to regenerate managed `.github/` artifacts from current vstack templates and project config.

## Result

You now have a baseline vstack installation and can continue with task-specific how-to guides.

## Next steps

- [First planner run](first-planner-run.md)
- [Fresh install](../how-to/fresh-install.md)
- [CLI commands](../reference/cli-commands.md)
- [What `.vstack/templates` is for](../explanation/vstack-templates.md)
