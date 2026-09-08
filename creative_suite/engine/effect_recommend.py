"""Rule-based cinematic effect recommender.

recommend(frag_record) ranks seeded cinematic_effects presets for one frag.

frag_record dict shape (all keys optional except classes):
    {
        "classes":    ["AIR_ROCKET", "CLUTCH_1V4", ...],   # classifier tags
        "attributes": {"health": 8, "victim_airborne": True, ...},
        "scores":     {"composite": 91.5, ...},
        "mode_pool":  "MAIN_CA",
    }

Rules (mandate):
- AIR_ROCKET + airborne victim  -> orbit / projectile-cam presets boosted
- CLUTCH_1V4 + low hp           -> clutch package + health treatment
- PIXEL_SHOT                    -> PIXEL_REPLAY_ZOOM_V1
- EXTREME_SPEED                 -> HIGH_SPEED_CHASE_V1
- RAPID_MULTIKILL / MULTIKILL   -> MULTIKILL_ESCALATE_V1
- hero-intensity presets only when composite score clears HERO_SCORE_MIN
- anti-fatigue: effect used within the last FATIGUE_WINDOW frags of the
  same part is demoted to the bottom of the ranking
- allowed_game_modes gating: preset with non-empty allowed_game_modes only
  fires when the frag's mode_pool matches (MAIN_CA matches ["CA"]).
"""
from __future__ import annotations

import json
import sqlite3

from creative_suite.database import cinematic_db as cdb

HERO_SCORE_MIN = 85.0     # composite score needed to unlock 'hero' presets
FATIGUE_WINDOW = 6        # look-back frag count for anti-fatigue demotion
FATIGUE_PENALTY = 1000.0  # subtracted from a fatigued effect's score

# classifier tag -> canonical trigger tag used in preset trigger_types
CLASS_ALIASES = {
    "RAPID_MULTIKILL": "MULTIKILL",
    "TRIPLE_KILL": "MULTIKILL",
    "QUAD_KILL": "QUADKILL",
    "AIR_SHOT": "airshot",
    "HIGH_SPEED": "EXTREME_SPEED",
}

# rule boosts: (required classes frozenset) -> {effect_name: boost}
_RULE_BOOSTS: list[tuple[frozenset, dict[str, float]]] = [
    (frozenset({"AIR_ROCKET"}),
     {"AIR_ROCKET_ORBIT_V1": 15.0, "AIR_ROCKET_PROJECTILE_V1": 12.0}),
    (frozenset({"AIR_GRENADE"}), {"AIR_GRENADE_FOLLOW_V1": 15.0}),
    (frozenset({"CLUTCH_1V4", "LOW_HP"}),
     {"CLUTCH_1V4_V1": 20.0, "LOW_HP_V1": 8.0, "CRITICAL_HP_V1": 8.0,
      "NEAR_DEATH_V1": 8.0}),
    (frozenset({"PIXEL_SHOT"}), {"PIXEL_REPLAY_ZOOM_V1": 15.0}),
    (frozenset({"EXTREME_SPEED"}), {"HIGH_SPEED_CHASE_V1": 15.0}),
    (frozenset({"MULTIKILL"}), {"MULTIKILL_ESCALATE_V1": 15.0}),
    (frozenset({"FINAL_FRAG"}), {"FINAL_FRAG_HERO_V1": 15.0}),
]


def _derived_classes(frag: dict) -> set[str]:
    """Expand raw classes with aliases and attribute-derived situations."""
    classes = {c["name"] if isinstance(c, dict) else c
               for c in frag.get("classes", [])}
    for c in list(classes):
        alias = CLASS_ALIASES.get(c)
        if alias:
            classes.add(alias)
    attrs = frag.get("attributes") or {}
    health = attrs.get("health")
    if health is not None:
        if health <= 25:
            classes.add("LOW_HP")
        if health <= 10:
            classes.add("CRITICAL_HP")
        if health <= 5:
            classes.add("NEAR_DEATH")
    if attrs.get("low_hp"):
        classes.add("LOW_HP")
    if attrs.get("victim_airborne") and "AIR_ROCKET" not in classes:
        classes.add("airshot")
    return classes


def _mode_allowed(allowed_modes: list[str] | None, mode_pool: str | None) -> bool:
    if not allowed_modes:
        return True  # empty / NULL = no gating
    if not mode_pool:
        return False
    up = mode_pool.upper()
    return any(m.upper() == up or m.upper() in up.split("_")
               for m in allowed_modes)


def recommend(frag_record: dict,
              conn: sqlite3.Connection | None = None,
              *,
              part_name: str | None = None,
              fatigue_window: int = FATIGUE_WINDOW,
              hero_score_min: float = HERO_SCORE_MIN,
              limit: int = 8) -> list[tuple[str, str, str]]:
    """Rank seeded effects for one frag.

    Returns [(effect_name, intensity, reason)] best-first. Deterministic:
    score desc, then name asc.
    """
    close_after = conn is None
    if conn is None:
        conn = cdb.connect()
    try:
        classes = _derived_classes(frag_record)
        composite = float((frag_record.get("scores") or {})
                          .get("composite", 0.0))
        mode_pool = frag_record.get("mode_pool")

        rows = conn.execute(
            "SELECT effect_id, name, intensity, trigger_types, "
            "allowed_game_modes FROM cinematic_effects WHERE enabled = 1"
        ).fetchall()

        scored: list[tuple[float, str, str, str]] = []
        for effect_id, name, intensity, triggers_j, modes_j in rows:
            triggers = set(json.loads(triggers_j) if triggers_j else [])
            matched = sorted(triggers & classes)
            if not matched:
                continue
            allowed = json.loads(modes_j) if modes_j else []
            if not _mode_allowed(allowed, mode_pool):
                continue
            if intensity == "hero" and composite < hero_score_min:
                continue  # hero presets reserved for top composite scores
            score = 10.0 * len(matched)
            reasons = ["matched " + "+".join(matched)]
            for required, boosts in _RULE_BOOSTS:
                if required <= classes and name in boosts:
                    score += boosts[name]
                    reasons.append("rule " + "+".join(sorted(required)))
            if intensity == "hero":
                reasons.append(f"hero unlocked (composite {composite:g})")
            if (part_name is not None and cdb.effects_used_recently(
                    conn, part_name, effect_id, fatigue_window)):
                score -= FATIGUE_PENALTY
                reasons.append(
                    f"fatigue: used within last {fatigue_window} frags")
            scored.append((score, name, intensity, "; ".join(reasons)))

        scored.sort(key=lambda t: (-t[0], t[1]))
        return [(name, intensity, reason)
                for _, name, intensity, reason in scored[:limit]]
    finally:
        if close_after:
            conn.close()
