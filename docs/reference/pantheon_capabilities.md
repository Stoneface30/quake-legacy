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
| **REVIEW_ENEMY_VISIBILITY** | **PARTIAL** | `master_profile._REVIEW_V2` | WolfcamQL | see below |

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

## REVIEW_ENEMY_VISIBILITY — PARTIAL, with the dead ends recorded

**Working:** enemies render as Keel (`cg_enemyModel keel/bright`,
`cg_forceModel 1`). `cg_useDefaultTeamSkins` defaults to **1** and forces
red/blue team skins over the enemy model — turning it off was a real fix.
Teammates are unaffected (`cg_disallowEnemyModelForTeammates` defaults to 1).

**Not working:** the enemy is not GREEN.

**Ruled out, from local source — do not retry these:**

- *Missing team metadata.* False. `player_teams_v1` has RED/BLUE for the test
  demo, so `CG_IsEnemy` (`sc_misc.c:352`) should resolve.
- *Cfg timing.* False. `wolfcam_view.c:1002` recomputes `cg.enemyModelColors`
  on cvar modification count, so a cfg set at postinit is picked up.
- *`createcolorskins` / `R_CreatePlayerColorSkinImages`.* **Ruled out.**
  `tr_image.c:1800` generates **red and blue** images from a fixed
  `Skin_Images` table. It is a team-colour system and cannot make green.

**Leading remaining hypothesis, untested:** the colour is applied as
`shaderRGBA` (`cg_players.c:6099-6105`), a per-entity vertex colour. A Q3
player shader declaring `rgbGen identity` rather than `rgbGen entity`
**ignores** entity RGBA entirely — which would explain a value that is set,
stored and propagated yet never visible. Checking it means reading the
`keel/bright` shader out of `pak00.pk3`. If confirmed, the route is
`remapshader` (`cg_consolecmds.c:8571`) onto a shader that does honour entity
colour — and because only enemies use `keel/bright`, that remap would hit
enemies alone.

**Decision:** recorded PARTIAL. Enemies are Keel-shaped and distinguishable;
they are tan rather than green. Human curation is not blocked on it.

## Capture determinism

Wolfcam archives `CVAR_ARCHIVE` values into its own config, so anything set
in an interactive session survives into the next launch — a `242ups`
speedometer once appeared in a review capture that no review cvar requested.
The review profile now sets every unwanted HUD element explicitly
(`cg_drawSpeed`, `cg_drawSpeedometer`, `cg_drawFPS`, `cg_lagometer`,
`cg_drawAttacker`, `cg_drawRewards`, `cg_drawKeys`, `cg_drawPickupItems`,
`cg_drawAmmoWarning`) rather than trusting whatever was archived.

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
