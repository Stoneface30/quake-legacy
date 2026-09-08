"""Every route to every creative idea, keyed by the corpus's own names.

WHY SEPARATE. `render_profile` owns what the runtime can do. This owns how
each of the user's ideas could be realised with it. Keeping them apart means
a renderer change edits one file and the creative language edits the other.

WHY MULTIPLE ROUTES. A chase and a camera spline are different primitives,
not two spellings of one: they differ in fidelity, in what can go wrong, and
in what they cost. Collapsing them would hide exactly the choice the
director needs to make. So an idea lists every route known, each with its
own coverage, and `best_route_now` picks among them rather than pretending
there was only ever one.

COVERAGE. FULL means the route delivers the idea. PARTIAL means it delivers
part of it and the shortfall is stated. STYLISED means it produces something
in the neighbourhood and must not be sold as the idea -- a picmip staircase
is not a world strip.
"""
from __future__ import annotations

from typing import Any

from creative_suite.engine.render_profile import (
    Implementation, ENGINE, CAPTURE_PASS, COMPOSITOR, SYNTHETIC,
    AVAILABLE_NOW, AVAILABLE_VIA_ASSETS, FUTURE_BACKEND, IMPLEMENTATIONS)

_I = Implementation

CORPUS_ROUTES: dict[str, tuple[Implementation, ...]] = {

    # ── world ───────────────────────────────────────────────────────────────
    "WORLD_STRIP": (
        _I(ENGINE, "r_picmip per shot", "STYLISED", AVAILABLE_NOW,
           "texture reduction, latched, whole shot; not a reveal"),
        _I(ENGINE, "entityfilter", "STYLISED", AVAILABLE_NOW,
           "hides ENTITIES; the world itself stays"),
        _I(CAPTURE_PASS, "mme_saveDepth + depth compositing", "PARTIAL",
           AVAILABLE_NOW, "geometry emerges from depth; textures do not fade"),
        _I(ENGINE, "per-frame surface suppression", "FULL", FUTURE_BACKEND),
    ),
    "WORLD_REBUILD": (
        _I(ENGINE, "per-frame surface suppression", "FULL", FUTURE_BACKEND),
    ),
    "WALL_XRAY_REBUILD": (
        _I(CAPTURE_PASS, "depth pass + mask compositing", "PARTIAL",
           AVAILABLE_NOW),
        _I(ENGINE, "per-frame surface suppression", "FULL", FUTURE_BACKEND),
    ),
    "MAP_CONSTRUCTION_INTRO": (
        _I(SYNTHETIC, "authored build animation", "FULL", FUTURE_BACKEND,
           "author-defined duration; nothing to discover"),
    ),
    "LOW_HP_REACTIVE_WORLD": (
        _I(ENGINE, "remapshader on health thresholds", "FULL", AVAILABLE_NOW,
           "live swap, revertible with clearremappedshader"),
        _I(ENGINE, "cvarinterp r_gamma", "STYLISED", AVAILABLE_NOW,
           "whole frame, not the world"),
    ),
    "MUSIC_REACTIVE_MATERIAL": (
        _I(ENGINE, "remapshader on musical anchors", "FULL", AVAILABLE_NOW),
        _I(ENGINE, "cvarinterp r_gamma ramp", "PARTIAL", AVAILABLE_NOW,
           "whole frame, not per material"),
    ),
    "TEAM_IDENTITY_MORPH": (
        _I(ENGINE, "remapshader on player skins", "PARTIAL", AVAILABLE_NOW,
           "a MATERIAL change. Not a model morph and must not be called one"),
        _I(ENGINE, "vertex morph", "FULL", FUTURE_BACKEND),
    ),
    "TEXTURE_COUNTDOWN_TEXT": (
        _I(ENGINE, "remapshader through numbered shaders", "FULL",
           AVAILABLE_NOW),
    ),
    "POST_WIN_TEAMMATE_MODEL_REVEAL": (
        _I(ENGINE, "remapshader on teammate skins", "PARTIAL", AVAILABLE_NOW),
        _I(COMPOSITOR, "marker overlay", "PARTIAL", AVAILABLE_NOW),
    ),

    # ── camera and projectile ───────────────────────────────────────────────
    "PROJECTILE_CINEMATIC": (
        _I(ENGINE, "chase <missile entity>", "FULL", AVAILABLE_NOW,
           "the engine rides the entity: no path, no sample budget. Entity "
           "lifetime and impact behaviour unswept"),
        _I(ENGINE, "cam10 viewEnt + angles ENT", "FULL", AVAILABLE_NOW,
           "authored path, engine-computed aim at the entity"),
        _I(ENGINE, "cam10 authored angles", "PARTIAL", AVAILABLE_NOW,
           "today's route; the aim is keyframed and can lag the subject"),
        _I(COMPOSITOR, "crop and track in post", "STYLISED", AVAILABLE_NOW),
    ),
    "RECONSTRUCTED_PROJECTILE_CINEMATIC": (
        _I(ENGINE, "cam10 over a reconstructed path", "PARTIAL", AVAILABLE_NOW,
           "the camera is real; the path it follows is DERIVED and must stay "
           "labelled so"),
    ),
    "GRENADE_ARC_FOLLOW": (
        _I(ENGINE, "chase <grenade entity>", "FULL", AVAILABLE_NOW),
        _I(ENGINE, "cam10 viewEnt", "FULL", AVAILABLE_NOW),
    ),
    "ROCKET_FLYBY_AUDIO_ANCHOR": (
        _I(ENGINE, "chase with offset and range", "PARTIAL", AVAILABLE_NOW),
        _I(ENGINE, "cam10 spline past the flight line", "PARTIAL",
           AVAILABLE_NOW, "measured: a long dolly fights level geometry"),
    ),
    "FLY_INTO_OBJECT": (
        _I(ENGINE, "cam10 spline into a surface", "PARTIAL", AVAILABLE_NOW,
           "collision repair fights it"),
    ),
    "ENEMY_POV_REAL": (
        _I(ENGINE, "chase <player entity>", "PARTIAL", AVAILABLE_NOW,
           "position only. The enemy's own view was never transmitted to "
           "this recorder, so a true POV is not available at any fidelity"),
    ),
    "ENEMY_POV_RECONSTRUCTED": (
        _I(ENGINE, "cam10 at a reconstructed eye", "PARTIAL", AVAILABLE_NOW,
           "DERIVED, never observed"),
    ),
    "ENEMY_POV_SYNTHETIC": (
        _I(SYNTHETIC, "authored", "FULL", FUTURE_BACKEND),
    ),
    "TELEPORTER_WORLD_PASS": (
        _I(ENGINE, "cam10 JUMP across the teleporter pair", "FULL",
           AVAILABLE_NOW, "map truth gives both ends whether or not the "
                          "recorder observed the transit"),
    ),

    # ── time ────────────────────────────────────────────────────────────────
    "RHYTHMIC_IMAGE_STUTTER": (
        _I(COMPOSITOR, "frame hold / repeat", "FULL", AVAILABLE_NOW,
           "measured: unequal figures survive to within 6.7 ms"),
    ),
    "FRAME_ECHO": (
        _I(COMPOSITOR, "frame blend", "FULL", AVAILABLE_NOW),
    ),
    "MULTI_EXPOSURE": (
        _I(COMPOSITOR, "frame accumulate", "FULL", AVAILABLE_NOW),
        _I(ENGINE, "mme_blurFrames", "PARTIAL", AVAILABLE_NOW,
           "accumulates at capture; not selectable per subject"),
    ),
    "MOSAIC_TILE_INTERPOLATION": (
        _I(COMPOSITOR, "tile region stepping", "FULL", AVAILABLE_NOW,
           "driven by unequal gesture IOIs"),
    ),
    "TEMPORAL_DECOMPOSITION": (
        _I(COMPOSITOR, "freeze + overlay", "FULL", AVAILABLE_NOW),
        _I(ENGINE, "entityfreeze", "PARTIAL", AVAILABLE_NOW,
           "one entity holds while the world runs on; scope unswept"),
    ),
    "SPEED_SCALED_SLOWMO": (
        _I(ENGINE, "cvarinterp timescale ... real", "FULL", AVAILABLE_NOW,
           "ramped before capture, so particles and blur follow the ramp"),
        # cam10 v10 has no timescale field; the ramp is a scheduled command.
        _I(ENGINE, "cam10 commandStr fires cvarinterp timescale", "PARTIAL",
           AVAILABLE_NOW,
           "the ramp is triggered BY the path, not carried in it"),
        _I(COMPOSITOR, "setpts", "PARTIAL", AVAILABLE_NOW,
           "measured; cannot recover detail the capture never had"),
    ),
    "VELOCITY_SIGNATURE": (
        _I(COMPOSITOR, "overlay from cached movement", "FULL", AVAILABLE_NOW),
    ),
    "HERO_THEN_DEATH_REWIND": (
        _I(COMPOSITOR, "reverse + replay", "FULL", AVAILABLE_NOW,
           "measured: exactly twice the slice, 0.0 ms error"),
        _I(ENGINE, "loop <start> <end>", "PARTIAL", AVAILABLE_NOW,
           "engine-side loop; exit semantics unswept"),
    ),
    "MICRO_ACTION_ACCENT": (
        _I(COMPOSITOR, "short hold", "FULL", AVAILABLE_NOW),
    ),
    "LAG_TELEPORT_STYLIZATION": (
        _I(COMPOSITOR, "stutter on the anomaly", "FULL", AVAILABLE_NOW),
    ),
    "RHYTHMIC_MOTIF_MONTAGE": (
        _I(COMPOSITOR, "cut sequence on the grid", "FULL", AVAILABLE_NOW),
    ),
    "SEMANTIC_COMPRESSION": (
        _I(COMPOSITOR, "trim to the recognised action", "FULL", AVAILABLE_NOW),
    ),

    # ── information ─────────────────────────────────────────────────────────
    "ONE_V_X_COUNT_DISPLAY": (
        _I(COMPOSITOR, "number overlay", "FULL", AVAILABLE_NOW),
        _I(ENGINE, "centerprint", "PARTIAL", AVAILABLE_NOW,
           "lit and compressed with the frame; less type control"),
    ),
    "DAMAGE_LEDGER_OVER_TARGET": (
        _I(COMPOSITOR, "tracked number overlay", "FULL", AVAILABLE_NOW),
    ),
    "ROUND_DAMAGE_COUNTER": (
        _I(COMPOSITOR, "number overlay", "FULL", AVAILABLE_NOW),
        _I(ENGINE, "centerprint", "PARTIAL", AVAILABLE_NOW),
    ),
    "DIEGETIC_SCOREBOARD": (
        _I(ENGINE, "remapshader on an ad surface", "PARTIAL", AVAILABLE_NOW,
           "a real surface in the world, lit with it"),
        _I(COMPOSITOR, "projected overlay", "PARTIAL", AVAILABLE_NOW),
    ),
    "PIP_WORLD_SURFACE": (
        _I(COMPOSITOR, "overlay of a second capture", "FULL", AVAILABLE_NOW,
           "measured: adds exactly zero time"),
        _I(ENGINE, "addmirrorsurface", "PARTIAL", AVAILABLE_NOW,
           "a real mirror surface; unswept"),
    ),
    "CHAT_REACTION": (
        _I(COMPOSITOR, "text overlay from the chat index", "FULL",
           AVAILABLE_NOW, "1,727 of 2,040 senders resolved"),
    ),
    "RAIL_COOLDOWN_TELEGRAPH": (
        _I(COMPOSITOR, "bar overlay", "FULL", AVAILABLE_NOW),
    ),
    "SHAFT_DUEL_STAT": (
        _I(COMPOSITOR, "stat overlay", "PARTIAL", AVAILABLE_NOW,
           "every cached LG contact series is empty, so the stat is not "
           "available to draw"),
    ),
    "CA_EXPLAINER": (
        _I(COMPOSITOR, "card", "FULL", AVAILABLE_NOW),
    ),
    "ONE_V_X_ENEMY_REVEAL": (
        _I(ENGINE, "entityfilter to isolate enemies", "PARTIAL", AVAILABLE_NOW,
           "entities only; the world stays"),
        _I(COMPOSITOR, "marker overlay", "PARTIAL", AVAILABLE_NOW),
        _I(ENGINE, "world strip + reveal", "FULL", FUTURE_BACKEND),
    ),
    "DANGER_CROSS_SIGN": (
        _I(COMPOSITOR, "marker overlay", "FULL", AVAILABLE_NOW),
    ),
    "NOPE_RETREAT": (
        _I(COMPOSITOR, "beat + overlay", "FULL", AVAILABLE_NOW),
    ),
    "COMMIT_1VX": (
        _I(COMPOSITOR, "sequence from round evidence", "FULL", AVAILABLE_NOW),
    ),
    "TEAM_ROUND_STORY": (
        _I(COMPOSITOR, "sequence from round evidence", "FULL", AVAILABLE_NOW),
    ),
    "ASSISTED_ROUND_FINISH": (
        _I(COMPOSITOR, "sequence + damage overlay", "FULL", AVAILABLE_NOW),
    ),
    "DAMAGE_CHASE_ASSIST": (
        _I(COMPOSITOR, "sequence + damage overlay", "FULL", AVAILABLE_NOW),
    ),
    "ROUND_WIN_PAYOFF": (
        _I(COMPOSITOR, "release cut", "FULL", AVAILABLE_NOW),
    ),
    "ROUND_LOSS_CONTINUATION": (
        _I(COMPOSITOR, "continuation cut", "FULL", AVAILABLE_NOW),
    ),

    # ── transitions and identity ────────────────────────────────────────────
    "DEATH_AS_TRANSITION": (
        _I(COMPOSITOR, "match cut on the death", "FULL", AVAILABLE_NOW,
           "measured"),
    ),
    "DEATH_MOTIF_BANK": (
        _I(COMPOSITOR, "montage from death events", "FULL", AVAILABLE_NOW),
    ),
    "MOVEMENT_TRANSITION": (
        _I(COMPOSITOR, "overlap on matched motion", "FULL", AVAILABLE_NOW,
           "measured: removes exactly the time requested"),
    ),
    "IDENTITY_MATCH_CUT": (
        _I(COMPOSITOR, "cut on matched silhouette", "FULL", AVAILABLE_NOW),
    ),
    "STRAFE_JUMP_AUDIO_MATCH": (
        _I(COMPOSITOR, "cut on the audio anchor", "FULL", AVAILABLE_NOW),
    ),
    "PROJECTILE_MORPH_BRIDGE": (
        _I(COMPOSITOR, "shape-matched dissolve", "STYLISED", AVAILABLE_NOW),
        _I(ENGINE, "vertex morph", "FULL", FUTURE_BACKEND),
    ),
    "WORLD_MORPH_TO_NEXT_SCENE": (
        _I(ENGINE, "vertex morph", "FULL", FUTURE_BACKEND),
    ),
    "TELEFRAG_GRAMMAR": (
        _I(COMPOSITOR, "cut on the telefrag", "FULL", AVAILABLE_NOW),
    ),
    "GAUNTLET_GRAMMAR": (
        _I(COMPOSITOR, "cut on the gauntlet kill", "FULL", AVAILABLE_NOW),
    ),

    # ── authored ────────────────────────────────────────────────────────────
    "GRENADE_FOOTBALL_GAG": (
        _I(SYNTHETIC, "authored", "FULL", FUTURE_BACKEND),
    ),
    "PROJECT_INTRO": (
        _I(SYNTHETIC, "authored", "FULL", FUTURE_BACKEND),
    ),
    "QUAKE_TRIBUTE_OUTRO": (
        _I(SYNTHETIC, "authored", "FULL", FUTURE_BACKEND),
    ),
}

IMPLEMENTATIONS.update(CORPUS_ROUTES)


def unmapped() -> list[str]:
    """Corpus ideas with no route recorded. Not blocked -- unexamined."""
    from creative_suite.engine import creative_corpus as cc
    return [e.name for e in cc.CORPUS if e.name not in IMPLEMENTATIONS]
