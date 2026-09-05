# Action worth watching that ends in no kill

*Asked for 2026-09-05, before the next mining pass: "when I do a high amount
of damage in low time or while doing a big mouse flick or clutch/pixel shot
but even when I don't have the kill — this could help see rounds where we
just see end frag but the action was video worthy."*

**Status: DESIGNED AND PROBED, NOT BUILT.** Nothing has been mined. This
document exists so the next extraction pass can include it rather than
needing a third one.

## The gap

Every reviewable moment in the corpus today is anchored to an **obituary**.
That was the right foundation — an obituary is a server fact, true for every
player whether or not anyone filmed it — but it means the archive can only
show moments where somebody *died*.

A round where the user did 250 damage across three enemies, missed the last
shot, and a teammate cleaned up is currently represented by the teammate's
kill. The fight itself is invisible.

## What is already extracted, and what is not

`semantic_events_v1` holds **34,316,804** rows. The relevant streams all
exist today:

| stream | rows | what it gives |
|---|---|---|
| `fire_weapon` source=`playerstate` | 3,074,889 | the recorder's own trigger pulls |
| `pain` with `client_num` | 1,000,344 | who was hurt, and when |
| `missile_hit` | 4,399,492 | rocket / grenade / plasma impacts |
| `missile_miss` | 7,556,558 | the near miss — a pixel shot that failed |
| `railtrail` | 441,526 | rail shots as world events |

So **damage bursts, near misses and rail activity need no new extraction at
all.** Two of the four things asked for do:

| wanted | derivable now? |
|---|---|
| high damage in a short time | **yes**, from `pain` + `fire_weapon` |
| pixel shot / near miss | **yes**, from `missile_miss` + `railtrail` |
| big mouse flick, away from a kill | **no** — `recognition_view_timeseries` holds 13,463 rows and every one is anchored to a frag. The view extractor exists (`view_extracted`, 3,415 demos) and would need to run over whole rounds rather than frag windows. |
| clutch survival with no kill | **partly** — health series exist for 3,523 demos, and the low-HP part is derivable; "clutch" also needs alive-counts, which the round layer already derives |

## Measured on one demo

`creative_suite/engine/probes/no_kill_action_probe.py`, read-only, one demo
(overkill, 99 kills):

```
recorder shots: 773   pain events: 491
damage bursts found: 34
  of which end in a kill : 21
  of which end in NOTHING: 13   <- currently invisible
```

The strongest of the invisible ones:

```
t=123825   13 pain on 5 enemies, 15 of my shots, no kill
t=376400    8 pain on 3 enemies, 16 of my shots, no kill
t=476550   10 pain on 5 enemies,  3 of my shots, no kill
```

Extrapolating from one demo is not a corpus estimate, but the order of
magnitude is roughly **ten thousand or more** no-kill moments across the
archive. That is a lot, and it is why this needs thresholds and a confidence
before it becomes a queue.

## The honest limits, stated up front

**A pain event proves damage, not authorship.** In a crossfire the victim's
pain may be a teammate's rocket. The probe already separates these: a burst
with 15 of the user's own shots inside the window is strong, one with 3 is
weak. Any built version must carry that confidence and must never present a
weak burst as "you did this".

**Pain is throttled** — median gap 925 ms, never under 100 ms. So a pain
count is a **lower bound** on hits, not a hit count, exactly as it is for
accuracy. `MIN_PAIN` is therefore a threshold on *observed* pain, and the
field must be named so nobody later reads it as damage in points.

**No damage numbers exist.** Quake Live demos do not carry a damage figure
for other players. "High damage" can only ever mean "many observed pain
events on several enemies while you were shooting".

## Proposed shape, if approved

A new item family beside the kill families — **not** a change to any existing
one, so nothing already reviewed is invalidated:

```
ACTION_BURST      occurrence-free, addressed by (content_hash, t_ms)
  observed_pain      int    lower bound, labelled as such
  distinct_victims   int
  my_shots           int    the recorder's own, in-window
  confidence         HIGH | AMBIGUOUS      by shot share
  ends_in_kill       bool   false is the interesting case
  round, map, weapon
```

It would enter the reviewer as its own corpus (opt-in, like `TELEFRAG_DOC`),
never mixed into the frag queue, and it would carry the same T1–T5 + tags +
GOLDEN + KEEP_CONTEXT vocabulary so judgements stay comparable.

**Cost.** The damage-burst half is a single pass over
`semantic_events_v1` and needs no demo re-parse. The flick half needs the
view extractor re-run over full rounds on ~3,400 demos, which is the
expensive part and can be decided separately.

## Recommendation

Build the damage-burst half in the next pass (cheap, already-extracted data,
directly answers "the action was video worthy"). Defer the whole-round view
extraction until there is evidence a flick away from a kill is worth the
re-run — the reviewer can tag `AIM` on the bursts it finds, and that is
evidence.
