# Review workbook — everything that needs your eyes

Fill this in while watching clips. Your words in the verdict columns become the scoring rules, so a blunt "boring, drop it" is as useful as a paragraph.

`WORTH`: `GOLDEN` / `HIGH` / `MED` / `LOW` / `DROP`, or `DISCOUNT` for anything that should push a frag DOWN the queue.

**Answers already written in this file are preserved when it is regenerated.** Counts and examples are re-read from the corpus every time, so a number here is never a number that used to be true.

Clips: `output/demo_v2/calibration_review.html`

---

## 0. What this run covers

| | |
|---|---:|
| demos scanned at the current taxonomy | 2,810 |
| frags in the corpus | 36,607 |
| distinct traits emitted | 80 |
| blooper candidates | 25,356 |

Clip windows are **5s before the kill and 5s after**, centred on the kill itself. A frag in the first seconds of a round starts 4s before the round goes live instead, so you see the countdown, the GO, then the frag. If a clip does not look like that, say so — it is a bug, not a preference.

## 1. NEW round & team traits — these have never been reviewed

Clan Arena has no respawn inside a round, so the round's own deaths give an exact count of who is still alive. These are counted facts, not guesses. What I cannot judge is how much any of them should be WORTH.

| trait | n | example | means | WORTH | verdict |
|---|---:|---|---|---|---|
| `ROUND_WINNING_FRAG` | 6,726 | FRAG:97476 | killed the last living opponent — the round ended on it | killed the last living opponent — the round ended on it |  |
| `CLUTCH_ROUND_WIN` | 2,152 | FRAG:97476 | won the round while the last one alive on his team | won the round while the last one alive on his team |  |
| `CLUTCH_1VN` | 3,311 | FRAG:114601 | last alive, 2+ opponents still up | last alive, 2+ opponents still up |  |
| `LAST_MAN_STANDING` | 5,463 | FRAG:114601 | last alive on his team, 1+ opponents up | last alive on his team, 1+ opponents up |  |
| `OUTNUMBERED_FRAG` | 4,654 | FRAG:117266 | his team had fewer players alive at the kill | his team had fewer players alive at the kill |  |
| `ROUND_OPENING_FRAG` | 2,683 | FRAG:120519 | within 5s of the round going live; clip opens on the countdown | within 5s of the round going live; clip opens on the countdown |  |
| `FIRST_BLOOD` | 5,848 | FRAG:117266 | first death of the round | first death of the round |  |
| `TRADE_KILL` | 2,097 | FRAG:112317 | the victim had just killed a teammate | the victim had just killed a teammate |  |
| `REVENGE_FRAG` | 4,651 | FRAG:98957 | killed whoever killed him last round | killed whoever killed him last round |  |
| `SNAP_ON_ARRIVAL` | 542 | FRAG:106923 | the opponent was only visible for a moment before dying | the opponent was only visible for a moment before dying |  |

Two questions only you can settle:

1. Should `ROUND_WINNING_FRAG` raise a clip on its own, or only when the frag itself is good? Right now it adds score. Tell me if that is wrong.
2. `ROUND_OPENING_FRAG` deliberately adds **no** score — an opening frag is shaped differently, not better. Confirm, or tell me it should count.

## 2. Traits already emitted (80)

`n` is how many frags carry it. A small `n` on something you care about means the detector is too strict, not that the moment is rare.

| trait | n | example | WORTH | verdict / what makes it good |
|---|---:|---|---|---|
| `DODGE_AND_KILL` | 13,180 | FRAG:36884 |  |  |
| `RAIL_FRAG` | 11,099 | FRAG:35570 |  |  |
| `FAST_WEAPON_SWITCH` | 8,691 | FRAG:37632 |  |  |
| `VERTICAL_ACTION` | 5,991 | FRAG:37632 |  |  |
| `HIGH_SPEED_FRAG` | 3,502 | FRAG:34191 |  |  |
| `DIRECT_ROCKET` | 3,258 | FRAG:33959 |  |  |
| `ESCAPE_TURNAROUND` | 2,625 | FRAG:117314 |  |  |
| `SPEED_TARGET_FRAG` | 2,361 | FRAG:34191 |  |  |
| `FLICK_SHOT` | 2,312 | FRAG:33959 |  |  |
| `MULTIKILL_DOUBLE` | 2,247 | FRAG:33790 |  |  |
| `LOW_HEALTH_WIN` | 1,846 | FRAG:114601 |  |  |
| `STRAFE_CHAIN_FRAG` | 1,581 | FRAG:114601 |  |  |
| `LAST_HP_FRAG` | 1,253 | FRAG:117314 |  |  |
| `LG_HIGH_ACCURACY` | 1,165 | FRAG:34249 |  |  |
| `MULTI_WEAPON_CHAIN` | 1,073 | FRAG:117314 |  |  |
| `LG_TRACKING` | 1,064 | FRAG:34249 |  |  |
| `DODGE_TO_KILL` | 963 | FRAG:33959 |  |  |
| `RAIL_CONSECUTIVE` | 856 | FRAG:35570 |  |  |
| `NEAR_MISS_ROCKET` | 743 | FRAG:33959 |  |  |
| `RAIL_AIR` | 702 | FRAG:34222 |  |  |
| `HIGH_SPEED_AIR_FRAG` | 629 | FRAG:114601 |  |  |
| `NEAR_MISS_RAIL` | 571 | FRAG:35570 |  |  |
| `WEAPON_COMBO` | 507 | FRAG:34106 |  |  |
| `DIRECT_CONFIRMED_GEO` | 387 | FRAG:33959 |  |  |
| `WEAPON_SWITCH_FINISH` | 362 | FRAG:117314 |  |  |
| `COMBO_KILL` | 329 | FRAG:117314 |  |  |
| `ROCKET_JUMP_ENTRY` | 296 | FRAG:116117 |  |  |
| `ROCKET_JUMP_FRAG` | 270 | FRAG:37632 |  |  |
| `AIR_ROCKET` | 246 | FRAG:33959 |  |  |
| `RAPID_MULTIKILL` | 201 | FRAG:35113 |  |  |
| `HEAVY_DAMAGE_SURVIVED` | 191 | FRAG:34106 |  |  |
| `AIR_ROCKET_GEO` | 146 | FRAG:34191 |  |  |
| `MULTIKILL_TRIPLE` | 144 | FRAG:34908 |  |  |
| `POPUP_COMBO` | 128 | FRAG:95194 |  |  |
| `DODGE_STRAFE` | 124 | FRAG:34191 |  |  |
| `TARGET_TRANSFER` | 109 | FRAG:117314 |  |  |
| `LOW_HP_FRAG` | 94 | FRAG:34106 |  |  |
| `RAIL_FLICK` | 69 | FRAG:34512 |  |  |
| `CLEAN_FLICK` | 64 | FRAG:33959 |  |  |
| `CLUTCH_1V2` | 61 | FRAG:34106 |  |  |
| `VERY_FAST_FRAG` | 53 | FRAG:33959 |  |  |
| `PREDICTION_TEMPORAL` | 41 | FRAG:33475 |  |  |
| `REACTION_SHOT_CANDIDATE` | 41 | FRAG:100477 |  |  |
| `CRITICAL_HP_FRAG` | 39 | FRAG:34474 |  |  |
| `EXTREME_SPEED` | 35 | FRAG:32972 |  |  |
| `CLUTCH_1V3` | 33 | FRAG:35570 |  |  |
| `NEAR_MISS_GRENADE` | 32 | FRAG:32617 |  |  |
| `EXTREME_FLICK` | 29 | FRAG:33959 |  |  |
| `REACTION_SHOT` | 27 | FRAG:32972 |  |  |
| `AIR_GRENADE` | 26 | FRAG:33475 |  |  |
| `PROJECTILE_DODGE_HERO` | 25 | FRAG:34191 |  |  |
| `LG_HIGH_PRESSURE` | 25 | FRAG:34249 |  |  |
| `HIGH_SPEED_MULTIKILL` | 25 | FRAG:114729 |  |  |
| `RAIL_DODGE_HERO` | 23 | FRAG:35570 |  |  |
| `LAST_HP_CANDIDATE` | 23 | FRAG:32467 |  |  |
| `NEAR_DIRECT` | 23 | FRAG:33390 |  |  |
| `LG_TRANSFER` | 22 | FRAG:108200 |  |  |
| `LG_DODGE_MASTER` | 21 | FRAG:34249 |  |  |
| `CORNER_PREFIRE_CONFIRMED` | 19 | FRAG:33790 |  |  |
| `PREDICTION_CANDIDATE` | 18 | FRAG:34336 |  |  |
| `DAMAGE_BURST` | 16 | FRAG:34249 |  |  |
| `AGGRESSIVE_TRACKING_SWEEP` | 14 | FRAG:32617 |  |  |
| `HIGH_SPEED_AIM_TRANSITION` | 11 | FRAG:33959 |  |  |
| `PIXEL_SHOT_GEO` | 11 | FRAG:33164 |  |  |
| `DODGE_HERO` | 9 | FRAG:35570 |  |  |
| `TINY_GAP_SHOT` | 7 | FRAG:33164 |  |  |
| `MULTIKILL_QUAD` | 7 | FRAG:35406 |  |  |
| `CLUTCH_1V4_PLUS` | 4 | FRAG:35123 |  |  |
| `LARGE_AIM_TRANSITION` | 2 | FRAG:34394 |  |  |
| `MULTIKILL_PENTA` | 1 | FRAG:127672 |  |  |

## 3. Bloopers — the ones that are funny, not good

25,356 candidates. These are detected as COMEDY, never as skill, and none of them raises a frag in the highlight queue. Tell me which are actually funny on screen and which are just noise.

| signal | n | means | funny? | verdict |
|---|---:|---|---|---|
| `HERO_THEN_DEATH` | 11,001 | did something good, then died immediately | did something good, then died immediately |  |
| `KILL_THEN_DEATH_FAST` | 6,139 | killed someone and died within moments | killed someone and died within moments |  |
| `CHAT_REACTION_NEARBY` | 2,218 | someone typed in chat right after — the players reacted | someone typed in chat right after — the players reacted |  |
| `TELEFRAG` | 1,443 | materialised inside someone | materialised inside someone |  |
| `ENVIRONMENTAL_DEATH` | 1,424 | the map killed them, not a player | the map killed them, not a player |  |
| `SELF_DAMAGE_DEATH` | 1,307 | killed themselves with their own weapon | killed themselves with their own weapon |  |
| `INSTANT_TRADE` | 920 | both died within a breath of each other | both died within a breath of each other |  |
| `GAUNTLET_KILL` | 904 | killed with the melee weapon | killed with the melee weapon |  |

`CHAT_REACTION_NEARBY` is the interesting one: the players themselves reacted. If those hold up, chat proximity is the cheapest comedy detector we have. Chat text is never exported — only that it happened.

## 4. Frag shapes (16)

| shape | n | means | WORTH | verdict |
|---|---:|---|---|---|
| `REFRAG` | 14,723 | you killed whoever just killed your teammate |  |  |
| `OVERKILL_BLOW` | 13,857 | the last hit did far more damage than needed |  |  |
| `DIED_WITH_SHOT_IN_FLIGHT` | 7,836 | they died with their own rocket still flying |  |  |
| `ECONOMY_KILL` | 6,924 | killed in the fewest hits that weapon allows |  |  |
| `POINT_BLANK` | 5,709 | contact range |  |  |
| `SHOT_DENIED` | 3,733 | they died and their in-flight rocket was aimed AT YOU |  |  |
| `UPSHOT_KILL` | 1,084 | you killed something far above you |  |  |
| `PLUNGE_KILL` | 972 | you killed something far below you |  |  |
| `FROM_THE_GRAVE` | 621 | your rocket killed after you were already dead |  |  |
| `RING_OUT` | 454 | knockback put them in a pit / lava / off the map |  |  |
| `MID_TELEPORT_DENIAL` | 347 | dead within half a second of teleporting in |  |  |
| `GAUNTLET_INTERRUPT` | 316 | melee on someone who was actively shooting |  |  |
| `SPLIT_TICK_DOUBLE` | 151 | two separate shots, two deaths, near-simultaneous |  |  |
| `COLLATERAL_DAMAGE` | 55 | one splash, two deaths |  |  |
| `WEAPON_TRIPTYCH` | 30 | three kills, three weapons, one burst |  |  |
| `SHOTGUN_SNIPE` | 22 | shotgun kill at a range it should not work at |  |  |

## 5. Thresholds I guessed — only watching settles these

Each is a number I chose without evidence. A wrong pick quietly poisons the whole trait.

| what | the question | example | your answer |
|---|---|---|---|
| ROUND_OPENING_FRAG at 5s | A kill 5s into a round gets the countdown; 5.1s does not. Watch one either side — is 5s the right line? | FRAG:120519, FRAG:97810, FRAG:109875 | A kill 5s into a round gets the countdown; 5.1s does not. Watch one either side — is 5s the right line? |
| countdown lead of 4s | Clips open 4s before the round goes live. Too long (dead air), too short (no build), or right? | FRAG:120519, FRAG:97810, FRAG:109875 | Clips open 4s before the round goes live. Too long (dead air), too short (no build), or right? |
| CLUTCH needs 2+ opponents | 1v1 as the last alive is LAST_MAN_STANDING but not a CLUTCH. Should a 1v1 round-decider count as a clutch? | FRAG:97476, FRAG:116117, FRAG:98107 | 1v1 as the last alive is LAST_MAN_STANDING but not a CLUTCH. Should a 1v1 round-decider count as a clutch? |
| TRADE_KILL within 3s | The victim killed a teammate within 3s. Does 3s still read as avenging them, or is it too long to feel connected? | FRAG:112317, FRAG:109526, FRAG:111465 | The victim killed a teammate within 3s. Does 3s still read as avenging them, or is it too long to feel connected? |
| SNAP_ON_ARRIVAL at 1s visible | The opponent was observable for under a second. Does that look like a snap reaction, or just someone walking into the crosshair? | FRAG:32972, FRAG:34107, FRAG:35677 | The opponent was observable for under a second. Does that look like a snap reaction, or just someone walking into the crosshair? |
| 5s/5s clip window | Is 5s before enough to read the setup, and 5s after enough to see the outcome? This one governs every clip you will watch. | — | Is 5s before enough to read the setup, and 5s after enough to see the outcome? This one governs every clip you will watch. |

## 6. Bugs and broken clips — tell me what you see

If a clip is wrong, it is more valuable to me than a clip that is good. Put anything here, however vague.

| what to watch for | why it matters | seen it? | notes |
|---|---|---|---|
| The clip ends before the frag happens | The old windows did this. It should be fixed; if you still see it, the round boundary is wrong somewhere I have not found. | The old windows did this. It should be fixed; if you still see it, the round boundary is wrong somewhere I have not found. |  |
| Several other people's frags before the one under review | The kill should sit in the middle of the clip. Earlier kills in shot means the window moved. | The kill should sit in the middle of the clip. Earlier kills in shot means the window moved. |  |
| Two different maps in one clip | Seen once. It means a seek landed in the wrong demo — a serious identity bug, and I want the clip id. | Seen once. It means a seek landed in the wrong demo — a serious identity bug, and I want the clip id. |  |
| The clip plays too fast or too slow | The capture writes 30fps and the header can claim 60. If motion looks wrong, name the clip. | The capture writes 30fps and the header can claim 60. If motion looks wrong, name the clip. |  |
| Wrong player followed / camera on someone else | The POV subject changes when the recorder dies. If the clip follows the wrong person at the kill, the subject tracking is off. | The POV subject changes when the recorder dies. If the clip follows the wrong person at the kill, the subject tracking is off. |  |
| Player names visible on screen | These clips are internal, but names must never reach a public export. If you see one in something meant to be public, stop me. | These clips are internal, but names must never reach a public export. If you see one in something meant to be public, stop me. |  |
| Health or armour numbers that cannot be right | Health is signed now, but a value over 200 in Clan Arena or a negative one on the HUD is a decoding bug. | Health is signed now, but a value over 200 in Clan Arena or a negative one on the HUD is a decoding bug. |  |
| A kill credited to nobody, or to the wrong killer | Environmental deaths are credited to the world on purpose. A PLAYER kill with the wrong name on it is not. | Environmental deaths are credited to the world on purpose. A PLAYER kill with the wrong name on it is not. |  |
| Countdown clips that start too early or in the wrong place | New this run. Nobody has ever looked at one. | New this run. Nobody has ever looked at one. |  |
| Black frames, freezes, missing HUD, wrong colours | Capture faults. They tell me the profile is wrong, not the frag. | Capture faults. They tell me the profile is wrong, not the frag. |  |

## 7. Open questions on my side — no answer needed, just visibility

| item | state |
|---|---|
| Damage DEALT by any player | Not transmitted by the protocol in any form. It will stay null forever; no amount of scanning changes it. |
| Non-POV player motion (air-to-air, juggles, chase-downs) | Opponents are inside the recorder's view about half the time, with gaps up to 46s. These traits cannot be measured honestly yet. |
| Round winners | The server almost never sends the winner. It is derived from the score change across the boundary, which is inference, not record. |
| Proxy cache key vs capture resolution | A test from the parallel engine session says the cache key does not track capture resolution. Their fix is in flight; noting it so it does not get lost. |
| Visual verification of the audited fixture | Seven specific moments are chosen and NOT yet captured. Nothing in the corpus depends on them; they exist to catch a wrong claim. |

---

*Regenerate with the workbook builder. Your answers survive; the numbers are re-read.*
