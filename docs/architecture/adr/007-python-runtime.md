# ADR-007: Python 3 as Canonical Runtime

> Maintained by: **agents** role

**date:** 2026-03-27\
**status:** accepted (consolidates superseded ADR-007/ADR-008 from DECISIONS.md)

## context

The toolchain was initially prototyped in TypeScript/Bun. In practice:

- Bun was not available on the development machines in use.
- Python implementations of the generator and validator covered 100% of the functionality.
- Maintaining two parallel implementations doubled the surface area for bugs.

## decision

**Python 3 is the sole canonical runtime** for vstack's toolchain:

- `scripts/gen_skill_docs.py` — template generator
- `scripts/validate_skills.py` — skill validation
- `scripts/skill_check.py` — health dashboard
- `test/test_skills.py` — test suite (pytest)

`package.json` is kept as a convenience wrapper (`npm run build` etc.) but no
`node_modules` are installed.

Zero external Python dependencies. All scripts use stdlib only:
`re`, `json`, `pathlib`, `subprocess`, `sys`, `textwrap`.

## alternatives considered

1. Keep TypeScript as canonical and install Bun — blocked by network/security constraints.
1. Keep both runtimes in sync — doubles maintenance, no benefit.
1. Use Node.js with npm — adds complexity for zero gain.

## rationale

Python 3.11+ is universally available on macOS, Linux, and CI systems.
The entire toolchain is under 1000 lines of Python 3 with zero external dependencies.

## impact on future orchestrated pipeline

The future orchestrated pipeline runner (`scripts/runner.py`) will be implemented in Python.
`asyncio` + `subprocess` provide sufficient primitives for sequential and parallel
stage execution.
