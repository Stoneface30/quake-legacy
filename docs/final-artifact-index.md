# QUAKE LEGACY — final artifact index

> Current review: [2026-09-05 status and verification](reference/project-review-2026-09-05.md). Entries below are dated historical evidence, not live readiness.

Single entry point for project state as of **2026-08-30**.

Two assets exist that did not before: a complete V1 video archive, and a
recovered raw Quake archive of 214,466 match kills that the broken parser had
made effectively invisible.

---

## V1 video archive — FROZEN

| artifact | path |
|---|---|
| **V1 manifest (canonical)** | `output/V1_FINAL_MANIFEST.json` |
| 68 final videos | `output/Part{1..12}_highlight[_epN].mp4` |
| per-episode manifests | `output/_hl_manifests/part{NN}_ep{MM}.json` |
| per-episode segment maps | `output/_hl_manifests/part{NN}_ep{MM}_segment_map.json` |
| coverage report | `output/video_coverage_report.json` |
| leftovers | `output/LEFTOVERS/manifest.{csv,json}` |

**Status: COMPLETE FOR ALL RENDERABLE SOURCES.**

    1075 / 1076 selected sources successfully rendered
       1 / 1076 source damaged and excluded
    1075 / 1075 renderable sources successfully rendered

68 episodes · duplicates 0 · unexplained missing 0 · broken outputs 0 · decode
QA 68/68 · true peak −5.50…−1.00 dBTP with 0 over the −1.0 ceiling.

**Do not overwrite.** V2 must render to a separate directory.

## Source exceptions

| artifact | path |
|---|---|
| exception manifest | `SOURCE_EXCEPTIONS/manifest.json` |
| recovered clip | `SOURCE_EXCEPTIONS/recovered/Demo (100) - 3 [RECOVERED].avi` |

`Demo (100) - 3.avi` — status **SOURCE_DAMAGED_PARTIALLY_RECOVERED**. Its first
28,672 bytes (the RIFF/hdrl header) are zero-filled; ~230 MB of payload survives.
A header graft from a same-batch sibling recovered 9.97 s of clean 1920×1080
MJPEG with audio, verified as genuine gameplay. Recovered **after** V1 was
frozen, so V1 was not modified. This is V2 material.

## Corpus database

| artifact | path |
|---|---|
| **frags_rebuilt.db** | `creative_suite/database/frags_rebuilt.db` |
| canonical demo hashes | `output/demo_canonical_hashes.json` |
| parser outliers | `output/parser_outliers.{csv,json}` |

4,292 unique demos (from 6,445 files, 2,153 byte-identical duplicates) · 0
failures · 0 packet errors · parser commit `5a1f08dd` · schema
`frags-rebuild-2`.

Three named metrics, never one field called "kills":

| metric | meaning | count |
|---|---|---:|
| `raw_obituary_entities` | every obituary emitted | 215,831 |
| `match_kills` (`frags`) | player-vs-player, suicides excluded | 214,466 |
| `match_kills` deduplicated (`frags_dedup`) | snapshot repeats collapsed | 214,184 |
| `recorder_kills` | attacker is the demo's recorder | 36,607 |
| `recorder_kills`, alias-owned demos | the personal pool | 34,987 |

## Parser certification

| artifact | path |
|---|---|
| certification | `docs/reference/parser-certification-2026-08-30.md` |
| Wolfcam procedure (supervised) | `docs/reference/wolfcam-crosscheck-procedure.md` |
| 2012 tinfo calibration | `output/tinfo_calibration_2012.json` |
| 2011 probes | `output/probe_2011_obituaries.json` |
| eType 95 | `output/probe_etype95.json` |

**CORE CORPUS PARSING: CERTIFIED.**
**OBITUARY EXTRACTION: PROVISIONAL** — certified for 2012 via `tinfo`
(precision 100%, recall 100%); the 2010-2011 era has no independent
individual-death oracle, because that build emits no `tinfo` and its `scores`
signal is round-level. Wolfcam closes it.

## Seek lists

| artifact | path | rows |
|---|---|---:|
| **recorder seek list (primary)** | `output/master_seek_recorder.{csv,json}` | 34,987 |
| recorder sequences | `output/recorder_sequences.{csv,json}` | 7,105 |
| all-match seek list (secondary) | `output/master_seek_all_match.{csv,json}` | 214,184 |
| recorder identity audit | `output/recorder_identity_audit.{csv,json}` | 4,292 |
| identity unresolved | `output/recorder_identity_unresolved.{csv,json}` | 182 |

The recorder list is the creative dataset. The all-match list is for round
context, killfeed reconstruction and other players' highlights.

## Clutch pools

| artifact | path | rows |
|---|---|---:|
| **recorder clutches (primary)** | `output/clutch_recorder.{csv,json}` | 1,746 |
| all players, deduplicated | `output/clutch_all_players.{csv,json}` | 1,794 |
| raw extraction (superseded) | `output/clutch_round_wins.{csv,json}` | 3,423 |

3,423 raw → 1,794 distinct after joining on canonical demo content hash
(1,629 duplicate rows removed). Recorder 1vN: 895 / 653 / 173 / 25.

## Clip provenance and hit anchors

| artifact | path |
|---|---|
| clip provenance | `output/clip_provenance.{csv,json}` |
| **hit anchors** | `output/hit_anchors.{csv,json}` |
| unrenderable sources | `output/unrenderable_sources.json` |

Provenance: 16 EXACT · 2 HIGH · 1,206 LOW (each with a 2-3 demo shortlist) ·
355 UNRESOLVED. Every one of the 756 `Demo (N)` numbers a clip references
resolves to a demo file that exists.

Anchors, template-matched against pak00 game sounds (not generic loudness):
1,419 clips analysed. On the 1,075 V1 sources: **530 HIGH_AV (49.3%)**, 543
MEDIUM_AV, 2 LOW_AV, 0 UNRESOLVED.

## Music

| artifact | path |
|---|---|
| analysis cache | `creative_suite/database/music_analysis.db` |
| **export** | `output/music_analysis.json` |

1,483 distinct tracks from 1,778 files, 0 failures, BPM 72-185 (median 123).
`phrase_confidence` is **NOT YET MEASURED** — librosa fits a constant tempo, so
beat-interval regularity is near 1.0 by construction and is not evidence of a
stable phrase.

## Reports

| artifact | path |
|---|---|
| overnight run | `docs/overnight-run-2026-08-30.md` |
| this index | `docs/final-artifact-index.md` |

## Not produced

**Action candidates** (`action_candidates.csv`) — deliberately skipped. The tag
system in the rebuild already carries `airshot`, `air_rocket`, `big_flick`,
`rocketjump_frag`, `air_combo`, `multikill`, `quadkill`, `high_acc_shaft` and
more, queryable directly from `frags_rebuilt.db`. A separate conservative CSV
would be a strictly weaker view of the same data.
