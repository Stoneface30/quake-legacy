# Bounded visual verification set

Seven moment types, one capture each, chosen because each one can be falsified by looking at it. Total footage is under two minutes.

Nothing here has been captured yet. Every row is `NOT_YET_VISUALLY_CHECKED`, and no decoded claim in the dossier depends on it — this set exists to catch a decoded claim that is wrong.

| # | Moment | Server time | Window | Claim | Falsified if |
|---:|---|---|---|---|---|
| 1 | `TERMINAL_KILL_AFTER_END_COMMAND` | 1:52.250 | 1:47.250..1:57.250 | round 1's end command is logged at 1:52.225, and the kill that decided it lands 25ms later. A cut at the command removes the frag. | the kill notification does not appear after the round-over state on screen |
| 2 | `WORLD_KILL` | 7:43.175 | 7:38.175..7:48.175 | entity 1022 is ENTITYNUM_WORLD, so this death has no player killer and must not be credited to anyone. | the obituary names a player as the killer |
| 3 | `LOW_HP_FRAG` | 6:51.325 | 6:46.325..6:56.325 | the recorder's own playerstate reads health 40 armour 0 at this kill. | the HUD health at the kill differs from 40 |
| 4 | `MULTI_KILL_ROUND` | 2:31.900 | 2:24.600..3:01.575 | round 3 contains 3 kills by the recorder at 2:31.900, 2:44.375, 3:01.600. The round is one review item with several effect anchors, not several unrelated clips. | fewer than 3 kill notifications for the recorder appear inside the round |
| 5 | `POV_SUBJECT_CHANGE` | 1:48.725 | 1:46.725..1:54.275 | the playerstate subject moves from the recorder to P12 for 3.5s. Any health or position read here belongs to P12. | the view does not change to a spectated player |
| 6 | `UNOBSERVED_SPAN_AND_REENTRY` | 5:59.825 | 5:11.475..6:02.825 | P10 leaves the recorder's snapshot for 46.4s and re-enters at 5:59.825. Nothing interpolates across that span; it is UNOBSERVED. | P10 is visible on screen during the gap |
| 7 | `DAMAGE_TAKEN_EXACT` | 2:44.250 | 2:41.250..2:46.250 | ps.damageCount is 80 and the recorder loses 27 health and 53 armour across the same pair. This is damage TAKEN, never damage dealt. | the HUD does not drop by 80 combined |

Capture rules: the render permit decides whether anything runs at all, a running game always wins, and captured media stays out of the repository because the in-game notifications carry player names. Record engine, cgame, pak and cfg hashes with each frame, or the frame proves nothing reproducible.
