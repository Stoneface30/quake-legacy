# PANTHEON capabilities — what exists, what it is for, how it is proven

*So sessions stop rediscovering the same things. Every row names a real
module and a real test. Status is what is TRUE today, not what is planned.*

| capability | status | API | backend | proof |
|---|---|---|---|---|
| **ActionTruth** | LIVE | `action_truth.for_item(item_id)` | caches only | `test_dossier.py` |
| **Scene** | LIVE | `scene.build_scene(hash, round)` · `scene_for_item()` | `kill_occurrences_v1` + `movement_moments_v1` | `test_scene.py` |
| **Canonical occurrence** | LIVE | `kill_occurrences_v1` | obituary derivation | `test_occurrences_and_identity.py` |
| **Identity** | LIVE | `identity.confirmed_user_identities()` | `identity_decisions` | `test_occurrences_and_identity.py` |
| **Production usage** | LIVE | `production_usage.set_state()` | `editorial.db` | `test_review_corpus.py` |
| **Annotation (3 scopes)** | LIVE | `creative_annotation` + `/scene_note` | `editorial.db` | `test_creative_annotation.py` |
| **Review capture profile** | LIVE | `master_profile.REVIEW_PROFILE_NAME` | WolfcamQL | `test_review_host.py` |
| **Media provenance** | LIVE | `media_provenance` | — | `test_v1_source_isolation.py` |
| **Public export seam** | LIVE (frozen) | `public_clip_export` | — | `test_public_clip_export.py` |
| **PUBLIC_BLIND_CAPTURE** | LIVE | `master_profile.profile_for_intent("PUBLIC_BLIND")` | WolfcamQL · `TR4SH_PUBLIC_EXPORT` | `test_public_export_no_burned_names.py` |
| **Production contract** | LIVE | `production_contract.classify()` · `action_truth_ref()` · `scene_ref()` | none (re-labels ActionTruth/Scene) | `test_production_contract.py` |
| **Choreography bridge** | LIVE | `production_contract.build_choreography_input_for_scene(scene_id)` · `GET /api/director/choreography_input/{scene_id}` | ActionTruth + Scene + persisted annotations | `test_note_reaches_production.py` |
| **Media job recovery** | LIVE | `review_proxy.reclaim_orphaned_jobs()` at app startup | `editorial.db` | `test_review_job_recovery.py` |
| **Origin supervision** | LIVE | `scripts/review_origin.ps1` + `scripts/install_review_task.ps1` | Startup-folder shim | restart proven by killing the process |
| **Process liveness** | LIVE | `process_liveness.process_alive(pid)` | `OpenProcess` (Windows) | `test_process_liveness.py` |
| **Live mobile flow** | PROVEN | `scripts/check_review_mobile_live.cjs` | real server, 390x844 | run 2026-09-05 |
| **Review tags** | LIVE | `review_tags.set_tag()` · `GET/POST /api/review/tag` | `editorial.db` | `test_review_tags_and_povs.py` |
| **POV cluster** | LIVE | `pov_cluster.povs_for(occurrence_id)` | `kill_events_v1` + `player_teams_v1` | `test_review_tags_and_povs.py` |
| **Queue hygiene** | LIVE | `review_corpus.junk_sql()` · `dismiss()` / `restore()` | `editorial.db` | `test_queue_hygiene.py` |
| **Capture determinism** | LIVE | `master_profile.profile_for_intent()` | WolfcamQL | `test_review_capture_determinism.py` |
| **REVIEW_ENEMY_VISIBILITY** | **PARTIAL — CLOSED** | `master_profile._REVIEW_V2` | WolfcamQL | see below |

---

## ActionTruth is the authority

`PANTHEON owns the semantics. Wolfcam is a capture backend. The UI does not
invent truth.`

One object describes a moment — actor, target, weapon, stack, damage, weapon
metrics, geometry, movement, timing, round, scene, traits, provenance — and
every consumer reads it. The reviewer does today; the effect planner, camera
planner, music planner and scene selection will. `dossier.py` is a thin
adapter over it and computes nothing.

If the reviewer said CRITICAL_HP and the choreographer computed something
else from the same rows, one of them would be lying to the director and there
would be no way to tell which.

## The production contract — what a planner may believe

`ActionTruth IS game truth. Scene IS story context. Human annotation IS
directing truth. ChoreographyPlan consumes all three.`

`production_contract` computes nothing. It classifies every field a
downstream planner can read, so the classification travels with the value:

| class | meaning | example |
|---|---|---|
| `OBSERVED` | the demo said this | `stack.at_frag.health`, `event.weapon` |
| `DERIVED` | arithmetic over observed facts, assumption written down | `round.alive_curve`, `geometry.flick_deg_per_s` |
| `MACHINE_SUGGESTION` | the recogniser's opinion, on its own scale | `event.machine_score`, `traits` |
| `HUMAN` | the director wrote it | every `DirectionNote` |
| `UNAVAILABLE` | not observed, not derived, **not zero** | health on 50.6% of the corpus |

```python
from creative_suite.engine import action_truth as at, production_contract as pc
ref = pc.action_truth_ref(at.for_item("FRAG:13420"))
ref.get("stack.at_frag.health")      # 156
ref.provenance["stack.at_frag.health"]  # OBSERVED
ref.factual("event.machine_score")   # False -- may rank, may not state
```

`classify()` **raises** on a field nobody has classified rather than
defaulting to `OBSERVED`. A new field that silently defaults to observed is
how an opinion gets laundered into a fact.

`is_factual()` is the question a planner asks before a treatment makes a
claim the viewer could check. A machine trait may decide *which* moment to
look at; it may never decide *what happened*.

## Scene as production reads it

`scene_ref(scene, round_note)` returns identity, bounds, canonical
occurrence **references**, movement references, human role and note per
event, and usage state — and no duplicated moment data. A test enumerates
the banned keys: no health, aim, damage or score may appear on a rail event,
because two copies of a moment eventually disagree and nobody can say which
one the film used.

`takes_verdict` separates the two kinds of rail event. A jump pad is
addressable so a note can hang on it and can never enter the review corpus
as a rateable moment.

## The choreography bridge

```python
ci = pc.input_for_item("FRAG:13420")
ci.scene          # SceneRef      -- story context
ci.actions        # ActionTruthRef -- game truth, classified
ci.direction      # DirectionNote -- the director's own words
```

Three fields, kept apart on purpose. Flattening them is how a machine trait
ends up outranking a human note.

**The words survive verbatim.** Given a real scene — F1, F2, JUMP PAD, F3,
F4 — with `"music buildup here"` on the pad, `"xray / enemy POV"` on F3 and
`"big finish on F4."` on the round, each arrives at the planning layer as the
exact string that was typed, attached to the exact event it was typed on.
Whitespace, case, punctuation and typos all survive; `parse_intent` offers a
machine READING alongside and never in place of the text.

Only `HUMAN_USER` and `IMPORTED_LEGACY_HUMAN` reach a planner as direction.
`AI_SUGGESTION`, `TEST` and `SYSTEM` notes are dropped at this boundary.

This module knows nothing about lanes, effects, cameras or music — a test
asserts it, by failing if `LANE_` or `ChoreographyPlan(` ever appears in its
source. It is a boundary, not a planner.

## PUBLIC_BLIND_CAPTURE — ask for the intent, not the cvars

`Private film may show names. Public blind export may not.`

```python
from creative_suite.engine import master_profile as mp
profile = mp.profile_for_intent(mp.PUBLIC_INTENT)   # "PUBLIC_BLIND"
```

`PUBLIC_BLIND` → `TR4SH_PUBLIC_EXPORT` (`b9977ff93228`). It is the **only**
capture intent whose output may be shown to someone outside this repository,
and the only one carrying a no-identity guarantee. The others —
`GAMEPLAY_MASTER`, `DIRECTOR_REVIEW`, `MOVEMENT_REVIEW`, `DIRECTOR_SESSION`,
`ARCHIVE_ANALYSIS` — film for the director or for the user's own movie, where
names on screen are correct and wanted.

### Every capture intent, and who the footage is for

No session should ever again call `capture_demo(profile=None)` and hope it
means the right thing. Ask for the intent; the profile is an implementation
detail and the cvars are the backend's business.

| intent | profile | id | audience | names on screen |
|---|---|---|---|---|
| `PUBLIC_BLIND` | `TR4SH_PUBLIC_EXPORT` | `b9977ff93228` | strangers voting blind | **never** — nine routes pinned and checked before a batch runs |
| `DIRECTOR_REVIEW` | `TR4SH_REVIEW_V2` | `83bf11fc916b` | the director, judging one moment | yes — local private data, and useful |
| `GAMEPLAY_MASTER` | `TR4SH_GAMEPLAY_MASTER_V2` | `091901df0daf` | the film's own footage | yes |
| `MOVEMENT_REVIEW` | `TR4SH_SPEED_REVIEW` | `160f2b7e8111` | judging movement | yes, plus movement HUD |
| `DIRECTOR_SESSION` | `TR4SH_DIRECTOR_SESSION` | `25a8b65f5c49` | interactive direction | yes |
| `ARCHIVE_ANALYSIS` | `TR4SH_ANALYSIS_HEADLESS` | `8e2493617225` | machines, not viewers | irrelevant |

Profile ids are content digests: change a cvar and the id moves, which is
what keeps the proxy cache honest.

**Why the indirection exists.** `public_clip_export` called
`capture_demo()` with no profile argument. `profile=None` does not mean "no
profile"; it means `PROFILE_NAME`, the batch profile, which deliberately draws
`cg_drawFragMessageTokens "You fragged %v"`. Opponent handles reached 6 of the
first 12 handoff clips. `profile_for_intent` **raises** on an unknown intent
rather than defaulting, because the default was the defect.

**What it guarantees**, checked by
`public_clip_export.assert_capture_profile_is_nameless()` before a batch
captures a single frame:

- frag message and killfeed — both gated by TIME cvars
  (`cg_drawFragMessageTime`, `cg_obituaryTime`); there is no
  `cg_drawFragMessage` boolean to switch off
- centre print, crosshair names, player names, friend markers
- follow/spectator chrome, attacker, team overlay
- chat, console notify
- the scoreboard, which shows itself on death and at round end — inside a ±5 s
  window

Two invariants: a **missing** pin fails closed (`None` is not `0`), and each
name token is paired with its gate (blanking a token is not safety — wolfcam
falls back to a built-in default).

**Proven:** frag message suppressed, pixel-verified across 30 samples of the 6
actor-POV clips. Killfeed suppressed **by invariant only** — a window with four
other-player kills is identical under both profiles on a full-frame text scan,
so it was never observed drawing and there is no before/after picture. Do not
cite one.

**Do not** use a pixel detector as the ship gate. `burned_name_guard.py` scores
a blown-out barred window (2903) higher than real text (1991); it is an A/B
diagnostic against a control, nothing more.

Detail: `public-export-name-disclosure.md` · contract:
`pantheon_export_contract.md`

## REVIEW_ENEMY_VISIBILITY — PARTIAL, and the investigation is CLOSED

`Green Keel is useful. It is not worth blocking the project.`

**Status: PARTIAL. Do not open this again without new evidence from a
captured frame.** Enemies are visible and the review view is usable; they are
not green, and the earlier claim that they render as Keel does not survive a
look at the pixels.

### What a measured A/B actually showed (2026-09-05)

Two captures of the same six-second window on `overkill`, identical but for
the profile, frames sampled at 2 fps:

| | pixels reading green | pixels reading tan |
|---|---|---|
| review profile as shipped | 0.00% | 2.23% |
| + explicit `cg_enemy*Skin "bright"` | 0.02% | 1.28% |

No difference. The change was reverted rather than kept, because a profile
edit with no measured effect still moves the profile id and would have
invalidated every cached review proxy for nothing.

**And the model in frame is not Keel.** Enlarging the two players visible
against the sky shows a slim orange humanoid with a teal helmet — the stock
player model, not the bulky Keel silhouette. `cg_enemyModel "keel/bright"`
and `cg_forceModel 1` are in the profile, ARE written to
`wolfcam_tr4sh_review_v2.cfg`, and are not reaching the renderer. The
previous note in this file claimed "enemies render as Keel"; that claim was
made from source and the frame does not support it.

### The named hypothesis is disproven, with numbers

`keel/bright` was suspected of declaring `rgbGen identity` and therefore
ignoring entity colour. It does not. From `pak00.pk3`,
`scripts/models_players.shader:3204`:

```
models/players/keel/bright
{
    { map .../bright.tga }                                  # base
    { map .../bright.tga  blendfunc GL_ONE GL_ZERO
      alphaFunc GE128     rgbGen entity }                   # <- entity colour
    { map .../bright2.tga blendfunc add rgbGen identity }   # weak glow
}
```

Measured on the shipped textures: **64.4%** of `bright.png` texels pass
`alphaFunc GE128` and are therefore tinted by `cg_enemyTorsoColor`, and the
additive glow is faint (mean 6.7/255). Simulating the three stages with
`0x2a8000` predicts **75.7%** of the tinted region reading plainly green.

**So `remapshader` is not the route.** There is no wrong shader to replace —
the shader already honours entity colour, and swapping it would change
nothing while risking every other surface that shares a material.

### The default skin, for the record

`models/players/keel/keel` (the DEFAULT skin) is one stage, `rgbGen
lightingdiffuse`, **no entity stage at all** — entity colour is silently
ignored — over a texture whose mean is tan (68/48/32). If the enemy ever does
render as Keel and still ignores colour, that is the skin in use.

### Dead ends — do not retry any of these

| hypothesis | verdict | evidence |
|---|---|---|
| team metadata missing | **false** | `player_teams_v1` carries RED/BLUE for the test demo |
| cfg timing / recompute | **false** | `wolfcam_view.c:1002` recomputes on modification count |
| `createcolorskins` | **false** | `tr_image.c:1800` generates red and blue from a fixed table |
| `keel/bright` uses `rgbGen identity` | **false** | it uses `rgbGen entity`; 64.4% coverage, measured |
| the skin half of `cg_enemyModel` fails to resolve | **no effect** | naming it explicitly changed 0.00% → 0.02% |
| `cg_useCustomRedBlueModels` gates the colour out | **false** | it defaults to `0`; the gate at `cg_players.c:6096` passes |

### What would settle it, if anyone ever needs to

Not more source reading — three of the six dead ends above came from reading
source and were wrong. The next step is a frame with an enemy in it and
`/cg_enemyModel` echoed from the live console, to see whether the cvar the
engine holds at draw time is the one the cfg set.

**Decision: enemies stay tan. Human curation is not blocked on a renderer
cosmetic, and this sprint was the last one spent on it.**

## The media job state machine

`A status read never moves a job.`

| state | means | set by |
|---|---|---|
| `MISSING` | no row | nobody |
| `QUEUED` | waiting for the single capture worker | first request · explicit retry · **startup reclaim** |
| `GENERATING` | wolfcam is filming it now | the worker |
| `READY` | mp4 exists on disk | the worker |
| `FAILED` | it will not happen without help | the worker on error · reclaim when the demo is gone |

**Two ways this produced an endless spinner, both fixed.**

*Polling requeued failures.* `request_proxy` treated FAILED as "try again",
so every two-second poll restarted the job: FAILED -> QUEUED -> FAILED,
forever, and the page never saw a settled failure so it never offered Retry.
Only an explicit `retry=True` revives a failure now.

*Jobs outliving their process.* The queue is in memory; the state is in
SQLite. After any restart, rows marked QUEUED describe work no worker knows
about — and `request_proxy` returns early on QUEUED **before** it would start
a worker, so no later request could ever recover them. The row showed
RENDERING, not FAILED, so there was not even a Retry to press. Measured on
the live queue: **16 orphaned jobs**, the oldest stuck for over two hours.

`reclaim_orphaned_jobs()` runs once per process, from the app's startup hook
via `_ensure_worker` — which both starts the drain thread and adopts the
orphans. Reclaiming without starting the worker was its own bug for one
iteration: jobs went onto a queue nothing was reading.

Only the CURRENT capture profile is reclaimed. A row from an older profile
can never be looked up (the profile id is in the cache key), and re-capturing
it would spend forty seconds of wolfcam on a clip nobody is waiting for.

## Origin supervision

`A 302 from review.conchita.uk does not mean the origin is up.`

Cloudflare Access answers with a redirect to its login page whether or not
anything is listening behind it, so the site looks healthy until you finish
signing in. The tunnel points at **127.0.0.1:8766** — not 8765, which is a
different service on this machine and returns its own JSON 404.

`scripts/review_origin.ps1` is a supervised loop: it starts uvicorn bound to
loopback, waits, and restarts it with exponential backoff, logging to
`output/review_origin.log`. `scripts/install_review_task.ps1` puts a shim in
the per-user Startup folder so it survives logout and needs no admin rights
(`Register-ScheduledTask` is refused unelevated here). Proven by killing the
uvicorn process: back up in about four seconds.

Binding to loopback is deliberate — the Access guard keys on the Host header,
so an origin listening on the LAN would be reachable without signing in.

## Windows process liveness

`os.kill(pid, 0)` is a POSIX probe. On Windows it calls `TerminateProcess`,
so the "am I alone?" check for a capture lock could kill the very process it
was asking about. `process_liveness.process_alive(pid)` opens a SYNCHRONIZE
handle and queries it instead, and fails CLOSED: access denied counts as
alive, because a lock takeover based on a failed query is worse than waiting.
Two remaining `os.kill` calls in the tree are deliberate signals in
`comfy-pilot`, not liveness probes.

## The review taxonomy — frozen 2026-09-05

`Quality is the verdict. Purpose is the tags. They never collapse.`

One verdict, always exactly one:

    T1 FEATURE / FX     T2 TRANSITION     T3 RHYTHM / MONTAGE
    T4 KEEP / NORMAL    T5 PASS / FILLER

Any number of tags, including none:

| group | tags | keys |
|---|---|---|
| weapon | RAIL · LG · ROCKET · GRENADE | Q L O E |
| craft | AIM · PREDICTION · MOVEMENT · TEAMPLAY | A P M T |
| drama | CLUTCH · MULTIKILL · FUNNY · VOICE | C K F V |
| history | LEGACY · ICONIC_PLAYER | Y I |
| camera | CLEAN_POV · ALT_POV | Z W |
| structural | KEEP_CONTEXT · GOLDEN | S G |

**Why they must stay apart.** `T4` alone tells an editor almost nothing six
months later. `T4 + PREDICTION + ROCKET + CLEAN_POV` tells them where the
clip belongs. A mechanically ordinary frag can be `T3 + LEGACY + VOICE +
KEEP_CONTEXT` and be one of the most valuable things in the archive; an
astonishing frag can be `T4 + ALT_POV`, which is an instruction to go and
find a better camera, not a lower score.

**GOLDEN is not a sixth band.** It is an instruction: no ranking, sampling or
downselect may hide this moment. `review_tags.golden_occurrence_ids()` is
what anything doing selection must consult, and it accepts human provenance
only — a machine-written GOLDEN is stored and visible but never
authoritative.

**KEEP_CONTEXT says the frag is not the unit.** A mediocre kill can sit
inside an extraordinary fifteen seconds.

**The vocabulary is frozen** so that a judgement made at review one thousand
means what it meant at review one. Adding a tag later is safe; changing what
one MEANS is not. `AIR_ROCKET`, `MID_AIR`, `CAMERA_GOOD` and `LEGACY_VALUE`
are deliberately refused: the first two are already machine traits and a
human tag could disagree with a measurement, and the other two duplicate
`CLEAN_POV` and `LEGACY`.

## POV is its own axis

`A brilliant event from a useless POV and an ordinary event from a perfect
POV are completely different assets.`

`pov_cluster.povs_for()` reports every camera that filmed one moment:
`SELF_POV`, `VICTIM_POV`, `TEAM_POV`, `OTHER_POV`. Killer and victim are
stated facts from the demo; teammate is derived from `player_teams_v1` and
falls back to OTHER when team data is missing, because "a stranger filmed
it" and "your teammate filmed it" lead a director to different decisions.

6,576 occurrences have more than one recording. The reviewer sees
`3 POVs available`; the killer's own demo is not automatically the best shot.

## Deleting is guarded, not blocked

`X` deletes; nothing is destroyed and `U` restores. But a deletion makes a
moment **invisible to the film pipeline**, and nobody goes looking through
the deleted list for the only teleporter shot in the archive. So
`dismiss_risk()` warns first when the moment is GOLDEN, already tagged, uses
a rare means of death (< 400 in the archive), or has several cameras — and
then lets the human decide.

## Telefrags: excluded, not lost

1,443 telefrags leave every normal queue because the map decided them and
they demonstrate no aim. They stay reachable through the `TELEFRAG_DOC`
corpus (1,360 after warmup exclusion) because teleporters are part of what
Quake looks like. It never leaks into the main queue — a test pins that.

## Capture determinism

Wolfcam archives `CVAR_ARCHIVE` values into its own config, so anything set
in an interactive session survives into the next launch — a `242ups`
speedometer once appeared in a review capture that no review cvar requested.
The review profile now sets every unwanted HUD element explicitly
(`cg_drawSpeed`, `cg_drawSpeedometer`, `cg_drawFPS`, `cg_lagometer`,
`cg_drawAttacker`, `cg_drawRewards`, `cg_drawKeys`, `cg_drawPickupItems`,
`cg_drawAmmoWarning`) rather than trusting whatever was archived.

`test_review_capture_determinism.py` pins all nine, pins that they reach
the cfg on disk, and pins that the profile cfg is exec'd from `cgamepostinit`
-- AFTER `q3config.cfg` is read, which is the half that actually makes the
pins win. A missing pin fails the test rather than reopening the route.

Movement metrics belong in the dossier, not burned into the footage.

## Hard-won facts worth not rediscovering

- **Round 0 is not a round.** It is the no-round-system sentinel; grouping by
  it yields a "round" of 105 user frags spanning a whole match.
- **Pain events are throttled** — median gap 925 ms, never under 100 ms — so
  they cannot count hits for any weapon firing faster than that. LG accuracy
  is `NOT_DERIVABLE`, not 0%.
- **`lg_incoming_hit_ratio` is incoming.** It is the opponent's aim.
- **`recognition_lg_engagements` is an empty scaffold** — 0 of 4,000 sampled
  rows carry `my_fire`.
- **The obituary is a confirmed hit.** It names weapon and victim, so the
  killing shot always counts.
- **Latched renderer cvars only take effect from the command line.** A value
  written into a cfg is read, stored, and ignored.
- **`ensure_install()` must still write the profile cfgs.** Its early return
  once left a requested cfg absent and the capture ran with none of its cvars.
