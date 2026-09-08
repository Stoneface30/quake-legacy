# PROLOGUE — VERIFIED FACTS LEDGER

Nothing reaches the screen from this project unless it appears here with a
derivation. A number on screen is a claim; this file is where the claim is
paid for.

Measured 2026-09-04 against the live caches. Re-run `tools/verify_prologue_facts.py`
before locking any copy — these grow as review and derivation continue.

---

## 1. ARCHIVE SCALE (Part 3)

| Figure | Value | Derivation | Safe on screen as |
|---|---|---|---|
| Demos scanned | **4,292** | `count(*) from scanned_demos` (0 errors, 4,292 distinct hashes) | `4,292 DEMOS` |
| Of which Clan Arena | **4,222** (98.4%) | `frags_rebuilt.demos group by gametype` | `98% CLAN ARENA` |
| Maps recorded | **61** | `count(distinct map_name) from frags_rebuilt.demos` | `61 MAPS` |
| Maps with canonical kills | **58** | `count(distinct map) from kill_occurrences_v1` | — (use 61) |
| Canonical rounds (≥1 kill) | **78,730** | `count(*) from round_kills_v1`, over 3,084 demos | `78,730 ROUNDS` |
| Canonical kill occurrences | **206,268** | `count(*) from kill_occurrences_v1` | — (use 203,536) |
| Canonical **player** kills | **203,536** | `review_corpus.corpus_status(ALL_PLAYERS)` | `203,536 PLAYER KILLS` |
| **Confirmed-user frags** | **33,316** | `corpus_status(USER_FRAGS)` | `33,316 CONFIRMED USER FRAGS` |
| pTn confirmed-member frags | **14,212** | `corpus_status(PTN_FRAGS)` | `14,212 CLAN FRAGS` |
| User ∪ pTn (dedup by occurrence) | **47,528** | `corpus_status(USER_AND_PTN)` | — |
| Recorder-own archive (legacy) | **36,607** | `corpus_status(RECORDER_OWN_ARCHIVE)` | **NEVER** — not the user's frags |
| Recording hours | **≥ 453.1 h** | Σ per-demo (last kill − first kill) `demo_us`, 4,266 demos | `OVER 450 HOURS` |
| Years dated | 2010–2013 | `group by year`: 2010:14, 2011:1,070, 2012:1,194, 2013:529, unknown:1,485 | `2010 — 2013` |

### CORRECTIONS TO THE BRIEF

- **`~452 hours` was unsourced.** `frags_rebuilt.demos.duration_ms` is NULL for
  all 4,292 rows. The figure is now *derived* as the summed span from each
  demo's first kill to its last: **453.1 h**. This is a **lower bound** — it
  excludes warmup, the run-up to the first kill, and the tail after the last.
  On screen it must read **`OVER 450 HOURS`**, never `452`.
- **`61 maps` is correct, but not the way it was being reached.** 61 is
  distinct `map_name` over all recorded demos. Only **58** maps carry a
  canonical kill. Both are true; they answer different questions.
- **Do not print 138,301 rounds.** `frags_rebuilt.demos.rounds` sums to that,
  but **26 demos** carry a broken round counter (max observed: 10,599 rounds in
  one demo) contributing 56,349 phantom rounds. Median is 25. The canonical
  count from `round_kills_v1` is **78,730**, and that is the number to show.

### DENOMINATOR DISCIPLINE — enforced wording

| Never say | Say |
|---|---|
| "4,292 matches" | "4,292 **demos**" (one demo may span several matches) |
| "203,536 of my frags" | "203,536 **player kills** in the archive" |
| "36,607 of my frags" | never shown — that set means "the killer recorded this demo" |
| "452 hours" | "over **450** hours of recordings" |
| "138,301 rounds" | "**78,730** rounds" |

---

## 2. CLAN ARENA RULES (Part 2)

*Pending verification — see `01-clan-arena-rules.md`. No Part 2 copy is final
until every rule shown carries a source.*

---

## 3. MOVEMENT & SPEED (Part 1)

*Pending verification — see `02-movement-and-speed.md`. No UPS value appears on
screen unless it is measured from the action actually shown.*

---

## 4. STANDING RULES FOR THIS WORKSTREAM

1. **A number on screen is measured from the material shown**, or it is not
   shown. No stock figures, no remembered constants.
2. **V1 footage is never used.** Source isolation is enforced at capture.
3. **No unreviewed hero frag is consumed.** Historical material enters through
   named slots (see `06-historical-slots.md`) and only after human review
   assigns it a role.
4. **Human review has absolute priority on capture resources.** This workstream
   sits at priority 4 of 5.
5. **Synthetic explanatory material never touches career statistics.** It
   carries `SYNTHETIC_EXPLAINER` provenance and is excluded from every corpus
   count above.
