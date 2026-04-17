# SPLIT 1 — Close the Video Pipeline (YOUR checklist)

**What this is:** the exact list of things only YOU can do to ship Phase 1
end-to-end. Everything else is already automated or spec'd. When this list
hits zero, Parts 4-12 all render on one command and we move to Split 2.

**What this is NOT:** code for me. When something on this list creates work
for me, it's marked `→ Claude`. Your bits are marked `→ YOU`.

---

## Phase 1 Status Right Now (2026-04-17)

| Part | Render state | Your review state |
|---|---|---|
| 1-3 | Legacy tributes (pre-pipeline) | Reference only |
| 4 | Style B full 4.0 GB delivered | **PENDING** |
| 5 | Style B full delivered | **PENDING** |
| 6 | Style B full delivered | **PENDING** |
| 7-12 | Not rendered yet | — |

Music tracks downloaded for Parts 3-12 (`phase1/music/partXX_music.mp3`).
Beat-sync planner + concat-demuxer render path + PANTHEON intro + 75%
game audio + hard-cut Style B — all locked.

---

## YOUR Actions, In Order

### A. Review Part 4 (the hero)  → YOU
Path: `G:\QUAKE_LEGACY\output\previews\Part4_styleB_final.mp4` (4.2 GB, rendered 2026-04-17 17:58)
Sibling renders also ready:
- `Part5_styleB_final.mp4` (4.3 GB, 18:40)
- `Part6_styleB_final.mp4` (3.8 GB, 19:17)

Watch end-to-end once. Then on a second pass, give me timestamped feedback
on **only these six axes** (keeps feedback actionable):

1. **Chain flow** — does the clip order feel right? Where does it stall?
2. **Beat alignment** — any obvious miss where a frag should have snapped to a drop?
3. **Game audio level (75%)** — still too loud? too quiet? per section or globally?
4. **Multi-angle handling (Rule P1-K)** — does FP→FL→FP feel natural in the T1 peaks? Too many cuts? Too few?
5. **PANTHEON intro (first 7s)** — keep as-is, shorten, extend?
6. **Color grade** — too pastel (Part 4 v1 failure), too neutral, or right?

Feedback format (copy-paste template):
```
Part 4 feedback:
  0:15 — <observation>
  1:42 — <observation>
  ...
  Overall chain flow: 7/10 — <why>
  Overall beat alignment: 8/10 — <why>
  Game audio: keep 75% / raise to X / lower to X
  Multi-angle: working / too busy at Ymm:ss / too few at Zmm:ss
  Intro: keep 7s / other
  Grade: keep / shift <warmer|cooler|more contrast|less>
```

### B. Review Parts 5 & 6 same template  → YOU
Lighter — just flag if anything broke vs Part 4's behavior. If 5/6 are
"Part 4 with different clips" quality-wise, one-line approve is fine.

### C. Lock the final render quality ceiling (Rule P1-J)  → YOU
This was flagged in `HUMAN-QUESTIONS.md §5.4` and never formally ticked.
Current renders use NVENC av1_nvenc p7 CQ18. The question:

- Ship at `NVENC av1_nvenc p7 CQ18` (current, fast encode, excellent quality)
- OR `x264 CRF 15 preset slow` (CPU-heavy, slightly better psychovisual, 2-3× longer render)
- OR `x265 CRF 17 preset slow` (middle ground)

One-line answer. Defaults to current if you pass.

### D. Pick music for Parts 7-12 variations  → YOU
Tracks already downloaded: `phase1/music/part07_music.mp3` through
`part12_music.mp3`. Open `phase1/music/available_tracks.txt` to see
alternates on hand. For each Part 7-12, confirm "use what's already
there" or name a swap. If you pass, I use what's there.

### E. Gate ENG-1 decision (one-liner)  → YOU
Still open from earlier turn. Path A-now (wolfcam for `.dm_73` v1,
port later) or Path B-now (port protocol 73 into our engine first)?
**For Split 1 only, A is correct** — no reason to block video completion
on Split 2 work. Just need your "A" to formalize.

### F. Stage the 8 GB demo dump  → YOU
Move it to `G:\QUAKE_LEGACY\demos\` whenever convenient. Split 1 does
NOT need this. Only Split 2 does. Put on the list so it doesn't fall off.

---

## MY Side (for reference — I do these, you don't act)

- After (A)(B): I fix whatever feedback names. Re-render the affected Part only, not all three.
- After (C): I update `phase1/config.py` render preset and document in CLAUDE.md Rule P1-J.
- After (D): I validate each music track is beat-analyzable and generates `*.beats.json` cleanly.
- After (E): I skip any engine work until Split 2.
- After all Part 4/5/6 approved: I launch Parts 7-12 as a single background batch (3-5 hours total on RTX 5060 Ti), notify on completion.

---

## Known launch-readiness gap for Parts 7-12 (I'll fix at batch time)

Autonomous-tick inventory found: the existing `phase1/clip_lists/part07.txt` through `part12.txt` are **T1-only** (~30 clips each, sourced from `QUAKE VIDEO\T1\PartN\` only). Parts 4/5/6 Style B combined **all three tiers** (~150 clips each) per **Rule P1-A**.

State verified 2026-04-17 autonomous tick:

| Part | clip list (current) | Style B list needed | Music track | Beat cache |
|---|---|---|---|---|
| 7  | `part07.txt` T1-only (30 clips) | `part07_styleb.txt` (T1+T2+T3) | ✅ 7.9 MB | ✅ |
| 8  | `part08.txt` T1-only (30 clips) | `part08_styleb.txt` | ✅ 10.7 MB | ✅ |
| 9  | `part09.txt` T1-only (30 clips) | `part09_styleb.txt` | ✅ 7.3 MB | ✅ |
| 10 | `part10.txt` T1-only (30 clips) | `part10_styleb.txt` | ✅ 6.3 MB | ✅ |
| 11 | `part11.txt` T1-only (30 clips) | `part11_styleb.txt` | ✅ 13.7 MB | ✅ |
| 12 | `part12.txt` T1-only (30 clips) | `part12_styleb.txt` | ✅ 7.8 MB | ✅ |

**Music + beat caches are 100% ready.** The only missing piece is Style B list generation.

When you approve Part 4, I run one command to regenerate all six lists and kick the batch:
```
python -m phase1.experiment --part 7 8 9 10 11 12 --style B --nvenc
```
This scans T1+T2+T3 for each Part via `scan_part_frags()`, writes `partXX_styleb.txt`, and final-renders. No new decisions required.

---

## When Split 1 Closes

All 9 Parts (4-12) rendered and approved. Parts 1-3 remain legacy
tributes — if you want them re-rendered in the new pipeline that becomes
its own gate (Rule P1 applies but tier sources differ).

At that point Split 2 (TR4SH QUAKE) starts. I'll have the manifesto
ready and committed so we're not designing from cold start.

---

## What NOT to worry about right now

- The Command Center UI — parked until Split 1 closes
- Docker / FastAPI / SQLite choices — parked
- ComfyUI style packs — parked
- Sprite animation — parked
- Protocol 73 port — parked
- TR4SH QUAKE engine — spec'd but parked

Your eyes on one Part 4 render. That unlocks everything.
