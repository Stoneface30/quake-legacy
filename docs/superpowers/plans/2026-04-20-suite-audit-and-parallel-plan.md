# Suite Audit + Parallel Parts Plan + Phase1→Phase2 Wiring

**Date:** 2026-04-20
**Scope:** Three asks in one — (1) audit what got built vs the 2026-04-20
editor spec, (2) lay out Parts 4–12 so we can render them in parallel, and
(3) define the Phase 1 → Phase 2 wiring path so the pattern / effect /
transition DB becomes a first-class feedback loop instead of a graveyard.
**Status:** Draft, pending user go-ahead on the parallel plan.

---

## 1. Suite audit — spec vs shipped

Editor spec: `docs/superpowers/specs/2026-04-20-editor-design.md` §11 (9 build-steps).

| # | Deliverable | Shipped? | Notes |
|---|---|---|---|
| 1 | OTIO / MLT harness + smoke render | ✅ OTIO only | MLT **deliberately dropped** — see §1.1. OTIO export works. |
| 2 | Proxy generator + `/proxies` endpoint | ✅ | `/api/editor/proxy/{part}/{name}` lazy-generates 960×540 proxy. |
| 3 | Editor state schema + GET/PUT/PATCH | ✅ | `editor_state.json`, jsonpatch RFC 6902 ops, atomic `os.replace` writes (L154). |
| 4 | `/editor` route + three-pane layout | ✅ | Parts list · video timeline · inspector · render log. |
| 4b | Missing-chunks banner (unplanned) | ✅ | Rule L155 captured — transient render artifacts vs persisted storage. |
| 5 | Timeline video row + **WebCodecs** playback | ⚠ partial | HTML timeline + proxy swap works. **No WebCodecs / frame-accurate scrub yet.** |
| 6 | Audio rows via wavesurfer-multitrack | ❌ | Not started. Game + 3 music tracks all missing. |
| 7 | LiteGraph node panel + clip-to-node binding | ❌ | Not started. Effects picker today is plain list in editor.html only. |
| 8 | Theatre keyframes + Tweakpane inspector | ❌ | Plain HTML inspector exists; no keyframing, no bezier curves. |
| 9 | Render button + `render_versions` row | ✅ | SSE job stream, versions pane shows tag / mode / gates / time. |

**Gates (spec §7):**

| Gate | Status | Notes |
|---|---|---|
| G-T2-1 proxy ready before open | ⚠ partial | Lazy-gen works, missing-chunks banner surfaces the rarer root-cause. No per-chunk progress strip. |
| G-T2-2 OTIO round-trip | ❌ | We export; re-import + byte-equal round-trip not tested. |
| G-T2-3 MLT render parity | n/a | MLT dropped; render goes through `render_part_v6` (same code path as Cinema Suite, no parity risk). |
| G-T2-4 Rule P1-J v2 compliance | ✅ | Default mode=preview, ship requires explicit button + confirm dialog. |
| G-T2-5 CS-1 single-worker compliance | ✅ | Shared JobQueue from `_render_worker.py` returns 409 on double-submit. |
| G-T2-6 re-edit Part 5 smoke | ❌ | Needs user — blocks on live hands-on. |

### 1.1 Deliberate spec deviations (log for the record)

- **MLT dropped.** Spec §10.1 flagged Windows wheel risk. A research pass
  confirmed `pip install mlt` has no Windows wheel and source-building
  MLT under MSYS2 is a 2-day rabbit hole with downstream GL driver quirks.
  Fallback taken: the editor state projects into `flow_plan.json + overrides.txt`
  and calls `render_part_v6` — the same renderer Phase 1 already uses.
  Net effect: no new renderer to validate, Rule P1-J ceilings already tuned,
  same `render_versions` row format. Lost capability: in-editor MLT XML
  export. Low real-world cost — users who want a non-MLT NLE go via OTIO,
  which ships.
- **Tweakpane dropped in Step 8 first pass.** Plain HTML form is live
  because it integrates with the state JSON immediately. Tweakpane will
  overlay later; no data-model change needed.
- **Versions pane gained P1-J v2 gate badges** beyond what the spec asked
  for — shows level_pass ✓/✗ and max_drift_ms inline. Good surprise.

### 1.2 Net state: editor is usable today

A user with Parts 4/5/6 on disk can, right now, open `/editor`, see the
timeline, reorder / remove / edit clips, trigger a preview render, watch
SSE progress, and see the render history. **What they cannot do yet** is
scrub on a frame-accurate WebCodecs timeline or see audio waveforms.
That gap is Steps 5–8, all parallelizable.

---

## 2. Parallel Parts 4–12 plan

Parts 4, 5, 6 have Style-B full renders on disk but are **PENDING user
review** per `SPLIT1_USER_CHECKLIST.md §A-B`. Parts 7–12 have clip lists
+ music stems but no renders. Everything is Rule P1-J v2 preview-quality
(CRF 23 veryfast) unless user explicitly ships.

### 2.1 Per-Part data status (verified 2026-04-20)

| Part | Clip list | Music stems (main) | Music intro/outro | Beats/flow plan | Preview render |
|---|---|---|---|---|---|
| 4 | 0 lines (uses `part04_styleb.txt`) | 5 stems | series default | ✅ | v12 on disk |
| 5 | 30 lines | 6 stems | series default | ✅ | v1_PREVIEW_freshstems on disk |
| 6 | 128 lines | 5 stems | series default | ✅ | styleB on disk (last night) |
| 7 | 30 lines | 5 stems | series default | ❌ | ❌ |
| 8 | 30 lines | 5 stems | series default | ❌ | ❌ |
| 9 | 30 lines | 5 stems | series default | ❌ | ❌ |
| 10 | 30 lines | 5 stems | series default | ❌ | ❌ |
| 11 | 29 lines | 5 stems | series default | ❌ | ❌ |
| 12 | 29 lines | 5 stems | series default | ❌ | ❌ |

**All nine parts are render-ready.** Parts 4/5/6 just need user sign-off
before we commit a v{N+1} ship render. Parts 7–12 need a first preview
pass so the user has material to react to.

### 2.2 The parallel strategy (single-box, respect CS-1)

CS-1 mandates depth-1 JobQueue per box. We work around that with two
lanes, both running on this machine:

- **Lane A — render (serial, one job at a time):**
  `scripts/batch_preview_4_to_12.sh` invalidates stale effect variants
  and queues Parts 4–12 through `render_part_v6` at preview quality.
  Wall-clock estimate: ~4 min × 9 parts ≈ **36 minutes**, vs 20 min × 9
  = 3 hours the old way (Rule P1-J v2 saves ~2.5 hours).
- **Lane B — analyze (parallel, IO-bound, no JobQueue conflict):**
  while Lane A renders, subagents crunch beat detection / music
  structure / event recognition / level audit for Parts 7–12 so flow
  plans are ready the moment each render lands. These tasks don't touch
  the wolfcam / ffmpeg worker, so they don't violate CS-1.

```
t=0m   [Lane A] Part 4 re-render preview (user picks best → ship)
t=0m   [Lane B-1]  Part 7 beats + music_structure + event recognition
t=0m   [Lane B-2]  Part 8 beats + music_structure + event recognition
t=0m   [Lane B-3]  Part 9 beats + music_structure + event recognition
                   ...B-4/5/6 parallel on 10/11/12
t=4m   [Lane A] Part 5 preview
t=8m   [Lane A] Part 6 preview
t=12m  [Lane A] Part 7 preview (flow plan from Lane B ready)
...
t=36m  [Lane A] Part 12 preview complete
```

### 2.3 Commit / checkpoint plan

After each lane-A preview lands: one commit `render(partNN): preview v1`
with the mp4 path + sync_audit.json line in the commit body. After all 9:
one `feat(render): preview pass 4-12 complete` tag, push to `dev`.

### 2.4 Gate before ship

No part moves from preview → ship until user watches it and approves via
`/editor` → Ship button (CS-3 creates `partNN/v{N}-ship` tag + row in
`render_versions`). Rule P1-J v2 stands.

### 2.5 Kick-off checklist (what I need from you)

1. ☐ Approve Lane A (batch preview 4–12) — I run `scripts/batch_preview_4_to_12.sh`.
2. ☐ Approve Lane B (parallel analysis subagents for Parts 7–12).
3. ☐ Confirm Parts 4/5/6 will be reviewed via `/editor` once preview pass lands.
4. ☐ Note any Part you want **skipped** (e.g. Part 11 if the clip list
   is shaky) — default is all 9 run.

---

## 3. Phase 1 → Phase 2 wiring (the ask: "fully wired, does most of phase2's work, maintains pattern/effect/transition DB")

This is where the real system emerges. We have:

- `database/effects_catalog.db` — **34 transitions + 42 effects + 0 scoring events.** Schema ready, empty rows.
- `database/frags.db` — 222 frags across 10 demos, 0 rendered_clips, 0 assembled_parts, 0 knowledge rows. Schema ready, empty of observational data.
- Phase 1 per-Part artifacts: `partNN_beats.json`, `partNN_flow_plan.json`, `partNN_music_plan.json`, `partNN_music_structure.json`, `partNN_levels.json`, `partNN_sync_audit.json`, `partNN_recognition_report.md`.

**The gap:** Phase 1 produces all this signal per Part, then it rots on
disk. Phase 2 starts from zero. The DB schema anticipates bridging them
but nothing writes to it yet.

### 3.1 The wiring, in three layers

```
                ┌─────────────────────────────────────────┐
                │  Phase 1 render                         │
                │  (render_part_v6)                       │
                └───────────────┬─────────────────────────┘
                                │
                                │ emits (already today):
                                │  - flow_plan.json
                                │  - beats.json
                                │  - music_plan.json + music_structure.json
                                │  - levels.json + sync_audit.json
                                │  - recognition_report.md
                                │
                                ▼
                ┌─────────────────────────────────────────┐
                │  NEW: phase1/artifacts_to_db.py          │ ← step W1
                │  walks output/partNN_*.json, upserts     │
                │  rows into effects_catalog.scoring_events│
                │  and frags.assembled_parts + .knowledge  │
                └───────────────┬─────────────────────────┘
                                │
                                ▼
              ┌───────────────────────────────────────────┐
              │ effects_catalog.db (running pattern score)│
              │   - every (effect, clip, outcome) tuple   │
              │   - every (transition, seam, outcome)     │
              │ frags.db.knowledge                        │
              │   - {phase=1, category='grade'|'music'|   │
              │      'beat_sync', key, value, confidence}│
              └───────────────┬───────────────────────────┘
                              │ feeds forward:
                              ▼
              ┌───────────────────────────────────────────┐
              │ phase1/flow_planner consults DB first:    │ ← step W2
              │   - which effects score >70 for T1 peaks? │
              │   - which transitions score >70 for drops?│
              │   - which grades score >70 for this map?  │
              │ Picks them preferentially instead of      │
              │ guessing from scratch every time.         │
              └───────────────┬───────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────────────────┐
              │ Phase 2 inherits a warm cache:            │ ← step W3
              │   - frags.db.knowledge already has        │
              │     per-weapon/per-map style weights      │
              │   - effects_catalog has scored templates  │
              │   - Phase 2 auto-cut model trains on      │
              │     human "ship" clicks as positive       │
              │     labels, no cold start.                │
              └───────────────────────────────────────────┘
```

### 3.2 Three concrete build-steps for the wiring

**W1 — Artifact harvester (the bridge)**
- File: `phase1/artifacts_to_db.py` (new, ~200 LOC).
- Runs after every render that produces a `part_XX` artifact bundle.
- Parses `flow_plan.json` → each applied (effect, clip, music_section)
  tuple becomes a row in `effects_catalog.scoring_events` with
  `method='rhythm_align'` and `score = |Δ_beat_ms| inverted to 0–100`.
- Parses `levels.json` + `sync_audit.json` → `knowledge` rows with
  `phase=1, category='level'|'drift', value=JSON`.
- Parses `recognition_report.md` → `knowledge` rows with
  `category='event_recognition', key=event_type, value=confidence`.
- Idempotent: upserts by `(target_kind, target_id, sample_ref)`.
- Tests: `tests/phase1/test_artifacts_to_db.py` against a fixture Part.

**W2 — DB-aware flow planner**
- File: edit `phase1/beat_sync.py::plan_flow_cuts_v2` (~50 LOC delta).
- Before picking an effect for a clip section, query
  `effects_catalog.effects` joined on `scoring_events` filtered by
  `tags LIKE '%t1%'` (or appropriate tier) and `AVG(score) > 70`.
- Prefer highest-scoring → break ties by recency → fall back to
  current hand-written picks if DB empty.
- Self-warming: first N renders have empty DB, behave as today;
  after scoring_events fills, picks improve.
- Tests: `tests/phase1/test_flow_planner_db.py` with a seeded DB.

**W3 — "Ship" click promotes rows**
- File: edit `creative_suite/api/editor.py::render_part` (add ~20 LOC).
- On successful ship render, boost `score` on every effect/transition
  row referenced in that Part's flow_plan by +5 (capped at 100).
- On explicit "reject" (future UI button), decrement by −5.
- Reuses existing `scoring_events` table — no schema change.
- Tests: `tests/api/test_editor_render_scoring.py`.

### 3.3 Once wired, what Phase 2 inherits

- 200+ scoring_events rows per Part × 9 parts = **~1,800 data points**
  about which effects work on which clip types.
- `knowledge.db` becomes a queryable "what did we learn?" table that
  the auto-cut ML model (FT-1+FT-2 territory) consumes as training
  labels — ship=positive, rejected=negative, unshipped=unknown.
- The pattern / effect / transition DB stops being an empty schema and
  becomes the **central source of truth** for the editorial decisions
  Phase 3 tries to automate.

### 3.4 Estimated cost to wire

| Step | Lines of code | Test lines | Wall time | Risk |
|---|---|---|---|---|
| W1 | ~200 | ~150 | 0.5 day | low — pure parse+upsert |
| W2 | ~50 | ~100 | 0.5 day | medium — must not break current flow-planner when DB empty |
| W3 | ~20 | ~40 | 0.25 day | low |

Total: **1.25 days, ~560 LOC** to turn the DB from decorative into
load-bearing.

---

## 4. Proposed sequencing

Three tracks, mostly parallel:

**Track 1 — editor polish (Tier 2 Steps 5–8)**
Runs in the background while user reviews Parts 4/5/6. Low priority — the
editor is already usable for the clip-edit workflow. Only blocks if the
user needs frame-accurate scrub or audio waveforms *this week*.

**Track 2 — parallel Parts 4–12 (§2 above)**
Fires today. 36 min of lane-A wall-clock + concurrent lane-B analysis.
Output: 9 preview mp4s + 9 fresh flow_plans, all committed on `dev`.

**Track 3 — Phase1→DB wiring (§3 above)**
Fires after Track 2 lands its first preview so W1 has real artifacts to
ingest. 1.25 days. W2 + W3 light up as soon as W1 commits.

**Gate before any of this starts: user approves this plan.**

---

*Hand-off:* when user ticks the §2.5 checklist, I dispatch one serial
render agent (Lane A) + six parallel analysis subagents (Lane B),
promoting the DB wiring to `in_progress` as soon as the first part
lands. User reviews Parts 4–6 in `/editor` in parallel with the render
queue continuing on 7–12.
