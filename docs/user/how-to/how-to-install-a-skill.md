# How to install a skill

Use this guide to include skill artifacts in your repository and verify that the result is managed correctly.

## Goal

Ensure the skills you want are generated under `.github/skills/` and not excluded by project config.

## 1. Confirm skill exclusions

Open `.vstack/config.yaml` and check the `exclude.skills` block.

- If `exclude.skills` contains a skill name, that skill is skipped.
- Remove the skill name (or remove the whole `exclude.skills` block) to include it.

Example exclusion block:

```yaml
exclude:
  skills:
    - terraform
    - helm
```

## 2. Regenerate skill artifacts

From repository root:

```bash
vstack init --only skill
```

This regenerates only the `skill` artifact family and applies your current exclusions.

If you are onboarding a repository that already has unmanaged skill files, adopt first when needed:

```bash
vstack init --only skill --adopt-name skill/<name>
```

## 3. Verify results

Check generated skill files:

```bash
ls .github/skills
```

Then verify managed state:

```bash
vstack manifest status --only skill
vstack manifest verify --only skill
```

## Related docs

- [Skills overview](../reference/skills-overview.md)
- [Configuration (`exclude` settings)](../reference/configuration.md#exclude-configuration)
- [Reinitialize](reinitialize.md)
