# DIRECTOR preview — CHANGE IT → REFRESH IT → SEE IT

**Date:** 2026-09-01 · **Verdict: PASS.** A DIRECTOR draft change now produces
a real wolfcam capture and updates the browser player. Two engine contracts
were discovered *by measuring the delivered file* — both produced `rc=0`, an
empty `qconsole.log`, and a movie that looked entirely plausible.

Modules: `creative_suite/engine/director_preview.py` (engine),
`creative_suite/api/director_draft.py` (endpoints),
`creative_suite/frontend/frags.js` + `frags.html` (panel).
Tests: `creative_suite/tests/test_director_preview.py` (33).

---

## 0. Headline findings

| # | Finding | Severity |
|---|---|---|
| 1 | **`playcamera` seeks the demo to the camera path's FIRST point.** A `video` command scheduled before that instant fires late; the head of the shot is silently lost. | **Critical** |
| 2 | Consequence: the camera path must cover **the guard margin too**, not just the edit window. Covering only the edit window yields a correct-**length** file with the hero frag **500 ms early**. | **Critical** |
| 3 | Total-duration matching cannot catch either. Finding 2 passed every duration assertion. | **High** (method) |
| 4 | The runtime baseline works, and the leak it prevents is not subtle: without it the frame is **covered** in wolfcam's camera-point readout. Proved from the frame. | Confirmed |
| 5 | A `PROJECTILE` camera at `distance=150` on `quarantine` is collision-**SHORTENED** to 205 of 511 samples; the shot's second half is a locked-off hold. Recorded, not hidden. | Medium — **open** |
| 6 | A music-only change re-captures, because `preview_key` covers the whole render. The `.cam10` is provably identical, so the capture is provably reusable — but reuse is not implemented. | Low — **open** |

---

## 1. Architecture

```
draft (director_draft.py, in memory, NEVER persisted)
  -> SceneRecipeV2          scene_recipe.py       WHAT / WHEN   (recipe_id)
  -> PreviewPlan            director_preview.py   resolved inputs
  -> compile_dense_camera   camera_compiler_v2 + cam10_writer   -> .cam10
  -> fx script / grade pk3  pantheon_fx / pantheon_grade
  -> capture cfg            pantheon_runtime.baseline_lines() FIRST
  -> wolfcam capture        wolfcam_capture (guard margin on both ends)
  -> deterministic trim + H.264 + music mux     ffmpeg
  -> output/demo_v2/director_previews/<preview_key>.mp4
```

Nothing here is new research; every stage is an existing proven primitive.
The new parts are the **identity** (§2), the **guard** (§3), and the two
engine contracts in §4.

### Endpoints

| Method | Path | Returns |
|---|---|---|
| `POST` | `/api/frags/{frag_id}/director/preview` | `{preview_key, generation, state}` |
| `GET` | `/api/director/preview/{preview_key}` | `{state, generation, media_url, error, stale}` |
| `GET` | `/api/director/preview/{preview_key}/media` | `FileResponse` mp4, Range supported |

`state ∈ QUEUED | CAPTURING | TRIMMING | READY | FAILED`.

State lives in `director_previews` inside **`editorial.db`** — the same NEW
database `review_proxy.py` owns. `frag_recognition.db` and `demo_v2.db` are
never opened for writing.

### Concurrency

`review_proxy.py`'s proven shape and no more: one daemon worker thread, the
existing exclusive `output/demo_v2/_capture.lock` marker with its PID
convention, skip-and-requeue while another writer holds it. Two wolfcam
processes never run at once.

---

## 2. Preview identity — the key (§12)

`preview_key = sha256(canonical draft + demo/frag identity + recipe_id +
edit duration + code versions)`.

What is deliberately **excluded**: `dirty`, `saved_recipe_id`, `preview`,
`controls`, and any camera control the selected mode does not consume (moving
`side_offset` in `ORBIT` must not throw away a good capture).

What is deliberately **included** — the code versions, because each can
change a pixel without any draft field moving:

```
pipeline          director-preview-v3
camera_compiler   cam10-v1
runtime_baseline  36493f7140a2315c24d1a7d6faec6ade…   (pantheon_runtime)
master_profile    <profile_id>
grade             <pantheon_grade.grade_hash(look)>
fx                {OFF|SUBTLE|HERO: script_hash}
capture           fps / w / h / guard_ms
```

The canary already established that a capture under a different runtime
baseline *is* a different capture; the same reasoning applies to every
generated engine asset.

**A READY artifact for the same key is returned without re-capturing** —
capture is ~6-10× realtime and is the entire budget. Reuse additionally
verifies that the cached file is still **the right length** (§3): the first
real capture of this pipeline cached a 5.13 s file for an 8.50 s TimeMap, and
without that check the cache would have kept serving it.

`PREVIEW_PIPELINE_VERSION` is the escape hatch and it earned its keep twice
this session — `v1 → v2 → v3`, each bump invalidating every stale artifact.

---

## 3. The generation guard (§12)

Keys are not enough. The user turns a knob, a capture starts; they turn
another, a second starts. **The first can finish last.** Its artifact is
valid and stays cached under its own key, but it must never become the frag's
current preview or the picture silently reverts to the older draft.

* Every request takes a monotonically increasing per-frag `generation`.
* Every response carries it.
* `GET` reports `stale` once a newer generation exists for that frag.
* The published pointer only moves forward — one SQL clause:

```sql
UPDATE director_preview_generations
   SET current_key = ?, current_generation = ?
 WHERE frag_id = ? AND current_generation < ?
```

Tested with two genuinely overlapping jobs
(`test_old_job_finishing_last_does_not_become_current`): a fresh draft A is
held mid-flight while a cached draft B completes instantly at a higher
generation; A then finishes. Asserted afterwards — A is `READY`, A is
`stale`, B is current, B is not stale.

The panel drops a `stale` result rather than showing it.

---

## 4. THE ENGINE CONTRACT — playcamera seeks to the camera's first point

Found in two stages, both by measuring the delivered file. Both captures
exited `rc=0` with `camera loaded (version 10)` and nothing else in the log.

### Stage 1 — a 5.13 s file for an 8.50 s TimeMap

A `PROJECTILE` arc is naturally authored over the rocket *flight*: for the
canary frag that is relative `3375 → 8500 ms` of an `0 → 8500 ms` window. The
camera path therefore began **3.375 s after the capture window did**.

```
edit duration (TimeMap)   8.500 s
delivered mp4             5.133 s      = 8.500 − 3.375, to within a frame
```

`playcamera` jumped the demo forward to its first camera point, and the
already-scheduled `at <start> video` fired at that jump instead of at
`start`.

### Stage 2 — the right length, the wrong moment

Extending the path to `0 … total_ms` produced **exactly 8.5000 s** and passed
every duration assertion. It was still wrong:

```
raw capture                 9.000 s     (expected 8.5 + 2×0.5 guard = 9.500 s)
frag-message first frame    4.0000 s
canonical impact edit_us    4.5000 s
error                       −500.0 ms   = −30 frames
```

The camera's first point was at the *edit* window start, 500 ms after the
`video` command; the head guard was never recorded, and the trim then
discarded 500 ms of real content.

**This is the finding that matters methodologically.** Stage 2 is invisible
to total-duration checking. Only locating the hero event itself exposes it.

### The rule

> A native camera path must cover **everything the capture records** — the
> edit window **and** the guard margin on both ends.

`_cover_window()` holds the first pose from `−GUARD_MS` and the last pose to
`total_ms + GUARD_MS`. Deterministic, and the held opening reads as a
locked-off shot on the launch point before the ride begins.

Regressed for every camera mode by
`test_camera_path_covers_the_capture_including_the_guard`.

---

## 5. Hero-event clock proof (§3)

Scene: **frag 24326**, the canary hero shot
(`CA-…qUARanTINe…`, ROCKET, `server_time 291650`, 46-point / 1125 ms rocket
flight). Frag **5979** was checked first and rejected on its evidence, not on
preference: its cached path is

```
launch t=553075   impact t=553075   points: 2   flight: 0 ms   distance: 38.7u
```

A point-blank rocket with no flight. `_usable_projectile()` now refuses paths
under 8 points or 200 ms and reports an honest fallback rather than filming
nothing (`test_unusable_projectile_path_falls_back_honestly`).

### Measurement

The locator is the **frag message's first frame**, not a brightness spike. A
moving camera produces brightness spikes of its own (the largest
frame-difference peak in this shot is at 2.78 s, where the camera starts
moving — 1.7 s from the impact). The frag message is drawn by the engine on
the obituary event, so its onset is engine-timestamped.

```
canonical impact edit_us      4 500 000 µs = 4.5000 s = frame 270 @ 60 fps
delivered mp4                 510 frames = 8.5000 s
raw capture                   570 frames = 9.5000 s   (= 8.5 + 2 × 0.5 guard)

frame 267  4.4500 s   no message
frame 268  4.4667 s   no message
frame 269  4.4833 s   no message
frame 270  4.5000 s   "You fragged fenris"   <- ONSET
```

```
ERROR = 0.0 ms = 0 frames   (target: <= 1 frame at 60 fps)
```

The onset is the frame immediately after the last clean frame, so the
measurement is exact to its own 1-frame granularity. **PASS.**

Frames inspected directly at 0.05 / 1.5 / 3.0 / 3.6 / 4.0 / 4.5 / 5.5 / 6.5 /
8.4 s: clean gameplay, no camera-authoring overlay, no HUD clutter.

### Open issue — the camera is collision-SHORTENED

```
camera: SHORTENED   205 / 511 samples   (backend NATIVE_CAM10)
```

A camera trailing 150 u behind a rocket down a `quarantine` corridor clips
level geometry, so `collision_check_dense` keeps only the clean prefix. The
`debug_camera` readout in the §6 leak frame confirms it live: at
`current time 291666` the engine reports `camera point 204 [204+]` — the last
point, held.

The shot is therefore a rocket ride for ~3.8 s and a **locked-off hold** for
the remaining ~5.7 s. It is not wrong and the hero moment is correctly timed,
but it is not the shot the intent describes. `camera_status` is recorded in
`director_previews` for every preview. Fixing it is camera tuning (the canary
solved the same class of problem by ramping stand-off and probing the map for
clear orbit azimuths), not plumbing, and is deliberately left to the director.

---

## 6. Runtime baseline reset proof (§4)

Proved from the **frame**, not from the cfg text.

1. **Contaminate.** One wolfcam run setting `cg_drawCameraPath 1` and
   `cg_drawCameraPointInfo 1`, then quit — archived to `q3config.cfg` exactly
   as a previous session would leak them. Verified by reading the file back:
   `cg_drawCameraPath = "1"`, `cg_drawCameraPointInfo = "1"`.
2. **Leak.** Capture with the profile, the camera and the video commands, but
   **without** `baseline_lines()`.
3. **Reset.** The identical cfg body with `baseline_lines()` prepended.
   Nothing else differs.

Same frame (5.0 s into the raw capture = the hero moment):

| | leak (no baseline) | reset (with baseline) |
|---|---|---|
| `YAVG` | **70.843** | 60.097 |
| `YMAX` | 235.000 | 235.000 |
| `UAVG` | 121.704 | 121.252 |
| `VAVG` | 132.512 | 132.747 |

`ΔYAVG = +10.75` — a tenth of the frame's average luminance, added by text.
The leak frame carries a full-screen white readout: `camera point 204 : 0`,
`current time: 291666.666666 [204 +]`, `camera time: 286650.000000`,
`origin: 653 1132 627`, `angles`, `camera type: interp`, `flags: origin
angles fov time`, and thirty more lines of velocity fields. The reset frame is
completely clean and otherwise identical.

After the baseline capture, `q3config.cfg` reads `cg_drawCameraPath "0"` /
`cg_drawCameraPointInfo "0"` — the baseline both suppresses the leak *and*
heals the archive for the next session.

**Bonus:** the leak frame is also a live confirmation of §5 —
`camera time: 286650.000000` is exactly `window_start − GUARD_MS`, proving the
path now starts at the guard boundary.

### Runtime regression tests

Two, because the runtime half cannot run in CI:

* `test_overlay_cvars_are_baseline_and_not_overridable` — the three overlay
  cvars are in `RUNTIME_BASELINE` at `0`, are **not** in `OVERRIDABLE`, and
  `baseline_lines({name: "1"})` raises. The leak the baseline exists to
  prevent must not be reachable through the baseline's own API.
* `test_every_capture_cfg_resets_the_overlay_before_the_camera` — for every
  camera mode, the reset is emitted before `loadcamera` / `playcamera` /
  `video`. Ordering is the whole point: a reset after the profile resets
  nothing that matters.

---

## 7. Music in the preview (§13) and the architecture test (§38)

Music Intelligence V2 is **consumed, never rebuilt**. The draft gains a
`music` section carrying a `MusicPlacement` — `track_hash`,
`source_start_us`, `program_edit_start_us`, `source_end_us` — and the only
thing read from `music_features_v2.db` is that track's path.

Mixing follows **P1-G v6**: one fixed level, `normalize=0`, no sidechain, no
level following; the only moves are a 0.25 s fade in and a 0.35 s fade out.

### §38 — same everything, only the music differs

`test_music_only_change_keeps_the_same_camera_artifact`: identical gameplay,
TimeMap, camera, FX and look; two different `MusicPlacement`s.

```
recipe_id           identical
.cam10 sha256       identical
.cam10 bytes        byte-for-byte identical
music placement     different
preview_key         different
```

The camera artifact is a pure function of geometry — `build_camera_artifact`
reads `plan.keyframes`, `plan.recipe` and the backend, and nothing about
music. The audio path provably cannot reach the video path.

`test_music_is_muxed_into_the_preview` closes the other half with real
ffmpeg: two previews differing only in music have **different `mean_volume`**
and durations within 50 ms of each other.

### Open — a music-only change still re-captures

`preview_key` covers the whole render, so changing the track invalidates it
and the engine runs again (~50-120 s). The §38 result is precisely the proof
that this is unnecessary: the capture is reusable under a *capture key* that
excludes music, with only the trim+mux re-run (~2 s). Not implemented — it
needs an eviction policy for cached AVIs (220 MB for 9.5 s at 1080p), and
inventing one without a size budget would be guessing.

---

## 8. Previewing is not saving (§11)

Nothing in this module writes a `SceneRecipe`, a `PantheonScene`, or a
`shot_plan`. Only `POST .../draft/save` persists, exactly as before.

`test_preview_never_persists_a_recipe` asserts it the only way that means
anything: after a draft change and a full preview, `cinematic.db` **does not
exist**, and `frag_recognition.db` / `demo_v2.db` have unchanged `mtime_ns`.

---

## 9. Cost, measured

| operation | cost |
|---|---|
| plan + camera authoring (58 keyframes) | < 5 ms |
| BSP load + collision check + `.cam10` write | ~0.3 s |
| fx script + grade pk3 + gamedir setup | ~0.02 s |
| **wolfcam capture, 9.5 s raw @ 60 fps 1920×1080** | **37 - 55 s** |
| trim + scale to 720p + H.264 + music mux | ~10 s |
| **end to end, cold** | **~53 s** |
| **end to end, cache hit** | **~0.05 s** (one ffprobe) |

The engine is the entire budget, as the canary found. The cache is therefore
the single highest-value part of this module, which is why the key is
conservative about what it excludes and strict about what it includes.

---

## 10. Mock mode

`CS_PREVIEW_DIRECTOR_MOCK=1` replaces **only wolfcam**. It still renders a
real raw AVI carrying the guard margin *and* a ragged 117 ms tail, still runs
the real trim, still compiles a real `.cam10`, and still muxes real music —
so the state machine, the trim contract, the key, the generation guard and
the §38 artifact identity are all exercised for real, headlessly.

Two diagnostic hooks, used to find §4 and kept:

* `CS_PREVIEW_KEEP_RAW=1` — copies the raw capture next to the mp4, which is
  how "the raw is 9.000 s, not 9.500 s" became visible.
* `CS_PREVIEW_ENGINE_LOG=1` — overrides the baseline's `logfile 0`.

---

## 11. Staging hygiene

`output/demo_v2/_wolfcam_staging/` was exclusively owned for this work.
`taskkill /IM wolfcamql.exe /F` before and after every capture. Every capture
restores in a `finally`: `capture.cfg` deleted, `cgamepostinit.cfg` back to
`// idle`, grade pk3 removed, `zzz_uhd_*.pk3` restored (moved aside, never
deleted). Verified on completion: 5 UHD packs present, no `.disabled` files,
no `capture.cfg`, `cgamepostinit.cfg` is `// idle`, generated `.cam10` and
`.fx` files removed, `q3config.cfg` back to `cg_drawCameraPath "0"`.

Nothing committed.

---

## 12. What was NOT done

* **No AVI capture cache** — see §7.
* **No slow motion in the preview TimeMap.** One `normal` 1/1 segment; slow
  motion is ~0.3 s of wall time per output frame (`timewarp_measurement.md`)
  and the preview loop is the wrong place for it. The TimeMap is still the
  trim authority, so adding a segment later changes the recipe and nothing
  else.
* **No camera-collision tuning** — see §5, recorded and left to the director.
* **`camera_status` is not surfaced in the panel.** The `GET` shape was fixed
  by the milestone contract and both agents build to it; the field is in the
  database and in `director_preview.get_preview()`.
* **`render_part_v6.py` untouched** (V1, frozen). **No music subsystem
  rebuilt.**
