# ADR-025: Introduce PyYAML as Sole Runtime Dependency

> Maintained by: **architect** role

**date:** 2026-05-09\
**status:** accepted\
**amends:** ADR-006 (scope clarification — see that document)

## context

vstack was initially released with `dependencies = []`, keeping `pip install vstack`
free of any transitive pulls. The frontmatter parser (`FrontmatterParser._parse_yaml_block`)
was hand-rolled specifically to preserve that property.

The YAML subset that vstack must parse has grown steadily as new config features were
added — `defaults:` blocks, `baseline:` flags, `hitl:` fields, `workflow:` blocks with
nested `stages` / `handoffs` object-lists, and raw mapping blocks for MCP-server config.
The parser now handles eight distinct structural cases, each represented by its own
state-machine flag, and relies on fragile indentation-level checks
(`line.startswith("  ")`, `"    "`, `"      "`) with no named constants and no
protection against tabs or irregular indentation.

Continuing to extend the hand-rolled parser as the config schema grows is a maintenance
liability that outweighs the benefit of zero runtime dependencies.

## decision

- Add `pyyaml` as the sole entry in `[project] dependencies` in `pyproject.toml`.
- Replace the `_parse_yaml_block` state-machine body with a single `yaml.safe_load` call.
- Keep the `FrontmatterContent` dataclass and `FrontmatterParser.parse` / `parse_yaml`
  public API surface unchanged so all callers remain unaffected.
- Retain `FrontmatterParser` as a class and its static methods; only the internal
  `_parse_yaml_block` implementation changes.

## alternatives considered

- **Keep the hand-rolled parser** — avoids the dependency but means every new config
  key may require new state-machine branches and indentation heuristics. Risk grows
  linearly with schema complexity.
- **Use `ruamel.yaml`** — preserves comments and round-trips YAML faithfully; valuable
  for tools that rewrite config files. vstack only reads config at install time, so
  round-trip fidelity is not needed. `ruamel.yaml` also carries more transitive weight
  than PyYAML.
- **Restrict the config schema** — deliberately keep frontmatter simple enough for the
  hand-rolled parser. This constrains future workflow and orchestration features
  (ADR-023, ADR-024) that already depend on nested YAML structures.
- **Optional dependency with stdlib fallback** — adds dead code paths and makes test
  coverage of the fallback artificial. The fallback would need its own maintenance,
  negating most of the benefit.

## rationale

PyYAML is the reference YAML 1.1 implementation for Python. It ships as a single
compiled wheel, has no runtime dependencies of its own on CPython 3.x, and is already
a transitive dependency of the vast majority of Python projects. `yaml.safe_load` has
a strong security track record when object deserialization is disabled (which `safe_load`
enforces by construction).

The trade-off is clear: one well-audited, widely-deployed library in exchange for
permanently removing a class of parser fragility from the codebase.

## impact

- `pip install vstack` will pull `pyyaml` (≈ 143 kB wheel on CPython).
- `pyproject.toml`: `dependencies = ["pyyaml>=6.0"]`.
- `FrontmatterParser._parse_yaml_block`: implementation replaced; public API unchanged.
- Tests: existing parser tests continue to pass against the new implementation;
  test_parser coverage remains at 100 %.
- ADR-006 is amended with a scope note; its decision (no external binaries in skill
  content) is unaffected.

## impact on future orchestrated pipeline

The orchestrated pipeline runner (ADR-024) generates and reads `config.yaml` files
for each agent. Having a proper YAML parser available as a runtime dependency means
those config files can use the full YAML 1.1 feature set without risking parser
regressions.
