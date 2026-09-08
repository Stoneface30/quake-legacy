# Demo V2 Mining — Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Build the pre-capture data layer for the new demo-derived V2 series: demo_v2 output scaffold, `generated_clips` provenance DB, small-demo classification, ranked recorder capture windows (top 20/50/100), and a human review package — everything the charter requires *before* any WolfcamQL capture runs.

**Architecture:** All computation reads the certified `frags_rebuilt.db` (read-only) and the overnight artifacts (`master_seek_recorder`, `clutch_recorder`). New products write only under `output/demo_v2/` and a new `creative_suite/database/demo_v2.db`. The frozen V1 archive and `frags_rebuilt.db` are never modified. Capture itself is gated on user review (Gate P-2 analog) and is explicitly OUT of this plan.

**Tech Stack:** Python 3.11 (E:\PersonalAI\venv), sqlite3 stdlib, csv/json stdlib, pytest. No new dependencies.

**Charter mapping:** §2 (separate tree) → Task 1 · §28 (new source DB) → Task 1 · §4 (small demos) → Task 2 · §5+§9+§17 (seek windows, generous context, multikill offsets) → Task 3 · §6 (clutch) → Task 3 (clutch-aware windows) · §26 (promotion pipeline stage 1: candidate → score → review data) → Task 4.

**Hard-rule constraints honored:** V1 outputs untouched (§32); `frags_rebuilt.db` opened with `mode=ro`; Gate P-2 — no batch WolfcamQL in this plan; no player names in anything destined for the public repo (output/ is gitignored — verify in Task 1).

---

## Data facts (verified 2026-08-30)

- `creative_suite/database/frags_rebuilt.db`: tables `demos` (4,292 rows; has `size_bytes, duration_ms, rounds, players, accepted_frags, packet_errors, parse_error, duplicate_of, recorder_is_alias`), `frags`, `frags_dedup`, `build_info`.
- `output/master_seek_recorder.csv`: 34,987 rows; columns `demo, year, map_name, server_time_ms, clock, round, attacker_client, attacker_name, victim_client, victim_name, mod, weapon_name, tags, ms_to_prev, ms_to_next, kills_in_capture_window, rank_score, rank_reasons`.
- `output/clutch_recorder.csv`: 1,746 rows; columns `demo, canonical_demo_hash, round, map, player_name, player_client, enemies_alive_at_start, kills_during_clutch, weapons, clutch_start_ms, clutch_end_ms, duration_ms, outcome, rank_score`.
- Demos on disk: 6,445 files, 1,569 under 800 KB (these map to demos-table rows via `size_bytes`; duplicates carry `duplicate_of`).

---

### Task 1: demo_v2 scaffold + generated_clips provenance DB

**Files:**
- Create: `creative_suite/database/demo_v2_db.py`
- Create: `creative_suite/tests/test_demo_v2_db.py`
- Runtime-created: `output/demo_v2/` tree, `creative_suite/database/demo_v2.db`

Schema (charter §28):

```sql
CREATE TABLE IF NOT EXISTS generated_clips (
    generated_clip_id INTEGER PRIMARY KEY,
    demo_name TEXT NOT NULL,
    canonical_demo_hash TEXT,
    server_time_ms INTEGER NOT NULL,        -- primary frag time
    round INTEGER,
    capture_start_ms INTEGER NOT NULL,
    capture_end_ms INTEGER NOT NULL,
    frag_offsets_ms TEXT NOT NULL,          -- JSON list, every kill offset from capture_start (§17)
    recorder_client INTEGER,
    weapon TEXT,
    tags TEXT,
    rank_score REAL,
    class TEXT NOT NULL,                    -- T1_NEW | T2_NEW | CLUTCH_PREMIUM | ACTION_PREMIUM
    clutch_context TEXT,                    -- JSON or NULL
    source_size_bytes INTEGER,
    source_quality TEXT,
    avi_path TEXT,                          -- NULL until captured
    qa_status TEXT DEFAULT 'PENDING',       -- PENDING | PASS | FAIL
    used_in_part TEXT,
    promotion_status TEXT DEFAULT 'CANDIDATE',  -- CANDIDATE | REVIEWED | CAPTURED | QA_PASS | PROMOTED | REJECTED
    promotion_reason TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
```

`demo_v2_db.py` exposes `connect(db_path=None)` (creates schema), `insert_candidate(conn, row: dict) -> int`, `ensure_output_tree(root=None)` creating `output/demo_v2/{review,generated_clips,parts}`.

- [x] Step 1: failing tests — schema creation, insert round-trip, output tree creation (tmp_path)
- [x] Step 2: run, verify fail
- [x] Step 3: implement
- [x] Step 4: run, verify pass; verify `output/` is gitignored
- [x] Step 5: commit

### Task 2: Small-demo classification (§4)

**Files:**
- Create: `engine/parser/small_demo_classify.py`
- Create: `creative_suite/tests/test_small_demo_classify.py`
- Output: `output/demo_v2/small_demo_classification.{csv,json}`

Pure function `classify(row: dict) -> str` over a demos-table row, threshold 800 KB handled by caller. Decision order:

NULLs coerced first: `duration_ms = duration_ms or 0`, `rounds = rounds or 0`, `accepted_frags = accepted_frags or 0`, `packet_errors = packet_errors or 0`.

1. `parse_error` not null → `CORRUPT_UNREADABLE`
2. `packet_errors > 0` and `accepted_frags > 0` → `CORRUPT_RECOVERABLE`
3. `packet_errors > 0` → `TRUNCATED_BUT_PARSEABLE`
4. `accepted_frags > 0` and (`duration_ms` ≤ 120000 or `rounds` ≤ 1) → `VALID_SHORT_CLIP`
5. `accepted_frags > 0` → `VALID_PARTIAL_DEMO`
6. `accepted_frags == 0` → `ABORTED_RECORDING` (covers 0-round warmup aborts)
7. unreachable rows → `UNKNOWN` (kept as safety catch-all)

Selection excludes duplicates: `WHERE size_bytes < 800*1024 AND duplicate_of IS NULL`; a separate `duplicate_files` count is reported so the on-disk 1,569 number reconciles. Tests must cover: each branch, NULL duration/rounds row, 0-frag/0-round row → ABORTED_RECORDING.

CLI main: read db read-only (`file:...?mode=ro`), select `size_bytes < 800*1024`, classify, write CSV+JSON with per-class counts, include `has_recorder_frags` and max frag score per demo (join `frags` on `by_recorder=1`) so tiny-but-valuable demos surface (§4 last line).

- [x] Steps: failing tests for each class branch → fail → implement → pass → run CLI on real DB → commit

### Task 3: Recorder capture windows (§5, §9, §17, §6)

**Files:**
- Create: `engine/parser/capture_windows.py`
- Create: `creative_suite/tests/test_capture_windows.py`
- Output: `output/demo_v2/capture_windows_full.{csv,json}`, `capture_windows_top20.csv`, `top50`, `top100`

Logic:
0. Load `demos` table from `frags_rebuilt.db` (read-only) → `name → (content_hash, size_bytes, recorder_client)` map (follow `duplicate_of` to canonical hash). Dedupe `clutch_recorder` rows by `(canonical_demo_hash, round, clutch_start_ms)` before any join; join windows↔clutches on canonical hash, never on filename.
1. Load `master_seek_recorder.csv`. Group rows per demo; merge consecutive recorder kills into one window when gap ≤ `CHAIN_GAP_MS = 5000`.
2. Window bounds: `capture_start = first_kill - PRE_MS (5000)`, `capture_end = last_kill + POST_MS (3000)`. Keep every kill offset (`frag_offsets_ms`, JSON, relative to capture_start) — §17.
3. Clutch join (by canonical hash): windows with any kill inside `[clutch_start_ms, clutch_end_ms]` extend to `clutch_start - PRE_MS … clutch_end + POST_CLUTCH_MS (4000)` and get `clutch_context` JSON (enemies_alive, kills, weapons, outcome) — §9.
4. Post-extension re-merge: after clutch extension, overlapping windows in the same demo are merged (union of kills/offsets, single clutch_context). THEN clamp start ≥ 0. This prevents duplicate CLUTCH_PREMIUM windows when intra-clutch kill gaps exceed CHAIN_GAP_MS.
5. Window score: `max(rank_score) + 0.5 * (sum of others) + clutch bonus (2.0 * enemies_alive_at_start if clutch)`.
6. Field derivations (explicit): `server_time_ms` = time of the highest-`rank_score` kill in the window (the "money shot"); `round` = round of that same kill; `clock_start`/`clock_end` = mm:ss rendered from capture_start_ms/capture_end_ms of demo servertime relative to the primary kill's known `clock`↔`server_time_ms` pair (fallback: raw ms if clock missing); `canonical_demo_hash` + `source_size_bytes` + `recorder_client` from the step-0 demos map.
7. Class assignment: clutch windows → `CLUTCH_PREMIUM`; score ≥ P99 → `T1_NEW`; ≥ P95 → `T2_NEW`; else `ACTION_PREMIUM` if any movement/air tag else unclassed (kept in full list only).
8. Emit full list + top20/50/100 CSVs with `demo, canonical_demo_hash, map, round, clock_start, clock_end, capture_start_ms, capture_end_ms, duration_s, n_kills, weapons, tags, frag_offsets_ms, score, class, clutch_context`.
9. Insert top-100 into `demo_v2.db` `generated_clips` as `promotion_status='CANDIDATE'`, `avi_path=NULL`, `source_quality=NULL` (set at capture QA time).

- [x] Steps: failing tests (merge logic, clamp, clutch extension by hash across duplicate names, post-extension re-merge produces ONE window, offsets preserved, scoring monotonicity, primary-kill field derivation) → fail → implement → pass → run on real data → sanity-check top rows → commit

### Task 4: Review package (Gate P-2 analog, §26 stage "review data")

**Files:**
- Create: `engine/parser/review_package.py`
- Output: `output/demo_v2/review/candidate_review.html`

Self-contained HTML (no external assets): summary counts, top-100 capture windows table, top-50 clutches table, small-demo class distribution, sortable via tiny inline JS, PANTHEON grey/silver aesthetic. Player names allowed (output/ is local-only, gitignored).

- [x] Steps: implement (presentation code — smoke test only: file exists, contains N rows) → run → open check → commit

### NOT in this plan (later phases, user-gated)

- WolfcamQL batch capture (needs Gate P-2 sign-off on the review package)
- Xaero asset generation, PANTHEON V2 intro/outro (ComfyUI, separate creative phase)
- Music phrase/section upgrade (§19–21)
- demo_v2 Part rendering (§24)
