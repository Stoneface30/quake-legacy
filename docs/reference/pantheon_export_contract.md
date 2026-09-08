# QUAKE_LEGACY → THE_PANTHEON export contract

*Written 2026-09-03. This is the whole interface. If something is not in this
document, THE_PANTHEON does not depend on it.*

## The division

QUAKE_LEGACY knows the game — the `.dm_73` format, the netcode, WolfcamQL,
BSP geometry, the camera system, the entire cinematic vocabulary.
THE_PANTHEON needs none of it. It needs a clip and enough metadata to run a
blind vote.

So the seam is deliberately the narrowest thing that could work: **a
ten-second MP4 and one JSON line**. Nothing else crosses, in either
direction.

What this means in practice:

- No public website code lives in `G:\QUAKE_LEGACY`.
- No `.dm_73`, WolfcamQL, BSP, PANTHEON camera or effect dependency is
  required to consume an export.
- No THE_PANTHEON database is written from QUAKE_LEGACY. Export is a
  directory on disk; import is THE_PANTHEON's business.
- A community score does not flow back into the director system. See
  *Three scores* below.

## Two windows, on purpose

| | window | why |
|---|---|---|
| internal review clip | **±3 s (6 s)** | the director is judging a moment they already know; six seconds is enough to place it |
| public voting clip | **±5 s (10 s)** | a stranger needs run-up to understand a play before scoring it |

These are not a setting waiting to be unified. A test
(`test_the_public_window_is_ten_seconds_and_review_stays_six`) pins both so
neither drifts into the other.

When a demo does not reach five seconds before the event, the clip is
shorter and `event_offset_ms` reports where the event actually landed.
It is never padded and never claims a centred 5000.

## Where it lands

```
G:\QUAKE_LEGACY\exchange\pantheon\
    clips.jsonl          one JSON object per line, one per clip
    clips\
        ql_<20 hex>.mp4
```

Gitignored. A copy of this folder is a complete, self-describing handoff —
the manifest sits beside the media and refers to it by relative path.

## The manifest row

```json
{
  "export_version": "pantheon-clip-v1",
  "exported_at": "2026-09-03T...+00:00",
  "external_source_id": "ql_9b3176f7b54eb07394a7",
  "game": "quake_live",
  "event_type": "FRAG",
  "event_time_ms": 264275,
  "event_offset_ms": 5000,
  "duration_ms": 10016,
  "clip_path": "clips/ql_9b3176f7b54eb07394a7.mp4",
  "content_hash": "<sha256 of the mp4>",
  "map": "campgrounds",
  "weapon": "ROCKET",
  "mod": 6,
  "actor_display_name": "Tr4sH",
  "actor_identity_id": null,
  "recorder_display_name": null,
  "is_actor_pov": true,
  "machine_score": 41.0,
  "machine_score_version": "recognition-v4",
  "source_note": null,
  "source_demo_ref": "<demo content hash>",
  "source_provenance": "QUAKE_LEGACY/RECORDED_OBSERVED/DEMO_EV_OBITUARY",
  "public_eligible": false,
  "identity_visibility": "AFTER_VOTE",
  "overlays_added": []
}
```

### `external_source_id`

A digest of `(demo content hash, event time, killer slot, victim slot)`,
prefixed `ql_`. Stable across re-exports, and opaque: it leaks nothing.

The reason it is a digest rather than a filename is that **Quake Live demo
filenames embed player aliases**. `source_demo_ref` is the demo's content
hash — enough for this repository to find the demo again, useless to anyone
who does not already hold the corpus. No filesystem path appears anywhere in
a manifest row.

### `is_actor_pov` — the field that matters most

`false` means this footage is **somebody else's camera pointed at the
actor**. A frag by NaikoMarie recorded in another player's demo is
NaikoMarie's frag *observed*; it is not NaikoMarie's first-person view.

Anything that presents an observed frag as the actor's own POV is wrong —
in the review UI, in an export, in public metadata, and in the film.

### `machine_score` — null is not zero

The recogniser's score exists **only where the actor is the recorder**.
Every feature behind it — aim, tracking, movement, visibility — is computed
from the recorder's own player state, which is not the actor's.

So a foreign-camera frag carries `machine_score: null`, not `0`. The two are
not comparable, and treating null as a low score would rank observed frags
last for a reason that has nothing to do with how good they are.

### `stats`, `machine_subscores`, `stats_availability`

A voter looking at ten seconds of Quake cannot see how far the rail went, how
fast the victim was moving, or that this was the second kill in a 100 ms
burst. Those separate a good play from a lucky one and are already measured.

Three kinds of number, kept apart:

- **`stats`** are **measurements** — game units, milliseconds, degrees,
  health. They mean the same thing to anyone: `distance_units`,
  `actor_speed_ups`, `victim_speed_ups`, `victim_air_height_units`,
  `flick_degrees`, `flick_duration_ms`, `flick_speed_deg_per_s`,
  `target_visible_ms`, `actor_health`, `actor_armor`,
  `lg_damage_dealt_3s`, `damage_taken_in_fight`, `incoming_hit_ratio`,
  `lowest_health_in_fight`, plus `recognised_as` (the classes the recogniser
  detected, e.g. `DODGE_TO_KILL`).
- **`machine_subscores`** are the recogniser's **opinions on its own scale** —
  `accuracy_score`, `tracking_score`, `movement_score` and the rest. They are
  components of the highlight score, **not percentages**. Reading a 7.5
  "accuracy" as 7.5% or 75% would both be wrong.
- **`stats_availability`** is `FULL_RECORDER_STATE` or `OBSERVED_ONLY`.

**Universal stats hold for every actor**, because an obituary is a server
fact rather than an observation of one player: `round`, `multikill_size`,
`actor_kills_this_round`, `ms_since_actors_prev_kill`,
`ms_to_actors_next_kill`.

Everything else comes from the **recorder's** player state. When the actor
did not hold the camera, there is no such state and those fields are simply
absent — `OBSERVED_ONLY`.

> **A missing field is unmeasurable, not zero.** Treating an absent
> `distance_units` as "close range" would be a conclusion the data does not
> support. `stats_note` says this in words on every observed clip.

Metadata can be rebuilt without re-capturing: `refresh_manifest()` recomputes
every row for clips already on disk. Media is expensive (~40 s of WolfcamQL
per clip); metadata is not, and a new stat should never cost a re-render.

### `public_eligible` — default `false`

Ten years of archive footage was not recorded with the internet in mind. No
export asserts a publication right. An importer that ignores this field
still cannot publish by accident, because the safe answer travels with the
clip.

Only the user changes it.

### `identity_visibility` — `AFTER_VOTE`

Identity travels **as a field, not as pixels**. The actor's name is in the
manifest precisely so it is *not* in the video: pixels cannot be un-shown, a
field can be withheld. THE_PANTHEON controls disclosure — hide identity and
community score before the vote, reveal the nickname after if it chooses.

### `overlays_added` — always `[]`

No name, no rank, no score, no director tag, no PANTHEON overlay of any kind
is drawn onto a public clip. **A voting clip that tells you whose play it is
has already voted for you.**

The native in-game HUD is footage, not editorialising, and the world layer is
left alone — **but the HUD's identity layer is not.** That distinction was
learned the hard way: this document previously said the HUD was simply left
alone, the export captured with the batch profile, and
`cg_drawFragMessageTokens "You fragged %v"` put opponent handles into six of
the first twelve clips. See `public-export-name-disclosure.md`.

## The clip itself — capture intent `PUBLIC_BLIND`

**Ask for the intent, not the cvars.**

```python
from creative_suite.engine import master_profile as mp
profile = mp.profile_for_intent(mp.PUBLIC_INTENT)   # "PUBLIC_BLIND"
```

`PUBLIC_BLIND` resolves to `TR4SH_PUBLIC_EXPORT` (`b9977ff93228`) — the only
capture intent whose output may be shown to someone outside this repository,
and the only one carrying a no-identity guarantee. Every other intent
(`GAMEPLAY_MASTER`, `DIRECTOR_REVIEW`, `MOVEMENT_REVIEW`, `DIRECTOR_SESSION`,
`ARCHIVE_ANALYSIS`) films for the director or for the user's own movie, where
names on screen are correct and wanted. `profile_for_intent` raises on an
unknown intent rather than defaulting — a silent fallback to the batch profile
is precisely the defect it exists to prevent.

Framing is otherwise plain: FPV, no PANTHEON camera, no world effects, no
choreography, no speed ramps. H.264 CRF 20, `+faststart`, AAC audio, 1920x1080.

The purpose is **judge the play**. Anything this export added to the frame
would be judged instead.

### What `PUBLIC_BLIND` guarantees

Every route by which the engine can draw a handle is held at 0 and *checked
before a batch captures a single frame*, by
`public_clip_export.assert_capture_profile_is_nameless()`:

- frag message (`cg_drawFragMessageTime`) and killfeed (`cg_obituaryTime`) —
  both are TIME gates; there is no `cg_drawFragMessage` boolean to switch off
- centre print, crosshair names, player names, friend markers
- follow/spectator chrome, attacker, team overlay
- chat and console notify
- the scoreboard, which shows itself on death and at round end — inside a
  ±5 s window

Two invariants, not one. A **missing** pin fails closed (`None` is not `0`), so
deleting a line refuses the export instead of quietly reopening a route. And
each name token is checked against its gate: blanking a token is not safety,
because wolfcam falls back to a built-in default.

The gate is a **configuration** check by design. A pixel detector was built,
measured and rejected for this job — a blown-out barred window scores higher
than real text. It survives as a diagnostic only
(`creative_suite/engine/burned_name_guard.py`).

Every manifest row records `capture_profile_id` so a clip's provenance is
answerable later. `overlays_added: []` only ever described what the export drew
on top; the engine draws one layer below it.

## Choosing what crosses

```bash
python -m creative_suite.engine.export_cli status
python -m creative_suite.engine.export_cli query --mine --weapon ROCKET --limit 5 --dry-run
python -m creative_suite.engine.export_cli query --clan --limit 10
python -m creative_suite.engine.export_cli ids ql_9b3176f7b54eb07394a7
```

Three ways to choose and **no way to choose everything**. `MAX_BATCH` is 50
and an oversized ask is *refused*, not trimmed — silent truncation is how
you discover weeks later that half an export never happened.

There is no `--all`. The metadata for every attributed kill is queryable
here; that is a different thing from having exported the media for it. The
all-player catalogue is a potential future seed for THE_PANTHEON, but
queryability and export are kept separate on purpose.

## Three scores, kept apart

| score | who | range | lives in |
|---|---|---|---|
| machine score | the recogniser | unbounded float | `recognized_frags` |
| director role | the user | T1–T5 | `human_reviews` (private) |
| community score | the public | 1–20 | THE_PANTHEON only |

The director's review is **private creative truth** and does not leave this
repository. A future `external_community_score` field may exist, but nothing
in the QUAKE_LEGACY scoring or director system depends on one today, and
nothing should be built as though it will.
