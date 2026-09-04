# PART 3 — ONE SEARCHABLE QUAKE CAREER / WHAT IS PANTHEON?

**Target length:** 70–100 s. **Standalone cut:** "THE PANTHEON — TEASER".

---

## THE VISUAL THESIS

> **The machine organises. The human curates.**

Part 3 must answer *why this film exists* without becoming a software demo. The
answer is not "we built a tool". It is:

> **Eleven years of playing were recorded and then forgotten. The recordings
> were always there. What was missing was a way to ask them a question.**

The archive is the character. It has been asleep, and Part 3 is it waking up.

---

## BEAT BOARD

| # | t | dur | Picture | Text |
|---|---|---|---|---|
| 0 | 0.0 | 3.0 | Continues Part 2's multiplying round grid — now unreadable, thousands. Pull back. | — |
| 1 | 3.0 | 3.0 | Grid resolves into **one demo filename** on black. Cursor. Nothing else. | — |
| 2 | 6.0 | 4.0 | Filenames stack: 1 → 10 → 100 → thousands, scrolling past legibility. Counter settles. | **`4,292 DEMOS`** |
| 3 | 10.0 | 3.0 | Timeline draws itself left to right. Density blooms 2011–2012. | **`2010 — 2013`** |
| 4 | 13.0 | 3.0 | Counter climbs, decelerating. | **`OVER 450 HOURS`** |
| 5 | 16.0 | 4.0 | 61 map wireframes bloom in a constellation, each at its true recording weight (campgrounds 1,089 → hearth 9). | **`61 MAPS`** |
| 6 | 20.0 | 3.0 | Constellation collapses into a round grid — each cell one real round. | **`78,730 ROUNDS`** |
| 7 | 23.0 | 3.0 | Grid dissolves into individual kill events, a swarm. | **`203,536 PLAYER KILLS`** |
| 8 | 26.0 | 4.0 | Swarm sorts. Most go dark. One subset stays lit. | **`33,316 OF THEM WERE MINE`** |
| 9 | 30.0 | 4.0 | Identity resolves quietly — no portrait, no biography. | `Tr4sH` · `pTn` |
| 10 | 34.0 | 2.0 | Hard cut to black. | — |
| **THE MACHINE** |
| 11 | 36.0 | 8.0 | Queries fire as **text typed live**, each resolving instantly to a matching clip strip: `rail airshot` · `air rocket` · `1v3` · `telefrag` · `high speed` · `round win`. Each returns a count. | `THE ENGINE KNOWS WHAT HAPPENED` |
| 12 | 44.0 | 3.0 | Six strips play at once, silent, gridded. | — |
| **THE HUMAN** |
| 13 | 47.0 | 3.0 | Everything stops. One clip, alone, centre frame. | `THE MACHINE ORGANISES.` |
| 14 | 50.0 | 5.0 | Five role tiles resolve — FEATURE / TRANSITION / RHYTHM / KEEP / PASS. One lights. | `THE HUMAN CURATES.` |
| 15 | 55.0 | 3.0 | A typed annotation appears beside it in the user's own hand: *"enemy POV / xray / slow impact"* | — |
| 16 | 58.0 | 3.0 | The note **becomes** the effect — the clip re-renders as described. | — |
| **THE PROMISE** |
| 17 | 61.0 | 8.0 | Rapid promise montage: round story · projectile camera · teleport transition · material transformation · rhythmic rail sequence. 1.5 s each, no explanation. | — |
| 18 | 69.0 | 3.0 | Everything drains to black. | — |
| 19 | 72.0 | 4.0 | PANTHEON mark. | `ONE SEARCHABLE QUAKE CAREER` |
| 20 | 76.0 | 2.0 | — | → **THE MOVIE** |

**Beats 13–16 are the heart of the prologue.** Everything before them is scale;
this is the argument. A machine finds 33,316 things. A human looks at one of
them and says *what it is for* — and the film is made of those answers. Beat 16
(the note becoming the effect) is the single most important shot in Part 3,
because it shows the human judgement actually driving the picture.

**Beat 8 is the denominator beat.** The swarm going dark is not decoration — it
is the visual form of the distinction between 203,536 player kills and 33,316
confirmed-user frags. It prevents the misreading the brief warns about, without
a disclaimer card.

---

## NOT A SOFTWARE DEMO — the enforced rules

1. **The review site never appears.** No browser chrome, no cursor over a web
   UI, no buttons. The five roles appear as typographic tiles in the film's own
   language, never as screenshots.
2. **Queries are shown as language, not as an interface.** Beat 11 is text
   appearing on black and footage answering it. That is a *search* reading as
   telepathy, not as a form field.
3. **Counts are the payoff of a shot, never a label on one.** Every number lands
   at the end of a movement that earned it.
4. **No dashboards, no charts with axes, no progress bars.** The only permitted
   data forms are the primitives in `07-graphics-primitives.md`.

---

## NUMBERS — exact permitted wording

From `creative_suite/prologue/facts.py`, re-derived live. **These are the only
permitted forms.** The verifier fails the build if any drifts.

| On screen | Value | Never say |
|---|---|---|
| `4,292 DEMOS` | 4,292 | "4,292 matches" |
| `98% CLAN ARENA` | 4,222 / 4,292 | — |
| `61 MAPS` | 61 | (58 carry a canonical kill — different question) |
| `78,730 ROUNDS` | 78,730 | "138,301 rounds" (counter-inflated) |
| `OVER 450 HOURS` | ≥ 453.1 h | "452 hours" (was unsourced) |
| `203,536 PLAYER KILLS` | 203,536 | "203,536 of my frags" |
| `33,316 CONFIRMED USER FRAGS` | 33,316 | — |
| `14,212 CLAN FRAGS` | 14,212 | — |
| — | 36,607 | **never shown** — means "the killer recorded this demo" |

`33,316 OF THEM WERE MINE` (beat 8) is permitted **only** immediately after
`203,536 PLAYER KILLS`, because the contrast is what makes it honest.

---

## IDENTITY — how little to say

Beat 9 gets 4 seconds and two words on screen: `Tr4sH`, `pTn`. No portrait, no
years-played card, no biography. The archive already said everything: 4,292
demos over four dated years is a life, and stating it would make it smaller.

**Opponent names are never shown.** Per the public-repo rule, any frame that
would burn a nickname into the HUD is disqualified from the prologue.

---

## THE PROMISE MONTAGE (beat 17) — spend nothing

Five techniques, 1.5 s each, no explanation, never repeated later in the film in
the same form. This foreshadows `TACTICAL_ROUND_STORY`, projectile camera,
`TELEPORT_TRANSITION`, material transformation, and rhythmic weapon sequences —
and deliberately withholds `GRENADE_LAUNCH_AND_IMPACT_SEQUENCE`, enemy POV as a
full device, and every effect the movie proper opens with.

**Do not spend every trick in the intro.** The montage's job is to make the
viewer believe there is more, not to show them what it is.
