# Corpus parser-v2 rebuild — 50-demo dry run (2026-09-12)

This is step 3 of `docs/superpowers/plans/2026-09-12-corpus-parser-v2-rebuild.md`.

- **Build root:** `G:/QUAKE_LEGACY_WORKTREES/corpus_v2_dryrun`, a detached
  worktree at `b5ddc56d` and then `6c6062bd`.
- **Scope:** `--limit 50`.
- **Isolation:** the live corpus was only ever opened read-only.

## Result

All 11 stages completed with exit 0. The stages were:

- corpus
- recognition pass 1, norms, recognition
- kill events and semantic events
- clutch
- enrichment: view, refine, lg, projectile, health, dodge, stage2, reclassify,
  shapes
- occurrences
- mining, with the in-build promote
- lineage, rounds, roster, geography

**Wall time:** about 17 minutes. About 2 minutes of that was hashing all 6,445
demo files so they could be deduplicated.

**Stamps:** every database the build produced carries the parser-v2 stamp
(`corpus_status`: frags_rebuilt, frag_recognition, frag_shapes, mining_epoch
and map_geography are CURRENT). No unexpected or empty database appeared.

**Found by the dry run and fixed before the full run:**

- **A missing producer.** `reclassify_v2` joins `output/clutch_recorder.csv`,
  and no tracked code produced it. Its definition was recovered and proven on
  the v1 files: 1,794 of 1,794 rows for all players, and 1,746 of 1,746 for the
  recorder alone, selected by alias name. The file is now produced by
  `engine/parser/clutch_products.py` as its own stage (`6c6062bd`).
- **Two report problems.** The migration report could not print on a cp1252
  console. It also did not mark tables that have no `content_hash` column as
  unscoped.

## What v2 changes, and why

These figures come from the 50 demos in scope, v1 against v2.

| | v1 | v2 | explained |
|---|---:|---:|---|
| frags | 2,304 | 2,304 | 2,303 kept, 1 added, 1 removed; per-demo counts unchanged; `by_recorder` unchanged |
| frags with changed tags | | 214 | scores changed on 211, mean −0.25 (enrichment and reclassify inputs changed) |
| kill_events_v1, semantic_events_v1 | identical | identical | Obituaries and temp events carry their fields in full every time, so the entity fixes do not reach them. |
| missile_samples_v1 | 43,534 | 74,115 | The same 3,770 missile slots. Weapon-4 samples rose from 5,254 to 29,049, and there are 6,786 removal rows where v1 had none. v1 lost `eType` on missiles rebuilt from partial deltas, so it stopped tracking them. |
| teleport_transits_v1 confirmed / UNKNOWN | 1,846 / 960 | 2,721 / 85 | 875 transits are now confirmed, because the player state at both ends is correct. |
| server_text_v1 | 3,045 | 1,895 | All 1,148 v1-only rows are **resends**: the same text appears at an earlier time in v2. |
| round_state_v1 | 4,144 | 2,526 | Every v2 row exists in v1 by (demo, time, cs). The 1,618 extra v1 rows are resends. v1 **values were corrupt**: `114425"\n` where v2 has `114425`, and `"\n"` where v2 has empty. |
| team_changes_v1 | 706 | 692 | All 14 v1-only rows are resends. |
| action_moments_v1 | 795 | 887 | Missile hits and misses are observed better. |
| frag_shapes_v1 | 570 | 580 | Follows the new inputs. |

**Highlight top-N churn** (top-50 overlap 1, top-100 overlap 16, all 312
identical as a set) **is mostly an artefact of the dry run.** Its norms came
from about 305 frags, where v1's came from about 36,000. One shift may be real:
median visibility went from 8,025 ms to 13,475 ms, which the entity-presence
fix could cause. The full rebuild computes its norms from the whole v2 archive,
and that run's report is the one to judge rankings by.

**Human linkage.** Of the 14 human targets, 13 are kills in demos the dry run
never parsed. The single in-scope target matches exactly one v2 kill with the
same fingerprint, so it maps. The build's linkage gate now reports in-scope
targets separately.

## Clean-from-zero proof (user gate, 2026-09-12)

The orchestrator gained the `clutch` stage partway through the run above, and
that run was then resumed. A resume does not prove that the final DAG works
from nothing, so, as the user required, the same 50 demos were rebuilt in a
brand-new worktree at `c538d571`. The build root started with no state file
and no copied outputs. Only the resumed run's manifest was kept, for this
comparison. Then only that temporary build was deleted: its junctions were
removed first, and the live demo count stayed at 6,445 throughout.

| gate | result |
|---|---|
| all stages from zero | 11 of 11 completed, exit 0 |
| row counts, every table in every database | **0 of 81 differ** from the resumed run |
| migration report: frags, tables, highlights, why-buckets | **0 of 320 fields differ** |
| strict one-to-one linkage | identical: 1 ONE_TO_ONE, 13 OUT_OF_SCOPE, 0 manual review |
| provenance | commit `c538d571`, source tree clean. Inputs: 50 unique demos, 0 parse errors, demo-set SHA-256 `c5a11f88…`. 22 stage versions recorded. SHA-256 for every output database. |
| stamps | frags_rebuilt, frag_recognition, frag_shapes, mining_epoch and map_geography are CURRENT (parser v2) |

**Why-buckets on these 50 demos:**

- **Kills:** 1 recovered, 1 lost, none shifted.
- **Frag attributes:** 310 frags have changed entity-side attributes. These are
  mostly the dodge and near-miss evidence that v1's missile tracking lost; the
  speed percentiles also moved, but that is the small-sample norms artefact.
- **Classification:** 218 frags reclassified. The largest gains are
  DODGE_TO_KILL +90, NEAR_MISS_ROCKET +66 and NEAR_MISS_RAIL +58.
- **Clutch membership:** unchanged (13 for all players, 8 for the recorder).

**Clutch selection:** all 8 alias-selected rows are also the recorder's slot.
The `slot_only` count of 5 is recorded for review, never merged.

Timing was 3–5× slower than the resumed run. Worker CPU was around 20% each,
the machine was 30% busy and 10.7 GB of RAM was free, so the cause was disk
reads competing with other programs, not the build. Timing is not a gate.

The full evidence, aggregates only, is in
`docs/reference/2026-09-12-corpus-v2-clean50-migration.md`.
