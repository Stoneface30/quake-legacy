# GREEN KEEL — proven on pixels, filmed offscreen

**2026-09-06.** One real point-blank kill, filmed twice through
PANTHEON_QUAKE_OFFSCREEN at the same server time with the same camera,
differing only in the VisualProfile. Rebuild with `rebuild_proof.py`.

| | A_authentic.png | B_review.png |
|---|---|---|
| Profile | `AUTHENTIC` | `REVIEW` |
| Enemy silhouette | slim blue humanoid, the character the demo authored | **Keel** — heavy armour, the distinctive head |
| Strong-green pixels | 2 | **49,509** |
| Mean RGB of those | (159, 227, 166) | **(85, 230, 125)** vs the requested (60, 235, 90) |
| Visible window on the operator's desktop | none | none |
| Foreground stolen | no | no |

The moment: demo `e4bd2a36495928d0`, client 2 kills client 1 at serverTime
579,825 on asylum, the two bodies 81 units apart, so the enemy fills a real
share of the frame and a silhouette can actually be judged.

**Why both frames matter.** The count alone would not settle it — a green
light or a HUD element could produce green pixels. The pair shows the SAME
player at the SAME instant as two different characters: the review profile
changes who the enemy looks like, not merely his tint.

**What this does not claim.** Teammate and self were not in frame at this
instant, so "teammates unchanged, self unchanged" rests on the resolved cvar
set (the team family is cleared, and 11.3 registers no self-appearance
family at all) and not on these two pictures.

A first attempt at a different moment produced 27 green pixels and no
readable body: the enemy was in a far archway. Sampling twelve timestamps
across the clip and comparing the same instant in both captures is what
turned a guess into a measurement.
