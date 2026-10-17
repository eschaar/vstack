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

Python 3.11–3.15 is the supported and tested range. Python 3.14 is the default
development, build, and single-version CI runtime; compatibility targets for
linters and type checkers remain at Python 3.11.

As of 2026-10-17, the project adds Python 3.15 while retaining Python 3.11,
which receives upstream security support until October 2027. Dropping 3.11
would reduce the validation range but unnecessarily exclude existing consumers;
defaulting to 3.15 would adopt the newest runtime immediately. Instead, 3.14
remains the stable default while the full suite validates 3.11 through 3.15.
Package metadata declares `>=3.11` without an upper bound; future versions are
not claimed as tested until added to the matrix.

The repository pins the default interpreter to Python 3.14.8 and lists exact
patch versions for the other supported minors in `.python-version`. CI uses the
latest available patch in each selected minor. Existing virtual environments
are not automatically recreated when these pins change.

## impact on future orchestrated pipeline

The future orchestrated pipeline runner will be implemented in Python.
`asyncio` + `subprocess` provide sufficient primitives for sequential and parallel
stage execution.
Any future orchestrated pipeline runner must also support Python 3.11–3.15;
the default interpreter does not permit using Python 3.14-only APIs in shared code.
