"""Stats that travel with an exported clip.

A voter looking at ten seconds of Quake cannot see how far the rail went, how
fast the victim was moving, or that this was the third kill in two seconds.
Those are the things that separate a good play from a lucky one, and they are
already measured -- they were just never leaving the repository.

THREE KINDS OF NUMBER, KEPT APART.

`stats` are MEASUREMENTS: units, milliseconds, degrees, health. They mean the
same thing to anyone and need no knowledge of this project to read.

`machine_subscores` are the recogniser's OPINIONS on its own scale. Accuracy,
tracking, movement and the rest are components of the highlight score, not
percentages, and calling a 7.5 "accuracy" without saying whose scale it is on
would invite exactly the wrong reading.

`availability` says which of those could be produced at all. This is the part
that matters, because the answer differs per clip: everything derived from
the actor's aim, health, speed and view comes from the RECORDER's player
state, and when the actor is not the recorder there is no such state to read.
An observed frag gets the universal stats and nothing else, and says so,
rather than quietly shipping a shorter dictionary that looks like a complete
one.

WHAT IS UNIVERSAL. Anything read off the kill events themselves works for
every actor, because an obituary is a server fact rather than an observation
of one player: which round it was, how many kills the actor had in that
round, whether this kill was part of a multi-kill, and the gap to their
previous and next kill.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
RECOGNITION_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"

# How close two kills must be to count as one multi-kill. Quake Live's own
# excellent/rampage announcements use a rolling window; three seconds is the
# span a viewer reads as "that was one burst".
MULTIKILL_WINDOW_MS = 3000

FULL = "FULL_RECORDER_STATE"
OBSERVED = "OBSERVED_ONLY"

# Measurements worth showing a stranger, mapped from the recogniser's own
# attribute names to names that mean something without this codebase. Only
# real quantities -- no scores, no percentiles of a private distribution.
MEASURED = {
    "distance": ("distance_units", "how far the kill was made from"),
    "killer_speed": ("actor_speed_ups", "actor's speed, units per second"),
    "victim_speed": ("victim_speed_ups", "victim's speed, units per second"),
    "victim_air_height": ("victim_air_height_units", "victim's height off the ground"),
    "flick_degrees": ("flick_degrees", "how far the aim moved onto the target"),
    "flick_duration_ms": ("flick_duration_ms", "how long that movement took"),
    "deg_per_sec": ("flick_speed_deg_per_s", "angular speed of that movement"),
    "visibility_ms": ("target_visible_ms", "how long the target was visible"),
    "health_at_frag": ("actor_health", "actor's health at the kill"),
    "armor_at_frag": ("actor_armor", "actor's armour at the kill"),
    "lg_damage_burst_3s": ("lg_damage_dealt_3s", "lightning damage dealt in 3s"),
    "lg_taken_total_dmg": ("damage_taken_in_fight", "damage the actor took"),
    "lg_incoming_hit_ratio": ("incoming_hit_ratio", "share of incoming shots that hit"),
    "lg_min_health": ("lowest_health_in_fight", "how close the actor came to dying"),
}

# The recogniser's component scores. Its own scale, and labelled as such.
SUBSCORES = ("accuracy_score", "tracking_score", "movement_score",
             "precision_score", "speed_score", "air_score", "distance_score",
             "multikill_score", "flick_score", "visibility_score",
             "clutch_score", "drama_score", "combo_score")


def _conn(db: Path = RECOGNITION_DB) -> sqlite3.Connection:
    c = sqlite3.connect(db, timeout=60)
    c.row_factory = sqlite3.Row
    return c


def universal_stats(content_hash: str, server_time_ms: int,
                    killer_client: int | None, round_no: int | None,
                    db: Path = RECOGNITION_DB) -> dict[str, Any]:
    """What the kill events alone can say, for ANY actor.

    An obituary is a server fact, not an observation of one player, so these
    hold whether or not the actor held the camera.
    """
    if killer_client is None:
        return {}
    with _conn(db) as c:
        near = c.execute(
            "SELECT server_time_ms FROM kill_events_v1 WHERE content_hash=? "
            "AND killer_client=? AND killer_class='PLAYER' "
            "AND server_time_ms BETWEEN ? AND ? ORDER BY server_time_ms",
            (content_hash, killer_client,
             server_time_ms - MULTIKILL_WINDOW_MS,
             server_time_ms + MULTIKILL_WINDOW_MS)).fetchall()
        prev = c.execute(
            "SELECT MAX(server_time_ms) FROM kill_events_v1 WHERE content_hash=? "
            "AND killer_client=? AND killer_class='PLAYER' AND server_time_ms<?",
            (content_hash, killer_client, server_time_ms)).fetchone()[0]
        nxt = c.execute(
            "SELECT MIN(server_time_ms) FROM kill_events_v1 WHERE content_hash=? "
            "AND killer_client=? AND killer_class='PLAYER' AND server_time_ms>?",
            (content_hash, killer_client, server_time_ms)).fetchone()[0]
        in_round = None
        if round_no is not None:
            in_round = int(c.execute(
                "SELECT COUNT(*) FROM kill_events_v1 WHERE content_hash=? "
                "AND killer_client=? AND killer_class='PLAYER' AND round=?",
                (content_hash, killer_client, round_no)).fetchone()[0])
    return {
        "round": round_no,
        "multikill_size": len(near),
        "actor_kills_this_round": in_round,
        "ms_since_actors_prev_kill": (server_time_ms - prev) if prev is not None else None,
        "ms_to_actors_next_kill": (nxt - server_time_ms) if nxt is not None else None,
    }


def recorder_stats(content_hash: str, server_time_ms: int,
                   db: Path = RECOGNITION_DB
                   ) -> tuple[dict[str, Any], dict[str, Any]]:
    """Measurements and sub-scores from the recogniser, when they exist.

    They exist only where the actor held the camera. Returns ({}, {}) rather
    than zeros when they do not -- a zero would be read as a measurement.
    """
    with _conn(db) as c:
        row = c.execute(
            "SELECT * FROM recognized_frags WHERE content_hash=? "
            "AND server_time_ms=? LIMIT 1",
            (content_hash, server_time_ms)).fetchone()
    if row is None:
        return {}, {}
    try:
        attrs = json.loads(row["attributes"] or "{}")
    except (ValueError, TypeError):
        attrs = {}
    stats = {out: attrs[src] for src, (out, _) in MEASURED.items()
             if attrs.get(src) is not None}
    keys = row.keys()
    subs = {k: row[k] for k in SUBSCORES if k in keys and row[k]}
    try:
        classes = [c.get("name") for c in json.loads(row["classes"] or "[]")]
    except (ValueError, TypeError):
        classes = []
    if classes:
        stats["recognised_as"] = classes[:6]
    return stats, subs


def for_clip(content_hash: str, server_time_ms: int,
             killer_client: int | None, round_no: int | None,
             is_actor_pov: bool, db: Path = RECOGNITION_DB) -> dict[str, Any]:
    """The stats block that ships with one clip.

    `availability` is not decoration. A consumer that treats a missing
    `distance_units` as "close range" instead of "not measurable from this
    camera" would be drawing a conclusion the data does not support, and this
    field is what stops that.
    """
    stats = universal_stats(content_hash, server_time_ms, killer_client,
                            round_no, db)
    subs: dict[str, Any] = {}
    if is_actor_pov:
        measured, subs = recorder_stats(content_hash, server_time_ms, db)
        stats.update(measured)
    return {
        "stats": stats,
        "machine_subscores": subs,
        "stats_availability": FULL if is_actor_pov else OBSERVED,
        "stats_note": (
            "measurements in game units, milliseconds and degrees; "
            "machine_subscores are the recogniser's own scale, not percentages"
            if is_actor_pov else
            "the actor did not hold the camera, so nothing derived from their "
            "aim, health, speed or view exists for this clip. The stats "
            "present are read from the kill events themselves and hold for "
            "any actor. Absent fields are unmeasurable here, not zero"),
    }
