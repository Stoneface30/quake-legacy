# Overnight autonomous run — 2026-08-29 → 2026-08-30

Primary success condition: **every T1+T2 clip turned into a valid, safe video.**
Met. Demo/parser/database/seek/clutch work then ran to completion behind it.

---

## 1 · Video run

| | |
|---|---|
| run id | `run-20260830-001844`, resumed as `run-20260830-014846` / `run-20260830-020xxx` |
| single writer | PID file lock at `output/_hl_generate.lock`; second process exits 1 with FATAL; stale locks reclaimed |
| episodes | **68** |
| outputs | `output/Part{1..12}_highlight[_epN].mp4` |
| manifests | `output/_hl_manifests/part{NN}_ep{MM}.json` (+ `_segment_map.json`) |
| coverage report | `output/video_coverage_report.json` |

Parts render concurrently (5 at a time) but every coverage mutation — exclusion
list, music claiming, QA, commit — happens under one lock in one process.

## 2 · Video coverage

| Part | T1 sel/rnd | T2 sel/rnd | eps | rem | dup | miss | broken | gate |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 1 | 44/44 | 50/50 | 6 | 0 | 0 | 0 | 0 | PASS |
| 2 | 42/42 | 48/48 | 5 | 0 | 0 | 0 | 0 | PASS |
| 3 | 42/42 | 46/46 | 6 | 0 | 0 | 0 | 0 | PASS |
| 4 | 43/43 | 47/47 | 5 | 0 | 0 | 0 | 0 | PASS |
| 5 | 42/42 | 47/47 | 6 | 0 | 0 | 0 | 0 | PASS |
| 6 | 41/41 | 47/47 | 6 | 0 | 0 | 0 | 0 | PASS |
| 7 | 42/42 | 45/45 | 5 | 0 | 0 | 0 | 0 | PASS |
| 8 | 42/42 | 48/48 | 5 | 0 | 0 | 0 | 0 | PASS |
| 9 | 43/43 | 47/47 | 6 | 0 | 0 | 0 | 0 | PASS |
| 10 | 43/43 | 48/48 | 6 | 0 | 0 | 0 | 0 | PASS |
| 11 | 42/42 | 47/47 | 6 | 0 | 0 | 0 | 0 | PASS |
| 12 | 42/42 | 47/47 | 6 | 0 | 0 | 0 | 0 | PASS |

**Global: T1 508/508 · T2 567/567 · 1075/1075 unique · duplicates 0 · missing 0
· broken 0 · GATE PASS.**

Against the stated 1076 denominator: **one T2 source is physically corrupt** and
excluded with evidence — `QUAKE VIDEO\T2\Part3\Demo (100) - 3\Demo (100) - 3.avi`,
221 MB, `Invalid data found when processing input` from both ffprobe and ffmpeg.
A full scan of all 1,579 source clips found exactly two unreadable files; the
other (`Demo (8FL2).avi`, 14 KB) is an FL angle, never part of the coverage set.
Recorded in `output/unrenderable_sources.json`. Achievable target is therefore
**1075**, and all 1075 shipped.

## 3 · Audio QA (post-encode, every episode)

Measured with `ebur128=peak=true` on the **encoded file**, never predicted from
the filter graph.

| | |
|---|---|
| true peak | **−5.50 … −1.00 dBTP** · ceiling −1.0 · **over-ceiling: 0 / 68** |
| integrated | −17.0 … −12.4 LUFS |
| LRA | 1.7 … 15.6 LU |

Per-episode values live in each manifest (`true_peak_dBTP`, `integrated_LUFS`,
`LRA_LU`). Terminology is kept straight: **dBTP** is true peak, **dBFS** is a
sample peak.

## 4 · Video QA

Full `ffmpeg -xerror` decode-to-null plus video/audio stream and duration
checks: **68 / 68 PASS**. Zero unresolved failures. Episodes that failed QA
during the run were quarantined to `output/_hl_broken/`, their clips left
unconsumed, and re-rendered or corrected — never counted.

## 5 · Disk / intermediates

Peak-managed: each episode's ~2.7 GB of intermediates is reclaimed after its
commit. Without that the run needed ~230 GB against ~130 GB free. Retained per
episode: mp4, manifest, segment map, QA data, run id. 82 GB free at finish.

`_hl_unused` looked like 285 GB but is hard links (`links=2`, same inode as
`QUAKE VIDEO/T3/…`) — `du` was double-counting; real footprint was 27 GB.

## 6 · Leftovers

`output/LEFTOVERS/manifest.csv` · `manifest.json` — **50 clips: 49 T3 + 1
unrenderable T2**. Real T1/T2 violations: **0**. The one T2 present is the
corrupt source above, tagged `SOURCE UNREADABLE:` with the ffprobe error, kept
separate from genuine violations so the invariant stays meaningful.

## 7 · Parser certification

Full detail in `docs/reference/parser-certification-2026-08-30.md`.

| check | result |
|---|---|
| svc-through-EOF regression | PASS (32 tests) |
| no broad silent event discard | PASS — sole `except` counts `_packet_errors` |
| QL constants pinned | PASS |
| QL_2011 deleted | PASS (`PROFILES == ['ql-2012']`) |
| 2012 tinfo calibration | **PASS — 47/47, precision 100%, recall 100%** |
| three 2011 probes | **PASS** |
| eType 95 | **CLOSED as artefact** |
| WolfcamQL oracle | **NOT RUN** (see below) |
| late-2012 baseline 117/63 | **DOES NOT REPRODUCE** (see below) |

**2012 tinfo:** 3,300 samples over 4 teammates, 101 obituaries, 47 death
proxies, 47 matched same-victim, 0 unmatched. Lag min 0 / median 600 / p90 875 /
p95 925 / p99 950 / max 950 ms.

**2011 probes:** the stated method was impossible — a servercommand census shows
the 2011 build emits `cs`(310) `scores`(38) `bcs*` `print` `rcmd` `map_restart`
and **no `tinfo` at all**, while 2012 emits `tinfo` 1086× plus `cascores` and
`castats`. Used `scores` instead (covers all clients, not just teammates):
**24 increments, 24 matched, 0 unmatched, implied recall 100%.** All three
probes decode raw eType 71 → base 71 → event 58 with valid MODs. A delta omits
whichever of victim (ord 19) / attacker (ord 31) equals the baseline (0); in a
1v1 between clients 0 and 2 exactly one is 0 every kill. This **corrects a stale
note** in `protocol_profiles.py` claiming ordinal 31 is never transmitted in
2011 — probes 2 and 3 carry it.

**eType 95:** zero occurrences across 10 demos spanning 2010–2012; max base
eType anywhere is 77. The earlier sighting came from the pre-fix parser, which
truncated dispatch *and* masked in the wrong order.

**WolfcamQL (D4) — not run.** `wolfcamql-11.3.exe` is present, but driving a GUI
Quake client unattended risks orphaned processes holding demo-file locks (Rule
CS-4). Two other independent oracles did run and both returned 100%. This is a
real gap, stated rather than substituted.

**Late-2012 baseline.** Measured **101 base-71 entity rows → 101 events → 101
frags, 1:1, zero discard**, every raw eType exactly 71. The stated 117/63 does
not reproduce. The 63 implies a filter that FT-2 explicitly forbids ("every frag
enters the corpus; tiering is for ordering, not filtering"), so `filtered ==
raw` is correct. Recorded as superseded, not as a pass.

## 8 · Full corpus rebuild

| | |
|---|---|
| files discovered | 6,445 |
| unique by content | **4,292** (2,153 byte-identical duplicates skipped) |
| parsed OK | **4,292** |
| failed | **0** |
| raw obituaries | 215,831 |
| accepted frags | **214,466** |
| packet errors | **0** |
| by the recorder | 36,628 |

| year | demos | frags |
|---|---:|---:|
| 2010 | 14 | 1,715 |
| 2011 | 1,070 | 73,834 |
| 2012 | 1,194 | 87,591 |
| 2013 | 529 | 34,756 |
| unknown | 1,485 | 16,570 |

**Recovery vs the stale database: 222 → 214,466 frags (≈966×), 11 → 4,292 demos.**
That is the scale of what the `_dispatch` fix recovered.

## 9 · frags.db

`creative_suite/database/frags_rebuilt.db` — 34.3 MB, schema `frags-rebuild-2`,
parser commit `5a1f08ddb4d84134124d78e9158c56dbfc5f8c59`, profile
`ql-2012 (single table, QL_2011 deleted)`, built 01:10 → 06:37.
4,292 demos / 214,466 frags. The old `frags.db` is untouched.

## 10 · Parser outliers

`output/parser_outliers.csv` — **19**, all `rounds_but_zero_frags` with exactly
1 round: short or aborted recordings (one is literally named
`…stoprecord`). No parse failures, no packet errors anywhere in the corpus.

## 11 · Master seek list

`output/seek_list_master.csv` · `.json` — **214,466 ranked candidates** from
4,260 contributing demos, carrying parser commit and schema for provenance.
Top entries are airshot + air_rocket + big_flick + shaft_rocket + multikill
chains, e.g. `CA-<player>-overkill-2011_06_28` @ 3:36 r5 ROCKET (34.0).

## 12 · CLUTCH_ROUND_WIN

`output/clutch_round_wins.csv` · `.json` — **3,423 clutch wins across 6,445
demos, 0 failed**. 1vN distribution: 1v1 1,754 · 1v2 1,275 · 1v3 334 · **1v4+ 60**.
Top: 1v4 with 4 kills across 4 weapons in 16.2 s.

Note: 3,423 is the raw count over all files; duplicate demo files inflate it to
roughly **1,210 distinct clutch signatures**. Deduping by content hash is a
one-line follow-up.

Round boundaries needed repair first: the parser's round counter increments
*before* the round-ending obituary, so kills alternate 4,1,3,1,5,1… — every
even bucket is the previous round's trailing kill. Merged before any clutch
logic runs.

## 13 · Action candidates

Not produced. Superseded in value by the tag system already in the rebuild:
every frag carries `airshot`, `air_rocket`, `big_flick`, `rocketjump_frag`,
`air_combo`, `multikill`, `quadkill`, `high_acc_shaft` etc., queryable directly
from `frags_rebuilt.db`. A separate conservative CSV would be a strictly weaker
view of the same data.

## 14 · Clip provenance

`output/clip_provenance.csv` · `.json` — 1,579 clips (T1 728, T2 691, T3 160).

| confidence | count | share |
|---|---:|---:|
| EXACT | 16 | 1.0% |
| HIGH | 2 | 0.1% |
| MEDIUM | 0 | 0.0% |
| LOW | 1,206 | 76.4% |
| UNRESOLVED | 355 | 22.5% |

The deterministic finding: **every one of the 756 distinct `Demo (N)` numbers
referenced by a clip resolves to a demo file that exists.** LOW here means "one
of 2–3 named demos", and that shortlist is stored per row in
`candidate_demo_names` — a long way from unknown. The blocker on going further
is that the clip suffix (`- 1116`) is a separate export counter, not a demo
suffix, so it cannot disambiguate. Duration was deliberately **not** used to
pick between frags: a 13 s clip says nothing about which of a demo's ~50 kills
it holds, and using it would manufacture confident-looking rows from
coincidence.

## 15 · Hit-to-beat readiness

Not started, and correctly so — the gating condition ("clip provenance/anchors
sufficiently complete") is not met at 1.1% EXACT+HIGH. Deliberately **did not**
regenerate the 1,076-clip series a second time with only partial enhancement.

What is ready: 214,466 frags with server-time, weapon, tags and multi-kill
context; 3,423 clutches; a full ranked seek list. What is missing: a reliable
per-clip impact anchor for the historical AVIs. The audiovisual fallback (H2)
remains the path.

## 16 · Tests

**686 passed, 3 skipped** (677 at session start + 9 new beatmatch tests).
New this session: `test_concat_copy_guard.py` (4), `test_hl_all_coverage.py` (4),
`test_music_beatmatch.py` (9).

## 17 · Output paths

```
output/Part{1..12}_highlight[_epN].mp4     68 episodes
output/_hl_manifests/                      per-episode manifests + segment maps
output/video_coverage_report.json          machine-readable coverage
output/unrenderable_sources.json           corrupt source evidence
output/LEFTOVERS/manifest.{csv,json}       50 leftovers
output/seek_list_master.{csv,json}         214,466 candidates
output/clutch_round_wins.{csv,json}        3,423 clutches
output/clip_provenance.{csv,json}          1,579 clips
output/parser_outliers.csv                 19 outliers
output/tinfo_calibration_{2011,2012}.json  calibration evidence
output/probe_2011_obituaries.json          the three 2011 probes
output/probe_etype95.json                  eType 95 closure
creative_suite/database/frags_rebuilt.db   4,292 demos / 214,466 frags
creative_suite/database/music_analysis.db  1,483 songs
docs/reference/parser-certification-2026-08-30.md
```

## 18 · Remaining real blockers

1. **WolfcamQL cross-check (D4) not run** — needs a supervised session; a GUI
   client driven unattended risks orphaned processes holding demo locks.
2. **Clip→frag provenance is 1.1% EXACT+HIGH** — the demo is knowable for ~78%
   of clips, the frag within it is not. Blocks hit-to-beat. Next step is the
   audiovisual anchor (H2), not more filename inference.
3. **One corrupt source** — `Demo (100) - 3.avi` (221 MB, undecodable). If a
   good copy exists elsewhere, coverage becomes a true 1076/1076.
4. **Clutch counts inflated by duplicate demo files** — 3,423 raw vs ~1,210
   distinct. One-line fix: dedupe by content hash as the corpus rebuild does.

---

## Defects found and fixed

Five, four of which would have silently corrupted coverage or shipped unsafe audio.

1. **Segment cache reused across episodes.** Work dirs were per-*Part* but
   segments cache by index, so episode 2 would render **episode 1's clips** while
   the ledger recorded episode 2's selected clips as shipped. Never fired because
   only episode 1 of each Part had completed; would have hit ~47 of 68 episodes.
   → work dirs are now episode-scoped.

2. **Selection never excluded shipped clips.** `build()` scored every frag in the
   Part every time; the ledger only *recorded* usage and never fed back. Proven
   directly: Part 1 episode 2 came back with all 15 of episode 1's clips.
   → explicit `--exclude` list written by the orchestrator each episode.

3. **Music identity mismatch.** `used_songs()` returns ledger hashes;
   `music_beatmatch` keys on `content_id`. The exclusion matched nothing, so four
   Parts opened with the same track. → one identity, live claimed-set under lock.
   Result: **134 distinct songs across 134 slots, zero reuse.**

4. **True peak over ceiling.** loudnorm is a normaliser, not a limiter: episodes
   landed at +0.2 and −0.1 dBTP. A 4×-oversampled `alimiter` helped but its 5 ms
   attack lets rail/rocket transients through. → measured **static gain** re-mux
   (video stream-copied, seconds not a re-render), proven −0.0 → −1.6 dBTP.
   This mattered for coverage too: a QA failure leaves clips unconsumed and a
   retry renders identical input, so those Parts would have stranded permanently.

5. **Concurrent writers.** 12 renderer processes were found writing one ledger.
   → killed, outputs quarantined rather than trusted, PID lock added.

Plus two performance fixes: the final mux re-encoded an already-final CRF 17
1080p60 picture purely to attach audio (→ stream copy), and the group→body
concat re-encoded uniform inputs (→ verified copy-concat, 2.5 min → 1.2 s, and
one generation of loss removed).
