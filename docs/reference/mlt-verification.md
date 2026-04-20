# MLT Verification Record

**Date:** 2026-04-20
**Verdict:** ADOPT (via conda-forge) — install unblocked by user

**User ruling (2026-04-20):** conda-forge 600MB overhead is acceptable. Install via
`conda install -c conda-forge mlt` and proceed with MLT integration.

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

**ADOPT via conda-forge** — User confirmed conda-forge overhead (~600 MB) is acceptable.

Install: `conda install -c conda-forge mlt`

This unlocks:
- `melt` CLI (Gate 1: PASS after install)
- Python `mlt` or `mlt7` bindings
- AVI input via MLT's FFmpeg producer (Gate 2: expected PASS)
- Phase 4 CLI can ship a conda-aware variant or a Docker image (Gate 3: PASS)

**Action items:**
1. Install: `conda install -c conda-forge mlt` on this machine
2. Re-run Gate 1 and Gate 2 after install (verify melt handles `.avi` clips)
3. Write a `creative_suite/engine/mlt_pipeline.py` as optional render path
4. Gate: if MLT render quality matches FFmpeg at CRF 15-17, replace P1-BB concat with MLT XML pipeline for Parts 7-12

The existing direct-FFmpeg pipeline remains the default until Gate 2 is confirmed.
