"""Seed data for the cinematic effect database (mandate presets).

16 effect presets + 16 recipes (ordered timelines of named actions),
10 camera recipes, 8 audio effects. seed(conn) is idempotent: upsert by
name, version bumped only when a payload actually changes.

Timeline steps are dicts {"t_rel_ms": int, "action": str, "params": dict}
where t_rel_ms is relative to the frag moment (negative = before the kill).
Named actions: slow_to, freeze, reverse, resume, cut_to_camera, zoom_target,
overlay_enemy_count, health_pulse, feed_freeze, duck_music, play_audio,
color_grade, hud_hide, hud_show, speed_to, track_projectile.
"""
from __future__ import annotations

import sqlite3

from creative_suite.database import cinematic_db as cdb

CA_MODES = ["CA"]
ALL_MODES: list[str] = []  # empty = no gating


def _step(t_rel_ms: int, action: str, **params) -> dict:
    return {"t_rel_ms": t_rel_ms, "action": action, "params": params}


# ---------------------------------------------------------------- cameras

CAMERA_RECIPES = [
    {"name": "ORBIT_SLOW_180", "kind": "orbit",
     "params": {"degrees": 180, "duration_ms": 2000, "radius_units": 180,
                "height_offset": 32}},
    {"name": "ORBIT_HERO_360", "kind": "orbit",
     "params": {"degrees": 360, "duration_ms": 3000, "radius_units": 220,
                "height_offset": 48}},
    {"name": "FOLLOW_BEHIND", "kind": "follow",
     "params": {"distance_units": 140, "height_offset": 40, "lag_ms": 120}},
    {"name": "SIDE_TRACK_FAST", "kind": "side_track",
     "params": {"distance_units": 200, "speed_match": True}},
    {"name": "VERTICAL_ORBIT_RISE", "kind": "vertical_orbit",
     "params": {"start_pitch": -10, "end_pitch": 55, "duration_ms": 2200}},
    {"name": "TOP_DOWN_TACTICAL", "kind": "top_down",
     "params": {"height_units": 600, "duration_ms": 1500}},
    {"name": "REVERSE_TRACK_REVEAL", "kind": "reverse_track",
     "params": {"distance_units": 260, "duration_ms": 1800}},
    {"name": "PROJECTILE_FOLLOW_ROCKET", "kind": "projectile_follow",
     "params": {"offset_units": 60, "roll_deg": 8, "fov": 95}},
    {"name": "BEHIND_PROJECTILE_NADE", "kind": "behind_projectile",
     "params": {"offset_units": 48, "arc_compensate": True}},
    {"name": "BULLET_TIME_ARC", "kind": "bullet_time_arc",
     "params": {"degrees": 120, "duration_ms": 1600, "time_scale": 0.2}},
]

# ---------------------------------------------------------------- audio

AUDIO_EFFECTS = [
    {"name": "HEARTBEAT_LOW_HP",
     "treatment": {"layer": "heartbeat_slow", "bpm": 70, "gain_db": -8,
                   "lowpass_hz": 900},
     "description": "Slow heartbeat layered under game audio at low HP."},
    {"name": "HEARTBEAT_CRITICAL",
     "treatment": {"layer": "heartbeat_fast", "bpm": 120, "gain_db": -5,
                   "lowpass_hz": 700, "music_duck_db": -6},
     "description": "Fast heartbeat + muffled world audio at critical HP."},
    {"name": "IMPACT_DROP",
     "treatment": {"oneshot": "sub_drop", "gain_db": -3,
                   "align": "action_peak"},
     "description": "Sub-bass drop aligned to the money shot."},
    {"name": "CLUTCH_TENSION",
     "treatment": {"layer": "tension_riser", "gain_db": -10,
                   "build_ms": 4000, "music_duck_db": -4},
     "description": "Rising tension bed during clutch situations."},
    {"name": "FINAL_KILL_RELEASE",
     "treatment": {"oneshot": "impact_release", "gain_db": -2,
                   "tail_reverb_s": 1.5, "music_duck_db": -6},
     "description": "Release hit on the round/game-winning frag."},
    {"name": "REVERSE_WHOOSH",
     "treatment": {"oneshot": "reverse_whoosh", "gain_db": -6,
                   "align": "rewind_start"},
     "description": "Whoosh accompanying a reverse/rewind replay."},
    {"name": "SLOWMO_FILTER",
     "treatment": {"filter": "lowpass_sweep", "lowpass_hz": 1200,
                   "pitch_shift_semitones": -3, "wet": 0.7},
     "description": "Muffled pitched-down game audio while time is slowed."},
    {"name": "PROJECTILE_FOCUS",
     "treatment": {"filter": "bandpass_focus", "center_hz": 400,
                   "world_duck_db": -9, "doppler": True},
     "description": "World ducks; the tracked projectile carries the mix."},
]

# ------------------------------------------------------------ helpers

_HEALTH_PULSE_HUD = {"elements": ["health"], "pulse_hz": 1.6,
                     "color": "#ff2020"}
_ENEMY_COUNT_HUD = {"overlay": "enemy_counter", "position": "top_center"}


def _effect(name: str, category: str, description: str, *,
            trigger_types: list[str], intensity: str,
            camera: str | None = None, allowed_game_modes=None,
            time_recipe=None, tracking_recipe=None, fx_recipe=None,
            audio: list[str] | None = None, hud_recipe=None,
            color_recipe=None, parameters=None, quality_level="final",
            engine_requirements="wolfcamql") -> dict:
    return {
        "name": name, "category": category, "description": description,
        "trigger_types": trigger_types,
        "allowed_game_modes": (allowed_game_modes if allowed_game_modes
                               is not None else ALL_MODES),
        "camera_recipe": {"camera": camera} if camera else None,
        "time_recipe": time_recipe,
        "tracking_recipe": tracking_recipe,
        "fx_recipe": fx_recipe,
        "audio_recipe": {"effects": audio} if audio else None,
        "hud_recipe": hud_recipe,
        "color_recipe": color_recipe,
        "parameters_json": parameters or {},
        "intensity": intensity,
        "quality_level": quality_level,
        "engine_requirements": engine_requirements,
    }


EFFECTS = [
    _effect("LOW_HP_V1", "situation",
            "Low-HP survival treatment: heartbeat, health pulse, "
            "slight desaturation.",
            trigger_types=["LOW_HP"], intensity="subtle",
            audio=["HEARTBEAT_LOW_HP"], hud_recipe=_HEALTH_PULSE_HUD,
            color_recipe={"saturation": 0.85, "vignette": 0.2}),
    _effect("CRITICAL_HP_V1", "situation",
            "Critical-HP treatment: fast heartbeat, hard health pulse, "
            "heavy vignette + desaturation.",
            trigger_types=["CRITICAL_HP", "LOW_HP"], intensity="medium",
            audio=["HEARTBEAT_CRITICAL"],
            hud_recipe={**_HEALTH_PULSE_HUD, "pulse_hz": 2.8},
            color_recipe={"saturation": 0.6, "vignette": 0.45}),
    _effect("CLUTCH_1V2_V1", "clutch",
            "1v2 clutch: enemy counter overlay + tension bed.",
            trigger_types=["CLUTCH_1V2"], intensity="subtle",
            allowed_game_modes=CA_MODES, audio=["CLUTCH_TENSION"],
            hud_recipe=_ENEMY_COUNT_HUD),
    _effect("CLUTCH_1V3_V1", "clutch",
            "1v3 clutch: enemy counter, tension bed, per-kill counter tick.",
            trigger_types=["CLUTCH_1V3"], intensity="medium",
            allowed_game_modes=CA_MODES, audio=["CLUTCH_TENSION"],
            hud_recipe=_ENEMY_COUNT_HUD),
    _effect("CLUTCH_1V4_V1", "clutch",
            "1v4 clutch: full clutch package — counter, tension, health "
            "pulse, release on last kill.",
            trigger_types=["CLUTCH_1V4"], intensity="hero",
            allowed_game_modes=CA_MODES,
            audio=["CLUTCH_TENSION", "FINAL_KILL_RELEASE"],
            hud_recipe={**_ENEMY_COUNT_HUD, "health_pulse": True}),
    _effect("MULTIKILL_ESCALATE_V1", "multikill",
            "Escalating treatment per kill in a multikill: each kill slows "
            "deeper and hits harder.",
            trigger_types=["MULTIKILL", "QUADKILL"], intensity="medium",
            time_recipe={"per_kill_slow": [0.9, 0.7, 0.5, 0.35]},
            audio=["IMPACT_DROP"],
            fx_recipe={"per_kill_zoom": [1.0, 1.05, 1.1, 1.18]}),
    _effect("PIXEL_REPLAY_V1", "replay",
            "Pixel-shot replay: freeze at impact, zoom to the gap, resume.",
            trigger_types=["PIXEL_SHOT"], intensity="medium",
            camera="BULLET_TIME_ARC",
            time_recipe={"freeze_ms": 700, "slow_rate": 0.3},
            fx_recipe={"zoom_target": "impact_point", "zoom_scale": 2.2},
            audio=["SLOWMO_FILTER", "IMPACT_DROP"]),
    _effect("FLICK_REPLAY_V1", "replay",
            "Flick replay: reverse to pre-flick, replay the flick slowed "
            "with crosshair trail.",
            trigger_types=["FLICK_SHOT"], intensity="medium",
            time_recipe={"reverse_ms": 900, "slow_rate": 0.35},
            fx_recipe={"crosshair_trail": True},
            audio=["REVERSE_WHOOSH", "SLOWMO_FILTER"]),
    _effect("LG_TRACKING_V1", "tracking",
            "LG tracking showcase: accuracy overlay + beam glow while "
            "the shaft stays locked.",
            trigger_types=["LG_TRACKING", "air_shaft"], intensity="subtle",
            tracking_recipe={"lock": "victim", "show_accuracy": True},
            fx_recipe={"beam_glow": 1.4},
            hud_recipe={"overlay": "lg_accuracy", "position": "bottom_center"}),
    _effect("AIR_ROCKET_ORBIT_V1", "airshot",
            "Airshot orbit: time crawls, camera orbits the airborne victim "
            "at impact.",
            trigger_types=["AIR_ROCKET", "airshot"], intensity="hero",
            camera="ORBIT_HERO_360",
            time_recipe={"slow_rate": 0.2, "window_ms": 1600},
            audio=["SLOWMO_FILTER", "IMPACT_DROP"],
            color_recipe={"contrast": 1.1}),
    _effect("AIR_ROCKET_PROJECTILE_V1", "airshot",
            "Airshot projectile cam: ride the rocket from muzzle to the "
            "airborne victim.",
            trigger_types=["AIR_ROCKET", "airshot"], intensity="medium",
            camera="PROJECTILE_FOLLOW_ROCKET",
            tracking_recipe={"track": "projectile", "handoff": "impact"},
            time_recipe={"slow_rate": 0.45, "window_ms": 1200},
            audio=["PROJECTILE_FOCUS", "IMPACT_DROP"]),
    _effect("AIR_GRENADE_FOLLOW_V1", "airshot",
            "Air grenade arc cam: follow the nade along its arc into the "
            "airborne victim.",
            trigger_types=["AIR_GRENADE", "air_nade"], intensity="medium",
            camera="BEHIND_PROJECTILE_NADE",
            tracking_recipe={"track": "projectile", "handoff": "explosion"},
            time_recipe={"slow_rate": 0.5, "window_ms": 1400},
            audio=["PROJECTILE_FOCUS", "IMPACT_DROP"]),
    _effect("HIGH_SPEED_CHASE_V1", "movement",
            "Extreme-speed chase cam: side-track matching player velocity, "
            "speedometer overlay.",
            trigger_types=["EXTREME_SPEED", "HIGH_SPEED"], intensity="medium",
            camera="SIDE_TRACK_FAST",
            tracking_recipe={"track": "recorder", "speed_match": True},
            fx_recipe={"motion_blur": 0.3, "fov_widen": 8},
            hud_recipe={"overlay": "speedometer", "position": "bottom_left"}),
    _effect("ROCKET_JUMP_V1", "movement",
            "Rocket-jump rise: vertical orbit rising with the jump, "
            "landing frag punch.",
            trigger_types=["ROCKET_JUMP"], intensity="subtle",
            camera="VERTICAL_ORBIT_RISE",
            time_recipe={"slow_rate": 0.6, "window_ms": 1000},
            audio=["IMPACT_DROP"]),
    _effect("PREDICTION_PROJECTILE_V1", "prediction",
            "Prediction shot: cut to projectile cam the moment it leaves, "
            "victim walks into it.",
            trigger_types=["PREDICTION_SHOT"], intensity="medium",
            camera="PROJECTILE_FOLLOW_ROCKET",
            tracking_recipe={"track": "projectile", "reveal": "victim_path"},
            time_recipe={"slow_rate": 0.5, "window_ms": 1500},
            audio=["PROJECTILE_FOCUS"]),
    _effect("FINAL_FRAG_HERO_V1", "hero",
            "Round/game-winning frag: freeze the feed, orbit, release hit, "
            "grade lift.",
            trigger_types=["FINAL_FRAG", "ROUND_WIN"], intensity="hero",
            allowed_game_modes=CA_MODES, camera="ORBIT_HERO_360",
            time_recipe={"freeze_ms": 900, "slow_rate": 0.25,
                         "window_ms": 2200},
            audio=["FINAL_KILL_RELEASE"],
            hud_recipe={"feed_freeze": True},
            color_recipe={"contrast": 1.15, "lift": 0.05}),
]

# ---------------------------------------------------------------- recipes

RECIPES = [
    {"name": "LOW_HP_V1", "frag_classes": ["LOW_HP"],
     "description": "Heartbeat + health pulse survival bed.",
     "timeline": [
         _step(-3000, "play_audio", effect="HEARTBEAT_LOW_HP"),
         _step(-3000, "health_pulse", hz=1.6),
         _step(-3000, "color_grade", saturation=0.85, vignette=0.2),
         _step(1500, "resume")]},
    {"name": "CRITICAL_HP_V1", "frag_classes": ["CRITICAL_HP"],
     "description": "Critical HP: fast heartbeat, hard pulse, duck music.",
     "timeline": [
         _step(-4000, "play_audio", effect="HEARTBEAT_CRITICAL"),
         _step(-4000, "health_pulse", hz=2.8),
         _step(-4000, "duck_music", db=-6),
         _step(-4000, "color_grade", saturation=0.6, vignette=0.45),
         _step(1500, "resume")]},
    {"name": "CLUTCH_1V2_V1", "frag_classes": ["CLUTCH_1V2"],
     "description": "1v2: counter overlay + tension.",
     "timeline": [
         _step(-5000, "overlay_enemy_count", count=2),
         _step(-5000, "play_audio", effect="CLUTCH_TENSION"),
         _step(1000, "resume")]},
    {"name": "CLUTCH_1V3_V1", "frag_classes": ["CLUTCH_1V3"],
     "description": "1v3: counter ticks down per kill.",
     "timeline": [
         _step(-6000, "overlay_enemy_count", count=3),
         _step(-6000, "play_audio", effect="CLUTCH_TENSION"),
         _step(0, "overlay_enemy_count", count=2),
         _step(1000, "resume")]},
    {"name": "CLUTCH_1V4_V1", "frag_classes": ["CLUTCH_1V4"],
     "description": "1v4 hero clutch: counter, tension, pulse, release.",
     "timeline": [
         _step(-8000, "overlay_enemy_count", count=4),
         _step(-8000, "play_audio", effect="CLUTCH_TENSION"),
         _step(-8000, "health_pulse", hz=2.0),
         _step(-200, "slow_to", rate=0.4, ramp_ms=150),
         _step(0, "play_audio", effect="FINAL_KILL_RELEASE"),
         _step(600, "resume")]},
    {"name": "MULTIKILL_ESCALATE_V1", "frag_classes": ["MULTIKILL"],
     "description": "Each kill slows deeper, zooms tighter, hits harder.",
     "timeline": [
         _step(0, "slow_to", rate=0.9, ramp_ms=100),
         _step(0, "zoom_target", scale=1.05),
         _step(0, "play_audio", effect="IMPACT_DROP"),
         _step(400, "resume"),
         _step(1200, "slow_to", rate=0.7, ramp_ms=100),
         _step(1200, "zoom_target", scale=1.1),
         _step(1200, "play_audio", effect="IMPACT_DROP"),
         _step(1700, "resume"),
         _step(2600, "slow_to", rate=0.5, ramp_ms=100),
         _step(2600, "zoom_target", scale=1.18),
         _step(2600, "play_audio", effect="IMPACT_DROP"),
         _step(3400, "resume")]},
    {"name": "PIXEL_REPLAY_V1", "frag_classes": ["PIXEL_SHOT"],
     "description": "Freeze at impact, zoom to the pixel gap, resume.",
     "timeline": [
         _step(-400, "slow_to", rate=0.3, ramp_ms=120),
         _step(0, "freeze", duration_ms=700),
         _step(0, "cut_to_camera", camera="BULLET_TIME_ARC"),
         _step(0, "zoom_target", target="impact_point", scale=2.2),
         _step(0, "play_audio", effect="IMPACT_DROP"),
         _step(700, "resume", ramp_ms=200)]},
    {"name": "FLICK_REPLAY_V1", "frag_classes": ["FLICK_SHOT"],
     "description": "Reverse to pre-flick, replay slowed with trail.",
     "timeline": [
         _step(100, "freeze", duration_ms=300),
         _step(400, "reverse", duration_ms=900),
         _step(400, "play_audio", effect="REVERSE_WHOOSH"),
         _step(1300, "slow_to", rate=0.35, ramp_ms=100),
         _step(1300, "play_audio", effect="SLOWMO_FILTER"),
         _step(2400, "resume", ramp_ms=150)]},
    {"name": "LG_TRACKING_V1", "frag_classes": ["LG_TRACKING"],
     "description": "Accuracy overlay + beam glow during the lock.",
     "timeline": [
         _step(-2500, "overlay_enemy_count", overlay="lg_accuracy"),
         _step(-2500, "zoom_target", scale=1.08),
         _step(500, "resume")]},
    {"name": "AIR_ROCKET_ORBIT_V1", "frag_classes": ["AIR_ROCKET"],
     "description": "Hero orbit around the airborne victim at impact.",
     "timeline": [
         _step(-300, "slow_to", rate=0.2, ramp_ms=150),
         _step(-300, "play_audio", effect="SLOWMO_FILTER"),
         _step(-200, "cut_to_camera", camera="ORBIT_HERO_360"),
         _step(0, "play_audio", effect="IMPACT_DROP"),
         _step(1300, "resume", ramp_ms=200)]},
    {"name": "AIR_ROCKET_PROJECTILE_V1", "frag_classes": ["AIR_ROCKET"],
     "description": "Ride the rocket from muzzle to airborne victim.",
     "timeline": [
         _step(-900, "cut_to_camera", camera="PROJECTILE_FOLLOW_ROCKET"),
         _step(-900, "play_audio", effect="PROJECTILE_FOCUS"),
         _step(-900, "slow_to", rate=0.45, ramp_ms=120),
         _step(0, "play_audio", effect="IMPACT_DROP"),
         _step(300, "resume", ramp_ms=150)]},
    {"name": "AIR_GRENADE_FOLLOW_V1", "frag_classes": ["AIR_GRENADE"],
     "description": "Follow the nade arc into the airborne victim.",
     "timeline": [
         _step(-1400, "cut_to_camera", camera="BEHIND_PROJECTILE_NADE"),
         _step(-1400, "play_audio", effect="PROJECTILE_FOCUS"),
         _step(-1400, "slow_to", rate=0.5, ramp_ms=120),
         _step(0, "play_audio", effect="IMPACT_DROP"),
         _step(400, "resume", ramp_ms=150)]},
    {"name": "HIGH_SPEED_CHASE_V1", "frag_classes": ["EXTREME_SPEED"],
     "description": "Side-track chase at matched speed with speedometer.",
     "timeline": [
         _step(-3000, "cut_to_camera", camera="SIDE_TRACK_FAST"),
         _step(-3000, "overlay_enemy_count", overlay="speedometer"),
         _step(0, "speed_to", rate=1.0),
         _step(800, "resume")]},
    {"name": "ROCKET_JUMP_V1", "frag_classes": ["ROCKET_JUMP"],
     "description": "Vertical orbit rising with the jump.",
     "timeline": [
         _step(-1200, "cut_to_camera", camera="VERTICAL_ORBIT_RISE"),
         _step(-1200, "slow_to", rate=0.6, ramp_ms=120),
         _step(0, "play_audio", effect="IMPACT_DROP"),
         _step(500, "resume", ramp_ms=150)]},
    {"name": "PREDICTION_PROJECTILE_V1", "frag_classes": ["PREDICTION_SHOT"],
     "description": "Projectile cam reveals the victim walking into it.",
     "timeline": [
         _step(-1600, "cut_to_camera", camera="PROJECTILE_FOLLOW_ROCKET"),
         _step(-1600, "track_projectile", reveal="victim_path"),
         _step(-1600, "play_audio", effect="PROJECTILE_FOCUS"),
         _step(-1600, "slow_to", rate=0.5, ramp_ms=120),
         _step(200, "resume", ramp_ms=150)]},
    {"name": "FINAL_FRAG_HERO_V1", "frag_classes": ["FINAL_FRAG"],
     "description": "Feed freeze, hero orbit, release hit, grade lift.",
     "timeline": [
         _step(-400, "slow_to", rate=0.25, ramp_ms=150),
         _step(0, "feed_freeze"),
         _step(0, "freeze", duration_ms=900),
         _step(0, "cut_to_camera", camera="ORBIT_HERO_360"),
         _step(0, "play_audio", effect="FINAL_KILL_RELEASE"),
         _step(0, "color_grade", contrast=1.15, lift=0.05),
         _step(900, "resume", ramp_ms=250)]},
]


def seed(conn: sqlite3.Connection) -> dict:
    """Idempotently seed cameras, audio effects, effects and recipes.

    Upsert by name; version bumps only when a payload changes.
    Returns counts of rows now present per table.
    """
    for cam in CAMERA_RECIPES:
        cdb.upsert_camera(conn, cam)
    for aud in AUDIO_EFFECTS:
        cdb.upsert_audio(conn, aud)
    for eff in EFFECTS:
        cdb.upsert_effect(conn, eff)
    for rec in RECIPES:
        cdb.upsert_recipe(conn, rec)
    counts = {}
    for table, key in (("camera_recipes", "cameras"),
                       ("audio_effects", "audio"),
                       ("cinematic_effects", "effects"),
                       ("cinematic_recipes", "recipes")):
        counts[key] = conn.execute(
            f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    return counts
