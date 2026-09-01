# dm_73 Parser Certification — 2026-08-30

Certification pass run before rebuilding `frags.db` from the whole corpus.
Every claim below is backed by a command in `engine/parser/` and an artifact in
`output/`. Where a stated baseline did not reproduce, that is recorded as such
rather than smoothed over.

Parser commit at certification: `5a1f08dd`
Profile: `ql-2012` — a single entity-state table. `QL_2011` remains deleted.

---

## Root causes: kept separate

These are two different bugs. Merging them is what produced a wasted
investigation cycle, so they stay apart.

**1. PROVEN — original undercount.** `_dispatch` consumed only the first
service message of a packet instead of looping to `svc_EOF`. Every snapshot
that followed a `serverCommand` in the same packet was discarded. Recovery on
stratified old demos, builds ~`.350` → `.495`:

| before | after |
|---:|---:|
| 0 | 126 |
| 3 | 143 |
| 1 | 165 |
| 0 | 140 |
| 2 | 147 |
| 3 | 103 |
| 3 | 123 |
| 0 | 296 |

**2. PROVEN, and separate — diagnostic masking.** A broad `except Exception:
pass` around the dispatch call swallowed a `NameError` introduced during the
enum refactor. The result was a believable but wrong measurement. The handler
now counts failures into `_packet_errors` and records `_first_packet_error`;
it never silently discards.

---

## D1 — 2012 tinfo calibration · PASS

`engine/parser/tinfo_calibrate.py` · artifact `output/tinfo_calibration_2012.json`
Fixture: `CA-Gr0sTR4SH-asylum-2012_11_11-19_54_18.dm_73`

`tinfo` is a teammate-status servercommand (count, then groups of six:
clientNum, location, health, armor, weapon, powerup). A teammate's health
crossing `>0 → 0` is a `TINFO_DEATH_PROXY`, decoded by a completely different
code path from the entity stream — which is what makes it a genuine
independent signal. Proxies are matched only to an obituary for the **same
victim**; matching on time alone would pair unrelated deaths in a busy round
and manufacture a good score.

| measure | value |
|---|---|
| tinfo samples | 3300 (clients 2, 3, 4, 5) |
| obituaries decoded | 101 |
| TINFO_DEATH_PROXY | 47 |
| matched, same victim | 47 |
| unmatched | 0 |
| **proxy precision** | **100.0%** |
| eligible obituaries | 47 |
| seen by tinfo | 47 |
| **tinfo recall** | **100.0%** |

Lag, proxy → obituary: min 0, median 600, p90 875, p95 925, p99 950, max 950 ms.
The real signal sits inside 1 s; the 3000 ms window is generous.

`tinfo` is a **diagnostic only**. It never feeds `frags.db`.

## D2 — false-proxy classification · not exercised

Zero unmatched proxies on the 2012 fixture, so there was nothing to classify.
The classifier exists (`classify_unmatched`: round reset, round end, respawn or
state transition, disconnect, obituary outside window, unknown) and will report
`unknown` honestly rather than invent an explanation.

## D3 — three 2011 death probes · PASS (support downgraded, see below)

`engine/parser/probe_events.py` · artifact `output/probe_2011_obituaries.json`
Fixture: `CA-hearth-2011_08_02-18_48_01.dm_73`

**The stated method was not available**, and that is a property of the build,
not of our decoder. A servercommand census shows the 2011 demo emits
`cs`(310) `scores`(38) `bcs*` `print` `rcmd` `map_restart` — and **no `tinfo`
at all**, while the 2012 demo emits `tinfo` 1086× alongside `cascores` and
`castats`. `tinfo` is a later QL addition.

Roster: client 0 `s73rn` RED · client 1 `Tr4sH` SPECTATOR · client 2
`NaikoMarie` BLUE — a 1v1 with a spectator.

| probe | t (ms) | ent | raw→base eType | norm. event | eventParm | ordinals present | resolved |
|---|---:|---:|---|---:|---|---|---|
| 1 | 70500 | 128 | 71 → 71 | 58 | 11 LIGHTNING | 1,2,5,12,14,**19** | s73rn(0) killed NaikoMarie(2) |
| 2 | 100050 | 115 | 71 → 71 | 58 | 10 RAILGUN | 1,2,5,12,14,**31** | NaikoMarie(2) killed s73rn(0) |
| 3 | 119600 | 120 | 71 → 71 | 58 | 11 LIGHTNING | 1,2,5,12,14,**31** | NaikoMarie(2) killed s73rn(0) |

All three decode coherently. The delta omits whichever of victim (ordinal 19) /
attacker (ordinal 31) equals the **baseline** (0); in a 1v1 between clients 0
and 2, exactly one of the pair is 0 in every kill. An absent ordinal means
"equals baseline", not "missing data", and client 0 is a real player rather than
a fabricated default.

This **corrects a stale note** in `protocol_profiles.py` claiming ordinal 31 is
never transmitted in 2011 — probes 2 and 3 carry it.

### CORRECTION: the `scores` evidence is round-level, not a death oracle

An earlier statement in this session read "24 score increments, 24 matched,
implied detector recall 100%". **That overstated what the signal is**, and the
claim is withdrawn.

Measured on the same fixture (`scores` row width 18, 3 clients):

- field 1 changed for **multiple clients simultaneously in all 11 update
  events**; the count of updates where it changed for exactly one client is
  **zero**
- probe 3's nearby update moves client 0 (+3) **and** client 2 (+4) at once
- probe 1 has **no `scores` update within 3000 ms at all**

So `scores` in Clan Arena is a **ROUND-RESULT proxy**. Matching an obituary to a
score increment demonstrates temporal coincidence with a round boundary; it does
not independently establish who died. Correct naming:

    2011 scores signal = ROUND_RESULT_PROXY, not INDIVIDUAL_DEATH_ORACLE

What genuinely supports the three probes is therefore narrower, and is stated as
such: the decode is internally coherent (raw eType 71 → base 71 → event 58, a
valid MOD, and victim/attacker consistent with a 3-player roster in which one of
them is a spectator), and probes 2 and 3 sit 25 ms before a round-result update,
which corroborates **timing** only.

`OLD-DEMO OBITUARY DECODE = COHERENT`
`OLD-DEMO INDIVIDUAL-DEATH GROUND TRUTH = NOT ESTABLISHED` — pending Wolfcam.

## D4 — WolfcamQL oracle · NOT RUN (recorded blocker)

`wolfcamql-11.3.exe` and `wolfcamql-11.1.exe` are present at
`engine/engines/ghidra/binaries/`. The check was **not** performed: it needs a
GUI Quake client driven to specific timestamps and its output captured, which
is not something to start unattended (Rule CS-4 exists precisely because an
orphaned wolfcam process holds demo-file locks and hangs the desktop).

This is a real gap, stated plainly rather than substituted. A supervised
ten-minute procedure covering the same three events is written up at
`docs/reference/wolfcam-crosscheck-procedure.md`.

The gap matters more than first assessed. `tinfo` on 2012 is a genuine
independent death oracle and returned 100%. `scores` on 2011 is NOT — it is
round-level (see the correction under D3) — so for the 2011 era Wolfcam is the
only independent check still available.

## D5 — eType 95 · NOT REPRODUCIBLE WITH THE CORRECTED PARSER

`engine/parser/probe_events.py --etype 95` · artifact `output/probe_etype95.json`

Scanned 10 demos spanning 2010–2012, deliberately sampled across build eras:

- base eType 95 occurs **0 times**
- maximum base eType observed anywhere is **77**
- packet errors 0 on every demo

Grand base-eType histogram across the sample: 1 (72599), 33 (23289),
61 (29683), 60 (16469), 3 (15334), 63 (3542), 52 (1922), 31 (1295),
71 (1426 obituaries), 10 (437), 77 (291), 34 (2).

Stated precisely:

    eType95 occurrences with the corrected parser = 0
    across sampled 2010 / 2011 / 2012 / 2013 fixtures

No lifecycle table is given because there are no rows to tabulate. That absence
is itself the evidence.

**Probable cause of the historical observation.** The earlier sighting was made
with the pre-fix parser, which had two defects that both fabricate eType values:
packet dispatch stopped at the first service message (so entity state was
reconstructed from a truncated stream), and the event code was computed
subtract-then-mask rather than mask-then-subtract, which produces values that
correct masking never yields. Either alone can manufacture a base eType that
does not exist on the wire. Which of the two produced 95 specifically was not
isolated, and doing so would require resurrecting the broken parser — not worth
the time.

Closed as: **HISTORICAL eType95 OBSERVATION NOT REPRODUCIBLE WITH CORRECTED
PARSER.** It is explicitly NOT claimed to be a gameplay entity; there is no
current evidence that it is anything at all.

## D6 — certification gate

| requirement | status | evidence |
|---|---|---|
| svc-through-EOF regression passes | PASS | 32 tests in `test_dm73_dispatch.py`, `test_dm73_netcode.py`, `test_frag_classify.py` |
| no broad silent event discard | PASS | sole `except Exception` at `demo_parse.py:530` increments `_packet_errors` and records the first error |
| QL constants pinned | PASS | `_EV_OBITUARY=58`, `_ET_EVENTS=13`, `_F_VICTIM=19`, `_F_KILLER=31`, `_F_EVPARM=14`, `_F_ETYPE=12` |
| QL_2011 remains deleted | PASS | `PROFILES == ['ql-2012']` |
| recovered fixtures stable | PASS | 2010-era demos yield 125–165 obituaries, packet errors 0 |
| three 2011 probes match | PASS | D3 above |
| Wolfcam shows no differential | **NOT RUN** — procedure written | D4 above |
| packet errors 0 on fixtures | PASS | 0 across every demo examined |
| late-2012 regression stable | **DOES NOT REPRODUCE** | see below |
| full test suite | PASS | 677 passed, 3 skipped |

### The late-2012 regression baseline — RESOLVED

The stated baseline was **117 raw obituary entities → 63 filtered kills**.
Measured now on `CA-Gr0sTR4SH-asylum-2012_11_11-19_54_18.dm_73`:

- base-71 entity rows observed: **101**
- decoded obituary events: **101**
- accepted frags after classification: **101**
- every raw eType is exactly `71` (no `0x300` event-bit variants present)
- distinct `(time, entity)` pairs: 101 — so **1:1, no loss and no dedup**

Two separate differences, neither of which is a defect:

1. **117 vs 101 entities.** Nothing is being discarded — the mapping from
   base-71 entity rows to events is exactly one-to-one. The older 117 was
   produced by a parser that masked in the wrong order, which fabricates
   entities that correct masking never yields.
2. **63 vs 101 filtered.** `frag_classify` keeps every frag. That is the
   locked FT-2 rule: *"Every frag enters the corpus (no minimum threshold);
   tiering is for ordering, not filtering."* A filter that drops 38 of 101
   kills would violate it. `filtered == raw` is the correct behaviour.

#### Where the old numbers came from — traced 2026-08-30

The pair does not exist anywhere in the repository: not in the working tree, not
in git history, not in any test. It survives only as a figure quoted in a brief,
with no committed artifact behind it. So the four questions are answered from
the corpus itself rather than from a recoverable old test.

**1. Was 117 from the same demo bytes?** Cannot be established — nothing records
which fixture or commit produced it. But 117 is not exotic: **six demos in the
corpus yield exactly 117 raw obituaries**, all late-2012
(`CA-<player>-hiddenfortress-2012_11_02`, `CA-<player>-overkill-2012_07_28`,
`CTF-falloutbunker-2012_01_29`, and three others). The named fixture yields 101.
So 117 most likely came from a *different* demo.

**2. Was 63 recorder-only?** No. The named fixture's recorder subset is **20**,
not 63. Corpus-wide, 43 demos accept exactly 63 kills but **zero** demos have
exactly 63 recorder kills. And no demo anywhere reports 117 raw with 63
accepted.

**3. Was 101 caused by corrected event dedup?** No. On that fixture the mapping
from base-71 entity rows to events is 1:1 — 101 rows, 101 events, every raw
eType exactly 71 with no `0x300` variants. Separately there *is* a small
snapshot-repeat defect (below), but it collapses only 1 row on this fixture.

**4. Did the definition of an accepted kill change?** **Yes, and this is the
answer.** `frag_classify.classify()` drops obituaries where `killer == victim` —
suicides and world deaths are not frags. Corpus-wide that is **1,365 of 215,831
(0.63%)**, verified directly: `CA-<player>-overkill-2011_07_04` has 65 raw
obituaries, 8 self-inflicted, 57 accepted — exactly 65 − 8.

That single filter is far too small to turn 117 into 63 (a 46% cut), so the old
63 encoded a **stronger** filter that no longer exists. FT-2 forbids
reintroducing one: *"every frag enters the corpus; tiering is for ordering, not
filtering."*

#### The metric is no longer overloaded

One field called `kills` caused this. Three named quantities replace it, pinned
by `creative_suite/tests/test_frag_metrics.py`:

| metric | meaning | corpus |
|---|---|---:|
| `raw_obituary_entities` | every obituary the parser emits | 215,831 |
| `match_kills` | player-vs-player kills, suicides excluded | 214,466 |
| `recorder_kills` | kills whose attacker is the demo's recorder | 36,607 |

The tests assert the *relationships* (match_kills ≤ raw; the gap stays small
enough to be suicides; recorder is a proper subset; dedup never invents rows),
not one fixture's magic numbers, so they stay meaningful as the corpus grows.

#### A real defect found while doing this

One kill can be emitted once per snapshot its event entity survives — the dedup
guard is keyed on `entity_num`, and entity removal clears that state, so a
re-created event entity re-fires. Signature: identical victim/attacker/weapon at
25 ms spacing. Corpus impact **282 rows of 214,466 (0.13%)**.

A parser-level fix was attempted and **reverted**: keying the guard on
`(event, victim, attacker, parm)` from `accumulated` over-suppressed badly
(143 → 12 obituaries on one fixture) because those fields are not per-event-
instance at that point. Rather than risk the certified decoder for 0.13%, the
correction is applied downstream in `frags_dedup` (214,466 → 214,184), and
`test_snapshot_repeat_rate_stays_small` bounds it so it cannot grow unnoticed.

---

## Certification levels

Explicit levels, so optional archaeology cannot block a working production
parser.

### CERTIFIED — CORE CORPUS PARSING

Met.

| requirement | result |
|---|---|
| unique demos parsed | **4,292 / 4,292** |
| failures | **0** |
| packet errors | **0** |
| event-build errors | **0** |
| dispatch regression locked | 32 tests |
| old demos recover plausible counts | 0-3 → 103-296 across builds .350-.495 |
| outliers attributable to the parser | **0** (19 outliers, all short or aborted recordings) |

This is the level the corpus rebuild, the seek lists, the clutch pool and the
recorder products all rest on. It is solid.

### PROVISIONAL — OBITUARY EXTRACTION

Not yet fully certified. Two of three conditions are met:

| condition | status |
|---|---|
| current fixture semantics clearly defined | **MET** — `raw_obituary_entities` / `match_kills` / `recorder_kills` are named and test-pinned; the one filter is suicides (0.63%) |
| three 2011 probes independently supported | **NOT MET** — the decode is coherent and internally consistent, but the 2011 `scores` signal proved round-level, so no independent oracle establishes the individual victim for that era |
| no material Wolfcam disagreement | **NOT RUN** — supervised procedure written |

2012-era obituary extraction *is* independently supported: `tinfo` gives
precision 100% and recall 100% over 47 death proxies. The gap is specific to
2010-2011, where the build emits no `tinfo`.

Practically this means the corpus numbers are trustworthy and the 2011 slice
carries one unverified assumption. Running the ten-minute Wolfcam procedure
closes it.

### NOT REQUIRED FOR CERTIFICATION

- perfect `tinfo` coverage across all eras (the older builds do not emit it)
- complete semantics for every QL event
- resolution of every historical diagnostic artifact (e.g. isolating which of
  the two pre-fix defects fabricated eType 95)

## Verdict

**CORE CORPUS PARSING: CERTIFIED.** 4,292/4,292 demos, zero failures, zero
packet errors, zero parser-attributable outliers.

**OBITUARY EXTRACTION: PROVISIONAL** for the 2010-2011 era, certified for 2012
via `tinfo`. One condition outstanding — an independent check on the three 2011
probes — with a supervised procedure ready to close it.

Three claims made earlier in this work were wrong and are corrected above rather
than quietly dropped:

- "2011 `scores` gives 100% recall" — the signal is **round-level**, not an
  individual death oracle. Withdrawn.
- "117/63 does not reproduce because 63 implies a forbidden filter" — a filter
  *does* exist (suicides, 0.63%); it is simply far too small to explain 63. The
  full trace is above.
- "raw always equals accepted" — false corpus-wide; 754 demos differ, by exactly
  their suicide count.

The corpus rebuild stands. Nothing here invalidates the 214,466 recovered kills.
