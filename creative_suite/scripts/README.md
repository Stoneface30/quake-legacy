# scripts/ — Pipeline Utilities

Operational utilities for the Quake Legacy pipeline. Each script is self-contained and safe to run
from the repo root with `PYTHONPATH=. python scripts/<name>.py`.

---

## Clip-list integrity (Phase 1)

These two are **mandatory pre-flight** before any Part render. Skip them and you ship a broken mix.

### `rescan_clips.py` — disk-authoritative styleb rebuilder

Walks `QUAKE VIDEO/T{1,2,3}/PartN/` and produces the canonical `partNN_styleb.txt` from ground truth.

**Why it exists.** The styleb files are hand-edited. Drift between disk and list produces two
classes of failure:

1. **Cut frags** — a new FL angle lands on disk but never makes it into the styleb.
2. **Broken multi-angle grammar** — FL clips listed on consecutive lines (instead of the
   `FP > FL1 > FL2` grammar Rule P1-K requires) get rendered as separate frags, producing
   4-angle ping-pong instead of the intended FP-backbone + one FL slow-contrast replay.

**What it does.**

- Groups AVIs by **subdirectory** (not demo number — the same demo can produce multiple distinct
  frags in the same Part; grouping by number collapses them).
- Root-level AVIs are singles. Each non-root subdirectory contains exactly one non-FL AVI (the FP
  anchor) plus zero or more `Demo (NFL1).avi`, `Demo (NFL2).avi` files that attach to that anchor.
- Emits `FP > FL1 > FL2` as a single line so `phase1/clip_list.py::parse_clip_entry` triggers
  Rule P1-K. FL angles are sorted by index so replay ordering is deterministic.
- Tier-groups the output: T1 multi-angle first, then T1 singles, then T2, then T3.
- Cross-checks each entry against `resolve_clip_path()` — flags `ghosts_in_styleb` (references not
  on disk) and `orphans_on_disk` (files on disk missing from styleb).

**Usage.**

```bash
# Dry-run audit for Parts 4, 5, 6, 7 (default):
PYTHONPATH=. python scripts/rescan_clips.py

# Audit a single Part:
PYTHONPATH=. python scripts/rescan_clips.py --parts 6

# Rebuild the styleb in place (destructive):
PYTHONPATH=. python scripts/rescan_clips.py --apply --parts 4 5 6 7
```

**Outputs.**

- `output/clip_audit_partNN.json` — structured audit (per-tier frag/multi counts, orphans, ghosts,
  FL-index ordering mismatches).
- `output/clip_audit_partNN_proposed.txt` — rebuilt styleb content (printed even without `--apply`).
- `output/clip_audit_summary.txt` — one-line summary per Part.

**Caveats.**

- `[slow]` flags and per-clip overrides are **not** preserved by `--apply`. Re-patch them
  afterward (or consume `partNN_overrides.txt` which is independent and survives rebuild).

---

### `validate_clip_lists.py` — pre-flight resolver check

Parses each `partNN_styleb.txt`, calls `resolve_clip_path()` on every segment, and reports:

- Total entries and multi-angle entry count.
- Tier distribution (T1 / T2 / T3 / unknown).
- Missing files (first 10 listed).

**Usage.**

```bash
PYTHONPATH=. python scripts/validate_clip_lists.py
```

**When to run.** Before every Part render, and always after `rescan_clips.py --apply`.

---

## Demo corpus management (Phase 2)

### `demo_inventory.py`

Scans `G:\QUAKE_LEGACY\WOLF WHISPERER\WolfcamQL\wolfcam-ql\demos\` and any additional demo roots
configured in `phase2/config.py`, computing SHA-256 hashes and metadata (map, duration, client
slots) for each `.dm_73`. Feeds the dedup pass.

### `demo_dedup_move.py`

Reads the inventory, groups by SHA-256, keeps the canonical copy in `demos/`, moves duplicates to
`demos/_duplicates/`. **Never deletes.** Writes `docs/research/demo-dedup-report-YYYY-MM-DD.md`.

### `sweep_remaining.py`

Finds `.dm_73` files not yet inventoried (e.g. new drops into the corpus folder) and adds them
to the inventory incrementally.

### `backfill_manifests.py`

For demos that existed before the inventory pipeline was built — generates their per-demo
manifest JSON from header parse.

### `finalize_report.py`

Generates the human-readable dedup + inventory summary for docs.

---

## Smoke-test & quality gates

Every Part render writes two JSON gate files the chain driver blocks on:

| File | Gate | Ship threshold |
|---|---|---|
| `output/partNN_sync_audit.json` | `max_drift_ms` — A/V drift at 1 min / 3 min / 5 min marks | ≤ 40 ms |
| `output/partNN_levels.json` | `delta` — game LUFS/true-peak minus music LUFS | ≥ 12 LU (Rule P1-G v4) |

A render that fails either gate is NOT copied to `deliverables/`. Re-run root-cause analysis in the
corresponding render log before re-queuing.

---

## Contributing a new utility

- One responsibility per script. If it does two things, split it.
- No side-effects on first run unless `--apply` is passed.
- Write JSON artifacts to `output/`, never back into `phase1/`.
- If the script is safe to run unattended (no destructive behavior without explicit flag), note it
  here under the appropriate section.
