# Corpus parser-v2 rebuild — plan

**Goal.** Rebuild the demo corpus once with DM73Parser v2 (proved by gate G1)
into a new, versioned database set. Keep the v1 corpus untouched for
comparison. Produce a quantified migration report. Promote only after the
downstream mining and highlight regressions pass, and only with the user's go.

**Constraints (user, 2026-09-12):**

- no reparse before G1 fully passes (done: `0957d29d`)
- one rebuild, not iterations over the live corpus
- the old corpus is preserved
- protocol 91 is a compatibility gate, not a blocker for a protocol-73-only
  corpus

Status and defect list: `docs/reference/2026-09-12-corpus-parser-v2-status.md`.
What depends on what: `docs/reference/2026-09-12-corpus-entity-derived-map.md`.

## Architecture: a separate build root, never the live corpus

About 60 modules hard-code `<root>/creative_suite/database/<name>.db`.

- Most take `<root>` from `_data_root()`, which follows `QUAKE_LEGACY_ROOT`.
- A few use the code root: `rebuild_corpus`, `derive_kill_events`,
  `enrich_semantic_events`, `stage2_visibility`, `recognition_norms`,
  `recorder_products`.
- Two use a literal `G:/`: `full_corpus_v3`, `ca_reference`.

Refactoring all of them is the risky option. Instead:

- **Build root** `G:/QUAKE_LEGACY_CORPUS_V2/`: a git worktree of this branch at
  a pinned commit, so it is both the code root and, via `QUAKE_LEGACY_ROOT`,
  the data root.
- **Its `creative_suite/database/`** is a real, initially empty directory. It
  becomes the new corpus.
- **`demos/`** is a junction to `G:/QUAKE_LEGACY/demos`, read only; nothing in
  the chain writes demos.
- **Hard guard:** the orchestrator refuses to run if the resolved database
  directory equals the live one (`G:/QUAKE_LEGACY/creative_suite/database`).
- **Empty-database trap (HL-9):** after every stage, list `*.db` in the build
  root. A database that is not in the expected set, or that is empty, fails
  the stage. SQLite creates whatever it opens, so a missing input would
  otherwise pass silently.

## Tasks

### 1. Make the chain safe to point elsewhere

- `full_corpus_v3.py`: `ROOT`/`DB` from `_data_root()`. The `clear` stage is
  skipped on a fresh build: nothing to clear, and it must never run
  `DELETE FROM` against the live DB. The `F:/QL_BACKUP` precondition applies
  only when clearing.
- `ca_reference.py:49`: `FRAGS_DB` from `_data_root()`.
- Test: import every module in the chain with `QUAKE_LEGACY_ROOT=<tmp>` and
  assert that each `*_DB` path it exposes lies under `<tmp>`.

### 2. The orchestrator: `engine/parser/rebuild_corpus_v2.py`

- **How it runs:** one subprocess per stage, `cwd=<build root>`,
  `QUAKE_LEGACY_ROOT=<build root>`.
- **Resumable:** a state file records finished stages.
- **Memory:** a RAM guard stops the run below 6 GB free (lesson of
  2026-09-12).
- **Stages:** the order in the entity map.
  1. rebuild_corpus
  2. recognition_scan
  3. derive_kill_events, enrich_semantic_events
  4. full_corpus_v3 without `clear`
  5. kill_occurrences, funny_candidates, movement_moments
  6. mine_action_moments, mine_aim_events, then mining_epoch promote
  7. demo_lineage, round_model, match_roster, map_geography
  8. The performance index chain, a separate decision: large, and PANTHEON's
     own.
- **When done:** `corpus_status.stamp(db, 2, git_commit=..., stages=...)` on
  every database produced, and a manifest (row counts, sizes, wall time per
  stage).

### 3. Dry run

`--limit 50` demos into a scratch build root. Every stage must complete, no
unexpected databases may appear, every produced database must be stamped, and
the migration report must run against the v1 corpus restricted to the same 50
demos. Fix anything found, then delete the scratch root.

### 4. The one full rebuild

Protocol-73 demos only. A protocol-91 demo, if the corpus scan
(`G:/QUAKE_LEGACY_WORKTREES/protocol_scan.tsv`) finds one, is recorded and
excluded — gate G1 has no p91 field table. Before starting, check disk space
and that no other session is writing the corpus. HL-8 does not apply: pure
parsing, no game process.

### 5. The migration report: `engine/parser/corpus_migration_report.py`

Aggregates only; no player names (public repo).

- **Per database and table:** row counts, v1 vs v2.
- **frags:** frags added, removed and changed, keyed by `(content_hash,
  server_time_ms, victim_client)`. Per-demo count deltas as a distribution.
  `by_recorder` flips. Tag and weapon distribution shifts.
- **Events:** kill_events_v1 and semantic_events_v1 counts by type; missile
  sample counts; teleport transits.
- **Command-derived tables:** duplicates removed (server_text_v1,
  accuracy/scores); configstring-derived name and team changes.
- **Human linkage:** how many editorial.db verdicts (frag identity) resolve in
  v1 vs v2. A verdict that stops resolving is a regression to explain, not an
  acceptable loss.

Output: `docs/reference/<date>-corpus-v2-migration.md` plus a JSON.

### 6. Regression gates

- The chunked test suite with `QUAKE_LEGACY_ROOT=<build root>`, compared
  against the 2026-09-12 baseline. Only the known pre-existing failures are
  allowed.
- Mining: action-moment and aim-event counts per class, v1 vs v2, with every
  class that moves by more than 10 % explained.
- Highlights: the highlight / round-review selection (FT-2 criteria), with
  top-N overlap v1 vs v2 reported. Every human-rated frag must still be found.
- User eye-check (human gate): a sample of frags whose tags changed.

### 7. Promotion (user's explicit go only)

- Move the live corpus databases to
  `creative_suite/database/_corpus_parser_v1_2026-09-12/` (kept, never
  deleted).
- Copy the v2 set in.
- `corpus_status --write` must report CURRENT for every rebuilt database.
