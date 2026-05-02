# ADR-007: Python 3 as Canonical Runtime

> Maintained by: **architect** role

**date:** 2026-03-27\
**status:** accepted (consolidates superseded ADR-007/ADR-008 from DECISIONS.md)

## context

The toolchain was initially prototyped in TypeScript/Bun. In practice:

- Bun was not available on the development machines in use.
- Python implementations of the generator and validator covered 100% of the functionality.
- Maintaining two parallel implementations doubled the surface area for bugs.

## decision

**Python 3 is the sole canonical runtime** for vstack's toolchain.
The implementation lives in the `src/vstack/` package:

- `src/vstack/cli/` — CLI command handlers
- `src/vstack/artifacts/` — generic template generator
- `src/vstack/manifest/` — manifest read/write and upgrade
- `src/vstack/frontmatter/` — YAML frontmatter parsing and validation
- `tests/vstack/` — pytest test suite (100% coverage enforced)

Zero external Python dependencies at runtime. All runtime code uses stdlib only:
`re`, `json`, `pathlib`, `subprocess`, `sys`, `textwrap`, `hashlib`, `dataclasses`.

## alternatives considered

1. Keep TypeScript as canonical and install Bun — blocked by network/security constraints.
1. Keep both runtimes in sync — doubles maintenance, no benefit.
1. Use Node.js with npm — adds complexity for zero gain.

## rationale

Python 3.11–3.14 is the supported range, matching CI and type-checking compatibility
requirements. The package is distributed via PyPI with no runtime dependencies beyond
the Python standard library.

## impact on future orchestrated pipeline

The future orchestrated pipeline runner will be implemented in Python.
`asyncio` + `subprocess` provide sufficient primitives for sequential and parallel
stage execution.
