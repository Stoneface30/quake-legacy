# MLT Verification Record

**Date:** 2026-04-20
**Verdict:** DEFER

## Gate 1: Availability

All three availability checks failed on this machine (Windows 11, Python 3.11):

- `melt --version` → **not found** (MLT CLI not in PATH)
- `python -c "import mlt7; ..."` → **not found** (no mlt7 Python binding installed)
- `python -c "import mlt; ..."` → **not found** (no mlt Python binding installed)
- `pip show mlt` / `pip show mlt7` → **not on pypi** (packages not installed)

**Gate 1 result: FAIL**

## Gate 2: AVI Compatibility

Skipped — Gate 1 failed (melt binary unavailable, cannot test AVI handling).

**Gate 2 result: SKIP**

## Gate 3: Cross-platform Deployment

Research into clean install paths for the target public CLI audience (Windows/Mac/Linux):

- `pip install mlt` → `ERROR: No matching distribution found for mlt` (not on PyPI)
- `pip install mlt7` → `ERROR: No matching distribution found for mlt7` (not on PyPI)
- PyPI search: no package named `mlt` or `mlt7` exists on PyPI as of 2026-04-20
- conda: not available in this environment; conda-forge does host `mlt` but it is a
  platform-specific native build requiring a separate conda stack, not pip-installable

MLT is a C library with optional Python bindings compiled against a specific MLT install.
There is no cross-platform `pip install` path. On Windows, MLT is available via:
- Shotcut installer (bundles melt.exe + Python bindings, not suitable for headless deploy)
- vcpkg (complex native build, no pre-built wheel)
- conda-forge (adds ~600 MB conda stack dependency)

None of these constitute a deployable dependency for a `pip install quake-legacy` CLI.

**Gate 3 result: FAIL**

## Decision

**DEFER** — MLT is not available on this machine, not installable via pip, and has no
cross-platform pip deployment path. The project's Phase 4 public CLI vision requires
`pip install quake-legacy` to work cleanly on Windows/Mac/Linux without a separate
native library install. MLT cannot satisfy that constraint today.

The existing direct-FFmpeg pipeline (`creative_suite/engine/`, P1-BB split graph +
PCM WAV + CFR) remains the correct approach. No migration needed.

## If DEFERRED: Next action

Revisit this decision if **any** of the following change:

1. An `mlt` or `mlt7` wheel appears on PyPI with Windows/Mac/Linux support
   (check: `pip index versions mlt` — currently returns no versions)
2. MLT gains a conda-forge package that can be declared as an optional conda dep
   without breaking the pip install path for non-conda users
3. The Phase 4 deployment target shifts to a Docker image (in which case
   `apt install melt` in the Dockerfile is trivial and Gate 3 would PASS)

To re-run these gates: repeat the three commands in Gate 1 and Gate 3, then
re-evaluate against the decision table in the P3-T5 spec.
