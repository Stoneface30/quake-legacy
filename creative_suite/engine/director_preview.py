"""DIRECTOR preview — CHANGE IT -> REFRESH IT -> SEE IT.

Directive §11-13, §38. The /frags DIRECTOR panel could already dial a camera
/ FX / look draft, but nothing realized it: the panel honestly said "UPDATING
PREVIEW - the video above still shows the LAST CAPTURE". This module closes
that loop. A draft change plus one REFRESH PREVIEW click produces a real
wolfcam capture of THAT draft, trimmed to the exact TimeMap edit duration,
transcoded to browser-playable H.264, and swapped into the player.

Nothing here is new research. Every stage is an existing, proven primitive:

    draft (director_draft.py, in memory, never persisted)
      -> SceneRecipeV2                     scene_recipe.py     WHAT / WHEN
      -> PantheonScene                     pantheon_scene.py   HOW IT LOOKS
      -> compile_dense_camera -> .cam10    camera_compiler_v2 + cam10_writer
      -> fx script / grade pk3             pantheon_fx / pantheon_grade
      -> capture cfg, baseline_lines FIRST pantheon_runtime
      -> wolfcam capture with guard margin wolfcam_capture
      -> deterministic trim + H.264 + music ffmpeg
      -> output/demo_v2/director_previews/<preview_key>.mp4

Three ideas carry the whole design:

**1. The preview key (§12).** ``preview_key`` is a sha256 over the canonical
draft state, the demo/frag identity, the resolved TimeMap, the music
placement, and every code version that can change a pixel (camera compiler,
runtime baseline, fx script, grade shader, this pipeline). Same key = same
picture, so a READY artifact is returned without re-capturing. Capture is
~6-10x realtime; not re-running one is the single largest saving available.

**2. The generation guard (§12).** Keys are not enough. A user turns a knob,
a preview starts; they turn another knob and a second preview starts. The
FIRST capture may well finish LAST. Its artifact is still valid and is still
cached under its own key -- but it must never become the frag's current
preview, or the picture silently reverts to the older draft. Every request
takes a monotonically increasing per-frag ``generation``; every response
carries it; ``GET`` reports ``stale`` once a newer generation exists; and the
published "current" pointer only ever moves forward.

**3. Previewing is not saving (§11).** Nothing in this module writes a
SceneRecipe, a PantheonScene, or a shot_plan. State lives in
``director_previews`` inside ``editorial.db`` (the same NEW database
review_proxy.py owns); the recognition databases are never opened for
writing. Only ``POST .../draft/save`` persists a recipe, exactly as before.

Concurrency is review_proxy.py's proven shape and no more: ONE daemon worker
thread, the existing exclusive ``output/demo_v2/_capture.lock`` marker with
its PID convention, skip-and-requeue while another writer holds it. Two
wolfcam processes must never run at once.

``CS_PREVIEW_DIRECTOR_MOCK=1`` renders the whole flow headlessly (pattern:
``CS_PROXY_MOCK`` / ``CS_CAPTURE_MOCK``) so every state transition, the key,
the generation guard, the trim contract and the music mux are all testable
without the GUI engine.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import queue
import shutil
import sqlite3
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from creative_suite.engine import (cam10_writer, camera_compiler_v2,
                                   presentation,
                                   camera_paths, master_profile,
                                   pantheon_fx, pantheon_grade,
                                   pantheon_runtime, review_proxy,
                                   wolfcam_capture)
from creative_suite.engine.scene_recipe import (DemoRef, EventAnchor,
                                                EvidenceRef, MusicPlacement,
                                                SceneRecipeV2, TimeSegment)

REPO_ROOT = Path(__file__).resolve().parents[2]

# Bump when anything in THIS module changes the resulting pixels. It is part
# of preview_key, so a bump invalidates every cached artifact by construction
# instead of silently serving output from an older pipeline.
#   v1 -> v2: `_cover_window` — a native camera path must span the whole
#             capture window, or playcamera jumps the demo forward and eats
#             the head of the shot (measured; see that function's docstring).
#   v2 -> v3: ...and the guard margin too. v2 produced a correct-LENGTH file
#             with the hero frag 500 ms early — the exact failure that
#             total-duration matching cannot catch.
#   v3 -> v4: the capture profile is now a FUNCTION of the camera mode
#             (presentation.py). Every non-FPV capture before this exec'd the
#             gameplay-HUD profile, so "You fragged" is burned into them.
PREVIEW_PIPELINE_VERSION = "director-preview-v4"

# The two halves of preview identity (§12, split 2026-09-01).
#
# ``PREVIEW_PIPELINE_VERSION`` above versions everything that reaches the
# CAPTURED PIXELS. ``ASSEMBLY_PIPELINE_VERSION`` versions only the cheap
# post pass (music mux / audio mix). They are versioned separately for the
# same reason the keys are split: touching the mux must not throw away every
# capture on disk, and touching the capture must invalidate everything.
ASSEMBLY_PIPELINE_VERSION = "director-assembly-v1"

PREVIEW_DIR = REPO_ROOT / "output" / "demo_v2" / "director_previews"
# The SAME lock review_proxy.py and capture_batch_run.py take. Deliberately
# shared: it is the "one wolfcam at a time" lock, not a per-feature lock.
LOCK_PATH = REPO_ROOT / "output" / "demo_v2" / "_capture.lock"
FFMPEG = REPO_ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffmpeg.exe"
FFPROBE = REPO_ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffprobe.exe"
MUSIC_FEATURE_DB_PATH = (REPO_ROOT / "creative_suite" / "database"
                         / "music_features_v2.db")

# Capture guard (timewarp_measurement.md "mandatory trim contract"): a raw
# capture's length is NOT authoritative -- +/-1 video frame and up to ~150 ms
# of non-deterministic trailing audio. Record this much extra demo time on
# BOTH ends at rate 1/1, then trim deterministically to the exact TimeMap
# edit duration. 500 ms is >3x the worst measured audio tail.
GUARD_MS = 500

FPS = wolfcam_capture.FPS          # 60
PREVIEW_WIDTH, PREVIEW_HEIGHT = 1280, 720   # preview, not master (P1-J)
PREVIEW_CRF = "20"
PREVIEW_PRESET = "veryfast"

# P1-G: music plays at ONE FIXED LEVEL. No sidechain, no level following.
MUSIC_VOLUME = 0.75
GAME_AUDIO_VOLUME = 0.85
AUDIO_BITRATE = "160k"

# --------------------------------------------------------------------------
# Visual artifact cache budget (measured, not guessed — 2026-09-01)
#
# MEASUREMENT. ``output/demo_v2/director_previews`` held 1 file / 1.72 MB on
# disk while ``director_previews`` in editorial.db held 4 READY rows — three
# artifacts had already been hand-deleted, which is precisely the unbounded
# growth this budget exists to make unnecessary. The surviving artifact is
# the canary preview: 8.500 s, 1,721,178 bytes, 1.62 Mbit/s at 1280x720
# CRF 20. That is ~202 KB per second of preview, so a typical 7-12 s preview
# window costs 1.4-2.4 MB. Free space on G: at measurement time: 111 GB of
# 932 GB (89% used).
#
# BUDGET. 4 GiB. At the measured rate that is ~2,000 cached captures (~4.7
# hours of preview footage) — far more than one director session can dial —
# while spending 3.6% of the free space that actually exists on the volume.
# A budget as a fraction of a nearly-full 932 GB disk would be reckless; a
# budget of a few hundred MB would evict a working set the user is still
# A/B-ing against. Override with ``CS_PREVIEW_VISUAL_BUDGET_BYTES``.
VISUAL_CACHE_BUDGET_BYTES = int(
    os.getenv("CS_PREVIEW_VISUAL_BUDGET_BYTES") or 4 * 1024 ** 3)

STATE_EVICTING = "EVICTING"

STATE_QUEUED = "QUEUED"
STATE_CAPTURING = "CAPTURING"
STATE_TRIMMING = "TRIMMING"
STATE_READY = "READY"
STATE_FAILED = "FAILED"
STATES = (STATE_QUEUED, STATE_CAPTURING, STATE_TRIMMING, STATE_READY,
          STATE_FAILED)

# look -> (grade variant, do the zzz_uhd_*.pk3 texture packs participate)
LOOK_POLICY: dict[str, tuple[str, bool]] = {
    "ORIGINAL": (pantheon_grade.GRADE_ORIGINAL, False),
    "UHD": (pantheon_grade.GRADE_ORIGINAL, True),
    "PANTHEON": (pantheon_grade.GRADE_PANTHEON_SUBTLE, True),
}

_LOCK_RETRY_S = 5.0
_MAX_LOCK_WAITS = 240

_queue: "queue.Queue[dict[str, Any] | None]" = queue.Queue()
_worker: threading.Thread | None = None
_worker_mutex = threading.Lock()
_gen_mutex = threading.Lock()


class PreviewBuildError(RuntimeError):
    """The draft cannot be turned into a capturable preview."""


# ---------------------------------------------------------------------------
# Persistence — director_previews in editorial.db (the NEW db, per project
# rule; frag_recognition.db / demo_v2.db are never written).
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS director_previews (
    preview_key        TEXT PRIMARY KEY,
    frag_id            INT NOT NULL,
    generation         INT NOT NULL,
    state              TEXT NOT NULL,
    error              TEXT,
    mp4_path           TEXT,
    recipe_id          TEXT,
    camera_artifact    TEXT,
    camera_status      TEXT,
    music_track_hash   TEXT,
    edit_duration_us   INT,
    created_at         TEXT,
    updated_at         TEXT
);
CREATE TABLE IF NOT EXISTS director_preview_generations (
    frag_id            INT PRIMARY KEY,
    latest_generation  INT NOT NULL,
    current_generation INT NOT NULL DEFAULT 0,
    current_key        TEXT
);
-- The EXPENSIVE half of a preview: one trimmed, transcoded capture, keyed by
-- visual_capture_key and carrying NO music. Many delivered previews (one per
-- music placement) share one row here. ``state`` is the crash-safety flag:
-- an artifact is only ever read back as usable while it says READY, and
-- eviction flips it to EVICTING BEFORE the file is touched.
CREATE TABLE IF NOT EXISTS director_visual_artifacts (
    visual_key         TEXT PRIMARY KEY,
    state              TEXT NOT NULL DEFAULT 'READY',
    path               TEXT NOT NULL,
    bytes              INT NOT NULL DEFAULT 0,
    edit_duration_us   INT,
    camera_artifact    TEXT,
    camera_status      TEXT,
    created_at         TEXT,
    last_used_at       TEXT
);
CREATE INDEX IF NOT EXISTS director_visual_artifacts_lru
    ON director_visual_artifacts (state, last_used_at);
"""


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _conn() -> sqlite3.Connection:
    """Writable connection to editorial.db.

    Resolved through ``review_proxy.EDITORIAL_DB_PATH`` at call time (not
    import time) so a test that monkeypatches that attribute redirects this
    module too — one editorial database, one place to point it.
    """
    path = Path(review_proxy.EDITORIAL_DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=15, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.executescript(_SCHEMA)
    # CREATE TABLE IF NOT EXISTS never adds a column to an existing table, so
    # additive columns need an explicit, idempotent migration.
    have = {r["name"] for r in con.execute("PRAGMA table_info(director_previews)")}
    for column, decl in (("camera_status", "TEXT"),
                         ("visual_key", "TEXT"),
                         ("assembly_key", "TEXT"),
                         ("last_used_at", "TEXT")):
        if column not in have:
            con.execute(f"ALTER TABLE director_previews ADD COLUMN {column} {decl}")
    con.commit()
    return con


# ---------------------------------------------------------------------------
# Identity — the preview key (§12)
# ---------------------------------------------------------------------------

def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)


def canonical_visual_draft(draft: dict[str, Any]) -> dict[str, Any]:
    """The part of a draft that reaches the CAPTURED PIXELS — and only that.

    ``dirty`` / ``saved_recipe_id`` / ``preview`` / ``controls`` are panel
    bookkeeping: two drafts that differ only there are the SAME picture and
    must produce the same key, or the cache never hits. Camera controls are
    filtered to the ones the selected mode actually consumes, so nudging
    ``side_offset`` in ORBIT (where it is not drawn and not used) does not
    invalidate a perfectly good artifact.

    ``music`` is deliberately ABSENT: it is muxed after the capture and
    cannot reach a rendered frame (the §38 architecture test proves it by
    compiling a byte-identical ``.cam10`` across two music placements).
    """
    from creative_suite.api import director_draft as dd
    camera = dict(draft.get("camera") or {})
    mode = camera.get("mode", "ORBIT")
    used = dd.MODE_CONTROLS.get(mode, ())
    fx = dict(draft.get("fx") or {})
    look = dict(draft.get("look") or {})
    return {
        "camera": {"mode": mode,
                   **{k: round(float(camera[k]), 4)
                      for k in used if k in camera}},
        "fx": {k: fx[k] for k in sorted(fx)},
        "look": {"look": look.get("look", "ORIGINAL"),
                 "show_depth": bool(look.get("show_depth", False))},
        "backend": draft.get("backend", cam10_writer.BACKEND_NATIVE_CAM10),
    }


def canonical_assembly(draft: dict[str, Any]) -> dict[str, Any]:
    """The part of a draft that only the CHEAP POST PASS consumes.

    Music placement plus the fixed mix constants it is applied with. Nothing
    here can change a captured frame, which is exactly why a change confined
    to this dict must never trigger a recapture.
    """
    return {
        "music": canonical_music(draft.get("music")),
        "mix": {"music_volume": MUSIC_VOLUME,
                "game_volume": GAME_AUDIO_VOLUME,
                "audio_bitrate": AUDIO_BITRATE},
        "version": ASSEMBLY_PIPELINE_VERSION,
    }


def canonical_draft(draft: dict[str, Any]) -> dict[str, Any]:
    """Both halves, for the code that builds a plan rather than a key.

    ``build_plan`` needs the camera AND the music in one dict; the keys do
    not. Keeping this as the union means the plan builder is unchanged by the
    key split.
    """
    return {**canonical_visual_draft(draft),
            "music": canonical_music(draft.get("music"))}


def canonical_music(music: dict[str, Any] | None) -> dict[str, Any] | None:
    """A MusicPlacement selection, normalized. ``None`` means game audio only."""
    if not music:
        return None
    return {
        "track_hash": str(music["track_hash"]),
        "source_start_us": int(music["source_start_us"]),
        "program_edit_start_us": int(music.get("program_edit_start_us", 0)),
        "source_end_us": (None if music.get("source_end_us") is None
                          else int(music["source_end_us"])),
    }


def code_versions(look: str, fx_levels: tuple[str, ...], camera_mode: str = "FPV") -> dict[str, Any]:
    """Every code artifact that can change a pixel, hashed.

    Recorded rather than assumed: the canary proved a scene can be identical
    on paper and different on screen because ``RUNTIME_BASELINE`` gained an
    entry (``cg_drawCameraPath``). A capture under a different runtime
    baseline IS a different picture, so the baseline hash is part of identity.
    """
    grade, _packs = LOOK_POLICY[look]
    profile = presentation.profile_for(camera_mode)
    return {
        "pipeline": PREVIEW_PIPELINE_VERSION,
        "camera_compiler": cam10_writer.CAMERA_COMPILER_VERSION,
        "runtime_baseline": pantheon_runtime.baseline_hash(),
        # The profile the CAMERA MODE resolves to, not a global constant: the
        # same camera under a different HUD is a different frame.
        "master_profile": master_profile.profile_id(profile),
        "presentation": presentation.presentation_for(camera_mode),
        "grade": pantheon_grade.grade_hash(grade),
        "fx": {level: pantheon_fx.script_hash(level)
               for level in sorted(set(fx_levels))},
        "capture": {"fps": FPS, "w": PREVIEW_WIDTH, "h": PREVIEW_HEIGHT,
                    "guard_ms": GUARD_MS},
    }


def compute_visual_capture_key(*, frag_id: int, demo_sha256: str,
                               demo_name: str, recipe_id: str,
                               edit_duration_us: int,
                               draft: dict[str, Any]) -> str:
    """"Does the EXPENSIVE wolfcam capture have to run again?"

    Everything that reaches a rendered frame, and nothing else:

    * frag identity + demo identity — a different demo is a different picture;
    * ``recipe_id`` + ``edit_duration_us`` — the TimeMap. This LOOKS post-only
      ("it's just a trim") and is NOT: the window start/end drive
      ``seekservertime`` and the ``video``/``stopvideo`` schedule, and
      ``_cover_window`` extends the camera path to ``total_ms + guard``. A
      longer edit is a longer, differently-framed capture, not a longer cut of
      the same one;
    * the visual draft — camera / fx / look / backend (see
      ``canonical_visual_draft``);
    * ``code_versions`` — pipeline, camera compiler, runtime baseline, master
      profile, grade, fx scripts, and the capture geometry (fps, w, h,
      guard_ms). The canary proved a scene can be identical on paper and
      different on screen when only ``RUNTIME_BASELINE`` moved.
    """
    canon = canonical_visual_draft(draft)
    fx_levels = tuple(canon["fx"].values()) or ("OFF",)
    payload = {
        "frag": {"id": int(frag_id), "demo_sha256": str(demo_sha256),
                 "demo_name": str(demo_name)},
        "recipe_id": str(recipe_id),
        "edit_duration_us": int(edit_duration_us),
        "draft": canon,
        "versions": code_versions(canon["look"]["look"], fx_levels,
                                  camera_mode=canon["camera"]["mode"]),
    }
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def compute_assembly_key(*, visual_capture_key: str, edit_duration_us: int,
                         draft: dict[str, Any]) -> str:
    """"Does only the CHEAP post pass have to run again?"

    Bound to ``visual_capture_key`` so an assembly key is never meaningful
    against the wrong capture, and to ``edit_duration_us`` because the music
    fade-out is placed relative to the end of the cut.
    """
    payload = {"visual": str(visual_capture_key),
               "edit_duration_us": int(edit_duration_us),
               "assembly": canonical_assembly(draft)}
    return hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()


def compute_preview_key(*, frag_id: int, demo_sha256: str, demo_name: str,
                        recipe_id: str, edit_duration_us: int,
                        draft: dict[str, Any]) -> str:
    """Identity of the DELIVERED mp4 = both halves.

    Unchanged as a contract: same draft -> same key, music change -> new key.
    What changed is that it is now derived, so the pipeline can answer the two
    underlying questions independently.
    """
    visual, assembly = compute_preview_keys(
        frag_id=frag_id, demo_sha256=demo_sha256, demo_name=demo_name,
        recipe_id=recipe_id, edit_duration_us=edit_duration_us, draft=draft)
    return hashlib.sha256(f"{visual}:{assembly}".encode("ascii")).hexdigest()


def compute_preview_keys(*, frag_id: int, demo_sha256: str, demo_name: str,
                         recipe_id: str, edit_duration_us: int,
                         draft: dict[str, Any]) -> tuple[str, str]:
    """``(visual_capture_key, preview_assembly_key)`` for this draft."""
    visual = compute_visual_capture_key(
        frag_id=frag_id, demo_sha256=demo_sha256, demo_name=demo_name,
        recipe_id=recipe_id, edit_duration_us=edit_duration_us, draft=draft)
    assembly = compute_assembly_key(visual_capture_key=visual,
                                    edit_duration_us=edit_duration_us,
                                    draft=draft)
    return visual, assembly


# ---------------------------------------------------------------------------
# Draft -> plan
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PreviewPlan:
    """Everything the capture needs, resolved once, before any engine runs."""
    frag_id: int
    demo_name: str
    demo_sha256: str
    demo_path: str
    recipe: SceneRecipeV2
    draft: dict[str, Any]
    keyframes: tuple[dict[str, Any], ...]
    camera_mode: str
    camera_fallback: str | None
    subject_track: tuple[tuple[float, float, float, float], ...]
    map_name: str
    music: MusicPlacement | None
    music_path: str | None

    @property
    def edit_duration_us(self) -> int:
        return (self.recipe.time_map[-1].edit_end_us
                - self.recipe.time_map[0].edit_start_us)

    @property
    def window_start_ms(self) -> int:
        return self.recipe.demo.window_start_us // 1000

    @property
    def window_end_ms(self) -> int:
        return self.recipe.demo.window_end_us // 1000


def _projectile_path(demo_name: str, server_time_ms: int) -> dict | None:
    """Cached recognition projectile path for this frag — READ ONLY."""
    from creative_suite.api import frags as frags_api
    db = Path(frags_api.FRAG_DB_PATH)
    if not db.exists():
        return None
    con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    try:
        row = con.execute(
            "SELECT path FROM recognition_projectile_paths "
            "WHERE demo_name = ? AND server_time_ms = ? "
            "ORDER BY version DESC LIMIT 1",
            (demo_name, int(server_time_ms)),
        ).fetchone()
    except sqlite3.Error:
        return None
    finally:
        con.close()
    if row is None:
        return None
    try:
        return json.loads(row[0])
    except (TypeError, ValueError):
        return None


# Evidence contract for choosing a projectile path to photograph.
#
# The POINT SERIES is the primary evidence; the launch/impact scalars are
# corroborating only. Both were audited across all 4,391 cached paths
# (2026-09-01): 4,135 agree exactly, 0 disagree, and 256 carry
# ``launch.t == impact.t``. All 256 of those have a point span of exactly
# 25 ms — one server snapshot tick — so the equal timestamps are the
# engine's time quantization, not corrupted data. A flight that lasts a
# single tick cannot resolve launch and impact to different ticks.
#
# The scalars are nonetheless not load-bearing here: deriving flight from
# the series makes the rule independent of that quantization floor.
MIN_FLIGHT_MS = 200      # below this there is no arc to fly a camera along
MIN_POINTS = 8           # enough samples for a smooth Catmull-Rom retarget
MIN_DISPLACEMENT_U = 64.0  # a path that never leaves the muzzle films nothing


def projectile_evidence(path: dict | None) -> dict:
    """Grade a cached projectile path against the evidence contract.

    Returns the measured quantities plus ``usable`` and, when unusable, a
    ``reason``. Measurement comes from ``points`` — see the contract note
    above for why the launch/impact scalars are corroborating only.
    """
    if not path:
        return {"usable": False, "reason": "no_path"}
    points = path.get("points") or []
    launch, impact = path.get("launch") or {}, path.get("impact") or {}
    ev: dict[str, Any] = {
        "points": len(points),
        "scalar_flight_ms": (None if launch.get("t") is None
                             or impact.get("t") is None
                             else int(impact["t"]) - int(launch["t"])),
    }
    if len(points) < 2:
        return {**ev, "usable": False, "reason": "too_few_points"}
    try:
        coords = [tuple(float(v) for v in p[1:4]) for p in points]
        span_ms = int(points[-1][0]) - int(points[0][0])
    except (TypeError, ValueError, IndexError):
        return {**ev, "usable": False, "reason": "malformed_points"}
    if not all(math.isfinite(v) for xyz in coords for v in xyz):
        return {**ev, "usable": False, "reason": "non_finite_coords"}
    displacement = math.dist(coords[0], coords[-1])
    ev.update(flight_ms=span_ms, displacement_u=round(displacement, 1))
    if span_ms <= 0:
        return {**ev, "usable": False, "reason": "non_positive_flight"}
    if len(points) < MIN_POINTS:
        return {**ev, "usable": False, "reason": "too_few_points"}
    if span_ms < MIN_FLIGHT_MS:
        return {**ev, "usable": False, "reason": "flight_too_short"}
    if displacement < MIN_DISPLACEMENT_U:
        return {**ev, "usable": False, "reason": "displacement_too_small"}
    return {**ev, "usable": True, "reason": None}


def _usable_projectile(path: dict | None) -> bool:
    """Whether this path has real flight to photograph.

    Frag 5979 is the cautionary case: one of the highest-scoring rockets in
    the corpus, but its cached path spans 25 ms / 38.7 u across 2 points — a
    point-blank shot with no arc. A projectile camera built on it films
    nothing, so the preview falls back rather than pretending otherwise.

    Note that the ~300 ms / 318.6 u direct rocket sometimes quoted alongside
    Frag 5979 is a *different* event: Frag 4121, also on asylum and also
    DIRECT_CONFIRMED, from the 2011-08-05 demo rather than 2011-12-20. The
    two are easy to conflate; only 4121 has an arc worth photographing.
    """
    return projectile_evidence(path)["usable"]


def build_preview_recipe(frag: dict[str, Any]) -> SceneRecipeV2:
    """A SceneRecipeV2 for the preview window.

    ONE ``normal`` 1/1 segment: the preview is a straight-through look at the
    draft, and slow motion is the single most expensive knob in the loop
    (timewarp_measurement.md: ~0.3 s of wall time per output frame). The
    TimeMap is still the authority for the trim — ``edit_duration_us`` is read
    from it, never from the captured file — so wiring a slow segment in later
    changes the recipe and nothing else.
    """
    window = frag.get("window") or {}
    start_us = int(window["start_ms"]) * 1000
    end_us = int(window["end_ms"]) * 1000
    if end_us <= start_us:
        raise PreviewBuildError("frag window has non-positive duration")
    frag_us = int(frag["server_time_ms"]) * 1000
    attributes = dict(frag.get("attributes") or {})
    impact_ms = attributes.get("projectile_impact_t")
    impact_us = int(impact_ms) * 1000 if impact_ms is not None else frag_us
    impact_us = min(max(impact_us, start_us + 1), end_us - 1)
    evidence = EvidenceRef(
        dataset="recognized_frags", record_id=str(frag["id"]),
        version=f"recognition-v{int(frag.get('recognition_version') or 0)}",
        detail={"weapon_name": frag.get("weapon_name"),
                # The cached projectile path was never observed: the extractor
                # inferred it. The impact EVENT is recorded; the trajectory is
                # a reconstruction and must be labelled as one downstream.
                "trajectory_provenance": "EVENT_CONSTRAINED_RECONSTRUCTION",
                "trajectory_origin": "inferred from impact + recorder view "
                                     "rays; missile entity not observed"})
    weapon = str(frag.get("weapon_name") or "PROJECTILE").upper()
    anchors = (
        EventAnchor(anchor_id="impact-0",
                    event_type=f"{weapon}_IMPACT",
                    ordinal=0, actor_scope="recorder",
                    resolved_demo_us=impact_us, evidence=evidence,
                    confidence=str(attributes.get("projectile_path_confidence")
                                   or "UNKNOWN")),
        EventAnchor(anchor_id="frag-0", event_type="FRAG", ordinal=0,
                    actor_scope="recorder", resolved_demo_us=frag_us,
                    evidence=evidence, confidence="CONFIRMED"),
    )
    return SceneRecipeV2(
        demo=DemoRef(sha256=str(frag.get("content_hash") or ""),
                     name=str(frag["demo_name"]),
                     window_start_us=start_us, window_end_us=end_us),
        time_map=(TimeSegment("normal", start_us, end_us, 0,
                              end_us - start_us, 1, 1),),
        anchors=anchors,
        # Deliberately NOT stamped with PREVIEW_PIPELINE_VERSION: a recipe
        # describes the SCENE, and letting a renderer version leak into it
        # changes recipe_id every time this module is touched. The pipeline
        # version belongs to the preview key, which is where it lives.
        filters={"source_frag_id": int(frag["id"])},
    )


def _resolve_music(music: dict[str, Any] | None
                   ) -> tuple[MusicPlacement | None, str | None]:
    """Turn a draft music selection into a MusicPlacement + a real file path.

    CONSUMES Music Intelligence V2 (``music_features_v2.db``, 396 tracks,
    ``semantic-region-matcher@2.0.0``). Nothing is analysed, cached or
    rebuilt here — the store is read for the track's path and nothing else.
    """
    canon = canonical_music(music)
    if canon is None:
        return None, None
    placement = MusicPlacement(
        track_id=canon["track_hash"],
        source_start_us=canon["source_start_us"],
        program_edit_start_us=canon["program_edit_start_us"],
        source_end_us=canon["source_end_us"])
    path = None
    db = Path(MUSIC_FEATURE_DB_PATH)
    if db.exists():
        from creative_suite.engine.music_features_v2 import MusicFeatureStore
        feature = MusicFeatureStore(db).get(canon["track_hash"])
        if feature is not None:
            path = feature.path
    return placement, path


def build_plan(frag: dict[str, Any], draft: dict[str, Any],
               demo_path: str | None = None) -> PreviewPlan:
    """Draft + frag evidence -> a fully resolved, capturable plan.

    Raises ``PreviewBuildError`` rather than guessing. Everything geometric
    comes from the cached recognition projectile path; when there is none (or
    it has no flight, per ``_usable_projectile``) the camera falls back to
    plain POV and says so in ``camera_fallback`` — an honest preview of what
    the engine can actually film beats a confident camera pointed at nothing.
    """
    recipe = build_preview_recipe(frag)
    canon = canonical_draft(draft)
    mode = canon["camera"]["mode"]
    path = _projectile_path(str(frag["demo_name"]),
                            int(frag["server_time_ms"]))
    usable = _usable_projectile(path)
    fallback: str | None = None
    if mode in ("PROJECTILE", "CHASE", "SIDE") and not usable:
        fallback = ("no usable cached projectile path for this frag "
                    "(need >= 8 points and >= 200 ms of flight)")
        mode = "ORBIT" if path else "FPV"
    if mode in ("ORBIT", "FREECAM") and not path:
        fallback = fallback or "no cached projectile geometry for this frag"
        mode = "FPV"

    track: tuple[tuple[float, float, float, float], ...] = ()
    keyframes: tuple[dict[str, Any], ...] = ()
    if mode != "FPV":
        keyframes, track = _author_camera(mode, canon["camera"], recipe, path)
        total_ms = (recipe.demo.window_end_us
                    - recipe.demo.window_start_us) // 1000
        keyframes = _cover_window(keyframes, total_ms)

    placement, music_path = _resolve_music(canon["music"])
    return PreviewPlan(
        frag_id=int(frag["id"]), demo_name=str(frag["demo_name"]),
        demo_sha256=str(frag.get("content_hash") or ""),
        demo_path=str(demo_path or ""), recipe=recipe, draft=canon,
        keyframes=keyframes, camera_mode=mode, camera_fallback=fallback,
        subject_track=track, map_name=str(frag.get("map") or ""),
        music=placement, music_path=music_path)


def _author_camera(mode: str, camera: dict[str, Any], recipe: SceneRecipeV2,
                   path: dict | None
                   ) -> tuple[tuple[dict[str, Any], ...],
                              tuple[tuple[float, float, float, float], ...]]:
    """Authored (sparse) keyframes for one camera mode, in shot-relative ms.

    Shot-relative because ``compile_dense_camera`` adds ``base_servertime``
    back; keeping authoring relative means the same arc is reusable at any
    demo time. Uses ONLY the existing analytic generators in
    ``camera_paths.py`` — this module invents no camera maths.
    """
    base_ms = recipe.demo.window_start_us // 1000
    impact_us = next(a.resolved_demo_us for a in recipe.anchors
                     if a.anchor_id == "impact-0")
    impact_rel = impact_us // 1000 - base_ms
    total_ms = (recipe.demo.window_end_us - recipe.demo.window_start_us) // 1000
    fov = float(camera.get("fov", 90.0))
    distance = float(camera.get("distance", 220.0))
    height = float(camera.get("height", 64.0))

    impact_pos = tuple(float(v) for v in (path or {}).get("impact", {})
                       .get("pos", (0.0, 0.0, 0.0)))
    track: list[tuple[float, float, float, float]] = []
    if path and path.get("points"):
        launch_t = int((path.get("launch") or {}).get("t", impact_us // 1000))
        track = [(launch_t - base_ms + t_rel, x, y, z)
                 for t_rel, x, y, z in path["points"]]

    if mode == "PROJECTILE" and track:
        flight = camera_paths.projectile_follow(track, distance, fov=fov)
        # Ride the rocket, then orbit the impact for the rest of the window.
        tail_ms = max(200.0, total_ms - impact_rel)
        orbit = camera_paths.orbit(
            impact_pos, radius=max(120.0, distance), height=height,
            arc_deg=105.0, duration_ms=tail_ms, t0_ms=float(impact_rel),
            start_deg=_approach_bearing(track), fov=fov)
        return tuple(flight + orbit[1:]), tuple(track)
    if mode == "SIDE" and track:
        # FIXED POINT beside and above the launch, perpendicular to the
        # initial flight direction, tracking the rocket with look-at and
        # holding on the impact for the tail. The shooter stands at the
        # launch point, so they are in frame as the shot leaves -- the
        # "curved angle from a fixed point" the review asked for. A static
        # position also has no path to clip; only the point itself must be
        # clear, which pre-flight checks per side. side_offset picks the
        # side (sign) and shifts along the flight (behind < 0 < ahead).
        d0 = camera_paths.track_direction(track, 0)
        perp = (-d0[1], d0[0], 0.0)
        n = (perp[0] ** 2 + perp[1] ** 2) ** 0.5 or 1.0
        perp = (perp[0] / n, perp[1] / n, 0.0)
        side = 1.0 if float(camera.get("side_offset", 1.0)) >= 0 else -1.0
        along = abs(float(camera.get("side_offset", 0.0)))
        lx, ly, lz = track[0][1], track[0][2], track[0][3]
        pos = (lx + side * perp[0] * distance - d0[0] * along,
               ly + side * perp[1] * distance - d0[1] * along,
               lz + height)
        kfs = [{"t_ms": float(t_ms), "pos": pos,
                "angles": camera_paths.look_at_angles(pos, (x, y, z)),
                "fov": fov} for t_ms, x, y, z in track]
        end_ms = float(total_ms)
        if end_ms > kfs[-1]["t_ms"]:
            kfs.append({"t_ms": end_ms, "pos": pos,
                        "angles": camera_paths.look_at_angles(pos, impact_pos),
                        "fov": fov})
        return tuple(kfs), tuple(track)
    if mode == "CHASE" and track:
        chase = camera_paths.chase(track, distance, up=height, fov=fov)
        tail_ms = max(200.0, total_ms - impact_rel)
        orbit = camera_paths.orbit(
            impact_pos, radius=max(120.0, distance), height=height,
            arc_deg=70.0, duration_ms=tail_ms, t0_ms=float(impact_rel),
            start_deg=_approach_bearing(track), fov=fov)
        return tuple(chase + orbit[1:]), tuple(track)
    if mode == "FREECAM":
        # A slow push-in on the impact: the least opinionated moving camera.
        near = camera_paths.orbit(
            impact_pos, radius=max(80.0, distance), height=height,
            arc_deg=18.0, duration_ms=float(total_ms), t0_ms=0.0,
            start_deg=_approach_bearing(track), fov=fov)
        return tuple(near), tuple(track)
    # ORBIT (and anything that fell through to it)
    orbit = camera_paths.orbit(
        impact_pos, radius=distance, height=height, arc_deg=120.0,
        duration_ms=float(total_ms), t0_ms=0.0,
        start_deg=_approach_bearing(track), fov=fov)
    return tuple(orbit), tuple(track)


def _cover_window(keyframes: tuple[dict[str, Any], ...], total_ms: int,
                  guard_ms: int = GUARD_MS) -> tuple[dict[str, Any], ...]:
    """Extend the authored path to span the whole capture, GUARD INCLUDED.

    MEASURED ENGINE CONTRACT, 2026-09-01, found in two stages by looking at
    the delivered file rather than at rc=0.

    *Stage 1.* The first real preview capture came back 5.13 s long for an
    8.50 s TimeMap. A PROJECTILE arc is naturally authored over the rocket
    flight (relative 3375-8500 ms for the canary frag), so the path began
    3.375 s after the capture window did.

    *Stage 2.* Extending the path to ``0 .. total_ms`` produced a file of
    exactly the right length — and with the hero frag 500 ms early. The raw
    capture was 9.000 s, not the 9.500 s the guard implies, and the frag
    message's first frame landed at 4.000 s instead of 4.500 s.

    Both stages have ONE cause: **``playcamera`` seeks the demo to the camera
    path's first point.** Whatever ``video`` command was scheduled before that
    instant fires late, at the jump, and the head of the shot is silently
    lost. rc=0, nothing in ``qconsole.log``, a perfectly plausible-looking
    movie — the failure is only visible if you measure where the hero event
    actually lands.

    So the contract is not "cover the edit window", it is **cover everything
    the capture records, guard margin included**. Holding the first pose from
    ``-guard_ms`` and the last pose to ``total_ms + guard_ms`` satisfies it
    deterministically, and the held opening reads as a locked-off shot on the
    launch point before the ride begins.
    """
    if not keyframes:
        return keyframes
    kfs = sorted(keyframes, key=lambda k: k["t_ms"])
    lead, tail = -int(guard_ms), int(total_ms) + int(guard_ms)
    out = list(kfs)
    if kfs[0]["t_ms"] > lead:
        out.insert(0, {**kfs[0], "t_ms": lead})
    if kfs[-1]["t_ms"] < tail:
        out.append({**kfs[-1], "t_ms": tail})
    return tuple(out)


def _approach_bearing(track) -> float:
    """Enter the orbit on the bearing the projectile arrived from, +10 deg.

    Same reasoning as the canary: starting the arc where the action already
    is avoids a cut to an unmotivated angle, and 10 deg of lead keeps the
    first frames moving.
    """
    if not track or len(track) < 2:
        return 0.0
    (x0, y0), (x1, y1) = (track[0][1], track[0][2]), (track[-1][1], track[-1][2])
    return math.degrees(math.atan2(y1 - y0, x1 - x0)) + 10.0


# ---------------------------------------------------------------------------
# Camera artifact — deliberately a pure function of geometry
# ---------------------------------------------------------------------------

# Recovery ladder (ITEM B) — the minimum surviving coverage that makes
# retiming worth doing. Retiming stretches the move by 1/fraction, so at 0.5
# the camera performs the authored move at half speed: still a move, and a
# slow push reads as deliberate. Below 0.5 the stretch factor exceeds 2x and
# the shot degenerates into a near-static creep — trading a dead hold for a
# dead crawl is not a recovery, so below this bar the ladder changes MODE
# instead of changing the clock.
RETIME_MIN_FRACTION = 0.5


def build_camera_artifact(plan: PreviewPlan, gamedir: Path,
                          camera_name: str, tracer=None) -> dict[str, Any]:
    """Compile the plan's camera into a ``.cam10``, recovering from a
    coverage failure rather than delivering a dead hold.

    §38 architecture test: this consumes ``plan.keyframes`` /
    ``plan.recipe`` / ``plan.draft["backend"]`` and NOTHING about music. Two
    plans that differ only in ``MusicPlacement`` therefore produce a
    byte-identical ``.cam10`` and an identical ``cam10_hash`` — which is the
    proof that the audio path and the video path are genuinely independent,
    not merely believed to be.

    THE RECOVERY LADDER. Collision can return SHORTENED — a clean prefix
    survives and the rest is discarded — but nothing shortens the CAPTURE, so
    the engine reaches the last camera point and holds it. When
    ``classify_coverage`` says that hold is ``PARTIAL_BAD`` (or the path is
    unusable outright), the rungs are tried in order and the FIRST acceptable
    one ships:

      0. **As authored.** Accepted when coverage is FULL or PARTIAL_OK.
      1. **Retime the survivor across the whole scene.** Cheapest and most
         faithful: the surviving prefix is already proven clear at every
         position, and rescaling only its clock cannot make a clear position
         solid, so the retimed path needs no new geometric argument. Gated on
         ``RETIME_MIN_FRACTION``. Chosen over "push further out and retry"
         because ``adjust_path`` has ALREADY run its 25 repair iterations by
         the time we see SHORTENED — pushing again is re-running a search that
         just failed, and pushing further from the subject in Quake geometry
         is as likely to leave the level as to find air.
      2. **Fall back to ORBIT around the impact.** The existing fallback mode
         (``_usable_projectile`` / ``camera_fallback``), re-authored here from
         the subject track's last point. An orbit is authored over the whole
         window by construction and sits on a radius around the point the
         action already happened at, so it is a genuinely different path
         through the geometry rather than a retry of the failed one. Its own
         coverage is classified, and rung 1 is applied to it if needed.
      3. **Give up honestly.** Recompile rung 0 and return it with
         ``coverage`` intact and ``camera_fallback`` saying the hold could not
         be recovered. Never silently degraded: the caller records it.

    The returned dict carries ``camera_fallback`` (the plan's own fallback
    note, plus whatever the ladder did) and ``camera_recovery`` (the rung
    name), on top of every key ``compile_dense_camera`` returns.
    """
    fallback = plan.camera_fallback
    if not plan.keyframes:
        return {"backend": None, "status": "NO_CAMERA", "cam10_hash": None,
                "cfg_lines": [], "cam10_path": None, "used_sample_count": 0,
                "original_sample_count": 0,
                "coverage": camera_compiler_v2.COVERAGE_INVALID,
                "covered_ms": 0.0, "scene_ms": 0.0, "hold_ms": 0.0,
                "covered_fraction": 0.0,
                "camera_fallback": fallback, "camera_recovery": "NONE"}
    tracer = tracer if tracer is not None else _tracer_for(plan)
    total_ms = (plan.recipe.demo.window_end_us
                - plan.recipe.demo.window_start_us) // 1000

    def _compile(keyframes: list[dict[str, Any]]) -> dict[str, Any]:
        return camera_compiler_v2.compile_dense_camera(
            keyframes, plan.window_start_ms, Path(gamedir),
            camera_name, hz=camera_compiler_v2.CINEMATIC_HZ, tracer=tracer,
            subject_track=list(plan.subject_track) or None,
            backend=plan.draft.get("backend",
                                   cam10_writer.BACKEND_NATIVE_CAM10),
            # Coverage is judged over the EDIT window only. The guard margin
            # either side is trimmed away by transcode_trimmed(), so a path
            # that stops inside the tail guard costs the viewer nothing.
            scene_start_ms=0.0, scene_end_ms=float(total_ms))

    def _ok(res: dict[str, Any]) -> bool:
        return res.get("coverage") in (camera_compiler_v2.COVERAGE_FULL,
                                       camera_compiler_v2.COVERAGE_PARTIAL_OK)

    def _done(res: dict[str, Any], rung: str,
              note: str | None) -> dict[str, Any]:
        res["camera_recovery"] = rung
        res["camera_fallback"] = "; ".join(x for x in (fallback, note) if x) or None
        return res

    # Rung 0 — as authored.
    authored = list(plan.keyframes)
    result = _compile(authored)
    if _ok(result):
        return _done(result, "NONE", None)

    # Rung 1 — retime the survivor over the full authored span (guard
    # included: `_cover_window`'s engine contract still has to hold).
    survivors = list(result.get("final_keyframes") or [])
    if (len(survivors) >= 2
            and result.get("covered_fraction", 0.0) >= RETIME_MIN_FRACTION):
        retimed = camera_compiler_v2.retime_to_span(
            survivors, float(authored[0]["t_ms"]), float(authored[-1]["t_ms"]))
        candidate = _compile(retimed)
        if _ok(candidate):
            return _done(candidate, "RETIMED",
                         f"camera path shortened by geometry "
                         f"({result['hold_ms']:.0f} ms hold); the surviving "
                         f"{result['covered_fraction'] * 100:.0f}% was retimed "
                         f"across the full scene")

    # Rung 2 — different camera mode: ORBIT around where the action landed.
    if plan.camera_mode != "ORBIT" and plan.subject_track:
        orbit_kfs = _orbit_recovery_keyframes(plan, total_ms)
        if orbit_kfs:
            candidate = _compile(list(orbit_kfs))
            note = (f"{plan.camera_mode} path was shortened by geometry "
                    f"({result['hold_ms']:.0f} ms hold); fell back to ORBIT")
            if _ok(candidate):
                return _done(candidate, "ORBIT", note)
            survivors = list(candidate.get("final_keyframes") or [])
            if (len(survivors) >= 2
                    and candidate.get("covered_fraction", 0.0)
                    >= RETIME_MIN_FRACTION):
                retimed = camera_compiler_v2.retime_to_span(
                    survivors, float(orbit_kfs[0]["t_ms"]),
                    float(orbit_kfs[-1]["t_ms"]))
                candidate = _compile(retimed)
                if _ok(candidate):
                    return _done(candidate, "ORBIT_RETIMED",
                                 note + " and retimed")

    # Rung 3 — nothing recovered. Ship the authored path and say so; the
    # last _compile() left a DIFFERENT path on disk under this camera name,
    # so recompiling rung 0 is what keeps the .cam10 and the returned dict
    # describing the same shot.
    result = _compile(authored)
    return _done(result, "UNRECOVERED",
                 f"camera holds statically for {result['hold_ms']:.0f} ms of a "
                 f"{result['scene_ms']:.0f} ms scene; no recovery available")


def camera_status_line(camera: dict[str, Any]) -> str:
    """One human-readable line describing the delivered camera, for the
    ``camera_status`` column the panel reads back.

    Coverage and the recovery rung are included because a SHORTENED path that
    still covers the scene and a SHORTENED path that leaves a two-second dead
    hold used to be the same string. ``camera_fallback`` is appended verbatim
    when set — the rule is that the preview never silently degrades.
    """
    parts = [f"{camera.get('status')} "
             f"{camera.get('used_sample_count')}/"
             f"{camera.get('original_sample_count')}",
             f"cov={camera.get('coverage')}",
             f"hold={float(camera.get('hold_ms') or 0.0):.0f}ms"]
    rung = camera.get("camera_recovery")
    if rung and rung != "NONE":
        parts.append(f"recovery={rung}")
    note = camera.get("camera_fallback")
    if note:
        parts.append(str(note))
    return " ".join(parts)


def _orbit_recovery_keyframes(plan: PreviewPlan, total_ms: int
                              ) -> tuple[dict[str, Any], ...]:
    """An ORBIT path around the projectile's last known position.

    The recovery mode needs no cached path dict: the subject track IS the
    projectile point series, so its last point is the impact position that
    ``_author_camera`` would have used, and ``_approach_bearing`` gives the
    same entry angle. Same generator, same window coverage, same guard.
    """
    track = list(plan.subject_track)
    if len(track) < 2:
        return ()
    center = tuple(float(v) for v in track[-1][1:4])
    cam = plan.draft.get("camera") or {}
    orbit = camera_paths.orbit(
        center, radius=max(120.0, float(cam.get("distance", 220.0))),
        height=float(cam.get("height", 64.0)), arc_deg=120.0,
        duration_ms=float(total_ms), t0_ms=0.0,
        start_deg=_approach_bearing(track), fov=float(cam.get("fov", 90.0)))
    return _cover_window(tuple(orbit), total_ms)


def _tracer_for(plan: PreviewPlan):
    """BSP tracer for collision checking, or None when the map is unavailable.

    A missing tracer is not fatal — ``collision_check_dense`` treats None as
    "cannot check" and reports VALID — but it IS worth knowing about, so the
    plan records the map name and the manifest records whether a tracer was
    used.
    """
    if not plan.map_name:
        return None
    try:
        return camera_paths.bsp_tracer(plan.map_name)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Capture cfg
# ---------------------------------------------------------------------------

def build_capture_cfg(plan: PreviewPlan, camera_cfg_lines: list[str],
                      clip_name: str, fx_level: str) -> str:
    """The capture script, with ``baseline_lines()`` FIRST — always.

    Ordering is the whole point (§4 / pantheon_runtime). ``q3config.cfg``
    persists every ``CVAR_ARCHIVE`` the last session touched; the canary
    found ``cg_drawCameraPath`` defaulting to 1 and rendering wolfcam's own
    path-editing overlay into an otherwise perfect capture, with rc=0 and
    nothing in any log. The reset must precede the profile, the camera and
    the video command, or it resets nothing that matters.
    """
    overrides = {
        "cg_fxfile": (pantheon_fx.SCRIPT_NAME if fx_level != "OFF" else ""),
        "mme_saveDepth": "1" if plan.draft["look"]["show_depth"] else "0",
    }
    if os.getenv("CS_PREVIEW_ENGINE_LOG"):
        # Diagnostic hook only. The baseline keeps logfile at 0 for master
        # captures; turning it on is how a failed capture gets investigated.
        overrides["logfile"] = "2"
    lines = list(pantheon_runtime.baseline_lines(overrides))
    profile = presentation.validate(plan.camera_mode,
                                    presentation.profile_for(plan.camera_mode))
    lines.append(f"exec {master_profile._CFG_FILES[profile]}")
    fov = plan.draft["camera"].get("fov")
    if fov is not None:
        lines.append(f"seta cg_fov {float(fov):.1f}")

    start_ms = plan.window_start_ms - GUARD_MS
    stop_ms = plan.window_end_ms + GUARD_MS
    name = wolfcam_capture._validate_cfg_token(clip_name)
    lines.append(f"seekservertime {start_ms - wolfcam_capture.SEEK_SETTLE_MS}")
    lines.extend(camera_cfg_lines)
    lines.append(f"at {start_ms} video avi name {name}")
    lines.append(f"at {stop_ms} stopvideo")
    lines.append(f"at {stop_ms + wolfcam_capture.INTER_WINDOW_MS} quit")
    return "\n".join(lines) + "\n"


def _fx_level(plan: PreviewPlan) -> str:
    """One fx script per capture; the strongest requested level wins."""
    order = {"OFF": 0, "SUBTLE": 1, "HERO": 2}
    return max(plan.draft["fx"].values() or ["OFF"], key=lambda v: order[v])


# ---------------------------------------------------------------------------
# ffmpeg helpers
# ---------------------------------------------------------------------------

def _run_ffmpeg(args: list[str], timeout: int = 900) -> None:
    proc = subprocess.Popen([str(FFMPEG), "-y", "-loglevel", "error", *args],
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        _, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        # CS-4 cascade: terminate -> wait(3) -> kill -> wait.
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except (subprocess.TimeoutExpired, OSError):
            try:
                proc.kill()
                proc.wait(timeout=10)
            except (subprocess.TimeoutExpired, OSError):
                pass
        raise RuntimeError(f"ffmpeg timeout after {timeout}s")
    if proc.returncode != 0:
        raise RuntimeError(
            f"ffmpeg rc={proc.returncode}: "
            f"{(err or b'')[:400].decode(errors='replace')}")


def probe_duration_s(path: Path) -> float:
    out = subprocess.run(
        [str(FFPROBE), "-v", "error", "-select_streams", "v:0",
         "-show_entries", "format=duration:stream=nb_frames,duration",
         "-of", "json", str(path)],
        capture_output=True, timeout=120)
    data = json.loads(out.stdout or b"{}")
    stream = (data.get("streams") or [{}])[0]
    frames = stream.get("nb_frames")
    if frames not in (None, "N/A"):
        try:
            return int(frames) / float(FPS)
        except (TypeError, ValueError):
            pass
    for source in (stream, data.get("format") or {}):
        value = source.get("duration")
        if value not in (None, "N/A"):
            return float(value)
    return 0.0


def transcode_trimmed(src: Path, dst: Path, *, skip_s: float, duration_s: float,
                      music_path: str | None = None,
                      music_start_s: float = 0.0,
                      game_volume: float = GAME_AUDIO_VOLUME) -> None:
    """The trim contract, executed (timewarp_measurement.md).

    ``-ss`` BEFORE ``-i`` on the source seeks to the guard boundary; ``-t``
    after it takes exactly the TimeMap's edit duration. The captured file's
    own length is never consulted — that is precisely the number measurement
    showed is not authoritative (+/-1 video frame, up to ~150 ms of
    non-deterministic trailing audio).

    Music, when present, is mixed at ONE FIXED LEVEL (P1-G v6): no sidechain,
    no level following, ``normalize=0`` so amix cannot quietly re-gain either
    input. The video filter graph is byte-identical with and without music.
    """
    args = ["-ss", f"{skip_s:.6f}", "-t", f"{duration_s:.6f}", "-i", str(src)]
    if music_path:
        args += ["-ss", f"{music_start_s:.6f}", "-t", f"{duration_s:.6f}",
                 "-i", str(music_path)]
        args += ["-filter_complex",
                 _mix_graph(duration_s, game_volume),
                 "-map", "0:v:0", "-map", "[a]"]
    else:
        args += ["-map", "0:v:0", "-map", "0:a:0?"]
        if game_volume != 1.0:
            args += ["-af", f"volume={game_volume}"]
    args += [
        "-vf", f"scale={PREVIEW_WIDTH}:{PREVIEW_HEIGHT}:flags=lanczos",
        "-r", str(FPS), "-vsync", "cfr",
        "-c:v", "libx264", "-preset", PREVIEW_PRESET, "-crf", PREVIEW_CRF,
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", AUDIO_BITRATE, "-shortest", str(dst),
    ]
    _run_ffmpeg(args)


def _mix_graph(duration_s: float, game_volume: float) -> str:
    """The ONE fixed-level mix (P1-G v6): no sidechain, no level following."""
    return (f"[0:a]volume={game_volume}[g];"
            f"[1:a]volume={MUSIC_VOLUME},"
            f"afade=t=in:st=0:d=0.25,"
            f"afade=t=out:st={max(0.0, duration_s - 0.35):.3f}:d=0.35[m];"
            f"[g][m]amix=inputs=2:duration=first:normalize=0[a]")


def has_audio(path: Path) -> bool:
    out = subprocess.run(
        [str(FFPROBE), "-v", "error", "-select_streams", "a",
         "-show_entries", "stream=index", "-of", "json", str(path)],
        capture_output=True, timeout=120)
    try:
        return bool((json.loads(out.stdout or b"{}").get("streams") or []))
    except ValueError:
        return False


def mux_preview_audio(visual_mp4: Path, dst: Path, *, duration_s: float,
                      music_path: str | None = None,
                      music_start_s: float = 0.0) -> None:
    """Stage 2: the cheap half. Music onto an existing capture, VIDEO COPIED.

    ``-c:v copy`` is what makes a music-only change cheap: not one frame is
    decoded or re-encoded, so the delivered mp4 carries EXACTLY the pixels of
    the cached capture and the whole cost is a short AAC pass. The video
    stream is bit-identical across every music placement of one capture —
    the disk-level counterpart of the §38 ``.cam10`` argument.
    """
    args: list[str] = ["-i", str(visual_mp4)]
    game_audio = has_audio(visual_mp4)
    if music_path and game_audio:
        args += ["-ss", f"{music_start_s:.6f}", "-t", f"{duration_s:.6f}",
                 "-i", str(music_path),
                 "-filter_complex", _mix_graph(duration_s, GAME_AUDIO_VOLUME),
                 "-map", "0:v:0", "-map", "[a]"]
    elif music_path:
        args += ["-ss", f"{music_start_s:.6f}", "-t", f"{duration_s:.6f}",
                 "-i", str(music_path),
                 "-filter_complex",
                 f"[1:a]volume={MUSIC_VOLUME},"
                 f"afade=t=in:st=0:d=0.25,"
                 f"afade=t=out:st={max(0.0, duration_s - 0.35):.3f}:d=0.35[a]",
                 "-map", "0:v:0", "-map", "[a]"]
    else:
        args += ["-map", "0:v:0", "-map", "0:a:0?"]
        if game_audio and GAME_AUDIO_VOLUME != 1.0:
            args += ["-af", f"volume={GAME_AUDIO_VOLUME}"]
    args += ["-c:v", "copy", "-c:a", "aac", "-b:a", AUDIO_BITRATE,
             "-movflags", "+faststart", "-shortest", str(dst)]
    _run_ffmpeg(args)


# ---------------------------------------------------------------------------
# Generations (§12) — the guard that makes overlapping jobs safe
# ---------------------------------------------------------------------------

def next_generation(frag_id: int) -> int:
    """Allocate this frag's next generation. Monotonic, never reused."""
    with _gen_mutex:
        con = _conn()
        try:
            con.execute(
                "INSERT INTO director_preview_generations "
                "(frag_id, latest_generation) VALUES (?, 1) "
                "ON CONFLICT(frag_id) DO UPDATE SET "
                "latest_generation = latest_generation + 1",
                (int(frag_id),))
            con.commit()
            return int(con.execute(
                "SELECT latest_generation FROM director_preview_generations "
                "WHERE frag_id = ?", (int(frag_id),)).fetchone()[0])
        finally:
            con.close()


def latest_generation(frag_id: int) -> int:
    con = _conn()
    try:
        row = con.execute(
            "SELECT latest_generation FROM director_preview_generations "
            "WHERE frag_id = ?", (int(frag_id),)).fetchone()
    finally:
        con.close()
    return int(row[0]) if row else 0


def current_preview(frag_id: int) -> dict[str, Any] | None:
    """The frag's published preview — the one the panel should be showing."""
    con = _conn()
    try:
        row = con.execute(
            "SELECT current_key, current_generation "
            "FROM director_preview_generations WHERE frag_id = ?",
            (int(frag_id),)).fetchone()
    finally:
        con.close()
    if not row or not row[0]:
        return None
    return {"preview_key": row[0], "generation": int(row[1])}


def _publish(frag_id: int, preview_key: str, generation: int) -> bool:
    """Advance the frag's current preview — ONLY forwards (§12).

    This is the whole guard in three lines of SQL. Request A (generation 1)
    can legitimately finish after request B (generation 2): its artifact is
    cached under its own key and can be served if asked for by key, but the
    ``WHERE current_generation < ?`` clause means it can never take the
    frag's current pointer back to the older draft.
    """
    with _gen_mutex:
        con = _conn()
        try:
            cur = con.execute(
                "UPDATE director_preview_generations "
                "SET current_key = ?, current_generation = ? "
                "WHERE frag_id = ? AND current_generation < ?",
                (preview_key, int(generation), int(frag_id), int(generation)))
            con.commit()
            return cur.rowcount > 0
        finally:
            con.close()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _row(preview_key: str) -> dict[str, Any] | None:
    con = _conn()
    try:
        row = con.execute("SELECT * FROM director_previews WHERE preview_key = ?",
                          (preview_key,)).fetchone()
    finally:
        con.close()
    return dict(row) if row else None


def _set_state(preview_key: str, state: str, *, error: str | None = None,
               mp4_path: str | None = None,
               camera_artifact: str | None = None,
               camera_status: str | None = None) -> None:
    con = _conn()
    try:
        sets = ["state = ?", "updated_at = ?"]
        params: list[Any] = [state, _now()]
        if error is not None or state == STATE_FAILED:
            sets.append("error = ?")
            params.append(error)
        if mp4_path is not None:
            sets.append("mp4_path = ?")
            params.append(mp4_path)
        if camera_artifact is not None:
            sets.append("camera_artifact = ?")
            params.append(camera_artifact)
        if camera_status is not None:
            # VALID / PUSHED_OUT / SHORTENED — recorded because a SHORTENED
            # path still renders a plausible movie whose second half is a
            # locked-off hold on the last clear sample. That is a real
            # limitation of the delivered shot, not an error, and it must be
            # discoverable after the fact.
            sets.append("camera_status = ?")
            params.append(camera_status)
        params.append(preview_key)
        con.execute(f"UPDATE director_previews SET {', '.join(sets)} "
                    "WHERE preview_key = ?", params)
        con.commit()
    finally:
        con.close()


def _artifact_is_sound(mp4: Path, edit_duration_us: int) -> bool:
    """A cached artifact is only reusable if it is still on disk AND still the
    right length.

    The length check is not paranoia. The first real capture of this pipeline
    produced a 5.13 s file for an 8.50 s TimeMap (see ``_cover_window``) and
    cached it as READY; without this check the cache would have kept serving a
    truncated shot for as long as the key stayed the same. The TimeMap is the
    authority for duration everywhere else in this module, so it is the
    authority here too.
    """
    if not mp4.exists():
        return False
    try:
        actual = probe_duration_s(mp4)
    except Exception:
        return False
    return abs(actual - edit_duration_us / 1_000_000.0) <= 2.0 / FPS


# ---------------------------------------------------------------------------
# Visual artifact cache — bounded, LRU, crash-safe
#
# One row per CAPTURE, not per delivered preview. A music-only change makes a
# new preview_key and a new mp4 but reuses this artifact untouched, which is
# the entire point of splitting the key.
# ---------------------------------------------------------------------------

# Visual keys of jobs currently in flight in THIS process. A capture that is
# being written, or is about to be read by an assembly step, must never be
# evicted out from under its job — the DB state alone cannot express "some
# thread is holding this path", so the pin set does.
_pinned_visual: dict[str, int] = {}
_pin_mutex = threading.Lock()


def visual_dir() -> Path:
    """Resolved at call time so a test monkeypatching PREVIEW_DIR moves this."""
    return PREVIEW_DIR / "visual"


def _pin_visual(visual_key: str) -> None:
    with _pin_mutex:
        _pinned_visual[visual_key] = _pinned_visual.get(visual_key, 0) + 1


def _unpin_visual(visual_key: str) -> None:
    with _pin_mutex:
        left = _pinned_visual.get(visual_key, 0) - 1
        if left > 0:
            _pinned_visual[visual_key] = left
        else:
            _pinned_visual.pop(visual_key, None)


def _pinned_keys() -> set[str]:
    """Keys eviction must skip: pinned in-process, or claimed by a queued job.

    The in-process pin covers a job that is running RIGHT NOW; the DB half
    covers a job that is queued behind the capture lock in this process and
    has not reached ``_generate`` yet. Both are "in flight" for the purposes
    of §12's generation guard, and neither may lose its capture.
    """
    with _pin_mutex:
        pinned = set(_pinned_visual)
    con = _conn()
    try:
        rows = con.execute(
            "SELECT DISTINCT visual_key FROM director_previews "
            "WHERE visual_key IS NOT NULL AND state IN (?,?,?)",
            (STATE_QUEUED, STATE_CAPTURING, STATE_TRIMMING)).fetchall()
    finally:
        con.close()
    return pinned | {str(r[0]) for r in rows}


def visual_hit(visual_key: str, edit_duration_us: int) -> dict[str, Any] | None:
    """A reusable capture for this key, or None. Records the LRU touch.

    "Least recently USED" is what the budget evicts on, so the touch happens
    here — on the read that makes an artifact useful — never on creation.
    """
    now = _now()
    con = _conn()
    try:
        row = con.execute(
            "SELECT * FROM director_visual_artifacts "
            "WHERE visual_key = ? AND state = ?",
            (visual_key, STATE_READY)).fetchone()
        if row is None:
            return None
        path = Path(str(row["path"]))
        if not _artifact_is_sound(path, int(edit_duration_us)):
            return None
        con.execute("UPDATE director_visual_artifacts SET last_used_at = ? "
                    "WHERE visual_key = ?", (now, visual_key))
        con.commit()
        return {**dict(row), "path": path}
    finally:
        con.close()


def register_visual(visual_key: str, path: Path, edit_duration_us: int, *,
                    camera_artifact: str | None = None,
                    camera_status: str | None = None) -> None:
    """Publish a freshly captured artifact as READY.

    Called only AFTER the atomic ``tmp.replace(final)``, so a row that says
    READY always refers to a fully written file.
    """
    now = _now()
    con = _conn()
    try:
        con.execute(
            "INSERT INTO director_visual_artifacts (visual_key, state, path,"
            " bytes, edit_duration_us, camera_artifact, camera_status,"
            " created_at, last_used_at) VALUES (?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(visual_key) DO UPDATE SET state = excluded.state,"
            " path = excluded.path, bytes = excluded.bytes,"
            " edit_duration_us = excluded.edit_duration_us,"
            " camera_artifact = excluded.camera_artifact,"
            " camera_status = excluded.camera_status,"
            " last_used_at = excluded.last_used_at",
            (visual_key, STATE_READY, str(path),
             path.stat().st_size if path.exists() else 0,
             int(edit_duration_us), camera_artifact, camera_status, now, now))
        con.commit()
    finally:
        con.close()


def _evict_visual(visual_key: str, path: Path) -> bool:
    """Remove one artifact. CRASH-SAFE, in that order and for that reason.

    1. flip the row to EVICTING and COMMIT. From this instant no reader can
       see the artifact as usable — ``visual_hit`` selects on
       ``state = READY`` — so a crash here loses a capture but can never
       serve a half-deleted one.
    2. unlink the file.
    3. delete the row.

    A crash between 1 and 2 leaves an EVICTING row plus a file: not readable,
    and swept on the next budget pass. Between 2 and 3: an EVICTING row with
    no file, same outcome. The dangerous ordering — unlink first, then update
    — is exactly what this avoids, because it would leave a READY row
    pointing at nothing for as long as the process stayed up.
    """
    con = _conn()
    try:
        changed = con.execute(
            "UPDATE director_visual_artifacts SET state = ? "
            "WHERE visual_key = ? AND state = ?",
            (STATE_EVICTING, visual_key, STATE_READY)).rowcount
        con.commit()
        if not changed:
            return False            # someone else got there first
    finally:
        con.close()
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        return False                # still EVICTING; retried next pass
    con = _conn()
    try:
        con.execute("DELETE FROM director_visual_artifacts WHERE visual_key = ?",
                    (visual_key,))
        con.commit()
    finally:
        con.close()
    return True


def _sweep_visual_dir() -> None:
    """Delete files in the visual dir that no READY row claims.

    Covers both crash residue (an EVICTING row's file, a ``.tmp.mp4`` from a
    capture that died mid-transcode) and rows deleted by hand. Scoped to
    ``visual_dir()`` and to that directory alone — nothing outside the cache
    is ever removed.
    """
    directory = visual_dir()
    if not directory.exists():
        return
    con = _conn()
    try:
        keep = {str(r[0]) for r in con.execute(
            "SELECT path FROM director_visual_artifacts WHERE state = ?",
            (STATE_READY,))}
        stale_rows = [(str(r[0]), str(r[1])) for r in con.execute(
            "SELECT visual_key, path FROM director_visual_artifacts "
            "WHERE state = ?", (STATE_EVICTING,))]
    finally:
        con.close()
    for entry in directory.glob("*.mp4"):
        if str(entry) in keep:
            continue
        try:
            entry.unlink(missing_ok=True)
        except OSError:
            pass
    for visual_key, _path in stale_rows:
        con = _conn()
        try:
            con.execute("DELETE FROM director_visual_artifacts "
                        "WHERE visual_key = ? AND state = ?",
                        (visual_key, STATE_EVICTING))
            con.commit()
        finally:
            con.close()


def visual_cache_usage() -> dict[str, Any]:
    con = _conn()
    try:
        row = con.execute(
            "SELECT COUNT(*) AS n, COALESCE(SUM(bytes), 0) AS b "
            "FROM director_visual_artifacts WHERE state = ?",
            (STATE_READY,)).fetchone()
    finally:
        con.close()
    return {"artifacts": int(row["n"]), "bytes": int(row["b"]),
            "budget_bytes": VISUAL_CACHE_BUDGET_BYTES}


def enforce_visual_budget(budget_bytes: int | None = None) -> list[str]:
    """Evict least-recently-USED captures until the cache fits its budget.

    Ordering is ``last_used_at`` ASC — the artifact nobody has asked for in
    the longest time goes first. NOT ``created_at``: the capture a user keeps
    A/B-ing against is often the oldest one they made, and evicting it because
    of its birthday would throw away the single most valuable entry in the
    cache. Pinned (in-flight) keys are skipped, never evicted.
    """
    budget = (VISUAL_CACHE_BUDGET_BYTES if budget_bytes is None
              else int(budget_bytes))
    _sweep_visual_dir()
    pinned = _pinned_keys()
    con = _conn()
    try:
        rows = [dict(r) for r in con.execute(
            "SELECT visual_key, path, bytes FROM director_visual_artifacts "
            "WHERE state = ? ORDER BY last_used_at ASC, created_at ASC",
            (STATE_READY,))]
    finally:
        con.close()
    total = sum(int(r["bytes"]) for r in rows)
    evicted: list[str] = []
    for row in rows:
        if total <= budget:
            break
        if row["visual_key"] in pinned:
            continue
        if _evict_visual(str(row["visual_key"]), Path(str(row["path"]))):
            total -= int(row["bytes"])
            evicted.append(str(row["visual_key"]))
    return evicted


# ---------------------------------------------------------------------------
# Public API (continued)
# ---------------------------------------------------------------------------

# A job may sit in an in-flight state for this long with NO live lock holder
# before it is considered orphaned. Long enough for a slow capture to be
# between lock releases; short enough that a dead process is noticed.
ORPHAN_AFTER_S = 120.0


def _in_flight_is_orphaned(existing: dict[str, Any]) -> bool:
    """True when the row says in-flight but nobody is actually doing it.

    Recovery gap found 2026-09-01: a capturing process died mid-job, left
    the row CAPTURING and the lock file holding a dead PID, and every later
    request_preview re-stamped the row instead of re-queuing.
    """
    if LOCK_PATH.exists():
        try:
            pid = int(LOCK_PATH.read_text().strip() or 0)
        except (OSError, ValueError):
            pid = 0
        if pid and pid != os.getpid():
            from creative_suite.engine.process_liveness import process_alive
            return not process_alive(pid)
        if pid == os.getpid():
            return False
    try:
        updated = datetime.fromisoformat(str(existing.get("updated_at")))
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - updated).total_seconds()
    except (TypeError, ValueError):
        return False
    return age > ORPHAN_AFTER_S


def request_preview(frag: dict[str, Any], draft: dict[str, Any],
                    demo_path: str | None = None) -> dict[str, Any]:
    """POST handler body: queue (or reuse) a preview for this exact draft.

    Every call allocates a NEW generation even when the artifact is reused,
    because "what the user is currently asking to see" is a different fact
    from "what has been rendered". Reuse then publishes immediately: a
    cache hit is a completed request, not a pending one.
    """
    plan_recipe = build_preview_recipe(frag)
    edit_us = (plan_recipe.time_map[-1].edit_end_us
               - plan_recipe.time_map[0].edit_start_us)
    identity = dict(frag_id=int(frag["id"]),
                    demo_sha256=str(frag.get("content_hash") or ""),
                    demo_name=str(frag["demo_name"]),
                    recipe_id=plan_recipe.recipe_id,
                    edit_duration_us=edit_us, draft=draft)
    visual_key, assembly_key = compute_preview_keys(**identity)
    key = compute_preview_key(**identity)
    generation = next_generation(int(frag["id"]))
    music = canonical_music(draft.get("music"))

    con = _conn()
    try:
        row = con.execute("SELECT * FROM director_previews WHERE preview_key = ?",
                          (key,)).fetchone()
        existing = dict(row) if row else None
        ready = bool(existing and existing["state"] == STATE_READY
                     and existing["mp4_path"]
                     and _artifact_is_sound(Path(str(existing["mp4_path"])),
                                            edit_us))
        state = STATE_READY if ready else STATE_QUEUED
        orphaned = bool(existing and not ready
                        and existing["state"] in (STATE_QUEUED, STATE_CAPTURING,
                                                  STATE_TRIMMING)
                        and _in_flight_is_orphaned(existing))
        if existing and not ready and existing["state"] in (
                STATE_QUEUED, STATE_CAPTURING, STATE_TRIMMING):
            if orphaned:
                # The process that was capturing this died (dead lock PID,
                # or nothing holds the lock and the row is stale). Re-queue
                # rather than re-stamp forever; the old path never retried.
                state = STATE_QUEUED
            else:
                state = existing["state"]     # already in flight; just re-stamp
        now = _now()
        con.execute(
            "INSERT INTO director_previews (preview_key, frag_id, generation,"
            " state, error, mp4_path, recipe_id, camera_artifact,"
            " music_track_hash, edit_duration_us, created_at, updated_at,"
            " visual_key, assembly_key, last_used_at)"
            " VALUES (?,?,?,?,NULL,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(preview_key) DO UPDATE SET "
            " generation = MAX(generation, excluded.generation),"
            " state = excluded.state, updated_at = excluded.updated_at,"
            " visual_key = excluded.visual_key,"
            " assembly_key = excluded.assembly_key,"
            " last_used_at = excluded.last_used_at",
            (key, int(frag["id"]), generation, state,
             existing["mp4_path"] if existing else None,
             plan_recipe.recipe_id,
             existing["camera_artifact"] if existing else None,
             music["track_hash"] if music else None, edit_us, now, now,
             visual_key, assembly_key, now))
        con.commit()
    finally:
        con.close()

    if state == STATE_READY:
        _publish(int(frag["id"]), key, generation)
        return {"preview_key": key, "generation": generation,
                "state": STATE_READY, "reused": True,
                "visual_capture_key": visual_key,
                "preview_assembly_key": assembly_key,
                "visual_reused": True}
    if (existing and existing["state"] in (STATE_CAPTURING, STATE_TRIMMING)
            and not orphaned):
        return {"preview_key": key, "generation": generation,
                "state": existing["state"], "reused": False,
                "visual_capture_key": visual_key,
                "preview_assembly_key": assembly_key}
    _queue.put({"preview_key": key, "frag": copy.deepcopy(frag),
                "draft": copy.deepcopy(draft), "generation": generation,
                "demo_path": demo_path, "lock_waits": 0,
                "visual_key": visual_key, "assembly_key": assembly_key})
    _ensure_worker()
    return {"preview_key": key, "generation": generation,
            "state": STATE_QUEUED, "reused": False,
            "visual_capture_key": visual_key,
            "preview_assembly_key": assembly_key}


def get_preview(preview_key: str) -> dict[str, Any] | None:
    """GET handler body. ``stale`` is the panel's cue to keep waiting."""
    row = _row(preview_key)
    if row is None:
        return None
    state = str(row["state"])
    mp4 = row["mp4_path"]
    error = row["error"]
    if state == STATE_READY and (not mp4 or not Path(str(mp4)).exists()):
        state, error = STATE_FAILED, "cached preview mp4 missing on disk"
    return {
        "state": state,
        "generation": int(row["generation"]),
        "media_url": (f"/api/director/preview/{preview_key}/media"
                      if state == STATE_READY else None),
        "error": error,
        "stale": int(row["generation"]) < latest_generation(int(row["frag_id"])),
        "frag_id": int(row["frag_id"]),
        "recipe_id": row["recipe_id"],
        "camera_artifact": row["camera_artifact"],
        "camera_status": row["camera_status"],
        "edit_duration_us": row["edit_duration_us"],
    }


def media_path(preview_key: str) -> Path | None:
    row = _row(preview_key)
    if not row or row["state"] != STATE_READY or not row["mp4_path"]:
        return None
    path = Path(str(row["mp4_path"]))
    return path if path.exists() else None


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------

def _worker_loop() -> None:
    while True:
        job = _queue.get()
        if job is None:
            _queue.task_done()
            return
        try:
            if not review_proxy._try_acquire_lock():
                job["lock_waits"] = job.get("lock_waits", 0) + 1
                if job["lock_waits"] > _MAX_LOCK_WAITS:
                    _set_state(job["preview_key"], STATE_FAILED,
                               error="capture lock held too long")
                else:
                    time.sleep(_LOCK_RETRY_S)
                    _queue.put(job)
                continue
            try:
                _generate(job)
            finally:
                review_proxy._release_lock()
        except Exception as exc:      # the worker must never die
            _set_state(job["preview_key"], STATE_FAILED, error=str(exc)[:500])
        finally:
            _queue.task_done()


def _ensure_worker() -> None:
    global _worker
    with _worker_mutex:
        if _worker is None or not _worker.is_alive():
            _worker = threading.Thread(target=_worker_loop,
                                       name="director-preview-worker",
                                       daemon=True)
            _worker.start()


def drain_for_tests(timeout: float = 120.0) -> None:
    """Block until the queue is empty. Test hook only."""
    _ensure_worker()
    deadline = time.time() + timeout
    while not _queue.empty() and time.time() < deadline:
        time.sleep(0.02)
    _queue.join()


def _generate(job: dict[str, Any]) -> None:
    """Two stages, two keys, one delivered mp4.

    Stage 1 (EXPENSIVE, ``visual_capture_key``): wolfcam capture + guard trim
    + H.264, cached in ``visual_dir()`` and shared by every preview that
    differs from this one only in music.

    Stage 2 (CHEAP, ``preview_assembly_key``): mux the music onto that
    artifact with ``-c:v copy``. No frame is re-encoded, so a music-only
    change costs an audio pass and nothing else.
    """
    key = job["preview_key"]
    frag, draft = job["frag"], job["draft"]
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    visual_dir().mkdir(parents=True, exist_ok=True)
    plan = build_plan(frag, draft, demo_path=job.get("demo_path"))
    duration_s = plan.edit_duration_us / 1_000_000.0
    final_mp4 = PREVIEW_DIR / f"{key}.mp4"

    visual_key = job.get("visual_key") or compute_visual_capture_key(
        frag_id=plan.frag_id, demo_sha256=plan.demo_sha256,
        demo_name=plan.demo_name, recipe_id=plan.recipe.recipe_id,
        edit_duration_us=plan.edit_duration_us, draft=draft)
    visual_mp4 = visual_dir() / f"{visual_key}.mp4"

    # Pinned for the whole job: from here until the assembly has read it, this
    # artifact is in flight and the budget must not evict it.
    _pin_visual(visual_key)
    try:
        hit = visual_hit(visual_key, plan.edit_duration_us)
        if hit is not None:
            visual_mp4 = Path(hit["path"])
            camera_artifact = hit.get("camera_artifact")
            _set_state(key, STATE_TRIMMING,
                       camera_artifact=camera_artifact,
                       camera_status=hit.get("camera_status"))
        else:
            camera_artifact, camera_status = _capture_visual(
                job, plan, visual_mp4, duration_s)
            register_visual(visual_key, visual_mp4, plan.edit_duration_us,
                            camera_artifact=camera_artifact,
                            camera_status=camera_status)
            # The capture that was just made is also the most recently used.
            visual_hit(visual_key, plan.edit_duration_us)
        _assemble(key, plan, visual_mp4, final_mp4, duration_s)
    finally:
        _unpin_visual(visual_key)
    _finish(job, plan, final_mp4, camera_artifact=camera_artifact)
    enforce_visual_budget()


def _capture_visual(job: dict[str, Any], plan: PreviewPlan, visual_mp4: Path,
                    duration_s: float) -> tuple[str | None, str | None]:
    """Stage 1. Produce the music-free capture artifact at ``visual_mp4``.

    Written to ``<key>.tmp.mp4`` and ``replace``d into place, so the file a
    READY row points at is never a partial write.
    """
    key = job["preview_key"]
    tmp_visual = visual_mp4.with_name(visual_mp4.stem + ".tmp.mp4")
    if os.getenv("CS_PREVIEW_DIRECTOR_MOCK"):
        _set_state(key, STATE_CAPTURING)
        # A real (tiny) capture stand-in of the RAW length -- guard included,
        # non-deterministic tail and all -- so the trim step below is exercised
        # for real rather than skipped in mock mode.
        raw = PREVIEW_DIR / f"{key}.raw.avi"
        raw_s = duration_s + 2 * GUARD_MS / 1000.0 + 0.117
        _run_ffmpeg([
            "-f", "lavfi", "-i", f"testsrc=size=320x180:rate={FPS}",
            "-f", "lavfi", "-i", "sine=frequency=330",
            "-t", f"{raw_s:.3f}", "-c:v", "mjpeg", "-c:a", "pcm_s16le",
            str(raw)], timeout=180)
        _set_state(key, STATE_TRIMMING)
        try:
            transcode_trimmed(raw, tmp_visual, skip_s=GUARD_MS / 1000.0,
                              duration_s=duration_s, music_path=None,
                              game_volume=1.0)
            tmp_visual.replace(visual_mp4)
        finally:
            raw.unlink(missing_ok=True)
            tmp_visual.unlink(missing_ok=True)
        return _mock_camera_hash(plan), None
    return _real_capture(job, plan, tmp_visual, visual_mp4, duration_s)


def _assemble(key: str, plan: PreviewPlan, visual_mp4: Path, final_mp4: Path,
              duration_s: float) -> None:
    """Stage 2. The delivered mp4 = capture + music, video stream-copied.

    ``-c:v copy`` is the measurable half of the split: the captured frames are
    remuxed, never re-encoded, so the cost of changing music is one short
    audio pass regardless of how expensive the capture was.
    """
    _set_state(key, STATE_TRIMMING)
    tmp_mp4 = PREVIEW_DIR / f"{key}.tmp.mp4"
    try:
        mux_preview_audio(
            visual_mp4, tmp_mp4, duration_s=duration_s,
            music_path=plan.music_path,
            music_start_s=(plan.music.source_start_us / 1e6
                           if plan.music else 0.0))
        tmp_mp4.replace(final_mp4)
    finally:
        tmp_mp4.unlink(missing_ok=True)


def _mock_camera_hash(plan: PreviewPlan) -> str | None:
    """Mock mode still compiles a REAL .cam10 into a scratch dir.

    The camera compiler needs no engine, so mocking it away would mock away
    exactly the artifact the §38 architecture test is about. The bytes are
    real; only wolfcam is replaced.
    """
    if not plan.keyframes:
        return None
    scratch = PREVIEW_DIR / "_mock_cameras"
    scratch.mkdir(parents=True, exist_ok=True)
    result = build_camera_artifact(plan, scratch, f"prev_mock_{plan.frag_id}",
                                   tracer=None)
    return result.get("cam10_hash")


def _real_capture(job: dict[str, Any], plan: PreviewPlan, tmp_mp4: Path,
                  final_mp4: Path, duration_s: float
                  ) -> tuple[str | None, str | None]:
    """Run wolfcam and deliver the MUSIC-FREE visual artifact at ``final_mp4``.

    Returns ``(cam10_hash, camera_status)`` for the cache row. Music never
    reaches this function — that is the split, enforced by the signature.
    """
    key = job["preview_key"]
    staging = wolfcam_capture.ensure_install()
    gamedir = staging / "wolfcam-ql"
    demo_path = Path(plan.demo_path) if plan.demo_path else None
    if demo_path is None or not demo_path.exists():
        resolved, _hash = review_proxy.demo_source(plan.demo_name)
        demo_path = resolved
    if demo_path is None or not Path(demo_path).exists():
        raise PreviewBuildError(f"demo file not found: {plan.demo_name}")
    safe = wolfcam_capture.stage_demo(Path(demo_path))

    camera_name = f"prev_{key[:16]}"
    camera = build_camera_artifact(plan, gamedir, camera_name)
    if camera.get("status") == camera_compiler_v2.REJECTED:
        raise PreviewBuildError(
            "camera path is fully blocked by level geometry "
            f"({camera.get('collision_report')})")
    fx_level = _fx_level(plan)
    pantheon_fx.write_script(fx_level, gamedir)
    grade, packs_on = LOOK_POLICY[plan.draft["look"]["look"]]
    pantheon_grade.build_pack(grade, gamedir)
    moved = _set_texture_packs(gamedir, packs_on)

    clip_name = f"prev{key[:12]}"
    cfg = build_capture_cfg(plan, list(camera.get("cfg_lines") or []),
                            clip_name, fx_level)
    videos = gamedir / "videos"
    videos.mkdir(parents=True, exist_ok=True)
    for old in videos.glob(f"{clip_name}*.avi"):
        old.unlink()
    try:
        wolfcam_capture.write_engine_file(gamedir / "capture.cfg", cfg)
        wolfcam_capture.write_engine_file(gamedir / "cgamepostinit.cfg",
                                          "exec capture.cfg\n")
        _set_state(key, STATE_CAPTURING,
                   camera_artifact=camera.get("cam10_hash"),
                   camera_status=camera_status_line(camera))
        raw_s = duration_s + 2 * GUARD_MS / 1000.0
        timeout = (wolfcam_capture.LAUNCH_OVERHEAD_S
                   + raw_s * wolfcam_capture.CAPTURE_SLOWDOWN
                   + plan.window_start_ms / 1000.0 / 12.0)
        # ASK THE ONE AUTHORITY. A preview is user-triggered, so unlike the
        # review queue it has nothing to defer INTO -- it fails fast and
        # says why, rather than opening a window over a live game.
        from engine.pantheon import render_permit
        decision = render_permit.check(purpose="director preview")
        if not decision.may_render:
            raise PreviewBuildError(decision.reason)
        # And when it does run: minimized, not activated.
        from creative_suite.engine.capture_guard import (
            quiet_startup_info)
        proc = subprocess.Popen(
            wolfcam_capture.wolfcam_cmd(safe, staging), cwd=staging,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            startupinfo=quiet_startup_info())
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            wolfcam_capture._terminate_cascade(proc)
            raise PreviewBuildError(f"wolfcam capture TIMEOUT after {timeout:.0f}s")
        except BaseException:
            wolfcam_capture._terminate_cascade(proc)
            raise
        candidates = sorted(videos.glob(f"{clip_name}*.avi"))
        if not candidates:
            raise PreviewBuildError("wolfcam produced no AVI for this preview")
        avi = candidates[0]
        _set_state(key, STATE_TRIMMING)
        try:
            transcode_trimmed(avi, tmp_mp4, skip_s=GUARD_MS / 1000.0,
                              duration_s=duration_s, music_path=None,
                              game_volume=1.0)
            tmp_mp4.replace(final_mp4)
        finally:
            if os.getenv("CS_PREVIEW_KEEP_RAW"):
                # Diagnostic hook: the raw capture is what proves the trim
                # contract actually discarded a guard margin.
                shutil.copy2(avi, PREVIEW_DIR / f"{key}.raw.avi")
            avi.unlink(missing_ok=True)
            tmp_mp4.unlink(missing_ok=True)
    finally:
        # Staging hygiene, every time: capture.cfg deleted, the post-init hook
        # back to idle, grade pack removed, texture packs restored.
        _restore_texture_packs(moved)
        pantheon_grade.remove_pack(gamedir)
        (gamedir / "capture.cfg").unlink(missing_ok=True)
        wolfcam_capture.write_engine_file(gamedir / "cgamepostinit.cfg",
                                          "// idle\n")
    return camera.get("cam10_hash"), camera_status_line(camera)


def _finish(job: dict[str, Any], plan: PreviewPlan, mp4: Path,
            camera_artifact: str | None) -> None:
    _set_state(job["preview_key"], STATE_READY, mp4_path=str(mp4),
               camera_artifact=camera_artifact)
    # §12: publish only if this generation is still the newest to reach READY.
    # A stale job keeps its cached artifact and loses the pointer race, which
    # is exactly the intended outcome.
    _publish(plan.frag_id, job["preview_key"], int(job["generation"]))


def _set_texture_packs(gamedir: Path, enabled: bool) -> list[tuple[Path, Path]]:
    """Move ``zzz_uhd_*.pk3`` aside for the ORIGINAL look. Never deletes."""
    moved: list[tuple[Path, Path]] = []
    if enabled:
        for disabled in Path(gamedir).glob("zzz_uhd_*.pk3.disabled"):
            disabled.rename(disabled.with_suffix(""))
        return moved
    for pack in sorted(Path(gamedir).glob("zzz_uhd_*.pk3")):
        aside = pack.with_name(pack.name + ".disabled")
        shutil.move(str(pack), str(aside))
        moved.append((aside, pack))
    return moved


def _restore_texture_packs(moved: list[tuple[Path, Path]]) -> None:
    for aside, original in moved:
        try:
            if aside.exists():
                shutil.move(str(aside), str(original))
        except OSError:
            pass
