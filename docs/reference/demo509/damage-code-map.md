# Damage received, damage dealt and hit feedback

This is the damage chapter of the [action-to-code reference](action-to-code-reference.md).
The sample is protocol 73. The local server code is an explanatory Q3-derived reference;
it is not the proprietary historical Quake Live server. Numerical server constants must
not be assumed to describe this match merely because they appear in this source.

## Damage calculation and recording

| Step | Source | Meaning and limit |
|---|---|---|
| Collision or weapon trace | [weapon chapter](weapon-code-map.md) | A collision, a successful hit and lethal damage are distinct facts. |
| Apply protection and damage | [G_Damage](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_combat.c:821) | Reference implementation handles protections, self damage, knockback, armor and health. |
| Armor absorption | [CheckArmor](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_combat.c:691) | Reference uses a rounded absorption fraction capped by available armor; damage flags may bypass it. |
| Split health and armor loss | [G_Damage accounting](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_combat.c:997) | Armor absorption is removed from the health damage. Direction and damage aggregates are accumulated. |
| Pack feedback | [P_DamageFeedback](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_active.c:36) | Aggregated blood plus armor damage is capped at 255; pitch/yaw encode direction. This is a feedback signal, not a per-shot ledger. |
| Serialize player state | [field table](/mnt/g/quake_legacy/engine/engines/_canonical/code/qcommon/msg.c:2244), [protocol selection](/mnt/g/quake_legacy/engine/engines/_canonical/code/qcommon/msg.c:2986) | Protocol 73 selects playerStateFieldsQ3 in this client. Delta state must be reconstructed before comparing values. |
| Export current sample | [Python reader](/mnt/g/quake_legacy/engine/parser/demo_parse.py:1004) | Stats are retained; several other arrays are consumed but discarded. Public snapshots contain health and armor. |

Zero-based scalar netfield indices are **not byte offsets**:

| Field | Index / encoding | What it can establish |
|---|---|---|
| damageEvent | 29 / 8 bits | Feedback transition counter, wrapping; not an unlimited hit count. |
| damageYaw / damagePitch | 30 / 31, 8 bits each | Quantized feedback direction; the reference uses both 255 for centered world damage. |
| damageCount | 32 / 8 bits | Capped aggregated feedback magnitude. Never sum repeated snapshot values. |
| generic1 | 33 / 8 bits | QL hit-beep category input in the client path below; not universally raw damage. |
| stats[STAT_HEALTH] | stats array index 0 / short | Recorded POV health, including potentially negative lethal values. |
| stats[STAT_ARMOR] | stats array index 4 / short | Recorded POV armor. |
| persistant[PERS_HITS] | persistant array index 1 / short | Hit-feedback counter. Its numerical meaning must be validated for the actual protocol/server. |
| persistant[PERS_ATTACKER] | persistant array index 6 / short | Last attacker slot; insufficient alone to assign every hit in an aggregate. |
| persistant[PERS_ATTACKEE_ARMOR] | persistant array index 14 / short | Packed attackee feedback in the reference implementation; not a universal per-target damage log. |

Stat IDs are defined in [bg_misc.c:43](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_misc.c:43).
Persistant array IDs are defined in [bg_misc.c](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_misc.c:60).
The existing Python scalar state retains damage fields internally but does not export them.
It discards persistant, ammo and powerup array values during reading. The sanitized
[evidence.json](evidence.json) consequently cannot validate those feedback transitions.
This is an **export gap**, not proof that the demo lacks those fields.

The native [MSG_ReadShort](/mnt/g/quake_legacy/engine/engines/_canonical/code/qcommon/msg.c:589)
returns a signed short. The Python reader returns unsigned values: health must be normalized
as signed 16-bit before lethal-damage arithmetic. The audited sample does this.
Never treat 65535 as a health refill; it represents -1 in that encoding.

## From damage to the screen and speakers

[CG_DamageFeedback](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_playerstate.c:388)
turns the feedback into directional view kick and screen damage position. It scales by
health and clamps kick strength; the displayed effect strength is **not numeric HP loss**.
The [playerstate transition](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_playerstate.c:1472)
checks a changed damageEvent and a nonzero damageCount before invoking it.

Pain is another branch. Reference P_DamageFeedback throttles pain emission, and its comment
explicitly describes post-protocol-90 health bucketing. Do not transfer that bucket rule to
this protocol-73 recording or interpret EV_PAIN.eventParm as damage inflicted. Pain sound
and damage view feedback are presentation signals; neither supplies a complete damage ledger.

[CG_CheckLocalSounds](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_playerstate.c:759)
reacts to PERS_HITS changes. For QL it selects a hit-beep category using generic1 / 64;
the neighboring CPMA calculation is a different protocol/mod branch. Camera, following and
sound settings can suppress feedback. A silent playback does not prove no hit occurred.

There is a deliberate ambiguity to preserve: the PERS_HITS header comment describes damage
points, but the local [G_Damage](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_combat.c:975)
reference increments or decrements it by one. A comment or a beep category therefore does
not justify publishing exact damage dealt for this demo.

## Verified sample: observed resource loss

These are consecutive P02 snapshots from round 6 in evidence.json. All times are server
milliseconds. They prove recorded resource changes; they do not identify an attacking weapon.

| Interval | Health | Armor | Observed health + armor decrease |
|---|---|---|---:|
| 218500 → 218525 | 200 → 198 | 100 → 95 | 7 |
| 218550 → 218575 | 198 → 196 | 95 → 90 | 7 |
| 218600 → 218625 | 196 → 194 | 90 → 85 | 7 |
| 220325 → 220350 | 194 → 160 | 85 → 19 | 100 |

For a comparable pair, `health_lost=max(0,H_before-H_after)` and
`armor_lost=max(0,A_before-A_after)`. Keep both components. This is net observed resource
loss within the sampling interval, not necessarily one hit, the weapon's base damage,
or damage dealt by the POV. Pickups, regeneration, resets, POV changes, overkill and multiple
hits can invalidate a naive interpretation. Split streams at client/life/round boundaries.

Round 6 records 195 health and 100 armor lost for the continuously observed primary POV.
Its three kills are documented separately in the weapon chapter. Its exact damage dealt
remains null in the audited record; assigning 295 dealt would reverse attacker and victim.

## Reusable recognition rule

Record received damage as an observed resource delta with its before/after snapshots and
sampling interval. Record hit confirmation separately, retaining the raw counter/category
and protocol interpretation. Record a lethal outcome from obituary with victim, killer and
MOD. Link these observations only when timing and entity identity support that relationship.
Use `unknown` for an unobserved attacker or exact dealt value. Do not substitute zero.
