"""Frag browser API — read-only view over frag_recognition.db + demo_v2.db.

Serves the /frags debug UI: browse all recognized frags, inspect their
recognition evidence (classes / attributes / reasons), and stream the
captured master AVI when one exists.

HARD RULES honored here:
- Both databases are opened with sqlite3 ``mode=ro`` URIs — never written.
- A frag maps to a master clip when ``demo_name`` matches and the frag's
  ``server_time_ms`` falls inside ``[capture_start_ms, capture_end_ms]``.
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse

from creative_suite.engine import review_proxy
from creative_suite.engine.music_features_v2 import MusicFeatureStore

router = APIRouter()

_DB_DIR = Path(__file__).parent.parent / "database"
# Module-level so tests can monkeypatch them.
FRAG_DB_PATH = _DB_DIR / "frag_recognition.db"
DEMO_V2_DB_PATH = _DB_DIR / "demo_v2.db"
MUSIC_FEATURE_DB_PATH = _DB_DIR / "music_features_v2.db"
MUSIC_AUDITION_DIR = Path(__file__).parents[2] / "output" / "demo_v2" / "music_auditions"

# classes-endpoint cache: {str(db_path): [{"name":..., "count":...}, ...]}
_classes_cache: dict[str, list[dict[str, Any]]] = {}
_taxonomy_cache: dict[str, dict[str, Any]] = {}

_TAXONOMY: tuple[dict[str, Any], ...] = (
    {"id": "best", "label": "BEST", "categories": (
        ("top_50", "Top 50", ()), ("user_love", "User LOVE", ()),
        ("user_keep", "User KEEP", ()),)},
    {"id": "rocket", "label": "ROCKET", "categories": (
        ("direct_rocket", "Direct", ("DIRECT_CONFIRMED_GEO", "DIRECT_ROCKET", "DIRECT_LIKELY")),
        ("air_rocket", "Air Rocket", ("AIRSHOT", "AIR_ROCKET", "AIR_ROCKET_GEO", "HIGH_AIR_ROCKET")),
        ("prediction_rocket", "Prediction", ("PREDICTION_TEMPORAL", "ROCKET_POPUP")),
        ("rocket_jump", "Rocket Jump", ("ROCKET_JUMP_FRAG", "ROCKET_JUMP_ENTRY")),
        ("high_speed_rocket", "High-Speed Rocket", ("HIGH_SPEED_ROCKET",)),)},
    {"id": "rail", "label": "RAIL / AIM", "categories": (
        ("pixel", "Pixel", ("PIXEL_SHOT_GEO", "PIXEL_SHOT_RENDER_CONFIRMED")),
        ("tiny_gap", "Tiny Gap", ("TINY_GAP",)), ("reaction", "Reaction", ("REACTION_SHOT",)),
        ("clean_flick", "Clean Flick", ("CLEAN_FLICK",)),
        ("extreme_flick", "Extreme Flick", ("EXTREME_FLICK",)),
        ("tracking_sweep", "Tracking Sweep", ("AGGRESSIVE_TRACKING_SWEEP",)),
        ("high_speed_aim", "High-Speed Aim", ("HIGH_SPEED_AIM_TRANSITION", "LARGE_AIM_TRANSITION")),
        ("long_range", "Long Range", ("LONG_RANGE_RAIL",)),
        ("air_rail", "Air Rail", ("AIR_RAIL", "RAIL_AIR")),)},
    {"id": "lightning", "label": "LIGHTNING", "categories": (
        ("lg_tracking", "Tracking", ("LG_TRACK", "LG_TRACKING", "LG_TRACKING_EXCELLENT")),
        ("lg_pressure", "High Pressure", ("LG_HIGH_PRESSURE",)),
        ("lg_transfer", "Target Transfer", ("LG_TARGET_TRANSFER",)),
        ("lg_multitarget", "Multitarget", ("LG_MULTITARGET",)),
        ("lg_dodge", "Dodge + Frag", ("LG_DODGE_MASTER", "DODGE_AND_FRAG")),
        ("lg_speed", "High-Speed LG", ("LG_HIGH_SPEED_TRACKING",)),)},
    {"id": "grenade", "label": "GRENADE", "categories": (
        ("air_grenade", "Air Grenade", ("AIR_GRENADE",)),
        ("prediction_grenade", "Prediction", ("PREDICTION_GRENADE",)),
        ("bounce_grenade", "Bounce", ("BOUNCE_PREDICTION", "MULTI_BOUNCE_FRAG")),
        ("direct_grenade", "Direct", ("DIRECT_GRENADE",)),)},
    {"id": "movement", "label": "MOVEMENT", "categories": (
        ("extreme_speed", "Extreme Speed", ("EXTREME_SPEED", "EXTREME_SPEED_FRAG")),
        ("high_speed_frag", "High-Speed Frag", ("HIGH_SPEED_FRAG", "VERY_HIGH_SPEED_FRAG", "VERY_FAST_FRAG")),
        ("high_speed_multikill", "High-Speed Multikill", ("HIGH_SPEED_MULTIKILL",)),
        ("strafe_chain", "Strafe Chain", ("STRAFE_CHAIN", "STRAFE_CHAIN_FRAG")),
        ("dodge_kill", "Dodge & Kill", ("DODGE_AND_KILL",)),
        ("escape_turn", "Escape / Turnaround", ("ESCAPE_TURNAROUND",)),)},
    {"id": "multikill", "label": "MULTIKILL", "categories": (
        ("double", "Double", ("DOUBLE", "MULTIKILL_DOUBLE")),
        ("triple", "Triple", ("TRIPLE", "MULTIKILL_TRIPLE")),
        ("quad", "Quad", ("QUAD", "MULTIKILL_QUAD")),
        ("five_plus", "5+", ("MULTIKILL_5_PLUS", "MULTIKILL_6_PLUS", "MULTIKILL_7_PLUS", "MULTIKILL_8_PLUS")),
        ("rapid_multikill", "Rapid", ("RAPID_MULTIKILL",)),
        ("high_density_multikill", "High Density", ("HIGH_DENSITY_MULTIKILL",)),
        ("multi_weapon", "Multi-Weapon", ("MULTI_WEAPON_CHAIN", "WEAPON_COMBO")),)},
    {"id": "clan_arena", "label": "CLAN ARENA", "categories": (
        ("clutch_1v2", "1v2", ("CLUTCH_1V2",)),
        ("clutch_1v3", "1v3", ("CLUTCH_1V3",)),
        ("clutch_1v4", "1v4+", ("CLUTCH_1V4_PLUS",)),
        ("last_man", "Last Man", ("LAST_MAN_SEQUENCE",)),
        ("round_save", "Round Save", ("ROUND_SAVE",)),
        ("team_wipe", "Team Wipe", ("TEAM_WIPE",)),
        ("round_comeback", "Round Comeback", ("ROUND_COMEBACK", "OUTNUMBERED_ROUND_WIN")),)},
)


def _category_classes(category_id: str) -> tuple[str, ...] | None:
    for family in _TAXONOMY:
        for item_id, _label, classes in family["categories"]:
            if item_id == category_id:
                return classes
    return None


# ---------------------------------------------------------------------------
# Combinable multi-select filter groups.
#
# docs/reference/frag-taxonomy-review.md organizes all 62 classes into 8
# families: Projectile skill, Rail, Aim, LG, Multikill/clutch/fights,
# Movement, Health drama, Weapon craft. Those 8 are collapsed pairwise into
# 4 named groups here, each exposed as its own combinable `<id>_group` query
# param on GET /api/frags:
#   - "skill"    = Projectile skill + Rail + Aim + LG        -> how hard was
#                  the shot (every family whose evidence is aim/positioning).
#   - "context"  = Multikill/clutch/fights + Health drama    -> how much was
#                  on the line when the kill happened.
#   - "movement" = Movement/speed (kept standalone — answers a different
#                  question than either bucket above: raw traversal speed).
#   - "craft"    = Weapon craft (kept standalone — weapon-swap technique,
#                  orthogonal to both aim skill and situational stakes).
# Semantics: within one group's comma-list, OR (frag matches if ANY listed
# class name is present in its `classes` JSON). Across different groups
# (and combined with the existing `class`/`weapon`/`category` filters), AND.
# Filter values are raw class names (e.g. "AIR_ROCKET"), not category ids —
# the same vocabulary already surfaced by GET /api/frags/classes.
# ---------------------------------------------------------------------------
_FILTER_GROUPS: dict[str, tuple[str, ...]] = {
    "skill": (
        # Projectile skill (rockets / grenades)
        "DIRECT_ROCKET", "DIRECT_CONFIRMED_GEO", "NEAR_DIRECT", "AIR_ROCKET",
        "AIR_ROCKET_GEO", "AIR_GRENADE", "PREDICTION_TEMPORAL",
        "PREDICTION_CANDIDATE",
        # Rail
        "RAIL_FRAG", "RAIL_AIR", "RAIL_CONSECUTIVE", "RAIL_FLICK",
        "PIXEL_SHOT_GEO", "PIXEL_SHOT_CANDIDATE", "TINY_GAP_SHOT",
        "REACTION_SHOT", "REACTION_SHOT_CANDIDATE", "CORNER_PREFIRE_CONFIRMED",
        # Aim
        "FLICK_SHOT", "CLEAN_FLICK", "EXTREME_FLICK",
        "HIGH_SPEED_AIM_TRANSITION", "AGGRESSIVE_TRACKING_SWEEP",
        "LARGE_AIM_TRANSITION", "TARGET_TRANSFER",
        # LG
        "LG_TRACKING", "LG_HIGH_ACCURACY", "LG_HIGH_PRESSURE",
        "LG_DODGE_MASTER", "LG_TRANSFER", "DAMAGE_BURST",
    ),
    "context": (
        # Multikill / clutch / fights
        "MULTIKILL_DOUBLE", "MULTIKILL_TRIPLE", "MULTIKILL_QUAD",
        "RAPID_MULTIKILL", "HIGH_SPEED_MULTIKILL", "CLUTCH_1V2", "CLUTCH_1V3",
        "CLUTCH_1V4_PLUS",
        # Health drama
        "LOW_HP_FRAG", "CRITICAL_HP_FRAG", "LAST_HP_FRAG", "LAST_HP_CANDIDATE",
        "LOW_HEALTH_WIN", "HEAVY_DAMAGE_SURVIVED",
    ),
    "movement": (
        "HIGH_SPEED_FRAG", "VERY_FAST_FRAG", "EXTREME_SPEED",
        "SPEED_TARGET_FRAG", "HIGH_SPEED_AIR_FRAG", "VERTICAL_ACTION",
        "STRAFE_CHAIN_FRAG", "ROCKET_JUMP_ENTRY", "ROCKET_JUMP_FRAG",
        "DODGE_AND_KILL", "ESCAPE_TURNAROUND",
        # Dodge / near-miss (engine/parser/extract_dodge_events.py,
        # 2026-09-01 — incoming rail/rocket/grenade fire that passed close
        # and missed, plus the composite "dodge then frag" moment)
        "NEAR_MISS_RAIL", "NEAR_MISS_ROCKET", "NEAR_MISS_GRENADE",
        "DODGE_STRAFE", "DODGE_TO_KILL",
        # Dodge QUALITY tier (reclassify_v2 DODGE QUALITY SCORE, 2026-09-01)
        # — the rare hero-grade subset of the broad evidence above.
        # DODGE_HERO is a strict subset of the two weapon-specific labels.
        "DODGE_HERO", "RAIL_DODGE_HERO", "PROJECTILE_DODGE_HERO",
    ),
    "craft": (
        "WEAPON_COMBO", "MULTI_WEAPON_CHAIN", "FAST_WEAPON_SWITCH",
        "WEAPON_SWITCH_FINISH", "COMBO_KILL", "POPUP_COMBO",
    ),
}
_FILTER_GROUP_LABELS = {
    "skill": "Skill", "context": "Context", "movement": "Movement",
    "craft": "Weapon Craft",
}


def _flatten_multi(values: list[str] | None) -> list[str]:
    """Accept a filter param passed as repeated query params AND/OR a
    comma-separated list within a single value; flatten to one list."""
    if not values:
        return []
    out: list[str] = []
    for raw in values:
        for part in raw.split(","):
            part = part.strip()
            if part:
                out.append(part)
    return out

_MASTER_SUBQ = (
    "(SELECT gc.generated_clip_id FROM dv.generated_clips gc "
    " WHERE gc.demo_name = rf.demo_name "
    "   AND rf.server_time_ms BETWEEN gc.capture_start_ms AND gc.capture_end_ms "
    " ORDER BY gc.generated_clip_id LIMIT 1)"
)


def _connect() -> sqlite3.Connection:
    """Read-only connection to frag_recognition.db with demo_v2.db attached."""
    if not FRAG_DB_PATH.exists():
        raise HTTPException(status_code=503, detail="frag_recognition.db not found")
    conn = sqlite3.connect(
        f"file:{FRAG_DB_PATH.as_posix()}?mode=ro", uri=True, check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    if DEMO_V2_DB_PATH.exists():
        conn.execute(
            "ATTACH DATABASE ? AS dv",
            (f"file:{DEMO_V2_DB_PATH.as_posix()}?mode=ro",),
        )
    else:
        # Attach an empty in-memory stand-in so queries referencing
        # dv.generated_clips still parse.
        conn.execute("ATTACH DATABASE ':memory:' AS dv")
        conn.execute(
            "CREATE TABLE dv.generated_clips ("
            " generated_clip_id INTEGER PRIMARY KEY, demo_name TEXT,"
            " server_time_ms INTEGER, capture_start_ms INTEGER,"
            " capture_end_ms INTEGER, tier TEXT, class TEXT, qa_status TEXT,"
            " avi_path TEXT, rank_score REAL, map TEXT, victims TEXT,"
            " mods TEXT, frag_offsets_ms TEXT)"
        )
    return conn


def _parse_json(text: Any, default: Any) -> Any:
    if not text:
        return default
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return default


def _class_names(classes_raw: Any) -> list[str]:
    """classes JSON is a list of {name,...} dicts or bare strings."""
    out: list[str] = []
    for c in _parse_json(classes_raw, []):
        if isinstance(c, dict):
            name = c.get("name")
            if name:
                out.append(str(name))
        elif isinstance(c, str):
            out.append(c)
    return out


def _master_row(conn: sqlite3.Connection, clip_id: int | None) -> dict[str, Any] | None:
    if clip_id is None:
        return None
    row = conn.execute(
        "SELECT * FROM dv.generated_clips WHERE generated_clip_id = ?", (clip_id,)
    ).fetchone()
    if row is None:
        return None
    d = dict(row)
    avi = d.get("avi_path")
    d["avi_on_disk"] = bool(avi) and Path(str(avi)).exists()
    for key in ("victims", "mods", "frag_offsets_ms"):
        d[key] = _parse_json(d.get(key), d.get(key))
    return d


@router.get("/api/frags/classes")
def list_class_labels() -> list[dict[str, Any]]:
    """Distinct class label names with counts (cached per db path)."""
    key = str(FRAG_DB_PATH)
    cached = _classes_cache.get(key)
    if cached is not None:
        return cached
    conn = _connect()
    try:
        counts: dict[str, int] = {}
        for (classes_raw,) in conn.execute(
            "SELECT classes FROM recognized_frags WHERE classes IS NOT NULL"
        ):
            for name in _class_names(classes_raw):
                counts[name] = counts.get(name, 0) + 1
        result = [
            {"name": name, "count": count}
            for name, count in sorted(counts.items(), key=lambda kv: -kv[1])
        ]
        _classes_cache[key] = result
        return result
    finally:
        conn.close()


@router.get("/api/frags/taxonomy")
def frag_taxonomy() -> dict[str, Any]:
    key = str(FRAG_DB_PATH)
    cached = _taxonomy_cache.get(key)
    if cached is not None:
        return cached
    conn = _connect()
    try:
        class_sets = [set(_class_names(raw)) for (raw,) in conn.execute(
            "SELECT classes FROM recognized_frags WHERE classes IS NOT NULL"
        )]
    finally:
        conn.close()
    families: list[dict[str, Any]] = []
    for family in _TAXONOMY:
        categories = []
        for item_id, label, classes in family["categories"]:
            if item_id == "top_50":
                count = min(50, len(class_sets))
            elif item_id == "user_love":
                count = review_proxy.count_reviews("LOVE")
            elif item_id == "user_keep":
                count = review_proxy.count_reviews("KEEP")
            else:
                wanted = set(classes)
                count = sum(bool(names & wanted) for names in class_sets)
            categories.append({"id": item_id, "label": label,
                               "count": count, "classes": list(classes)})
        families.append({"id": family["id"], "label": family["label"],
                         "categories": categories})
    result = {"families": families}
    _taxonomy_cache[key] = result
    return result


@router.get("/api/frags/filter-groups")
def list_filter_groups() -> dict[str, Any]:
    """Class names bucketed into the 4 combinable filter groups, with live
    counts (reuses the /api/frags/classes cache) — feeds the frontend's
    multi-select checkbox panel."""
    counts = {c["name"]: c["count"] for c in list_class_labels()}
    groups = [
        {
            "id": gid,
            "label": _FILTER_GROUP_LABELS.get(gid, gid.title()),
            "query_param": f"{gid}_group",
            "classes": [
                {"name": name, "count": counts.get(name, 0)} for name in classes
            ],
        }
        for gid, classes in _FILTER_GROUPS.items()
    ]
    return {"groups": groups}


@router.get("/api/frags")
def list_frags(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    min_score: float | None = Query(default=None),
    min_speed: float | None = Query(
        default=None,
        description="Filters on the raw recorder movement speed at the kill "
                     "(attributes.killer_speed, Quake units/sec — NOT the "
                     "percentile field). Frags with no killer_speed never match.",
    ),
    weapon: str | None = Query(default=None),
    class_: str | None = Query(default=None, alias="class"),
    demo: str | None = Query(default=None),
    mode_pool: str = Query(default="MAIN_CA"),
    has_master: bool | None = Query(default=None),
    sort: str = Query(default="score", description="score | time | speed | custom"),
    category: str | None = Query(default=None),
    skill_group: list[str] | None = Query(default=None),
    context_group: list[str] | None = Query(default=None),
    movement_group: list[str] | None = Query(default=None),
    craft_group: list[str] | None = Query(default=None),
    custom_weights: str | None = Query(
        default=None,
        description="JSON object {class_name: weight}. When present, "
                     "custom_score = highlight_score + sum(weight for each "
                     "matching class on the frag) is computed per-request "
                     "only (never persisted) and returned per row. "
                     "sort=custom re-sorts the whole filtered set by it.",
    ),
) -> dict[str, Any]:
    weights: dict[str, float] | None = None
    if custom_weights:
        try:
            parsed = json.loads(custom_weights)
            if not isinstance(parsed, dict):
                raise ValueError("must be a JSON object")
            weights = {str(k): float(v) for k, v in parsed.items()}
        except (ValueError, TypeError) as exc:
            raise HTTPException(
                status_code=422, detail=f"invalid custom_weights: {exc}"
            ) from exc
    if sort == "custom" and not weights:
        raise HTTPException(
            status_code=422, detail="sort=custom requires custom_weights"
        )

    conn = _connect()
    try:
        where: list[str] = []
        params: list[Any] = []
        if min_score is not None:
            where.append("rf.highlight_score >= ?")
            params.append(min_score)
        if min_speed is not None:
            where.append("json_extract(rf.attributes, '$.killer_speed') >= ?")
            params.append(min_speed)
        if weapon:
            where.append("rf.weapon_name = ?")
            params.append(weapon)
        if class_:
            where.append("rf.classes LIKE ?")
            params.append(f"%{class_}%")
        if category:
            classes = _category_classes(category)
            if classes is None:
                raise HTTPException(status_code=422, detail=f"unknown category: {category}")
            if classes:
                where.append("(" + " OR ".join("rf.classes LIKE ?" for _ in classes) + ")")
                params.extend(f'%"{name}"%' for name in classes)
            elif category == "top_50":
                where.append("rf.id IN (SELECT id FROM recognized_frags "
                             "ORDER BY highlight_score DESC, id ASC LIMIT 50)")
            elif category in ("user_love", "user_keep"):
                ids = review_proxy.reviewed_frag_ids(category.removeprefix("user_").upper())
                if not ids:
                    where.append("0")
                else:
                    where.append("rf.id IN (" + ",".join("?" * len(ids)) + ")")
                    params.extend(ids)
        # Combinable multi-select groups: OR within a group, AND across groups
        # (each populated group contributes its own where-clause item, which
        # is then AND-joined below with everything else — see _FILTER_GROUPS).
        for raw_group in (skill_group, context_group, movement_group, craft_group):
            names = _flatten_multi(raw_group)
            if names:
                where.append("(" + " OR ".join("rf.classes LIKE ?" for _ in names) + ")")
                params.extend(f'%"{name}"%' for name in names)
        if demo:
            where.append("rf.demo_name LIKE ?")
            params.append(f"%{demo}%")
        if mode_pool and mode_pool.lower() != "all":
            where.append("json_extract(rf.attributes, '$.mode_pool') = ?")
            params.append(mode_pool)
        if has_master is True:
            where.append(f"{_MASTER_SUBQ} IS NOT NULL")
        elif has_master is False:
            where.append(f"{_MASTER_SUBQ} IS NULL")
        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        total = conn.execute(
            f"SELECT COUNT(*) FROM recognized_frags rf {where_sql}", params
        ).fetchone()[0]

        custom_score_by_id: dict[int, float] = {}
        if sort == "custom":
            # Custom ranking needs the whole filtered set scored before we
            # can slice a page out of it — fetch just the lightweight
            # columns needed to score, order in Python, then page.
            assert weights is not None
            scoring_rows = conn.execute(
                f"SELECT rf.id, rf.classes, rf.highlight_score "
                f"FROM recognized_frags rf {where_sql}",
                params,
            ).fetchall()
            scored: list[tuple[float, int]] = []
            for srow in scoring_rows:
                names = _class_names(srow["classes"])
                cscore = (srow["highlight_score"] or 0.0) + sum(
                    weights.get(n, 0.0) for n in names
                )
                scored.append((cscore, srow["id"]))
            scored.sort(key=lambda t: (-t[0], t[1]))
            custom_score_by_id = {fid: cscore for cscore, fid in scored}
            page_ids = [fid for _, fid in scored[offset:offset + limit]]
            if page_ids:
                marks = ",".join("?" * len(page_ids))
                fetched = conn.execute(
                    f"SELECT rf.id, rf.demo_name, rf.round, rf.server_time_ms, "
                    f"       rf.weapon_name, rf.highlight_score, rf.classes, "
                    f"       rf.attributes, {_MASTER_SUBQ} AS master_clip_id "
                    f"FROM recognized_frags rf WHERE rf.id IN ({marks})",
                    page_ids,
                ).fetchall()
                rows_by_id = {r["id"]: r for r in fetched}
                rows = [rows_by_id[i] for i in page_ids if i in rows_by_id]
            else:
                rows = []
        else:
            if sort == "time":
                order_sql = "ORDER BY rf.server_time_ms ASC, rf.id ASC"
            elif sort == "speed":
                order_sql = (
                    "ORDER BY json_extract(rf.attributes, '$.killer_speed') DESC,"
                    " rf.id ASC"
                )
            else:
                order_sql = "ORDER BY rf.highlight_score DESC, rf.id ASC"
            rows = conn.execute(
                f"SELECT rf.id, rf.demo_name, rf.round, rf.server_time_ms, "
                f"       rf.weapon_name, rf.highlight_score, rf.classes, "
                f"       rf.attributes, {_MASTER_SUBQ} AS master_clip_id "
                f"FROM recognized_frags rf {where_sql} {order_sql} LIMIT ? OFFSET ?",
                [*params, limit, offset],
            ).fetchall()

        row_ids = [r["id"] for r in rows]
        reviews = review_proxy.get_reviews(row_ids)
        proxies = review_proxy.get_states(row_ids)
        items: list[dict[str, Any]] = []
        for row in rows:
            attrs = _parse_json(row["attributes"], {})
            master = _master_row(conn, row["master_clip_id"])
            full_classes = _class_names(row["classes"])
            item: dict[str, Any] = {
                "id": row["id"],
                "demo_name": row["demo_name"],
                "round": row["round"],
                "server_time_ms": row["server_time_ms"],
                "weapon_name": row["weapon_name"],
                "highlight_score": row["highlight_score"],
                "classes": full_classes[:5],
                "scene_score": attrs.get("scene_score") if isinstance(attrs, dict) else None,
                "mode_pool": attrs.get("mode_pool") if isinstance(attrs, dict) else None,
                "killer_speed": attrs.get("killer_speed") if isinstance(attrs, dict) else None,
                "attacker_speed_percentile": (
                    attrs.get("attacker_speed_percentile") if isinstance(attrs, dict) else None
                ),
                "map_name": (
                    attrs.get("map_name") or attrs.get("map") or
                    (master.get("map") if master else None)
                ) if isinstance(attrs, dict) else (master.get("map") if master else None),
                "master": (
                    {
                        "generated_clip_id": master["generated_clip_id"],
                        "tier": master.get("tier"),
                        "qa_status": master.get("qa_status"),
                        "class": master.get("class"),
                        "avi_on_disk": master["avi_on_disk"],
                    }
                    if master
                    else None
                ),
                "review": (
                    {
                        "verdict": reviews[row["id"]].get("verdict"),
                        "user_tier": reviews[row["id"]].get("user_tier"),
                    }
                    if row["id"] in reviews
                    else None
                ),
                "proxy": {
                    "state": proxies.get(row["id"], {}).get("state", "MISSING")
                },
            }
            if weights is not None:
                if sort == "custom":
                    item["custom_score"] = custom_score_by_id.get(row["id"])
                else:
                    item["custom_score"] = (row["highlight_score"] or 0.0) + sum(
                        weights.get(n, 0.0) for n in full_classes
                    )
            items.append(item)
        return {"total": total, "limit": limit, "offset": offset, "items": items}
    finally:
        conn.close()


@router.get("/api/frags/{frag_id}")
def frag_detail(frag_id: int) -> dict[str, Any]:
    conn = _connect()
    try:
        row = conn.execute(
            f"SELECT rf.*, {_MASTER_SUBQ} AS master_clip_id "
            "FROM recognized_frags rf WHERE rf.id = ?",
            (frag_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="frag not found")
        d = dict(row)
        master_clip_id = d.pop("master_clip_id", None)
        d["classes"] = _parse_json(d.get("classes"), [])
        d["attributes"] = _parse_json(d.get("attributes"), {})
        d["reasons"] = _parse_json(d.get("reasons"), d.get("reasons"))
        d["master"] = _master_row(conn, master_clip_id)
        d["review"] = review_proxy.get_review(frag_id)
        d["proxy"] = _proxy_state_payload(frag_id)
        d["window"] = _frag_window(d)
        return d
    finally:
        conn.close()


@router.get("/api/frags/{frag_id}/video")
def frag_video(frag_id: int):
    conn = _connect()
    try:
        row = conn.execute(
            f"SELECT {_MASTER_SUBQ} AS master_clip_id "
            "FROM recognized_frags rf WHERE rf.id = ?",
            (frag_id,),
        ).fetchone()
        if row is None:
            return JSONResponse(status_code=404, content={"reason": "frag not found"})
        master = _master_row(conn, row["master_clip_id"])
    finally:
        conn.close()
    if master is None:
        return JSONResponse(
            status_code=404, content={"reason": "no master clip captured for this frag"}
        )
    avi = master.get("avi_path")
    if not avi or not Path(str(avi)).exists():
        return JSONResponse(
            status_code=404,
            content={"reason": "master exists but AVI not on disk", "avi_path": avi},
        )
    return FileResponse(str(avi), media_type="video/x-msvideo", filename=Path(str(avi)).name)


# ------------------------------------------------------------ review proxies

def _frag_window(frag: dict[str, Any]) -> dict[str, int]:
    """Proxy capture window. The rule lives in review_proxy.capture_window.

    This used to spell the window out again, so the 4s/3s asymmetry and later
    the countdown lead-in had to be changed in two places to take effect.
    """
    round_start = None
    attrs = frag.get("attributes")
    if isinstance(attrs, str):
        try:
            attrs = json.loads(attrs)
        except (TypeError, ValueError):
            attrs = None
    if isinstance(attrs, dict):
        round_start = attrs.get("round_start_ms")
    w = review_proxy.capture_window(
        int(frag["server_time_ms"]),
        round_start_ms=round_start,
        master=frag.get("master"),
    )
    return {"start_ms": w["start_ms"], "end_ms": w["end_ms"]}


def _load_frag_with_master(frag_id: int) -> dict[str, Any]:
    conn = _connect()
    try:
        row = conn.execute(
            # attributes carries round_start_ms, which decides whether the
            # window opens on the round countdown. Without it selected here
            # the countdown lead-in silently never applied on this route.
            f"SELECT rf.id, rf.demo_name, rf.server_time_ms, rf.attributes, "
            f"{_MASTER_SUBQ} AS master_clip_id "
            "FROM recognized_frags rf WHERE rf.id = ?",
            (frag_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="frag not found")
        d = dict(row)
        d["master"] = _master_row(conn, d.pop("master_clip_id", None))
        return d
    finally:
        conn.close()


def _proxy_state_payload(frag_id: int) -> dict[str, Any]:
    st = review_proxy.get_state(frag_id)
    out: dict[str, Any] = {"state": st.get("state", "MISSING")}
    if st.get("error"):
        out["error"] = st["error"]
    if out["state"] == "READY":
        out["url"] = f"/api/frags/{frag_id}/proxy/video"
    for k in ("start_ms", "end_ms", "key"):
        if st.get(k) is not None:
            out[k] = st[k]
    return out


@router.post("/api/frags/{frag_id}/proxy")
def queue_proxy(frag_id: int) -> dict[str, Any]:
    frag = _load_frag_with_master(frag_id)
    window = _frag_window(frag)
    res = review_proxy.request_proxy(
        frag_id, frag["demo_name"], window["start_ms"], window["end_ms"], retry=True
    )
    if res.get("state") == "FAILED" and "key" not in res:
        # not persistable (e.g. demo unknown) — surface the error directly
        return {"state": "FAILED", "error": res.get("error")}
    return _proxy_state_payload(frag_id)


@router.get("/api/frags/{frag_id}/proxy")
def proxy_state(frag_id: int) -> dict[str, Any]:
    # 404 on unknown frag keeps the API honest; MISSING is for known frags.
    _load_frag_with_master(frag_id)
    return _proxy_state_payload(frag_id)


@router.get("/api/frags/{frag_id}/proxy/video")
def proxy_video(frag_id: int):
    st = review_proxy.get_state(frag_id)
    if st.get("state") != "READY":
        return JSONResponse(
            status_code=404,
            content={"reason": f"proxy not ready (state={st.get('state', 'MISSING')})"},
        )
    mp4 = Path(str(st["mp4_path"]))
    return FileResponse(str(mp4), media_type="video/mp4", filename=mp4.name)


def _music_auditions(frag_id: int) -> list[dict[str, Any]]:
    manifest = MUSIC_AUDITION_DIR / "manifest.json"
    if not manifest.exists():
        return []
    try:
        items = json.loads(manifest.read_text(encoding="utf-8")).get("items", [])
    except (OSError, ValueError, AttributeError):
        return []
    if not isinstance(items, list):
        return []
    safe = []
    for item in items:
        if not isinstance(item, dict) or item.get("frag_id") != frag_id:
            continue
        audition_id = item.get("audition_id")
        track_hash = item.get("track_hash")
        if audition_id not in {"A", "B", "C"}:
            continue
        if not isinstance(track_hash, str) or re.fullmatch(r"[0-9a-f]{64}", track_hash) is None:
            continue
        required = (
            "audition_id", "track_hash", "track_label", "region_kind",
            "region_start_us", "music_source_start_us", "anchor_edit_us",
            "action_edit_us", "score")
        if any(k not in item for k in required):
            continue
        safe.append({k: item[k] for k in required})
        for key in ("profile_type", "components", "music_anchor_us",
                    "signed_delta_us", "structure", "matcher_version",
                    "scene_recipe_id", "review_identity"):
            if key in item:
                safe[-1][key] = item[key]
        safe[-1]["video_url"] = f"/api/frags/{frag_id}/music-auditions/{item['audition_id']}/video"
        if len(safe) == 3:
            break
    return safe


@router.get("/api/frags/{frag_id}/music-auditions")
def list_music_auditions(frag_id: int) -> dict[str, Any]:
    _load_frag_with_master(frag_id)
    store = MusicFeatureStore(MUSIC_FEATURE_DB_PATH)
    return {"frag_id": frag_id, "items": _music_auditions(frag_id),
            "reviews": store.get_reviews(frag_id)}


@router.get("/api/frags/{frag_id}/music-auditions/{audition_id}/video")
def music_audition_video(frag_id: int, audition_id: str):
    item = next((x for x in _music_auditions(frag_id)
                 if x["audition_id"] == audition_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="music audition not found")
    path = MUSIC_AUDITION_DIR / f"{frag_id}_{audition_id}.mp4"
    if not path.is_file():
        raise HTTPException(status_code=404, detail="music audition media missing")
    return FileResponse(str(path), media_type="video/mp4", filename=path.name)


@router.put("/api/frags/{frag_id}/music-auditions/{audition_id}/review")
def write_music_audition_review(frag_id: int, audition_id: str,
                                body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    item = next((x for x in _music_auditions(frag_id)
                 if x["audition_id"] == audition_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="music audition not found")
    decision = body.get("decision", "undecided")
    notes = body.get("notes", "")
    if decision not in {"favorite", "reject", "undecided"} or not isinstance(notes, str):
        raise HTTPException(status_code=422, detail="invalid music review")
    store = MusicFeatureStore(MUSIC_FEATURE_DB_PATH)
    store.save_review(
        frag_id, item["track_hash"], item["region_start_us"], decision, notes,
        scene_recipe_id=item.get("scene_recipe_id"),
        matcher_version=item.get("matcher_version"),
    )
    return {"frag_id": frag_id, "audition_id": audition_id,
            "decision": decision, "notes": notes}


# ------------------------------------------------------------ editorial review

_VERDICTS = {"LOVE", "KEEP", "MAYBE", "DROP"}
_TIERS = {"S_PLUS", "S", "A", "B", ""}


@router.get("/api/frags/{frag_id}/review")
def read_review(frag_id: int) -> dict[str, Any]:
    review = review_proxy.get_review(frag_id)
    return review or {"frag_id": frag_id, "verdict": None,
                      "user_tier": None, "notes": None}


@router.put("/api/frags/{frag_id}/review")
def write_review(frag_id: int, body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    verdict = body.get("verdict")
    user_tier = body.get("user_tier")
    notes = body.get("notes")
    if verdict is not None and verdict not in _VERDICTS:
        raise HTTPException(status_code=422, detail=f"invalid verdict: {verdict}")
    if user_tier is not None and user_tier not in _TIERS:
        raise HTTPException(status_code=422, detail=f"invalid user_tier: {user_tier}")
    if notes is not None and not isinstance(notes, str):
        raise HTTPException(status_code=422, detail="notes must be a string")
    _load_frag_with_master(frag_id)  # 404 on unknown frag
    return review_proxy.put_review(
        frag_id, verdict=verdict, user_tier=user_tier, notes=notes
    )
