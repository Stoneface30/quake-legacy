# Music sync, effects and transitions — follow-up (banked, 2026-09-12)

**Status:** scoping document, not an implementation plan. Banked on purpose.

**Why it waits.** The user's direction (2026-09-12): finish ownership of the
first box before changing the second.

```text
DEMO -> PANTHEON -> RAW GAME CAPTURE  ->  render_highlight.py  ->  EDIT / MUSIC / OUTPUT
        (box 1: in progress)                 (box 2: this document)
```

When a beat lands wrong, the cause has to be attributable — demo timing, event
extraction, frame timestamping, audio timing, clip construction, slow-motion
retiming, music analysis, or final muxing. Changing both boxes at once makes
that impossible. This follow-up starts after the PANTHEON capture cutover
(`2026-09-12-pantheon-production-capture.md`, Task 11), or earlier only for
items the user explicitly pulls forward.

**The premise, from the user:** the whole video depends on effects and
transitions matching the rhythm. Today they mostly don't, because the delivered
path (`hl_*.py` → `render_highlight.py`) never received the sync machinery the
rules describe. Evidence: `docs/reference/2026-09-12-music-sync-and-effects-wiring-audit.md`.

## Step 0 — know what we ship today (no code change)

- Re-render **one** episode with the current `render_highlight.py`. Every
  delivered mp4 predates five code changes (08-31 ×2, 09-01 ×2, 09-08).
- Run the P1-BB drift audit on it (it has never run on a delivered video).
- User eye-check: the audit's five checks (opener, 6th/7th segment join,
  a short T1 slow-mo landing, the song change, overall level).

## Decisions the user owns (asked before any code)

1. **One pipeline.** `render_highlight.py` is the product; `render_part_v6.py`
   holds most of the sync machinery and still backs the Cinema Suite REBUILD
   button. Port the valuable pieces into `render_highlight.py` and retire v6,
   or keep both with clearly separate purposes?
2. **Music structure.** P1-R/P1-AA (three tracks, full songs, phrase-boundary
   truncation, BPM matching) vs the 08-29 "two songs" direction now shipping.
   Which is the rule?
3. **Effect cadence.** P1-Q-AUTO says every frag gets a ramp; the code accents
   every 3rd T1 clip plus short clips. Which is intended?
4. **Transitions.** P1-H says 0.40 s between every chunk; the code uses 0.35 s
   and hard-cuts every 6th join. Keep the group assembly (why it exists: encode
   limits?) or make every seam a dissolve?
5. **Intro.** P1-N (PANTHEON 5 s + title card 8 s) vs the generated 8 s opener.

## Candidate work, in dependency order

| # | Item | Depends on | Machine gate |
|---|---|---|---|
| 1 | **Event-recognised action peaks** (P1-Z) in the delivered path, replacing the loudness-envelope peak | decision 1 | recognised event within ±80 ms of the demo's event tick on a labelled set |
| 2 | **Sync calibration** in the delivered path: audible event ≈ +75 ms after the recognition tick; hero delta −15 ms (music minus gameplay) | 1 | measured onset in the delivered file vs the beat, stems isolated |
| 3 | **Effects placed on the beat grid** (P1-I, P1-Q): the slow-mo window, ramps and audio option chosen from event + music section jointly, not cadence | 1, 2, decision 3 | every accent's peak within tolerance of its target beat; no accent without a musical target |
| 4 | **Transitions on the grid**: every seam a beat-aligned dissolve of the agreed length; no hard group joins unless decided | decision 4 | seam timestamps on beats; no seam shorter than the agreed length |
| 5 | **Drift gate on every delivered render** (P1-BB): split graphs or a measured single graph, `max_drift_ms ≤ 40` as a ship gate | — | the gate itself |
| 6 | **Choreography / "song is the score"**: wire the solver into the delivered path, or retire it | 1–4, decision 1 | a solved plan renders to exactly the duration it promised |
| 7 | **4 s countdown lead-in** for round-start frags in delivered Parts (today review proxies only) | — | window starts 4 000 ms before the round start |
| 8 | **Effects atlas / transitions DB / HUD animation** reach a real render (`pandora`, `effect_templates`, `hud.py` have no delivered consumer) | 3, 4 | one delivered clip uses each, proven by frame grab |

## Rules hygiene done now (docs only)

CLAUDE.md render rules each carry a dated STATUS line measured against the
delivered path, and HL-4 is marked superseded by the ownership decision. Rule
*intent* is unchanged until the user settles decisions 1–5.
