# Security Report

**Branch:** `chore/split-docs-and-hardening`\
**Date:** 2026-05-14\
**Scope:** Current repository snapshot using static analysis and dependency audit.\
**Method:** OWASP Top 10 + STRIDE framing for a local CLI tool (no network/auth/database surface), with local dependency remediation and re-audit.

______________________________________________________________________

## Verdict

| Category                 | Findings                          | Blocking                                 |
| ------------------------ | --------------------------------- | ---------------------------------------- |
| Static analysis (bandit) | 1 LOW                             | No — informational; import advisory only |
| Dependency CVEs          | 0 known CVEs in current local env | No                                       |
| Secrets in source        | None                              | —                                        |
| Injection risk           | None identified                   | —                                        |
| Auth / access control    | N/A (local CLI, no network)       | —                                        |

> **Ship readiness: PASS** — no blocking security findings and local tooling advisories were remediated.

______________________________________________________________________

## OWASP Top 10 Assessment

This is a **local CLI tool** — no web server, no user sessions, no database, no network endpoints. Most OWASP categories are not applicable. Relevant categories are assessed below.

| #   | Category                  | Status | Notes                                                                       |
| --- | ------------------------- | ------ | --------------------------------------------------------------------------- |
| A01 | Broken Access Control     | N/A    | Local filesystem operations only                                            |
| A02 | Cryptographic Failures    | PASS   | No cryptographic operations in source                                       |
| A03 | Injection                 | PASS   | Subprocess uses fixed list args (no shell=True, no user-interpolated input) |
| A04 | Insecure Design           | PASS   | No privileged operations, no credential storage                             |
| A05 | Security Misconfiguration | PASS   | No config files with secrets; no exposed ports                              |
| A06 | Vulnerable Components     | PASS   | Local environment advisories remediated and re-verified                     |
| A07 | Auth / Identity Failures  | N/A    | No authentication surface                                                   |
| A08 | Software/Data Integrity   | PASS   | Checksums used for artifact validation in install/uninstall                 |
| A09 | Logging Failures          | PASS   | No sensitive data logged                                                    |
| A10 | SSRF                      | N/A    | No HTTP client usage                                                        |

______________________________________________________________________

## Static Analysis Findings (bandit)

```
bandit -r src/
Run started: 2026-05-14 14:22:20+00:00
Issues: 1  HIGH=0  MED=0  LOW=1
  [LOW] B404  vstack/constants.py:6 — Consider possible security implications associated with the subprocess module.
```

### S-001 — B404 subprocess import (LOW, informational)

**File:** `src/vstack/constants.py:6`

```python
import subprocess
```

Bandit flags any file that imports `subprocess`. This is a blanket informational note, not a finding tied to unsafe usage. The actual call site remains guarded (`# nosec B603 B607`) and uses a fixed arg list.

**Severity:** LOW — informational; not actionable.

______________________________________________________________________

## Dependency Audit (pip-audit)

Path note:

- CI workflow uses `pip-audit --requirement <(poetry export --without-hashes -f requirements.txt)`.
- In this local environment, `poetry export` is unavailable (`The requested command export does not exist`).
- Closest repo-used equivalent for local verification: direct `pip-audit` against the active virtualenv.

### Initial reproduction (before remediation)

```bash
source .venv/bin/activate
pip-audit
```

```text
Found 4 known vulnerabilities in 2 packages
pip 26.0.1     CVE-2026-3219
pip 26.0.1     CVE-2026-6357  fixed in 26.1
urllib3 2.6.3  CVE-2026-44431 fixed in 2.7.0
urllib3 2.6.3  CVE-2026-44432 fixed in 2.7.0
```

### Remediation applied

```bash
source .venv/bin/activate
python -m pip install --upgrade 'pip>=26.1' 'urllib3>=2.7.0'
```

Installed versions:

- `pip 26.1.1`
- `urllib3 2.7.0`

### Final verification

```
security check window (UTC): 2026-05-14T14:22:18Z → 2026-05-14T14:22:20Z
command: pip-audit
result: No known vulnerabilities found

note: pip-audit reports one non-blocking skip item for local package `vstack (0.0.0)` because it is not published on PyPI.
```

### S-002 — dependency advisories in local tooling environment (RESOLVED)

`pip-audit` initially reported advisories in local tooling packages (`pip`, `urllib3`). Those packages were upgraded in the active virtual environment and re-audited.

**Final status:** resolved.

______________________________________________________________________

## STRIDE Assessment

| Threat                 | Relevant surface                                  | Finding                               |
| ---------------------- | ------------------------------------------------- | ------------------------------------- |
| Spoofing               | No network/auth                                   | N/A                                   |
| Tampering              | Artifact checksums verified on uninstall          | PASS                                  |
| Repudiation            | No audit trail for local file ops                 | LOW — acceptable for a local dev tool |
| Information disclosure | No secrets stored, no network calls               | PASS                                  |
| Denial of service      | No resource-intensive loops exposed to user input | PASS                                  |
| Elevation of privilege | No sudo/elevated ops                              | PASS                                  |

______________________________________________________________________

## Secrets Scan

```
grep -r -E '(password|secret|api_key|token)\s*[=:]\s*["'\''][^"'\'']{8,}'  →  No matches in src/
```

No hardcoded secrets found.

______________________________________________________________________

## Summary of Advisory Items

| ID    | Severity | Location / package         | Action                                                         |
| ----- | -------- | -------------------------- | -------------------------------------------------------------- |
| S-001 | LOW      | `src/vstack/constants.py`  | Keep B404 import advisory documented; no unsafe subprocess use |
| S-002 | LOW      | `pip`, `urllib3` (dev env) | **Resolved** by upgrading to `pip 26.1.1` and `urllib3 2.7.0`  |

No remaining dependency CVEs were detected in the audited local environment. No security item blocks release.
