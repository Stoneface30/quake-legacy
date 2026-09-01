# Camera V2 — dense sampling, look-at, collision, runtime proof (2026-09-01)

Continuation of `cam10_runtime_contract.md`. That doc proved the camera
CAN move (9 keyframes, FREECAM_SAMPLED backend). This one proves it can
move SMOOTHLY, with decoupled look-at, on a collision-checked path, and
documents a second hard ceiling found while proving it.

**Note added later the same day**: `cam10_runtime_contract.md` was
subsequently corrected — the `playcamera` "engine bug" that motivated
building `FREECAM_SAMPLED` as the only backend turned out to be a CRLF
line-ending bug in this project's own `cam10_writer.py`, not an engine
defect. `NATIVE_CAM10` is now a proven-working backend too, and is the
default in `compile_dense_camera` (see the contract doc's "CORRECTED"
section). The `MAX_AT_COMMANDS=128` finding below is unaffected by that
correction — it's a real, independently-confirmed ceiling specific to
`FREECAM_SAMPLED`'s per-sample `at` commands, and doesn't apply to
`NATIVE_CAM10` (which reads up to 512 points from one file instead).

## New module: `creative_suite/engine/camera_compiler_v2.py`

Pipeline: `resample_dense()` (Catmull-Rom position / shortest-path angle
lerp / linear FOV) → `retarget_lookat()` (optional — decouples orientation
from position, e.g. "follow the rocket from the side while looking at the
rocket") → `collision_check_dense()` (runs the EXISTING
`camera_paths.validate_path`/`adjust_path` on the DENSE curve, not just
the sparse authored points) → `compile_dense_camera()` (backend
compilation, still `FREECAM_SAMPLED` — see below for why it stays the
default rather than being superseded).

## Second hard engine ceiling found: `MAX_AT_COMMANDS = 128`

A naive 60Hz/4000ms orbit (241 samples) hung capture identically to the
earlier `playcamera` symptom — but this is a DIFFERENT bug. Traced to
`cg_local.h:923` (`#define MAX_AT_COMMANDS 128`) and the insert logic at
`cg_consolecmds.c:6748-6781` (`CG_AddAtFtimeCommand`): a fixed 128-slot
array, sorted by fire time; once full, any NEW command whose time is
LATER than everything already queued is silently rejected. Our
`stopvideo`/`quit` lines are always last in file order (latest times), so
once the first 128 `freecamsetpos` samples filled the array, they were
the ones dropped — the demo never froze, it just played on forever with
no way to stop.

**Confirmed, not guessed**: reran with `logfile 2` — `qconsole.log`
contains the string `too many at commands` exactly **114** times for a
242-command cfg (241 freecamsetpos + 1 quit) against a 128-slot array:
242 − 128 = 114, exact.

**Fix**: `compile_dense_camera()` clamps effective Hz so total samples
stay under `MAX_CAMERA_SAMPLES = 128 − 8` (8 slots reserved for
video/stopvideo/quit/timeline commands), and reports `requested_hz` /
`effective_hz` / `hz_clamped` honestly rather than hiding the clamp. A
4000ms shot requesting 60Hz gets 29.75Hz (120 samples) instead — this is
a REAL, non-negotiable ceiling of the current engine, not a tunable
setting. Longer/denser shots than this ceiling allows need a chained
multi-window capture (splitting one shot across several `cgamepostinit`
re-execs, each with its own 128-command budget) — not built this session,
noted as the concrete next step for master-quality long shots.

## Runtime-proven, both for real

**Smooth orbit** (180°, 4000ms, 120 samples @ 29.75Hz effective): clean
capture (`rc 0`, ~92MB AVI). Frames 1.8s and 2.6s apart show continuous,
gradual view rotation — consistent framing of the same general area
shifting smoothly, not a jump cut. Demo's own HUD (frag messages)
progressed normally throughout, confirming the demo clock and the camera
driver coexist correctly at this density.

**Projectile-follow, real cached trajectory**: pulled a genuine `CONFIRMED`
rocket path from `recognition_projectile_paths`
(`CA-<player>-overkill-2012_12_06-19_31_30.dm_73`, launch 519875ms,
impact 523875ms, 161 cached points, 4000ms flight) via the new
`projectile_track_from_recognition()` adapter, fed it into the EXISTING
`camera_paths.projectile_follow()` generator (unmodified — no new
trajectory math), compiled at the same clamped density. Frame at t=1.0s
shows the camera literally riding just behind the rocket model mid-flight
toward a target; frame at t=3.0s shows the camera near the impact/landing
area with a body on the ground. This is the real cached evidence driving
the shot, not a synthetic path.

## Look-at decoupling status

`camera_paths.py`'s existing generators (`side_track`, `chase`,
`projectile_follow`, `follow_entity`) already decouple position (offset
from subject) from orientation (`look_at_angles` aimed back at the
subject) — this was NOT a gap. `retarget_lookat()` adds the more general
case: re-aiming an ALREADY-COMPUTED position track at a DIFFERENT,
independently-moving target track (e.g. a fixed orbit position that
tracks a moving combat centroid instead of its own orbit center),
including damping and an angular-speed cap for presentation-only
smoothing (the underlying target coordinates are never altered — only
tested with synthetic tracks so far, not yet run through a real capture).

## Collision on the dense path

`collision_check_dense()` wraps the existing `validate_path`/`adjust_path`
functions unchanged — the fix is entirely about WHAT gets passed to them
(the dense post-resample curve, so a 33ms-apart pair of samples is what
gets segment-checked, not a 500ms-apart pair of sparse authored points).
Classifies outcomes as `VALID` / `PUSHED_OUT` (repair succeeded) /
`SHORTENED` (a clean prefix survives) / `REJECTED` (unusable), plus an
approximate minimum wall clearance via 6-axis probe + binary search.
Verified against a synthetic wall tracer (tunneling-between-sparse-points
is caught) and, where the staged `pak00.pk3` is present, against the real
`aerowalk` BSP.

## What's deliberately NOT done yet

- Chained multi-window capture for shots needing > ~120 dense samples.
- A live capture proof of `retarget_lookat()` (unit-tested only so far).
- The camera debug-view VISUALIZATION artifact (directive section 12) —
  `compile_dense_camera()`'s return dict already carries all the raw data
  (authored/dense/final keyframes, collision report, clearance) a future
  `/frags` Director panel would need; rendering it as an image is
  deferred.

## Tests

`creative_suite/tests/test_camera_compiler_v2.py` — 22 passing, including
a test that locks in the exact 114-rejection math above as a regression
guard (`test_clamp_hz_to_budget_clamps_naive_60hz_4s_shot`).
