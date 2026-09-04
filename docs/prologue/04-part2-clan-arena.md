# PART 2 — WHAT IS CLAN ARENA?

**Target length:** 45–90 s, governed by clarity and music.
**Standalone cut:** "WHAT IS CLAN ARENA?"

---

## THE VISUAL THESIS

> **One life. Everything you need. Nothing to collect.**

Clan Arena strips out the half of Quake that is *inventory management*. There
are no weapon pickups on the map; you spawn with all eight. So the round is
purely about position, aim and movement — the three things Part 1 just taught.

That is why the prologue teaches Quake before it teaches CA: **Part 2 is Part 1
with a scoreboard and a stopwatch.**

The second idea, which is the emotional one:

> **A round is 25 seconds long. Then it happens again. 78,730 times.**

The median round in this archive is **25.4 seconds**. That fact bridges directly
into Part 3 — it makes "thousands of rounds like this" concrete rather than
rhetorical.

---

## STRUCTURE — the countdown IS the structure

The real 7-second countdown (verified: 95% of 66,703 samples ≈ 7,000 ms, 5-3-2-1-FIGHT)
is a gift. It is a pre-built tension device the game already ships, with an
announcer track the audience will hear again in the movie proper. **Part 2 opens
on the countdown and lets the rules be explained inside it.**

## BEAT BOARD

Built on `SYNTHETIC_CA_EXPLAINER` — a controlled round, never a historical one.

| # | t | dur | Picture | Text |
|---|---|---|---|---|
| 0 | 0.0 | 4.0 | **Map build:** VOID → WIREFRAME → GEOMETRY → TEXTURE → DETAIL. Camera high, orbiting. | `CLAN ARENA` |
| 1 | 4.0 | 2.0 | 8 player markers drop in, 4 red / 4 blue, spatially placed. | `TWO TEAMS` · `USUALLY FOUR A SIDE` |
| 2 | 6.0 | 3.0 | Loadout ring blooms around one marker: 8 weapon glyphs. | `EVERY WEAPON. EVERY ROUND.` |
| 3 | 9.0 | 2.0 | HP/armour tile sets to 200 / 100. | `200 HEALTH · 100 ARMOUR` |
| 4 | 11.0 | 3.0 | **Countdown.** Players frozen. Real announcer: 3 — 2 — 1. | `NOTHING TO PICK UP.` |
| 5 | 14.0 | 0.5 | **FIGHT.** Everything moves at once. | — |
| 6 | 14.5 | 6.0 | **Tactical camera.** Starts high, dives to first damage. Alive counter `4—4` locked top-centre. | — |
| 7 | 20.5 | 2.0 | First kill. Counter ticks **`4—3`**. Marker greys out and *stays* grey. | `ONE LIFE` |
| 8 | 22.5 | 5.0 | Camera follows a rocket in flight (foreshadows projectile camera). Splash. **`3—3`** | — |
| 9 | 27.5 | 4.0 | Two exchanges, fast. **`3—2`** → **`2—2`** | — |
| 10 | 31.5 | 3.0 | Freeze around the 2v2. Camera arcs. Alive markers pulse. | `NO RESPAWN` |
| 11 | 34.5 | 4.0 | Resume. **`2—1`** → last survivor, outnumbered. | — |
| 12 | 38.5 | 3.5 | Final kill. **`1—0`**. Server line resolves. | `ROUND WON` |
| 13 | 42.0 | 2.5 | **Reset.** Everything snaps back: 8 markers, full health, counter `4—4`. | `FIRST TO TEN.` |
| 14 | 44.5 | 4.0 | Reset repeats — 2×, 4×, 8×, then a grid of rounds filling the frame. | `AGAIN.` |
| 15 | 48.5 | 3.0 | Grid keeps multiplying past the frame edge. | → **Part 3** |

**Beat 7 is the teaching moment.** A marker greys out and does not come back.
The audience learns "one life" by watching a light stay off — no card required.
The card `ONE LIFE` only confirms what they already saw.

**Beats 13–15 are the bridge.** The reset is the mechanic, and it is also the
transition: repeat it until repetition itself becomes the subject, and Part 3
has already begun.

---

## THE SYNTHETIC ROUTE — cheapest deterministic option first

Ladder, in order. **Stop at the first rung that works.**

1. **Local CA match → normal `.dm_73` recording → current V2 capture.**
   A bot or local-server CA round on a small map, recorded exactly like any
   other demo, then captured through the existing V2 path. Requires **no new
   code** — the whole pipeline already handles CA demos, and the parser already
   derives `round_state_v1` / `round_kills_v1` from them, which means the alive
   counter is driven by real derived data rather than hand animation.
2. Scripted bot round with fixed seed, if (1) is not repeatable enough.
3. **Native synthetic demo compiler — do NOT build this** unless 1 and 2
   both fail. It is weeks of work to produce something rung 1 produces in an
   afternoon.

**Ruling: go with rung 1.** The decisive advantage is not cost — it is that a
real recording flows through the real derivation, so the graphics in Part 2 are
driven by the same tables that drive the movie. The explainer proves the
pipeline while explaining the game.

### Provenance — hard requirement
The synthetic round is recorded and derived like any demo, so it **would**
otherwise land in the corpus and inflate career statistics by a few dozen kills.
It must carry `provenance = SYNTHETIC_EXPLAINER` and be excluded from every
corpus count, every review queue, and every frag total.

This is enforced by test, not by convention — see
`creative_suite/tests/test_prologue_synthetic_isolation.py`.

---

## TACTICAL CAMERA — what it is and is not

The "Matrix-like principle" from the brief means: **camera and time make a
complex event legible.** Not bullet-time cosplay.

Rules for the Part 2 camera:
- It moves **because something happened**, never decoratively.
- It **freezes only on state changes** — a kill, a 2v2 becoming a 1v2.
- Slow-motion is used **once**, on the rocket in beat 8, and it exists to show
  travel time (900 ups, `TR_LINEAR`) — a real mechanic, not a flourish.
- The alive counter is **always on screen** from FIGHT to round end. It is the
  spine of the explanation.

This is a deliberate rehearsal of `TACTICAL_ROUND_STORY` for later ClanWar
material. Part 2 is where that grammar is established cheaply, on a round nobody
cares about losing.

---

## COPY

Locked-safe: `CLAN ARENA` · `TWO TEAMS` · `USUALLY FOUR A SIDE` ·
`EVERY WEAPON. EVERY ROUND.` · `200 HEALTH · 100 ARMOUR` · `NOTHING TO PICK UP.` ·
`ONE LIFE` · `NO RESPAWN` · `ROUND WON` · `FIRST TO TEN.` · `AGAIN.`

**Banned:** anything about round timelimit or timeout (UNVERIFIED — no "round
draw" text exists in 256,651 captured server messages); starting ammo counts
(UNVERIFIED); `4 VS 4` as a description of the *archive* rather than of the
synthetic picture on screen (only 52% of rosters are 4-a-side).
