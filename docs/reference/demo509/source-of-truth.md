# DEMO509 — worked source-of-truth reference

For the gameplay-to-engine mapping, start with the [action-to-code reference](action-to-code-reference.md). This file remains the audited sample timeline.

Date: 2026-09-06. **Status: audited decoded-event reference with a rendered round-6 spot-check. The other rounds have not been visually reviewed.** This document defines what this one recording can support, not a promise that every server event or another player’s complete state exists in the demo.

## Source and reproducibility

- Source fingerprint: `876bb6742ace7189e709d55356534ab206f2a095eea2e33d828c3bc3724e1545` (SHA-256).
- 2,804,478 bytes; 19,730 complete packet records; clean EOF and no trailing bytes.
- 19,729 decoded snapshots; 0 reported packet exceptions; 14,211 supported event records.
- Map **overkill**, Clan Arena. Observed server time **0:30.075–8:45.625**, 495.550s. This is a partial recording of the server timeline, not a clock starting at zero.
- Primary POV **P02** means the most frequently followed numeric client slot. It does not certify the user’s account identity. Other POV slots are P00, P03 and P06. No player names or account IDs appear in these outputs.
- [Interactive event explorer](explorer.html) and [complete sanitized evidence](evidence.json) contain every selected event, snapshot and round-control signal from this audit.

## What the audit corrected before trusting the timeline

1. The production parser emitted **29 pseudo-rounds, all with start_ms=0**. Server-command values retain a closing quote followed by a newline, so integer conversion fails. It also increments the round counter for the end sentinel `-1`. These native round labels are excluded here.
2. `CS_ROUND_STATUS` (661) supplies the round number and scheduled start. `CS_ROUND_TIME` (662) entering a positive time starts play; `-1` ends play. Repeated reliable commands do not create additional rounds. This recording announces **15 rounds**.
3. Round-end commands are logged against the previous snapshot. Each of the first 14 terminal kills appears **25ms after that logged command time**. Cutting at the logged command would remove the winning frag. This audit retains the interval through the next snapshot; both times are in the JSON.
4. Health is exposed as an unsigned short by this parser: e.g. 65535 represents -1, not enormous health. This audit converts health with `h - 65536 if h >= 32768 else h`. Resource-loss totals clamp death health to zero and never count POV switches as damage.
5. Round 15 has no ordinary `662=-1` transition. The red score reaches the configured round limit 10 at 519850–519875ms, followed by an intermission signal at 521550–521575ms. Its endpoint below is the **intermission evidence bound**, not an invented round-end signal.

Source checks: `engine/parser/demo_parse.py:691` (round counter), `:722` (server-command normalization), `:1019` (stats shorts), `:1087` (health mapping); `engine/engines/_canonical/code/cgame/cg_servercmds.c:2705` (661/662 semantics); `engine/engines/_canonical/code/game/bg_public.h:87` (intermission), `:108` (round indices); `engine/engines/_canonical/code/qcommon/msg.c:589` (signed short). Zero packet errors alone did **not** detect any of these semantic problems.

## Complete round ledger

Times below are absolute **server time**, suitable as data keys. They are not blindly interchangeable with the HUD clock or a seekclock argument. Kills cover all observed actors; P02 values refer only to the primary POV slot.

| Round | Start | End evidence bound | Kills | P02 kills | P02 deaths | P02 observed HP / armor lost |
|---:|---|---|---:|---:|---:|---:|
| 1 | 0:46.000 | 1:06.000 | 5 | 1 | 0 | 39 / 83 |
| 2 | 1:16.500 | 1:36.275 | 6 | 2 | 0 | 50 / 99 |
| 3 | 1:46.775 | 2:02.925 | 5 | 0 | 1 | 200 / 100 |
| 4 | 2:13.425 | 2:36.850 | 6 | 0 | 1 | 200 / 100 |
| 5 | 2:47.350 | 3:21.500 | 7 | 0 | 1 | 200 / 100 |
| 6 | 3:32.000 | 4:09.625 | 6 | 3 | 0 | 195 / 100 |
| 7 | 4:20.125 | 4:33.150 | 5 | 0 | 1 | 200 / 100 |
| 8 | 4:43.650 | 5:01.425 | 6 | 0 | 1 | 200 / 100 |
| 9 | 5:11.925 | 5:27.200 | 4 | 2 | 0 | 37 / 73 |
| 10 | 5:37.700 | 5:50.800 | 4 | 0 | 1 | 200 / 100 |
| 11 | 6:01.300 | 6:10.675 | 4 | 0 | 0 | 28 / 70 |
| 12 | 6:21.175 | 7:11.175 | 6 | 0 | 1 | 200 / 100 |
| 13 | 7:21.675 | 7:36.100 | 4 | 0 | 0 | 150 / 100 |
| 14 | 7:46.600 | 8:05.875 | 5 | 1 | 0 | 149 / 100 |
| 15 | 8:16.375 | 8:41.575 (intermission) | 6 | 1 | 1 | 200 / 100 |

HP/armor loss is **damage received or other resource depletion while this POV is observable**, not damage P02 dealt. It excludes missing intervals and POV changes and is not a full combat damage ledger. Enemy pain cues do not identify their attacker or reliably count shots.

## Worked multi-action example: round 6

Review the round as a complete sequence from **3:32.000 to 4:09.625**. P02 makes **three kills**, not three unrelated review clips. The last kill coincides with the round boundary and is lost by a naive cut at the command timestamp.

| Event | Server time | Time into round | Encoded action |
|---|---|---:|---|
| E05521 | 3:39.350 | 7.350s | P04 → P03: LIGHTNING |
| E05555 | 3:40.350 | 8.350s | P07 → P06: RAILGUN |
| E05568 | 3:41.225 | 9.225s | P02 → P04: ROCKET |
| E05833 | 4:03.525 | 31.525s | P02 → P05: RAILGUN |
| E05908 | 4:05.100 | 33.100s | P00 → P01: LIGHTNING |
| E05945 | 4:09.625 | 37.625s | P02 → P07: ROCKET_SPLASH |

**Editorial proposal, not a detected fact:** use the full round as source material; place effects around the three P02 outcomes at 221225, 243525 and 249625ms. Preserve the buildup and the long gap between kills. A stutter, local time effect or camera insert is a note for later construction; it is not already present in the recording. No automatic highlight score or batch selection was applied.

## Event → code → potential image contract

| Encoded evidence | What it establishes | What it does not establish | Source path |
|---|---|---|---|
| Obituary event 58, otherEntityNum2, otherEntityNum, eventParm | Killer slot, victim slot, MOD cause, snapshot timestamp | Aim quality, spectacle, complete damage contribution | parser `_build_event`; canonical `cg_event.c` EV_OBITUARY |
| EV_FIRE_WEAPON 20 on a player entity | Observed firing cue and WP weapon value | Hit, kill, or exact pellet/beam damage | parser event table; canonical `cg_event.c` |
| EV_MISSILE_HIT 47 / MISS 48 | Impact cue at encoded position; WP weapon namespace | Shooter attribution from generic client_num; splash damage amount | parser `_build_event`; canonical event handling |
| EV_RAILTRAIL 50 | Rail effect event | Confirmed kill or complete aim trajectory by itself | canonical `cg_event.c` rail effect branch |
| EV_PAIN 53 | Victim pain cue, subject to throttling/visibility | One pain = one shot; exact damage dealt by a named attacker | canonical pain event branch |
| Playerstate origin, angles, health, armor | Followed player’s reported state at snapshot time | All players’ private state throughout the round | parser `_parse_snapshot` / playerstate decoder |
| CS661, CS662, CS14 | Round identity/scheduling, active/end state, intermission signal | A round number from counting every configstring change | canonical `cg_servercmds.c:2705` |

A rendered frame is `Render(engine build, assets, demo state at t, camera, cfg, FX state)`. The bytes constrain the scene but do not fix camera, textures, HUD or postprocessing. A screenshot becomes visual evidence only when those inputs and its server timestamp are recorded. The explorer path plot is a **coordinate diagram**, not a gameplay screenshot.

## Every observed kill

| Event | Round | Server time | Killer | Victim | MOD cause |
|---|---:|---|---|---|---|
| E00622 | 1 | 0:50.050 | P05 | P03 | ROCKET_SPLASH |
| E00674 | 1 | 0:50.400 | P00 | P04 | LIGHTNING |
| E01067 | 1 | 1:01.750 | P02 | P07 | ROCKET |
| E01096 | 1 | 1:02.325 | P00 | P01 | LIGHTNING |
| E01130 | 1 | 1:06.000 | P00 | P05 | ROCKET_SPLASH |
| E01739 | 2 | 1:20.825 | P06 | P04 | LIGHTNING |
| E01756 | 2 | 1:20.950 | P05 | P03 | LIGHTNING |
| E01823 | 2 | 1:21.625 | P02 | P01 | RAILGUN |
| E02044 | 2 | 1:27.500 | P02 | P05 | ROCKET_SPLASH |
| E02076 | 2 | 1:29.075 | P07 | P00 | ROCKET |
| E02114 | 2 | 1:36.275 | P06 | P07 | SHOTGUN |
| E02863 | 3 | 1:53.900 | P04 | P00 | LIGHTNING |
| E02897 | 3 | 1:54.775 | P05 | P02 | LIGHTNING |
| E02905 | 3 | 1:54.825 | P03 | P01 | RAILGUN |
| E02981 | 3 | 1:57.625 | P05 | P06 | LIGHTNING |
| E03025 | 3 | 2:02.925 | P05 | P03 | ROCKET |
| E03503 | 4 | 2:17.500 | P01 | P02 | LIGHTNING |
| E03678 | 4 | 2:19.225 | P06 | P07 | LIGHTNING |
| E03739 | 4 | 2:20.525 | P06 | P01 | LIGHTNING |
| E03867 | 4 | 2:27.825 | P04 | P06 | RAILGUN |
| E03875 | 4 | 2:28.150 | P00 | P05 | RAILGUN |
| E03924 | 4 | 2:36.850 | P03 | P04 | ROCKET_SPLASH |
| E04660 | 5 | 2:53.325 | P07 | P02 | RAILGUN |
| E04671 | 5 | 2:53.575 | P00 | P01 | ROCKET_SPLASH |
| E04826 | 5 | 2:57.775 | P03 | P04 | RAILGUN |
| E04864 | 5 | 3:01.800 | P07 | P06 | RAILGUN |
| E04881 | 5 | 3:03.600 | P03 | P07 | RAILGUN |
| E05011 | 5 | 3:17.325 | P05 | P00 | RAILGUN |
| E05024 | 5 | 3:21.500 | P05 | P03 | RAILGUN |
| E05521 | 6 | 3:39.350 | P04 | P03 | LIGHTNING |
| E05555 | 6 | 3:40.350 | P07 | P06 | RAILGUN |
| E05568 | 6 | 3:41.225 | P02 | P04 | ROCKET |
| E05833 | 6 | 4:03.525 | P02 | P05 | RAILGUN |
| E05908 | 6 | 4:05.100 | P00 | P01 | LIGHTNING |
| E05945 | 6 | 4:09.625 | P02 | P07 | ROCKET_SPLASH |
| E06407 | 7 | 4:26.225 | P04 | P06 | LIGHTNING |
| E06478 | 7 | 4:27.575 | P01 | P03 | LIGHTNING |
| E06577 | 7 | 4:29.725 | P00 | P01 | ROCKET |
| E06633 | 7 | 4:31.750 | P04 | P02 | RAILGUN |
| E06697 | 7 | 4:33.150 | P05 | P00 | LIGHTNING |
| E07256 | 8 | 4:47.400 | P04 | P06 | LIGHTNING |
| E07344 | 8 | 4:48.200 | P00 | P01 | LIGHTNING |
| E07563 | 8 | 4:52.325 | P00 | P04 | LIGHTNING |
| E07569 | 8 | 4:52.400 | P05 | P03 | ROCKET_SPLASH |
| E07667 | 8 | 4:54.625 | P05 | P02 | LIGHTNING |
| E07791 | 8 | 5:01.425 | P07 | P00 | RAILGUN |
| E08337 | 9 | 5:22.225 | P03 | P01 | RAILGUN |
| E08512 | 9 | 5:23.700 | P02 | P07 | LIGHTNING |
| E08726 | 9 | 5:26.200 | P00 | P04 | SHOTGUN |
| E08739 | 9 | 5:27.200 | P02 | P05 | RAILGUN |
| E09224 | 10 | 5:41.525 | P05 | P06 | LIGHTNING |
| E09441 | 10 | 5:45.025 | P01 | P00 | LIGHTNING |
| E09593 | 10 | 5:48.625 | P01 | P03 | LIGHTNING |
| E09630 | 10 | 5:50.800 | P01 | P02 | ROCKET_SPLASH |
| E10166 | 11 | 6:05.325 | P03 | P04 | ROCKET_SPLASH |
| E10211 | 11 | 6:06.550 | P03 | P01 | RAILGUN |
| E10460 | 11 | 6:09.325 | P00 | P07 | LIGHTNING |
| E10598 | 11 | 6:10.675 | P00 | P05 | LIGHTNING |
| E10807 | 12 | 6:23.875 | P00 | P05 | ROCKET_SPLASH |
| E11034 | 12 | 6:29.325 | P03 | P01 | RAILGUN |
| E11108 | 12 | 6:31.050 | P04 | P02 | LIGHTNING |
| E11212 | 12 | 6:32.325 | P06 | P04 | LIGHTNING |
| E11237 | 12 | 6:32.900 | P07 | P00 | LIGHTNING |
| E11465 | 12 | 7:11.175 | P06 | P07 | RAILGUN |
| E12042 | 13 | 7:32.050 | P00 | P07 | ROCKET_SPLASH |
| E12066 | 13 | 7:32.775 | P03 | P05 | RAILGUN |
| E12195 | 13 | 7:34.225 | P00 | P01 | SHOTGUN |
| E12327 | 13 | 7:36.100 | P03 | P04 | RAILGUN |
| E13114 | 14 | 7:51.925 | P03 | P07 | ROCKET_SPLASH |
| E13175 | 14 | 7:52.800 | P04 | P03 | LIGHTNING |
| E13274 | 14 | 7:54.550 | P06 | P01 | LIGHTNING |
| E13335 | 14 | 8:01.025 | P06 | P04 | ROCKET_SPLASH |
| E13366 | 14 | 8:05.875 | P02 | P05 | ROCKET |
| E13677 | 15 | 8:19.200 | P04 | P03 | LIGHTNING |
| E13994 | 15 | 8:27.550 | P02 | P04 | ROCKET_SPLASH |
| E14018 | 15 | 8:28.150 | P05 | P02 | ROCKET |
| E14065 | 15 | 8:30.025 | P06 | P05 | RAILGUN |
| E14183 | 15 | 8:36.575 | P00 | P01 | ROCKET_SPLASH |
| E14208 | 15 | 8:39.875 | P06 | P07 | RAILGUN |

## Supported event inventory

| Type | Records |
|---|---:|
| fire_weapon | 6,842 |
| missile_miss | 2,779 |
| missile_hit | 2,168 |
| change_weapon | 692 |
| jump | 657 |
| pain | 448 |
| railtrail | 222 |
| jump_pad | 162 |
| obituary | 79 |
| teleport_in | 64 |
| death | 50 |
| gib_player | 16 |
| scoreplum | 16 |
| use_item | 11 |
| teleport_out | 5 |

These are observed supported event records, not the number of all actual actions on the server. The parser deliberately omits many event types (including footsteps); occluded/private state can be absent. Snapshot frequency is 40Hz in the regular 25ms portions; the decoder reported a few longer intervals, so motion between samples is not fully observed.

## Reuse on another demo

1. Fingerprint the actual input and parser/source versions; validate packet framing, clean EOF, monotonic time and reported decoder errors.
2. Identify protocol and gametype before selecting constants. Keep WP weapon IDs separate from MOD obituary causes.
3. Reconstruct round identity from explicit round metadata; preserve end-command timing uncertainty and terminal intermission behavior. Never use pseudo-round counters as the golden reference.
4. Assign file-local slot aliases and time-aware team membership. Preserve POV switches; do not treat a followed player as an account identity.
5. Retain all events in the round. Derive editorial priority separately from observations, with a stated score recipe and missing-data coverage.
6. Record image proof for selected timestamps: demo hash, actual binary/cgame hash, pak/assets hash, cfg hash, camera/POV, server timestamp, frame number and output hash. Compare rendered outcome to expected event cues.
7. Require a visual check and an independent parser cross-check before promoting derived metrics to a corpus-wide scoring rule. This audit has spot-checked the three P02 round-6 outcomes visually; the independent-decoder gate is still open.

## Related command research

[Capture, camera and effect command reference](../2026-09-06-capture-effects-command-reference.md) gives 20 source-confirmed command families. Runtime support in the installed engine is not implied. Use `seekservertime` for absolute millisecond keys; verify the scheduler and cfg behavior in the installed binary before automation.

## Remaining work before this is visual ground truth

- Completed: bounded round-6 capture and three outcome frame checks. Remaining: visually review the other rounds and confirm the precise server-time/frame relationship with a rendered timing overlay.
- Cross-check obituary count/timing with an independent decoder, not another invocation of the same Python parser.
- Fix and regression-test server-command normalization, signed health decoding and round phase handling before using native parser round fields as authoritative corpus data.
- Define and validate a damage-dealt estimator only if the required attacker/victim evidence exists; leave absent numbers null.

## Rendered round-6 proof

A single bounded engine capture now links this recording to actual game pixels. Local media remains under ignored `output/demo_v2/demo509-reference/` because the in-game notifications contain player names. Do not copy those pixels into a public commit.

- Requested server window: **212000–250625ms**, including one second after the final kill.
- Measured video: **1280×720, H.264, 30fps, 38.633333s**; audio/container duration 38.693016s. No final-production quality claim is made.
- Capture plus transcode elapsed: **24.6778s** in this one run; no old-profile benchmark was run.
- Capture profile fingerprint: `818a3cb60e48`.
- Engine SHA-256: `a588c56eb7e5318a516e33b2bdd15d8e75f221653d8c26edb9642a7c62bbc0e6`.
- Cgame SHA-256: `6d4f1db50e812da961464ab6ac6a16b6932a2e51f385441b4d97dd3bba2025c7`.
- MP4 SHA-256: `4a472be53ddbe5efadaf55caf7a913e953124b42e63dec1ddb748c31e256b3ca`.

| Decoded outcome | Zero-based video frame checked | Relative frame time | Visible corroboration |
|---|---:|---:|---|
| E05568, 221225ms | 281 | 9.3667s | Primary-POV kill notification; rocket/explosion outcome visible. |
| E05833, 243525ms | 951 | 31.7000s | Primary-POV kill notification; rail beam visible. |
| E05945, 249625ms | 1133 | 37.7667s | Primary-POV kill notification; final target death visible. |

These frames were selected shortly after each encoded outcome. They corroborate sequence and content, not an independently calibrated sub-frame timestamp. Exact MOD cause comes from the obituary, not from guessing the image. The scene is dark under the current review look; appearance is not yet a creative sign-off. Pak/asset hashes have not been frozen, so full pixel reproducibility remains incomplete.

Open `explorer.html` locally to play the round and click its event rows. The local clip is `output/demo_v2/demo509-reference/demo509-round06-reference.mp4`; the private contact sheets and machine capture record are beside it.
