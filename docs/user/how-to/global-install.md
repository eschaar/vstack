# Global install

Use global install when you want vstack artifacts in your VS Code user profile instead of a single repository.

## When to choose global install

Use `--global` when you want:

- one shared setup across multiple repositories,
- personal defaults in your VS Code user scope,
- no repository-local `.vstack/` project scaffold.

Use repository install when you need project-specific configuration and committed artifacts.

## Install globally

```bash
vstack install --global
```

Install selected artifact families only:

```bash
vstack install --global --only agent skill prompt instruction hook
```

## Update global artifacts

After upgrading the CLI:

```bash
pipx upgrade vstack
vstack init --global
```

## Verify global state

```bash
vstack manifest status --global
vstack manifest verify --global
```

## Notes

- Global install does not seed repository `.vstack/config.yaml`.
- Repository exclusions in `.vstack/config.yaml` do not apply to global scope.
- Use `--only` for selective global generation.

## Related docs

- [Install and upgrade](install-and-upgrade.md)
- [Uninstall](uninstall.md)
- [CLI commands](../reference/cli-commands.md)
