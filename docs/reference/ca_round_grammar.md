# CLAN ARENA ROUND GRAMMAR — learned from real rounds

Derived by `engine/parser/ca_reference.py` from five real CA demos in the
corpus (overkill ×3, blackcathedral, trinity), 0 packet errors across all of
them. Nothing here is asserted from memory: every entry traces to an observed
value sequence, and the extractor re-derives it on demand.

This file is the **specification the synthetic round compiler is built
against**. Where it disagrees with an assumption in code, this file wins,
because it is what the engine actually did.

---

## 1. ROUND STATE CONFIGSTRINGS

| idx | name | observed form |
|---|---|---|
| **661** | `CS_ROUND_STATUS` | `\time\<server_time_ms>\round\<N>` — a **future** timestamp for when the round begins. `\time\-1\round\0` means no round is pending. |
| **662** | `CS_ROUND_TIME` | round start ms; `-1` once the round is over |
| **663** | `CS_RED_PLAYERS_LEFT` | red alive count |
| **664** | `CS_BLUE_PLAYERS_LEFT` | blue alive count |
| 5 | `CS_WARMUP` | `\time\<ms>`, then `\time\-1`, then `\time\0` |
| 6 / 7 | `CS_SCORES1/2` | team round scores |
| 705 | `CS_ROUND_WINNERS` | winning team |

### The alive counters ramp UP at round start

The observed sequence at a round boundary is not what a naive model predicts.
Both counters are driven to `0` and then **counted up one at a time** to the
team size as players are placed:

```
+137150ms  cs 663 = '0'      <- reset
+137150ms  cs 664 = '0'
+137150ms  cs 661 = '\time\144150\round\1'   <- round 1 begins at 144150
+137150ms  cs 663 = '1'
+137150ms  cs 663 = '2'
+137150ms  cs 664 = '1'
+137150ms  cs 664 = '2'
... interleaved, up to the roster size
```

They then **count down** as players die. So "alive" is a level, not a diff,
and a synthetic round must emit the same ramp or the HUD starts wrong.

### Round start is announced BEFORE it happens

`661` carries a timestamp in the future — the countdown window. This is the
same ~7 s gap measured earlier from 66,703 samples, and it is why the round
can be announced and counted down before anything moves.

---

## 2. PLAYER ENTITY FIELD PROFILE

Profiled across every rendered player entity in the reference set. `change %`
is what separates a structural requirement from an animated one.

| field | present % | change % | observed values | meaning |
|---|---|---|---|---|
| 1 / 2 / 5 | ~100 | 35–80 | coordinates | `pos.trBase` X/Y/Z |
| 3 / 4 / 7 | ~95 | 36–74 | velocities | `pos.trDelta` |
| 6 / 8 | ~98 | 31–50 | angles | `apos.trBase` yaw / pitch |
| **10** | 98 | 8.2 | 1, 20, 257, 276, 309… | event + toggle bits |
| 11 | 96 | 8.1 | 1.0–7.0 | float, small enumerated |
| **12** | **100** | **0.0** | `1` | `eType` = ET_PLAYER |
| **13** | **100** | **7.7** | 7, 9, 10, 11 (+128) | **torsoAnim** |
| 14 | 56 | 0.4 | 6, 23, 73–79 | `eventParm` |
| **15** | **100** | **5.3** | 15, 16, 18, 19, 22 (+128) | **legsAnim** |
| **16** | 100 | 2.2 | 1022, 1023, small ints | `groundEntityNum`; 1023 = airborne |
| **17** | **100** | **0.0** | `1` | structural, always 1 |
| 18 | 88 | 1.3 | 1, 4, 5, 256, 260, 4096, 32768 | `eFlags` |
| **20** | 100 | 0.7 | 1–8 | `weapon` |
| **21** | 95 | 0.0 | client slot | `clientNum` |
| 22 | 88 | 0.2 | 45/90/135/…/360 | quantised angle (legs yaw) |
| **24** | **100** | **0.0** | `1` | structural, always 1 |
| 25/26/27 | 94 | 0.1 | coordinates | a second position |
| **28** | 100 | 0.1 | 2097409, 3151887, 4200463 | `solid` — packed bbox |
| 29 | 51 | 0.1 | `1` | — |

### The animation finding

Fields **13** and **15** are the two animation slots, each also appearing
+128. Read against Q3's `animNumber_t`:

- **13 = torsoAnim** — 7 `TORSO_ATTACK`, 9 `TORSO_DROP`, 10 `TORSO_RAISE`,
  11 `TORSO_STAND`
- **15 = legsAnim** — 15 `LEGS_RUN`, 16 `LEGS_BACK`, 18 `LEGS_JUMP`,
  19 `LEGS_LAND`, 22 `LEGS_IDLE`
- **128 = `ANIM_TOGGLEBIT`** — a repeated animation only replays when this
  flips, the same mechanism `EV_EVENT_BIT1/BIT2` give events

The first synthetic players held torso at 7 and legs at 15+128 permanently —
mid-attack and mid-run forever — which is exactly why they read as frozen.

### Fields that must be present and never change

`12` (eType), `17`, `24`, `28` (solid). These were absent from the first
synthetic entities. They are set from a real template rather than reasoned
about, because a player that does not render gives no feedback about which
one was missing.

---

## 3. EVENTS

An event is a **temp entity** whose `eType` is `ET_EVENTS (13) + code`, with
the two toggle bits above it. An obituary is therefore `eType 71`, carrying:

| field | meaning |
|---|---|
| 14 | MOD (`eventParm`) |
| 19 | victim (`otherEntityNum`) |
| 31 | killer (`otherEntityNum2`) |
| 1/2/5 | where it happened |

`EV_OBITUARY = 58`. Other events observed in the reference set: `pain`,
`fire_weapon`, `missile_hit`, `jump`, `jump_pad`.

**A float field written as 0 comes back absent**, so an event at `y = 0.0` has
no position and the parser builds no record. Synthetic events must avoid exact
zero coordinates.

---

## 4. MID-DEMO CONFIGSTRING CHANGES

`svc_configstring` appears **only inside the gamestate**. After that, a change
arrives as a reliable server command:

```
cs <index> "<value>"
```

Observed values carry a trailing `"` and newline through the parser's
absorption (`'3"\n'`), which any consumer comparing exact strings must expect.

---

## 5. WHAT THIS SPECIFIES FOR THE SYNTHETIC COMPILER

1. Emit the alive-counter **ramp up** at round start, not just the final level.
2. Announce the round through `661` with a **future** timestamp.
3. Give every player entity `12`, `17`, `24`, `28` and a real `16`.
4. Drive `13`/`15` from an animation state machine, flipping bit 128 to
   restart a repeat.
5. Send round-state changes as `cs` server commands, not `svc_configstring`.
6. Keep event coordinates off exact zero.
