# Uninstall

Use this guide to remove vstack-managed artifacts safely.

## Safety first

`vstack uninstall` removes only manifest-tracked artifacts in the selected scope.

By default, locally modified tracked files are preserved.

## Uninstall in a repository

From repository root:

```bash
vstack uninstall
```

Or use an explicit path:

```bash
vstack uninstall --target /path/to/repository
```

## Uninstall in global scope

Remove profile-scoped artifacts:

```bash
vstack uninstall --global
```

## Selective uninstall

Remove one artifact family:

```bash
vstack uninstall --only skill
```

Force-remove one modified artifact by name:

```bash
vstack uninstall --force-name verify
```

## Force behavior

Use force only after reviewing what is preserved by default.

```bash
vstack uninstall --force
```

This can remove modified tracked files that would otherwise be preserved.

## Verify result

For repository scope:

```bash
vstack manifest status
```

For global scope:

```bash
vstack manifest status --global
```

## Related docs

- [Global install](global-install.md)
- [Install and upgrade](install-and-upgrade.md)
- [CLI commands](../reference/cli-commands.md)
