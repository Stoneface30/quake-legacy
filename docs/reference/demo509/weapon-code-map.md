# DEMO509 — weapons, impacts, damage and death: action to code

This map connects recorded evidence to the local playback implementation.
The `game/g_*` code below is a **reference server implementation**, not the
historical proprietary Quake Live server that produced DEMO509. Its trace,
damage and event-emission structure explains the contract; its numerical damage,
spread, cooldown, radius and armor constants are not historical match facts.

All times below are recorded server milliseconds. P02 and other Pxx identifiers
are sanitized aliases. Evidence comes from
[evidence.json](/mnt/g/quake_legacy/docs/reference/demo509/evidence.json:1),
selected by `events[].event_id` because this JSON is serialized on one line.
The existing [source-of-truth.md](/mnt/g/quake_legacy/docs/reference/demo509/source-of-truth.md:1)
contains the round-six kill spot-checks. This document adds source tracing;
it does not claim new visual validation of every effect.

## Three number spaces that must stay separate

1. A raw QL73 event is an action code after removing sequence bits `0x300`.
2. A `WP_*` value is an equipped/firing/projectile weapon identifier.
3. A `MOD_*` value is a cause of death, carried by obituary `eventParm`.

The local QL-oriented event enum is in
[bg_public.h:790](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_public.h:790).
Its familiar weapon/event values below agree with this parser's QL73 constants.
The separate `EVQ3_*` and `EVQ3DM3_*` enums are **not** QL73 numbers.
[CG_EntityEvent](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_event.c:1737)
masks sequence bits and translates events only for `PROTOCOL_Q3`; copying a
Q3 normalized numeric enum into the raw QL73 parser is therefore unsafe.
Symbolic client cases below refer to that local playback enum.

| Meaning | WP field | Obituary MOD field |
|---|---:|---:|
| Machinegun | 2 | 3 |
| Shotgun | 3 | 1 |
| Grenade | 4 | 4 direct; 5 splash |
| Rocket | 5 | 6 direct; 7 splash |
| Lightning | 6 | 11 |
| Railgun | 7 | 10 |
| Plasma | 8 | 8 direct; 9 splash |

The parser's two lookup tables are at
[demo_parse.py:124](/mnt/g/quake_legacy/engine/parser/demo_parse.py:124).
In particular, `weapon:6` means lightning for a fire/impact record but rocket
for an obituary. The overloaded JSON key does not unify those number spaces.

## Recorded event envelope and parser limits

[Entity event detection](/mnt/g/quake_legacy/engine/parser/demo_parse.py:901)
reads changed entity fields. An event-only entity uses masked `eType` minus
`_ET_EVENTS`; an attached event uses `event & ~0x300`. Previous **raw** values
retain toggle bits to distinguish repeated identical actions.
Only `_CAPTURE_EVENTS` survive the whitelist at
[demo_parse.py:95](/mnt/g/quake_legacy/engine/parser/demo_parse.py:95).

[Playerstate events](/mnt/g/quake_legacy/engine/parser/demo_parse.py:808)
produce `source:"playerstate"`, `entity_num:null`, the followed client's slot,
current PS weapon, origin and event parameter. Their `weapon_name` is null.
A change event's snapshot weapon is not necessarily the destination weapon.

[Entity event output](/mnt/g/quake_legacy/engine/parser/demo_parse.py:940)
keeps event code, entity number, time, encoded client and position.
For selected weapon events it adds `s.weapon` and `eventParm`.
It does **not** export all impact fields such as `otherEntityNum`, rail
`origin2`, or the complete original delta. Missing fields must not be recreated
by pretending a nearby player was the target. A temporary entity's
`clientNum` is not a universal shooter identifier.
Position components may be null: the builder selects the fresh delta when it
exists, without individually filling every missing component from accumulated
state. Null is not a physical coordinate of zero.

## Weapon switch, trigger and muzzle presentation

**Reference mechanic:**
[PM_BeginWeaponChange](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_pmove.c:1484)
starts the drop phase; `PM_FinishWeaponChange` at line 1509 installs the new
weapon and raises it. Firing sets torso attack animation and weapon firing
state, then emits `EV_FIRE_WEAPON` at
[bg_pmove.c:1639](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/bg_pmove.c:1639).
[FireWeapon](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_weapon.c:811)
dispatches the reference server trace or projectile function by weapon.

**Wire → parser:** raw 18 → `change_weapon`; raw 20 → `fire_weapon`.
Equipped weapon comes from `s.weapon` or followed-player `ps.weapon`, in WP
space. A trigger/fire event establishes a shot action, not a hit or damage.

**Client:**
[EV_CHANGE_WEAPON](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_event.c:2295)
plays the selection sound;
[EV_FIRE_WEAPON](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_event.c:2302)
invokes `CG_FireWeapon` for the player entity.
[CG_FireWeapon](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_weapons.c:3159)
sets muzzle-flash timing and weapon-specific sound/effect state.
Weapon animations and continuous beams also consume ongoing entity/playerstate,
so one event is not a full rendered animation description.

## Rocket and grenade: flight, bounce, direct impact and splash

**Reference mechanic:**
[fire_grenade](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_missile.c:568)
and [fire_rocket](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_missile.c:653)
create moving missiles with WP launcher IDs, distinct direct/splash MODs,
trajectory and ownership. Grenade collision can bounce without exploding:
[G_MissileImpact:273](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_missile.c:273).
Impact damage occurs before presentation; client hits carry target
`otherEntityNum`. World impact uses miss/metal-miss. Radius damage then ignores
the directly hit entity in this reference implementation:
[g_missile.c:415](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_missile.c:415).
Timed explosions also emit a miss event before radius damage:
[G_ExplodeMissile](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_missile.c:70).

**Wire → parser:** 41 grenade bounce is not captured; 47 → `missile_hit`;
48 → `missile_miss`; 49 metal miss is not captured. `eventParm` encodes a
surface direction for the impact, not damage. `weapon` is WP4 or WP5.
A miss event can accompany splash damage and a splash kill: “miss” describes
the impact presentation, not a guarantee that nobody was hurt.
A hit event alone supplies neither final damage nor a kill.

**Client:**
[cg_event.c:2612](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_event.c:2612)
decodes direction and routes hits to `CG_MissileHitPlayer`; misses and metal
misses go to `CG_MissileHitWall` with the relevant impact sound class.
[CG_MissileHitWall](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_weapons.c:3389)
selects weapon-specific explosion, mark and sound effects.
[CG_MissileHitPlayer](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_weapons.c:3844)
handles flesh effects and explosive presentation.
[CG_GrenadeTrail](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_weapons.c:1278)
provides a trajectory-driven trail; projectile appearance does not require a
fresh fire event on every visible frame.

## Rail and lightning

**Rail reference:**
[weapon_railgun_fire](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_weapon.c:437)
traces through eligible targets, applies MOD_RAILGUN damage and emits a rail
trail. The trail carries start `origin2`, end `pos.trBase`, shooter `clientNum`
and impact-direction parameter. **Raw 50 → `railtrail`** captures the endpoint
and parameter but loses `origin2`; it is not a per-target damage ledger.
[cg_event.c:2647](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_event.c:2647)
feeds [CG_RailTrail](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_weapons.c:290)
and the endpoint impact path. A visible rail line proves a discharge,
not necessarily a hit; MOD10 obituary proves a rail-caused death.

**Lightning reference:**
[Weapon_LightningFire](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_weapon.c:617)
uses a trace and MOD_LIGHTNING damage, then emits missile hit/miss presentation
with `s.weapon=WP_LIGHTNING`. Thus raw 47/48 with WP6 can be LG, despite the
word “missile”. Repeated raw20 WP6 records are firing samples/events, not
independently measured damage units.
[CG_LightningBolt](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_weapons.c:1746)
builds the continuous beam from player/weapon state;
[cg_weapons.c:2744](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_weapons.c:2744)
calls it during weapon rendering. Impact events supplement the beam.

## Shotgun and bullet impacts

[Bullet_Fire](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_weapon.c:164)
traces a bullet, emits flesh or wall impact and applies reference damage.
Raw45 flesh uses `eventParm` as victim slot; raw46 wall uses it as encoded
normal. `otherEntityNum` identifies the shooter for these reference events.
Client dispatch at
[cg_event.c:2774](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_event.c:2774)
reaches [CG_Bullet](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_weapons.c:4527)
for tracer/flesh/wall presentation. Parameter semantics depend on event type.

[weapon_supershotgun_fire](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_weapon.c:349)
emits raw51 `EV_SHOTGUN` with origin, direction and random seed; reference
[ShotgunPattern](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_weapon.c:321)
traces pellets. [CG_ShotgunFire](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_weapons.c:4271)
reconstructs client presentation from that pattern data.
Raw45, raw46 and raw51 are **outside the current parser whitelist**.
Their absence from this evidence JSON cannot establish no bullets or pellets
were fired/hit. Fire WP2/WP3 and corresponding MOD obituaries remain distinct
possible evidence; no pellet count or shotgun damage is inferred here.

## Damage, death, corpse and gibs

[G_Damage](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_combat.c:821)
is the reference damage path;
[CheckArmor](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_combat.c:691)
and [damage accumulation](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_combat.c:1000)
separate armor absorption and blood/health damage.
Radius damage has its own distance/visibility path at
[G_RadiusDamage](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_combat.c:1192).
These paths explain why impact count × nominal weapon damage is invalid.

Reference death emits obituary fields `eventParm=MOD`,
`otherEntityNum=victim`, `otherEntityNum2=killer` at
[g_combat.c:513](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_combat.c:513).
Raw58 → parser `obituary`, with `weapon` deliberately reinterpreted as MOD.
Raw54–56 → `death`; raw63 → `gib_player`. Death sound and gib events are not
additional kills. Reference death animation selection/event emission is at
[g_combat.c:666](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_combat.c:666),
and gib emission at [g_combat.c:264](/mnt/g/quake_legacy/engine/engines/_canonical/code/game/g_combat.c:264).
Client [death cases](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_event.c:3578)
play model death sounds; raw58 reaches `CG_Obituary` for kill presentation.
[Gib dispatch](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_event.c:3723)
reaches [CG_GibPlayer](/mnt/g/quake_legacy/engine/engines/_canonical/code/cgame/cg_effects.c:1099),
including the QL-specific gib effect path. Client settings can alter visuals.

## Six concrete DEMO509 evidence records

| Event | Time / round | Recorded fact | Valid interpretation |
|---|---|---|---|
| E05082 | 212125 / 6 | P02 playerstate, raw18, WP5 | Switch action while snapshot still carries rocket; destination unproven by this row. |
| E05128 | 212550 / 6 | P02 playerstate, raw20, WP6 | Lightning firing; no damage amount in the row. |
| E05617 | 223600 / 6 | P02 encoded client, raw50, parameter143, endpoint (1279,1138,288) | Rail presentation endpoint; missing start and target cannot be invented. |
| E05568 | 221225 / 6 | raw58, killer P02, victim P04, MOD6 | Rocket direct-cause kill. |
| E05833 | 243525 / 6 | raw58, killer P02, victim P05, MOD10 | Railgun kill. |
| E05945 | 249625 / 6 | raw58, killer P02, victim P07, MOD7 | Rocket splash-cause kill. |

Across the sanitized evidence there are 6,842 fire records, 2,168 missile-hit
records, 2,779 missile-miss records, 222 railtrail records, 79 obituaries,
50 death records and 16 gib records. These are **output record counts**, not
validated unique shot totals or exact hit accuracy; event deduplication and
capture coverage must be audited before using them that way.
`focus_damage_dealt` is null for every round. Health/armor losses are observed
POV state deltas, not attacker attribution. Neither event proximity, pain
sound, blood, hit flash nor a death animation fills that missing damage ledger.
