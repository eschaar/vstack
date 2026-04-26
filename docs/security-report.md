# Security Report

**Branch:** `feat/improved_cli`
**Date:** 2026-04-26
**Scope:** Full source tree — static analysis (bandit) + dependency audit (pip-audit); security fixes for S-001 (assert guards) and S-002 (subprocess nosec)
**Method:** OWASP Top 10 + STRIDE (static analysis on a local CLI tool; no network surface, no auth surface, no DB)

______________________________________________________________________

## Verdict

| Category                 | Findings                    | Blocking                                 |
| ------------------------ | --------------------------- | ---------------------------------------- |
| Static analysis (bandit) | 1 LOW                       | No — informational; import advisory only |
| Dependency CVEs          | 1 (pip, LOW)                | No — dev/build tooling only              |
| Secrets in source        | None                        | —                                        |
| Injection risk           | None identified             | —                                        |
| Auth / access control    | N/A (local CLI, no network) | —                                        |

> **Ship readiness: PASS with notes** — no blocking security findings. Advisory items documented below.

______________________________________________________________________

## OWASP Top 10 Assessment

This is a **local CLI tool** — no web server, no user sessions, no database, no network endpoints. Most OWASP categories are not applicable. Relevant categories are assessed below.

| #   | Category                  | Status   | Notes                                                                       |
| --- | ------------------------- | -------- | --------------------------------------------------------------------------- |
| A01 | Broken Access Control     | N/A      | Local filesystem operations only                                            |
| A02 | Cryptographic Failures    | PASS     | No cryptographic operations in source                                       |
| A03 | Injection                 | PASS     | Subprocess uses fixed list args (no shell=True, no user-interpolated input) |
| A04 | Insecure Design           | PASS     | No privileged operations, no credential storage                             |
| A05 | Security Misconfiguration | PASS     | No config files with secrets; no exposed ports                              |
| A06 | Vulnerable Components     | ADVISORY | pip 26.0.1 has CVE-2026-3219 (dev tooling, not shipped)                     |
| A07 | Auth / Identity Failures  | N/A      | No authentication surface                                                   |
| A08 | Software/Data Integrity   | PASS     | Checksums used for artifact validation in install/uninstall                 |
| A09 | Logging Failures          | PASS     | No sensitive data logged                                                    |
| A10 | SSRF                      | N/A      | No HTTP client usage                                                        |

______________________________________________________________________

## Static Analysis Findings (bandit)

```
bandit -r src/
Issues: 1  HIGH=0  MED=0  LOW=1
  [LOW] B404  vstack/constants.py:6 — Consider possible security implications associated with the subprocess module.
```

### S-001 — `assert` used for runtime validation (RESOLVED)

**File:** `src/vstack/cli/report.py:224, 241, 243` (fixed)

**Resolution:** Replaced all three `assert isinstance(...)` guards with explicit `if not isinstance(...): raise TypeError(...)` guards. These now execute correctly in optimised builds (`python -O`) and are no longer flagged by bandit.

______________________________________________________________________

### S-002 — subprocess call flagged (RESOLVED)

**File:** `src/vstack/constants.py:53` (fixed)

**Resolution:** Added `# nosec B603 B607` comment at the `subprocess.check_output(...)` call to suppress the advisory and make the review decision explicit. The call uses a fixed argument list (`["git", "-C", str(repo_root), "tag", "--points-at", "HEAD"]`), no `shell=True`, and no user-controlled input. It remains safe.

The remaining bandit finding (B404 at line 6) is an **import-level advisory** with no associated code risk. It cannot be suppressed without disabling B404 globally.

______________________________________________________________________

### S-003 (residual) — B404 subprocess import (LOW, informational)

**File:** `src/vstack/constants.py:6`

```python
import subprocess
```

Bandit flags any file that imports `subprocess`. This is a blanket informational note, not a finding tied to unsafe usage. The actual call (line 53) is safe and suppressed via `# nosec B603 B607`.

**Severity:** LOW — informational; not actionable.

______________________________________________________________________

## Dependency Audit (pip-audit)

```
pip-audit result:
  Name  Version  ID             Fix Versions
  pip   26.0.1   CVE-2026-3219  (none listed)
```

### CVE-2026-3219 — pip tar+ZIP dual-format handling

pip processes concatenated tar+ZIP archives as ZIP regardless of filename, potentially leading to incorrect file installation from ambiguous archives.

**Assessment:** This affects `pip` itself as a **build/dev tool**, not vstack's shipped package or any runtime dependency. vstack has no runtime dependencies beyond Python stdlib. Users installing vstack from PyPI are not exposed by this CVE in any production path.

**Recommendation:** Upgrade pip in the development virtualenv (`pip install --upgrade pip`) once a fixed version is released. Track the CVE for a fix version.

**Severity:** LOW — dev tooling only; not a shipping blocker.

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

| ID    | Severity | File                        | Action                                                             |
| ----- | -------- | --------------------------- | ------------------------------------------------------------------ |
| S-001 | LOW      | `cli/report.py:224,241,243` | Replace `assert` with explicit `TypeError` guards                  |
| S-002 | LOW      | `constants.py:53`           | Add `# nosec B603 B607` to suppress false-positive bandit advisory |
| S-003 | LOW      | `pip 26.0.1`                | Upgrade pip in dev venv when fix is available                      |

None of these items block release.
