# Integration verifications (2026-09-01)

Two directive items answered by measurement rather than by building
something. Both were checks on numbers/behaviour already claimed
elsewhere, re-derived independently here.

## §15 — A/B/C audition loudness fairness: NO normalization needed

The directive asks for comparison-only gain normalization *if* same-scene
candidates differ materially in loudness, targeting ≈±0.3–0.5 LU within
each A/B/C group, so that "louder" does not read as "better".

Measured from `output/demo_v2/music_auditions/audio_audit_v2.json`
(ffmpeg-8.1 ebur128, `peak=true`, measured **after** final AAC encode):

| scene | A/B/C integrated LUFS | spread | true peak dBTP | duration |
|---|---|---|---|---|
| 5979 | −13.1 / −13.1 / −13.1 | **0.00 LU** | −2.8 / −2.9 / −2.9 | 8.638 s |
| 22076 | −12.2 / −12.2 / −12.2 | **0.00 LU** | −2.8 / −2.9 / −2.9 | 22.105 s |
| 22154 | −10.5 / −10.5 / −10.5 | **0.00 LU** | −2.7 / −2.8 / −2.9 | 7.012 s |

Worst within-group spread across all three scenes: **0.00 LU**, far
inside the ±0.3–0.5 LU target. The existing mix profile already
normalizes each group, so an audition-normalization layer would be dead
code. **Not built.**

Two things worth keeping visible:
- Loudness differs *between* scenes (−10.5 to −13.1 LUFS). That is fine
  and expected — the fairness requirement is *within* an A/B/C group,
  which is what a listener compares back-to-back.
- True peak sits at −2.7…−2.9 dBTP, comfortably inside the final-render
  contract of ≤ −1.0 dBTP, with the measurement taken post-AAC (the
  encode stage that exposed overshoot on the first delivery attempt).

## §23 — DODGE_HERO count reconciliation: 634 confirmed, and NOT additive

The directive warns not to assume filter memberships add up. Re-derived
directly from `recognized_frags.classes`:

| label | rows |
|---|---|
| `DODGE_HERO` | 134 |
| `RAIL_DODGE_HERO` | 192 |
| `PROJECTILE_DODGE_HERO` | 444 |
| `DODGE_TO_KILL` (broad) | 13,887 |

Reconciliation:

```
naive sum 134 + 192 + 444   = 770      <- WRONG, 21% overstatement
TRUE unique union           = 634
  overlap HERO & RAIL       =  40
  overlap HERO & PROJECTILE =  95
  overlap RAIL & PROJECTILE =   2
  in all three              =   1
DODGE_HERO ⊆ (RAIL | PROJECTILE) = True
union as % of broad         = 4.6%
```

The previously published **634 unique rows / 4.6% of the broad
detector** is correct. The subset contract holds: every `DODGE_HERO` row
is also a rail- or projectile-hero row, so `DODGE_HERO` is the
cross-weapon top tier rather than an independent fourth bucket — which
is why the memberships overlap and the naive sum overstates by 136 rows.

Anyone quoting these numbers should quote **634**, never 770.
