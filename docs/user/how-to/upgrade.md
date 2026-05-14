# Upgrade

Use this guide to upgrade vstack in an existing repository while keeping local project configuration.

## 1. Upgrade the CLI

```bash
pipx upgrade vstack
vstack --version
```

## 2. Re-generate Managed Artifacts

```bash
vstack init
```

`vstack init` is idempotent. You can run it repeatedly after upgrades.

## 3. Verify After Upgrade

The commands in this guide assume you run them from the repository root, so `--target` is omitted.

```bash
vstack validate
vstack manifest status
vstack manifest verify
```

## 4. Major Upgrade Path

For major version jumps, migrate docs artifacts first:

```bash
vstack migrate
vstack init
```

Preview migration without writing files:

```bash
vstack migrate --dry-run
```

For multi-major jumps:

```bash
vstack migrate --from 1 --to 3
vstack init
```

## 5. Legacy Manifest Upgrade

If you get a legacy manifest schema warning:

```bash
vstack manifest upgrade
vstack init
vstack manifest status
```

## Related Docs

- [Install and upgrade](install-and-upgrade.md)
- [Partial upgrade](partial-upgrade.md)
- [Reinitialize](reinitialize.md)
- [CLI commands](../reference/cli-commands.md)
