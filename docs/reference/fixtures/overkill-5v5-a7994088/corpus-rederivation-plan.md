# Safe corpus re-derivation plan

The fixture dossier changes what several corpus tables mean. This is how those
tables get rebuilt without destroying a single human verdict, and without a
repeat of the rescan that wiped health attributes while the version bookkeeping
reported success.

The plan is deliberately boring. Every step is reversible, every step is
verified against the fixture before it touches the corpus, and no step
overwrites a table that a human has written to.

---

## 0. What must never be touched

These are inputs to the re-derivation, never outputs.

| Protected | Where |
|---|---|
| HUMAN_USER verdicts, notes, tags | review tables |
| `GOLDEN`, `KEEP_CONTEXT`, `WORKSHOP`, `production_usage` | review tables |
| The 249 quarantined wrong-profile clips | media quarantine |
| Any other session's untracked files or branches | working tree |
| `demo-v2-mining` and every protected branch | git |

A re-derivation that cannot run without editing one of these is the wrong
re-derivation. Rewrite the step instead.

---

## 1. Findings that force a rebuild

Each one changes a stored value, not just a description of it.

| # | Finding | Affected |
|---|---|---|
| F1 | Health was read unsigned; `-1` stored as `65535` | every health-derived attribute |
| F2 | Deltas were decoded against a running accumulator, not `snapshot[messageNum − deltaNum]` | entity and playerstate state at 19.3% of snapshots |
| F3 | `MSG_ReadShort` was unsigned | stats shorts |
| F4 | A player entity's number **is** its client number | event attribution: 38.9% → 98.7% resolved |
| F5 | `--all` was a no-op, so 32,554 frags never got a health row | health attributes, low-HP tagging |
| F6 | Weapon constants: `MOD_*` and `WP_*` disagree and were conflated | weapon labels on frags |
| F7 | Round reconstruction: the native parser reports 27 pseudo-rounds where there are 14 | every round-scoped metric |
| F8 | **13 of 102 kills land after their round's end command** | clip windows, round attribution |
| F9 | `ps.damageCount` is exact on the recorder's own playerstate and unreliable on a spectated subject | damage-taken numbers |
| F10 | Entity presence, lifetimes and slot reuse are now exported | every per-player coverage claim |

F8 and F9 are new in this pass. F9 in particular means the corpus-wide 88.7%
reconciliation was never a decoder defect — it was a population defect.

---

## 2. Shape of the rebuild

**Rebuild beside, never in place.** Derived tables get a version column and a
new generation; the old generation stays readable until the new one is
accepted.

```
frag_recognition.db          (live, untouched during the run)
  └─ recognized_frags        v-current  ← reviewers keep reading this
  └─ recognized_frags        v-next     ← written by the run
review verdicts              (never rewritten; joined by frag identity)
```

Frag identity must survive the rebuild. Rows are matched on
`content_hash + server_time_ms + killer_slot + victim_slot`, never on a
row id — the renumbering trap that would have mis-attached 144 of 175 clips
came from treating an id as an identity.

---

## 3. Gates, in order

Nothing proceeds past a failed gate.

### Gate A — the fixture reproduces
Run the dossier builder on the fixture. Every number in
`dossier.json` must reproduce exactly: 102 kills, 14 rounds, 13 late kills,
62/62 recorder damage instances, 9 entity slots, 413 lifetime spans.
A drift here means the decoder changed under us.

### Gate B — the existing 45-demo validation still passes
The 45-demo stratified run already covers: health range, `damageCount` clamp,
damage reconciliation, server-time monotonicity, client-number range, packet
errors, missing delta references. **Do not restart a new 50-demo exercise.**

Genuinely missing strata, to be *added* to the existing 45 rather than
replacing them:

| Stratum | Why the 45 do not cover it | Size |
|---|---|---:|
| Demos with ≥ 3 POV subject changes | F9 only bites where the POV moves | 10 |
| Demos with a `WORLD` (1022) killer | entity-model edge, 1 case in the fixture | 5 |
| Demos with a round lacking a `662 = -1` end signal | F7/F8 boundary handling | 5 |
| Demos ≥ 20 MB | delta-reference history depth under load | 5 |

That is 45 + 25 = 70, additive, with the original 45 results preserved.

### Gate C — differential, not absolute
For every changed value, record old → new with a reason. A metric that changes
for no nameable reason is a defect in the rebuild, not a fix.
Publish the count of rows that changed per finding F1..F10. If a finding
changes zero rows, say so — the delta-reference fix alone changed nothing on
CA demos and that is a legitimate result, not a failed fix.

### Gate D — human data intact
Before and after the run, count and checksum: verdicts, notes, tags, GOLDEN,
KEEP_CONTEXT, WORKSHOP, production_usage. Identical, or the run is rolled back.

### Gate E — reviewer sees one framing
Clips are re-cut to a symmetric window around the kill's own timestamp
(5s before, 5s after), never around a round boundary — F8 is the reason.
Old proxies keep their keys and stay on disk; a new window is a new key.
The reviewer must never be shown two framings of the same moment.

---

## 4. Order of operations

1. **Freeze.** Record the git commit, the decoder sha256, and row counts of
   every table. Write them to the run manifest.
2. **Gate A.** Fixture reproduces.
3. **Rescan to a NEW database file.** The live database is opened read-only for
   the duration. Exclude demos under 500 KB, as agreed; record the excluded
   count as a population, not a silence.
4. **Gate B.** 45 + 25 strata.
5. **Derive** rounds, rosters, shapes and health onto the new generation.
   Health is extracted for ALL frags (F5), and damage-taken only on the
   recorder's own POV spans (F9).
6. **Gate C.** Differential report per finding.
7. **Join verdicts** by frag identity, not by row id. Report unmatched
   verdicts explicitly; an unmatched human verdict blocks acceptance.
8. **Gate D.** Human data checksums match.
9. **Accept**: point the reviewer at the new generation. The old generation
   stays on disk for one full review cycle.
10. **Gate E.** Re-cut clips at the symmetric window, queue, and only then
    invite review.

Steps 3 and 10 are the long ones and both respect the render permit: a running
game always wins, and a refused job stays `QUEUED`, never `FAILED`.

---

## 5. Rollback

The rebuild is a new file plus a pointer. Rollback is moving the pointer back.
Because verdicts were never rewritten, rollback loses no human work. The only
irreversible artefacts are new clip files, which are additive.

---

## 6. What this plan does not do

- It does not merge anything into `demo-v2-mining` or any protected branch.
- It does not re-run the 45-demo validation from scratch.
- It does not delete quarantined media.
- It does not promote any number to a corpus scoring rule. Promotion needs a
  visual check and an independent decoder cross-check, and both are still open
  — see the bounded verification set beside this plan.
