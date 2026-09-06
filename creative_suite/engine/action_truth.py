"""ActionTruth: the one description of what happened, for everyone.

PANTHEON OWNS THE SEMANTICS. Wolfcam is a capture backend; SQLite is storage;
the browser renders. What a moment WAS -- who did it to whom, with what, from
what health, at what speed, inside which round -- is computed here, once, and
every consumer reads the same answer.

WHO CONSUMES THIS. The reviewer today. The effect planner, the camera
planner, the music planner and scene selection next. If the dossier said an
action was CRITICAL_HP and the choreographer later computed something else
from the same rows, one of them would be lying to the director, and there
would be no way to tell which.

ONE RULE ABOVE ALL: PARTIAL TRUTH IS FINE, FALSE CERTAINTY IS NOT. Every
field is measured or absent. Missing health reads UNKNOWN, never 0. An
accuracy that cannot be attributed reads NOT_DERIVABLE with its reason, never
0%. Expensive decisions get made from this object.

SCOPE TRAVELS WITH THE NUMBER. Health, armor and the trigger stream belong to
whoever held the camera. On a foreign-camera observation they are the
cameraman's, not the actor's, and are withheld rather than relabelled.

The review-facing shape lives in `dossier.py`, which is a thin adapter over
this. Nothing computes truth twice.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
RECOGNITION_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"

UNKNOWN = None          # rendered as UNKNOWN; never 0

# Health thresholds for the production-context tags. These are creative
# context -- a low-health kill may want a heartbeat, a red world, slowed time
# -- and never a quality judgement.
LOW_HP = 40
CRITICAL_HP = 20
LOW_STACK = 50          # health + armor combined


def _conn(db: Path = RECOGNITION_DB) -> sqlite3.Connection:
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=60)
    c.row_factory = sqlite3.Row
    return c


def _attrs(row: sqlite3.Row | None) -> dict[str, Any]:
    if row is None:
        return {}
    try:
        return json.loads(row["attributes"] or "{}")
    except (ValueError, TypeError):
        return {}


def _stack(a: dict[str, Any], is_actor_pov: bool) -> dict[str, Any]:
    """Health and armor through the action, or an honest absence.

    Health is the RECORDER's. When the actor is somebody else this is the
    cameraman's stack and says nothing about the person who made the kill,
    so it is withheld.
    """
    if not is_actor_pov:
        return {"available": False,
                "reason": "health belongs to whoever held the camera, and "
                          "that was not the actor"}
    h = a.get("health_at_frag")
    if h is None:
        return {"available": False,
                "reason": "not extracted for this frag -- health covers "
                          "31.4% of the corpus, and the rest reads UNKNOWN"}
    tags = []
    armor = a.get("armor_at_frag")
    if h <= CRITICAL_HP:
        tags.append("CRITICAL_HP_ACTION")
    elif h <= LOW_HP:
        tags.append("LOW_HP_ACTION")
    if armor is not None and (h + armor) <= LOW_STACK:
        tags.append("LOW_STACK_ACTION")
    if a.get("min_health_10s") is not None and a["min_health_10s"] <= CRITICAL_HP \
            and h > a["min_health_10s"]:
        tags.append("SURVIVAL")
    return {
        "available": True,
        "start": {"health": a.get("engagement_start_health"),
                  "armor": a.get("engagement_start_armor")},
        "min": {"health": a.get("min_health_10s"),
                "armor": a.get("min_armor_10s")},
        "at_frag": {"health": h, "armor": armor},
        "biggest_drop": a.get("biggest_drop_10s"),
        "health_recovered": a.get("health_recovered"),
        "tags": tags,
        "provenance": "OBSERVED — recorder playerstate",
    }


def _movement(a: dict[str, Any], occurrence_id: int,
              db: Path) -> dict[str, Any]:
    """Speed at the action, plus any linked movement moment."""
    out: dict[str, Any] = {"speed_at_frag": a.get("killer_speed"),
                           "percentile": a.get("attacker_speed_percentile"),
                           "victim_speed": a.get("victim_speed"),
                           "victim_air_height": a.get("victim_air_height")}
    with _conn(db) as c:
        m = c.execute(
            "SELECT kind, peak_speed, mean_speed, entry_speed, exit_speed, "
            "duration_ms, speed_pctile, traits FROM movement_moments_v1 "
            "WHERE related_occurrence_id=? LIMIT 1", (occurrence_id,)).fetchone()
    if m is not None:
        try:
            traits = json.loads(m["traits"] or "[]")
        except (ValueError, TypeError):
            traits = []
        out["moment"] = {"kind": m["kind"], "peak": m["peak_speed"],
                         "mean": m["mean_speed"], "entry": m["entry_speed"],
                         "exit": m["exit_speed"],
                         "duration_ms": m["duration_ms"],
                         "percentile": m["speed_pctile"], "traits": traits}
    return out


def _traits(a: dict[str, Any], row: sqlite3.Row | None,
            occurrence_id: int, db: Path) -> list[str]:
    """Machine facts worth a chip. Descriptive; never a human verdict."""
    out: list[str] = []
    if row is not None:
        try:
            out += [c.get("name") for c in json.loads(row["classes"] or "[]")
                    if c.get("name")]
        except (ValueError, TypeError):
            pass
    with _conn(db) as c:
        if c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND "
                     "name='funny_candidates_v1'").fetchone():
            f = c.execute("SELECT signals FROM funny_candidates_v1 WHERE "
                          "occurrence_id=?", (occurrence_id,)).fetchone()
            if f:
                try:
                    out += json.loads(f["signals"] or "[]")
                except (ValueError, TypeError):
                    pass
    seen, uniq = set(), []
    for t in out:
        if t and t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq


def _timing(scene, occurrence_id: int) -> dict[str, Any]:
    """Where this action sits in its scene, and how far the neighbours are.

    "F2 of 4, next one 3.85s later, jump pad 8s after that" is what tells a
    director whether a round is a build or four separate incidents.
    """
    if scene is None:
        return {"available": False}
    frags = [e for e in scene.events if e.kind == "USER_FRAG"]
    me = next((e for e in scene.events if e.occurrence_id == occurrence_id),
              None)
    if me is None:
        return {"available": False}
    idx = next((i for i, e in enumerate(frags)
                if e.occurrence_id == occurrence_id), None)
    prev_f = frags[idx - 1] if idx not in (None, 0) else None
    next_f = frags[idx + 1] if idx is not None and idx + 1 < len(frags) else None
    others = [e for e in scene.events
              if e.occurrence_id is None and e.t_ms != me.t_ms]
    nearest = min(others, key=lambda e: abs(e.t_ms - me.t_ms)) if others else None
    return {
        "available": True,
        "frag_index": me.frag_index,
        "frags_in_scene": len(frags),
        "ms_since_previous_user_frag": (me.t_ms - prev_f.t_ms) if prev_f else None,
        "ms_to_next_user_frag": (next_f.t_ms - me.t_ms) if next_f else None,
        "offset_in_scene_ms": me.offset_ms,
        "scene_duration_ms": scene.end_ms - scene.start_ms,
        "nearest_scene_event": ({"label": nearest.label,
                                 "delta_ms": nearest.t_ms - me.t_ms}
                                if nearest else None),
    }


def _career_rank(rf: sqlite3.Row | None, db: Path) -> int | None:
    """Where this frag sits in the career ranking, worst first."""
    if rf is None or rf["highlight_score"] is None:
        return UNKNOWN
    with _conn(db) as c:
        return int(c.execute(
            "SELECT COUNT(*) FROM recognized_frags WHERE highlight_score < ?",
            (rf["highlight_score"],)).fetchone()[0]) + 1


# WHICH FAMILIES THIS MODULE CAN SPEAK FOR.
#
# `source_id` is an integer, and an integer means nothing on its own. Before
# this gate, `ACTION:41` reached here and was read as occurrence 41 -- an
# unrelated kill by an unrelated player -- and the reviewer was shown its
# health, its weapon and its opponent as though they described the action.
# Nothing errored, because 41 is a perfectly good occurrence id.
#
# So dispatch is by NAMESPACE, and anything this module cannot describe gets
# an explicit refusal rather than somebody else's truth.
OCCURRENCE_BACKED = ("USER_FRAG", "FRAG", "TELEFRAG", "DEATH", "CLAN_FRAG",
                     "ALL_KILL")


def for_item(item_id: str, db: Path = RECOGNITION_DB) -> dict[str, Any] | None:
    """Everything truthfully known about one moment.

    Keyed by review item today because that is how the reviewer
    addresses a moment; the canonical identity underneath is the
    occurrence id, which is what production will key on.
    """
    from creative_suite.engine import action_stats as ast
    from creative_suite.engine import production_usage as pu
    from creative_suite.engine import review_corpus as rc
    from creative_suite.engine import round_story as rs
    from creative_suite.engine import scene as sc
    from creative_suite.engine.quake_names import display_name

    it = rc.item(item_id)
    if it is None:
        return None
    # FAIL CLOSED. An unsupported family is UNSUPPORTED, never another
    # family's moment that happens to share an integer.
    family = str(item_id).split(":", 1)[0]
    if family not in OCCURRENCE_BACKED or it.item_type not in OCCURRENCE_BACKED:
        return {"item_id": item_id, "available": False,
                "target_type": it.item_type,
                "reason": (f"{it.item_type} is not an occurrence-backed "
                           f"family; ActionTruth describes canonical kills "
                           f"and cannot speak for this target")}
    occ_id = it.source_id

    with _conn(db) as c:
        o = c.execute(
            "SELECT o.*, k.content_hash, k.is_recorder_killer, "
            "k.killer_name_raw, k.victim_name_raw "
            "FROM kill_occurrences_v1 o JOIN kill_events_v1 k "
            "ON k.kill_event_id = o.best_observation_id "
            "WHERE o.occurrence_id=?", (occ_id,)).fetchone()
        rf = None
        if o is not None:
            rf = c.execute(
                "SELECT attributes, classes, highlight_score, "
                "recognition_version FROM recognized_frags WHERE "
                "content_hash=? AND server_time_ms=? LIMIT 1",
                (o["content_hash"], o["server_time_ms"])).fetchone()
    if o is None:
        return {"item_id": item_id, "available": False,
                "reason": "this family has no canonical occurrence"}

    a = _attrs(rf)
    pov = bool(o["is_recorder_killer"])
    stats = ast.for_action(o["content_hash"], o["server_time_ms"], o["mod"],
                           o["victim_client"], pov,
                           display_name(o["victim_name_raw"]) or None, db=db)
    ctx = rs.round_context(o["content_hash"], o["round"])
    scene = sc.build_scene(o["content_hash"], o["round"]) if o["round"] else None
    usage = pu.states([occ_id]).get(occ_id, {})

    return {
        "item_id": item_id,
        "available": True,
        "event": {
            "occurrence_id": occ_id,
            "actor": display_name(o["killer_name_raw"]) or None,
            "opponent": display_name(o["victim_name_raw"]) or None,
            "weapon": o["mod_name"],
            "map": o["map"],
            "round": o["round"],
            "time_in_round_ms": (o["server_time_ms"] - ctx.start_ms) if ctx else None,
            "camera": ("ACTOR OWN POV" if pov else
                       "OBSERVED — another player's demo"),
            "is_actor_pov": pov,
            "machine_score": rf["highlight_score"] if rf else UNKNOWN,
            "machine_score_version": (f"recognition-v{rf['recognition_version']}"
                                      if rf else UNKNOWN),
            # item() does not compute a rank for a single lookup, so it is
            # counted here: how many scored frags sit below this one.
            "career_rank": _career_rank(rf, db),
            "career_total": it.total_items,
            "death_cause": o["death_cause"],
            "n_observations": o["n_observations"],
        },
        "usage": {"state": usage.get("state", "AVAILABLE"),
                  "detail": usage.get("detail", "")},
        "stack": _stack(a, pov),
        "action": stats.to_dict(),
        "damage": {
            # Only where a ledger genuinely exists. There is no general
            # per-engagement damage attribution, and deriving one from health
            # deltas would credit the user with a teammate's splash.
            "lg_dealt_3s": a.get("lg_damage_burst_3s"),
            "taken_in_fight": a.get("lg_taken_total_dmg"),
            "lowest_health_in_fight": a.get("lg_min_health"),
            "available": any(a.get(k) is not None for k in
                             ("lg_damage_burst_3s", "lg_taken_total_dmg")),
            "scope": "lightning-gun engagements only",
        },
        "geometry": {"distance_units": a.get("distance"),
                     "flick_degrees": a.get("flick_degrees"),
                     "flick_duration_ms": a.get("flick_duration_ms"),
                     "flick_deg_per_s": a.get("deg_per_sec"),
                     "target_visible_ms": a.get("visibility_ms")},
        "movement": _movement(a, occ_id, db),
        "traits": _traits(a, rf, occ_id, db),
        "round": (ctx.to_dict() if ctx else None),
        # How this moment sits in the sequence. A director choosing where the
        # music builds needs the gaps, not just the events.
        "timing": _timing(scene, occ_id),
        "scene": ({"scene_id": scene.scene_id, "mode": scene.mode,
                   "reason": scene.reason, "user_frags": scene.user_frags,
                   "total_kills": scene.total_kills,
                   "media_start_ms": scene.media_start_ms,
                   "media_end_ms": scene.media_end_ms,
                   "events": scene.to_dict()["events"]} if scene else None),
    }
