# Fixture dossier — overkill, Clan Arena 5v5

A complete observable account of ONE recording, decoded from its bytes and checked against the engine's own source. It exists so that any corpus number can be tested against a file whose truth is written down, rather than against another run of the same code.

Identities are file-local slot aliases. The recording does contain player names and the filename contains a nickname; neither is reproduced here.

## 1. Fixture identity

| Field | Value |
|---|---|
| Demo SHA-256 | `a79940882e30b337f2d436207cabbe7cdb2542bec5688450c312823c3e428067` |
| Size | 2,709,923 bytes |
| Packet records | 20,890, clean EOF marker, 0 trailing bytes |
| Filename | withheld (contains a nickname); sha256 `5f486071468cc6a0` |
| Map / gametype / protocol | overkill / CA / 73 |
| Observed server time | 1:13.825 .. 9:58.675 (524.9s) |

The recording begins partway through the server timeline. `server_time_first_ms` is a data key, not a match start and not a HUD clock.

## 2. Decoder provenance

| Field | Value |
|---|---|
| Decoder | `engine/parser/demo_parse.py` sha256 `a234eb417c68a699` |
| Repository commit | `1871e6ee8587` |
| Snapshots / events | 20,889 / 16,971 |
| Packet errors | 0 |
| Missing delta references | 0 |

Zero packet errors is a framing result and proves nothing semantic. The checks that matter are named below, each against a source path:

- **entity model** — code/game/bg_public.h (MAX_CLIENTS 64, ENTITYNUM_WORLD 1022, ENTITYNUM_NONE 1023, ET_EVENTS 13)
- **unchanged entities omitted** — code/qcommon/msg.c MSG_WriteDeltaEntity: with !lc and force=qfalse nothing is written, so an entity present and unchanged costs zero bytes; removal is an explicit bit
- **damage feedback** — code/game/g_active.c P_DamageFeedback
- **round configstrings** — code/cgame/cg_servercmds.c:2705
- **signed short** — code/qcommon/msg.c:589

## 3. Populations — five counts that must never be interchanged

| Population | Count |
|---|---:|
| all observed kills | 102 |
| kills by primary pov slot | 10 |
| deaths of primary pov slot | 8 |
| kills by world | 1 |
| player slots in roster | 10 |
| player slots seen as entities | 9 |

`PLAYER_SLOTS_SEEN_AS_ENTITIES` is one lower than the roster because **the server never sends a client its own entity**. The recorder's body is absent from the entity stream by construction, and its state arrives through the playerstate instead. Any coverage metric that treats that absence as a gap is measuring the protocol, not the match.

## 4. Who recorded this file

| Field | Value |
|---|---|
| Primary POV slot | P00 |
| POV spans | 28 |
| Spans away from the primary slot | 19 |
| ... beginning within 15s of one of its own deaths | 18 |

POV time by slot (seconds): P00 407.4, P13 32.6, P12 25.9, P02 21.9, P04 2.0

The demo was recorded by the client whose playerstate is the default subject. 18 of 19 spans away from P00 begin within 15s of one of that slot's own deaths, which is the Clan Arena spectate-after-death pattern. This establishes WHICH SLOT recorded the file. It does not establish an account name, and no name is written into this dossier.

**Consequence for every per-frag metric:** the playerstate subject changes 27 times in this file. A value read "at the frag" without checking the subject can belong to whoever the camera had drifted onto.

## 5. Teams

| Team | Slots |
|---|---|
| RED | P05, P07, P09, P10, P15 |
| BLUE | P00, P02, P04, P12, P13 |

Source: the configstring team field per slot. It is corroborated independently, without reading that field at all:

> A teammate stays inside the recorder's PVS for most of a round; an enemy enters and leaves it repeatedly. Occupancy spans per slot therefore separate the two teams without reading the team field at all.

| Slot | Team | Occupancy spans |
|---|---|---:|
| P02 | BLUE | 13 |
| P04 | BLUE | 14 |
| P05 | RED | 73 |
| P07 | RED | 63 |
| P09 | RED | 74 |
| P10 | RED | 66 |
| P12 | BLUE | 13 |
| P13 | BLUE | 13 |
| P15 | RED | 84 |

The recorder is on BLUE. Its four teammates hold 13–14 spans each; the five opponents hold 63–84. Two structurally different populations, and the split agrees with the configstring exactly. A demo whose team field is missing can still be split this way.

## 6. Rounds

| Field | Value |
|---|---:|
| Rounds reconstructed | 14 |
| Pseudo-rounds the native parser reports | 27 |
| Rounds with no end signal | 1 |
| **Kills landing AFTER their round's end command** | **13** |

CS_ROUND_STATUS(661) announces the round number and scheduled start; CS_ROUND_TIME(662) > 0 is play running and -1 is play over. Values carry a trailing quote and newline and must be normalised before integer conversion.

| Round | Start | End command | Kills | POV kills | Kills after end cmd | Max lag |
|---:|---|---|---:|---:|---:|---:|
| 1 | 1:29.750 | 1:52.225 | 7 | 1 | 1 | 25ms |
| 2 | 2:02.750 | 2:14.075 | 6 | 0 | 1 | 25ms |
| 3 | 2:24.600 | 3:01.575 | 8 | 3 | 1 | 25ms |
| 4 | 3:12.100 | 3:34.775 | 8 | 1 | 1 | 25ms |
| 5 | 3:45.300 | 4:11.000 | 8 | 1 | 1 | 25ms |
| 6 | 4:21.525 | 4:48.450 | 9 | 0 | 1 | 25ms |
| 7 | 4:58.975 | 5:55.150 | 9 | 0 | 1 | 25ms |
| 8 | 6:05.675 | 6:27.200 | 5 | 0 | 1 | 25ms |
| 9 | 6:37.725 | 6:51.650 | 7 | 1 | 1 | 25ms |
| 10 | 7:02.175 | 7:24.975 | 7 | 2 | 1 | 25ms |
| 11 | 7:35.500 | 7:59.525 | 7 | 0 | 1 | 25ms |
| 12 | 8:10.050 | 8:27.700 | 7 | 0 | 1 | 25ms |
| 13 | 8:38.225 | 9:05.425 | 6 | 0 | 1 | 25ms |
| 14 | 9:15.950 | none (NO_END_SIGNAL) | 8 | 1 | - | - |

### The 25ms rule

Every one of the 13 rounds that carries an end command has **exactly one** kill after it, at **exactly 25 ms** — one 25ms server frame, with no spread at all (observed lags: 25).

The reason is mechanical: the round-end command is logged against the PREVIOUS snapshot, so the kill that ended the round arrives in the next one. The independent audit of a different overkill recording (`docs/reference/demo509`) measured the same 25ms across its own 14 rounds. Two files, two audits, the same constant.

**Rule:** a round window ends at the end command PLUS ONE SNAPSHOT. Any consumer that cuts at the command timestamp loses the winning frag of every round in the corpus.

**This is the clip-window defect, measured.** 13 of 102 kills in this file are logged after the end command of the round they belong to — they are the winning frags. A clip cut at the end-command timestamp removes the very kill the round was decided by. Round windows must run to the next snapshot after the command, and clips must be built around the kill's own timestamp rather than around a round boundary.

## 7. Kill ledger

All 102 observed kills are decoded and assigned to a round (102 of 102). 0 team kill(s); 1 by the world or self.

| Means of death | Kills |
|---|---:|
| LIGHTNING | 39 |
| RAILGUN | 35 |
| ROCKET_SPLASH | 18 |
| ROCKET | 4 |
| SHOTGUN | 3 |
| GRENADE | 1 |
| GRENADE_SPLASH | 1 |
| TRIGGER_HURT | 1 |

Every row is RECORDED: `EV_OBITUARY` carries `otherEntityNum2` (killer), `otherEntityNum` (victim) and `eventParm` (MOD). The full ledger is in `dossier.json` under `kill_ledger`, one row per kill with an id, a round and both teams.

The one kill credited to `WORLD` is entity 1022 (`ENTITYNUM_WORLD`) and is environmental, not a player frag. It must be excluded from any player statistic and included in any account of the round.

## 8. Per-player observability

> Coverage is the fraction of the recording during which this slot was inside the recorder's snapshot at all. Outside it, there is NO state -- not a stale value and not a zero. Any per-player metric must publish this denominator.

| Slot | Team | POV | Spans | Coverage | Longest gap | Kills | Deaths |
|---|---|---|---:|---:|---:|---:|---:|
| P00 | BLUE | yes | - | 0.0% | - | 10 | 8 |
| P02 | BLUE |  | 13 | 70.5% | 30.6s | 9 | 8 |
| P04 | BLUE |  | 14 | 56.6% | 33.6s | 8 | 13 |
| P05 | RED |  | 73 | 38.9% | 38.1s | 8 | 11 |
| P07 | RED |  | 63 | 43.8% | 38.9s | 6 | 12 |
| P09 | RED |  | 74 | 41.4% | 36.9s | 3 | 12 |
| P10 | RED |  | 66 | 51.4% | 46.4s | 12 | 11 |
| P12 | BLUE |  | 13 | 68.5% | 36.9s | 10 | 9 |
| P13 | BLUE |  | 13 | 82.1% | 29.0s | 19 | 7 |
| P15 | RED |  | 84 | 53.6% | 24.0s | 16 | 11 |

Median coverage is **53.6%**. Half of every opponent's time in this match produced no state at all, in gaps running to tens of seconds. That is the denominator for any trait that needs a non-POV player's motion.

Row provenance: 93,694 RECORDED, 0 DELTA_INHERITED. DELTA_INHERITED is 0 here because a live player changes at least one field every snapshot. The label still matters: it is what distinguishes 'present and unchanged' from 'absent', which the exporter previously could not express.

## 9. Events

16,971 supported records.

| Type | Records | Without a resolved client |
|---|---:|---:|
| fire_weapon | 8032 | 106 |
| missile_miss | 3561 | 3559 |
| missile_hit | 2544 | 2544 |
| jump | 801 | 6 |
| change_weapon | 787 | 7 |
| pain | 545 | 0 |
| railtrail | 232 | 32 |
| jump_pad | 145 | 1 |
| obituary | 102 | 102 |
| death | 59 | 0 |
| teleport_in | 56 | 56 |
| use_item | 48 | 0 |
| gib_player | 32 | 4 |
| scoreplum | 17 | 17 |
| teleport_out | 10 | 10 |

**Carrier rule.** A player-carried event (fire, jump, pain, death, weapon change) rides the actor's own entity, and for entity numbers below MAX_CLIENTS the entity number IS the client number. A temp-entity event (obituary, impacts, rail trails) is a freestanding ET_EVENTS entity allocated by G_Spawn from g_entities[MAX_CLIENTS] upward, so it never carries a client and its actor must come from the event's own fields.

Every record with no resolved client is a temp-entity event, which is correct: those entities have no client by construction and their actor must be read from the event's own fields. A null client on such a row is the right answer, not a miss.

Footsteps, water, bullet and bounce impacts and several movement events are outside the capture whitelist. Absence of an exported record is not absence of the action.

## 10. Damage and resources

> P_DamageFeedback sets count = damage_blood + damage_armor, clamps it at 255, and stores it in ps.damageCount. That is damage TAKEN by the playerstate subject, aggregated over a server frame. EV_PAIN's parm is the victim's health AFTER, not a damage amount. Damage DEALT by the recorder is not transmitted and stays null.

| Population | Instances | Reconciling exactly | Rate |
|---|---:|---:|---:|
| all playerstate subjects | 80 | 68 | 85.0% |
| recorder's own playerstate | 62 | 62 | **100.0%** |
| follow-spectated subject | 18 | 6 | 33.3% |

**Numerator:** snapshot pairs where damageEvent toggled, damageCount > 0, the playerstate subject did not change, and neither health nor armour increased across the pair.

**The denominator excludes:**
- spans where the POV subject changed between the pair
- pairs where a pickup raised health or armour inside the same frame
- damage taken by any player who is not the current playerstate subject

Every reconciliation failure is on a follow-spectated subject; on the recorder's own playerstate the identity holds exactly. Roughly half the failures resolve within 125ms (the feedback field and STAT_HEALTH are sampled a frame or two apart) and the rest show a damageCount value repeating across different subjects with no resource change at all, which is a field inherited across a playerstate subject switch rather than a hit. RULE: measure damage taken only on the recorder's own POV spans. A corpus figure computed across all subjects is diluted by spectate spans, not by a decoder defect.

Health range observed: [-58, 200]. MSG_ReadShort is signed (msg.c:589); an unsigned read renders -1 as 65535.

Damage **dealt** stays null for every player, in this file and in general. It is not transmitted in any form.

## 11. What this file cannot support

| Trait | Status | Reason |
|---|---|---|
| AIR_TO_AIR / JUGGLE / ORBIT_KILL / CHASE_DOWN | `REFUSED_UNOBSERVED` | needs continuous velocity and ground contact for a NON-POV player; that slot's coverage is 82% at best here and gaps run to tens of seconds |
| damage dealt / damage efficiency | `REFUSED_UNOBSERVABLE` | not transmitted by the protocol in any form |
| shots fired by a non-POV player | `REFUSED_PARTIAL` | EV_FIRE_WEAPON is only seen while the firer is in PVS |
| round winner | `DERIVED_ONLY` | CS_ROUND_WINNERS is almost never sent; a score delta across the boundary is DERIVED, not RECORDED |

A refusal is a result. Absent values stay null and never become zero.

## 12. Provenance vocabulary used here

| Label | Meaning |
|---|---|
| `RECORDED` | a field or event decoded from this file's bytes |
| `DELTA_INHERITED` | carried forward from the delta reference snapshot; the entity was present and did not change |
| `DERIVED` | computed from recorded values by a calculation stated here |
| `SOURCE_EXPLAINED` | a code path in the canonical tree explains the mechanism; it does not certify this server's constants |
| `UNOBSERVED` | outside the recorder's snapshot; no value exists |
| `REFUSED_*` | the question cannot be answered from this evidence |

A label does not imply any other label. Nothing in this dossier is `VISUALLY_CHECKED`; that set is specified separately and is not yet run.
