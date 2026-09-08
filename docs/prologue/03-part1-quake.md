# PART 1 — WHAT IS QUAKE / WHY FAST ARENA FPS MATTERS

**Target length:** 60–80 s. **Standalone cut:** "WHY FAST ARENA FPS STILL WORKS".

---

## THE VISUAL THESIS

> **Quake is not a fast shooter. It is a shooter where speed is something you
> build, and can lose.**

That is the distinction the audience must feel, and it is defensible from one
line of engine source: `pm_accelerate = 10.0` on the ground,
`pm_airaccelerate = 1.0` in the air (`bg_pmove.c:38-39`). You keep accelerating
while airborne — slowly, and only if you steer correctly. Speed is *earned*,
continuously, by a player doing something difficult.

Everything else in Part 1 is that idea in different clothes:
- A teleporter **throws your speed away** — flat 400 ups out, 160 ms with no
  steering (`g_misc.c:79`).
- A jump pad **ignores what you brought** — its launch is solved from the map's
  geometry when the map loads (`g_trigger.c:160-192`).
- A rocket jump **buys speed with health**.

Speed is a currency. That is a story, and it takes ten seconds of footage.

---

## THE THESIS WE MAY *NOT* CLAIM

The brief's "maybe arena FPS was built for the wrong era" line is a good line.
It is also an unfalsifiable claim about culture. **It ships only as a question,
never as an assertion**, and never adjacent to a number that would lend it
false authority.

| Banned | Permitted |
|---|---|
| "Arena FPS is what audiences want now" | "Maybe the world caught up." (as a question, on its own card) |
| "Modern shooters are slow / bad" | *no comparison to another game appears at all* |
| Any esports viewership statistic | *nothing* — we have no such data |

**Hard rule: Part 1 never names, shows, or implies another game.** The
invitation works because it is about Quake. The moment it becomes about what
Quake is *better than*, it becomes the rant the brief bans.

---

## BEAT BOARD

Times are cumulative. `⟨SLOT_X⟩` = placeholder pending human review.

| # | t | dur | Picture | Sound | Text |
|---|---|---|---|---|---|
| 0 | 0.0 | 2.0 | **Black.** | A single footstep. Then a jump. Nothing else. | — |
| 1 | 2.0 | 3.5 | ⟨SLOT_ACCEL⟩ one unbroken strafe run, no cuts. PANTHEON speed readout climbs. | Game audio only, dry. | `320` → `420` → `520` → `620` counting up **in the engine's own colour bands** |
| 2 | 5.5 | 0.2 | ⟨SLOT_ROCKET_JUMP⟩ | impact | — |
| 3 | 5.7 | 0.2 | ⟨SLOT_RAIL_FLICK⟩ | rail | — |
| 4 | 5.9 | 0.4 | ⟨SLOT_AIR_ROCKET⟩ | explosion | — |
| 5 | 6.3 | 0.2 | ⟨SLOT_TELEPORT⟩ | telein/teleout | — |
| 6 | 6.5 | 0.2 | ⟨SLOT_JUMPPAD⟩ | pad | — |
| 7 | 6.7 | 0.6 | ⟨SLOT_LG_TRACK⟩ | LG hum | — |
| 8 | 7.3 | 0.2 | ⟨SLOT_TELEFRAG⟩ | telefrag | — |
| 9 | 7.5 | **1.2** | **Black. Total silence.** | — | — |
| 10 | 8.7 | 1.3 | Black | low hit | **`QUAKE.`** |
| 11 | 10.0 | 1.5 | Black → first geometry | — | **`FAST ARENA FPS`** |

**Beat 9 is the most important cut in Part 1.** Seven events in 1.5 s, then 1.2 s
of absolutely nothing. The chaos is only legible because of the silence that
frames it. *Fast does not mean chaotic* is enforced structurally, not by slowing
anything down.

### Second movement — "now read it again"

| # | t | dur | Beat |
|---|---|---|---|
| 12 | 11.5 | 6.0 | **Replay beat 1's run** — same footage, now annotated. Air-accel vector drawn against ground-accel. One card: `MOVEMENT IS A WEAPON` |
| 13 | 17.5 | 4.0 | **The trade.** Rocket jump at 0.25×, health bar drops, speed graphic spikes. `SPEED COSTS HEALTH` |
| 14 | 21.5 | 3.0 | **The reset.** Teleport at speed → exit at flat 400. `A TELEPORTER TAKES YOUR SPEED` |
| 15 | 24.5 | 8.0 | **Weapon language** — 4 cards, 2 s each, each over one ⟨SLOT⟩ |
| 16 | 32.5 | 4.0 | Rising density montage, ⟨SLOT_RHYTHM ×6⟩ cut to music |
| 17 | 36.5 | 2.5 | Hard stop. **`THIS IS AN ARENA.`** → Part 2 |

### Weapon language (beat 15) — measured, not asserted

The archive itself ranks the weapons. From 206,268 canonical occurrences:

| Weapon | Kills | Card |
|---|---|---|
| Lightning | **77,688** | `LG — you must not stop tracking` |
| Railgun | **61,106** | `RAIL — instant, to 8,192 units` |
| Rocket (direct + splash) | **51,176** | `ROCKET — 900 ups. Lead it.` |
| Gauntlet | **904** | `GAUNTLET — 904 times in 200,000.` |

The gauntlet card is the best joke in the prologue and it is a fact. Three
weapons are 92% of everything that ever happened; the gauntlet is 0.4%, which is
exactly why it means what it means. **No weapon tutorial. Four cards.**

---

## COPY CANDIDATES

Locked-safe (every one traceable):
- `QUAKE.` · `FAST ARENA FPS` · `MOVEMENT IS A WEAPON` · `SPEED COSTS HEALTH`
- `A TELEPORTER TAKES YOUR SPEED` · `THIS IS AN ARENA.`
- `RAIL — INSTANT, TO 8,192 UNITS` · `ROCKET — 900 UPS` · `904 TIMES IN 200,000`

Thesis cards — **one only, and only if it does not play as smug in the cut**:
- `MAYBE IT WAS BUILT FOR THE WRONG ERA.`
- `NO WAITING.`
- `BEFORE SHORT-FORM VIDEO, THERE WAS THIS.`

Rejected: anything comparing Quake to another game; any UPS number not measured
from the shot on screen; any claim about what audiences want.

---

## SPEED ON SCREEN — the ruling

Use a **PANTHEON speed graphic driven by measured `peak_speed`**, not the
Wolfcam HUD. Reasons: (a) the capture profile that would draw the HUD number is
currently broken — it sets `cg_drawSpeedometer`, which is a q3mme cvar
WolfcamQL does not have (see `02-movement-and-speed.md` §3); (b) our own graphic
is honest about being a measurement; (c) it is styled to the film.

Numbers climb through the **engine's real colour bands — 320 / 420 / 520 / 620**
(`cg_draw.c:844-857`), so the graphic agrees with what the engine itself would
have coloured.

**Binding:** the number shown is `peak_speed` of the moment on screen, from
`movement_moments_v1`. Never a stock figure. It is a ~0.3 s segment average, so
it *understates* the instantaneous peak — we are never overclaiming.

---

## SLOT REQUIREMENTS → pool sizes today

| Slot | Requirement | Qualifying now |
|---|---|---|
| `SLOT_ACCEL` | HIGH_SPEED, 1.0–2.5 s, peak ≥ 700 ups, unbroken, readable trajectory | **469** moments |
| `SLOT_ACCEL` (frag ending) | as above, `ENDS_IN_FRAG` | **166** moments |
| `SLOT_RAIL_FLICK` | RAILGUN, T1/T3, clean impact, ≤ 0.6 s | 61,106 candidates |
| `SLOT_AIR_ROCKET` | ROCKET direct, victim airborne | pending airshot derivation |
| `SLOT_TELEFRAG` | `mod_name = TELEFRAG` | **1,443** |
| `SLOT_LG_TRACK` | LIGHTNING, sustained contact ≥ 0.6 s | 77,688 candidates |
| `SLOT_TELEPORT` | `teleport_transits_v1`, confirmed | see corpus |
| `SLOT_JUMPPAD` | `JUMPPAD_ACTION` | **40,342** |

Every pool is deep. **Nothing is auto-assigned** — human review assigns a role,
and only then does a moment become a candidate for a slot.
