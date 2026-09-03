# Creative protocols — preserved, not built

*Written 2026-09-04. These are the user's creative concepts, recorded while
the data that would support them is fresh. **None of this is implemented.**
Manual review decides which material earns the investment; building any of it
before that would be perfecting effects for arbitrary machine-ranked clips,
which is the exact mistake this review sprint exists to avoid.*

---

## TACTICAL_ROUND_STORY (Clan Arena round as a scene)

A Clan Arena round starts 4v4 and resolves. The frag is the review unit; the
**round is the potential scene unit**.

**Opening.** Begin above the map, both teams visible, pTn/ClanWar treatment —
models, materials, world styling and team colours morphed toward the clan
identity (Nauru palette: gold and deep blue).

**Movement.** The camera descends into the fight and travels *through* it
rather than locking to one FPV. Focus follows the most important event;
brief holds or freezes where something needs explaining; then it continues
along the battle path.

> "Matrix-like" here means **time and viewpoint used to explain a complex
> battle** — not a literal reproduction of a specific film effect.

**Narrative beats**, in the order the round supplies them:

first meaningful damage → position changes → team damage → first kill →
alive-count change → next kill → important dodge → projectile → 1vX →
final kill → round win.

**Data already available** (`round_story.py`, live in the review UI):

- round number, start/end, duration
- every observed kill with actor, victim, weapon, and whether the actor is
  the user or a clanmate
- team sizes and a **derived** alive curve (one life per round, so team size
  minus observed deaths — arithmetic over obituaries, not a server value)
- teleports inside the round window
- `ROUND_STORY_CANDIDATE` machine tag with its reasons

**Still needed:** FIRST MEANINGFUL DAMAGE as a distinct event (not the first
logged micro-event), with time, actor, target, damage, weapon and confidence.
Round win/loss is not yet reliably attributed.

**Not a verdict.** `ROUND_STORY_CANDIDATE` is a machine tag. The five buttons
remain the only human truth.

---

## GRENADE_LAUNCH_AND_IMPACT_SEQUENCE (the "double view")

**Not a mosaic wall.** One grenade after another.

For each selected grenade:

```
PASS A   the player's own FPV around the launch      (~0.2–0.5s, short)
PASS B   the SAME grenade's impact, from
           enemy POV               (a real alternate demo observation)
         OR best available observed POV
         OR a reconstructed / fixed projectile camera
then     the NEXT grenade
```

**The editorial point is CHAOS → COMPREHENSION.** The first view is what the
player experienced and feels chaotic. The second view is where the audience
understands where the grenade went and why the hit was special.

**Provenance is never blurred.** Three distinct kinds of footage:

| | meaning |
|---|---|
| `RECORDED_POV` | the actor's own camera |
| `OBSERVED_POV` | a real alternate demo — somebody else was recording |
| `RECONSTRUCTED` / `SYNTHETIC_CAMERA` | derived from projectile paths |

A reconstructed camera is **never** presented as historical player FPV. Where
no genuine enemy POV exists, one is not invented and labelled real.

**Timing is not fixed.** Effect Lab, the music and the user's eye decide.

**Source pool** — selected by manual review, not by the machine: direct hits,
near-directs, multi-bounce hits, long flights, hits after the grenade leaves
POV, interesting flybys, strange geometry, plus whatever the user marks T1 or
T3.

**Available today:** `GRENADE` + `DIRECT_CONFIRMED_GEO` filter returns 37
occurrences; `NEAR_MISS_GRENADE` 537. The occurrence layer already knows when
a second demo observed the same grenade kill — that is where a genuine enemy
POV comes from.

**Generalises later** to ten rail frags, air rockets, telefrags, jump pads,
deaths, weapon switches, movement beats. The T3 RHYTHM pool exists to feed
exactly these.

---

## What review feeds

| verdict | becomes |
|---|---|
| **T1 FEATURE / FX** | deep FX, camera and animation research |
| **T2 TRANSITION** | the transition-matching system |
| **T3 RHYTHM / MONTAGE** | repeated and musical montage grammars, including the grenade sequence above |
| **T4 KEEP / NORMAL** | clean gameplay, restrained presentation |
| **T5 PASS / FILLER** | not primary, never deleted |

Notes are part of this. `"xray"`, `"full round"`, `"teamfight"`, `"nade
double view"`, `"enemy POV"`, `"10 rails"` — searchable, and they carry
intent no five-way classification can.

---

## A machine tag describes what happened. The verdict decides what it is for.

FUNNY / WEIRD is a **candidate corpus, not a dismissal class**. A grenade or
rocket that flies close past a player may well be FEATURE material deserving
one of the largest treatments. The tag says *this might be unusual*; only the
user says *this matters*.
