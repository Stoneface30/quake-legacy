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
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse

from creative_suite.engine import review_proxy

router = APIRouter()

_DB_DIR = Path(__file__).parent.parent / "database"
# Module-level so tests can monkeypatch them.
FRAG_DB_PATH = _DB_DIR / "frag_recognition.db"
DEMO_V2_DB_PATH = _DB_DIR / "demo_v2.db"

# classes-endpoint cache: {str(db_path): [{"name":..., "count":...}, ...]}
_classes_cache: dict[str, list[dict[str, Any]]] = {}

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


@router.get("/api/frags")
def list_frags(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    min_score: float | None = Query(default=None),
    weapon: str | None = Query(default=None),
    class_: str | None = Query(default=None, alias="class"),
    demo: str | None = Query(default=None),
    mode_pool: str = Query(default="MAIN_CA"),
    has_master: bool | None = Query(default=None),
    sort: str = Query(default="score"),
) -> dict[str, Any]:
    conn = _connect()
    try:
        where: list[str] = []
        params: list[Any] = []
        if min_score is not None:
            where.append("rf.highlight_score >= ?")
            params.append(min_score)
        if weapon:
            where.append("rf.weapon_name = ?")
            params.append(weapon)
        if class_:
            where.append("rf.classes LIKE ?")
            params.append(f"%{class_}%")
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
        order_sql = (
            "ORDER BY rf.server_time_ms ASC, rf.id ASC"
            if sort == "time"
            else "ORDER BY rf.highlight_score DESC, rf.id ASC"
        )
        total = conn.execute(
            f"SELECT COUNT(*) FROM recognized_frags rf {where_sql}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"SELECT rf.id, rf.demo_name, rf.round, rf.server_time_ms, "
            f"       rf.weapon_name, rf.highlight_score, rf.classes, "
            f"       rf.attributes, {_MASTER_SUBQ} AS master_clip_id "
            f"FROM recognized_frags rf {where_sql} {order_sql} LIMIT ? OFFSET ?",
            [*params, limit, offset],
        ).fetchall()

        reviews = review_proxy.get_reviews([r["id"] for r in rows])
        items: list[dict[str, Any]] = []
        for row in rows:
            attrs = _parse_json(row["attributes"], {})
            master = _master_row(conn, row["master_clip_id"])
            items.append(
                {
                    "id": row["id"],
                    "demo_name": row["demo_name"],
                    "round": row["round"],
                    "server_time_ms": row["server_time_ms"],
                    "weapon_name": row["weapon_name"],
                    "highlight_score": row["highlight_score"],
                    "classes": _class_names(row["classes"])[:5],
                    "scene_score": attrs.get("scene_score") if isinstance(attrs, dict) else None,
                    "mode_pool": attrs.get("mode_pool") if isinstance(attrs, dict) else None,
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
                }
            )
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
    """Proxy capture window: the master's capture window when one exists,
    else server_time_ms - 4s .. + 3s."""
    master = frag.get("master")
    if master and master.get("capture_start_ms") is not None:
        return {
            "start_ms": int(master["capture_start_ms"]),
            "end_ms": int(master["capture_end_ms"]),
        }
    t = int(frag["server_time_ms"])
    return {
        "start_ms": t - review_proxy.WINDOW_PRE_MS,
        "end_ms": t + review_proxy.WINDOW_POST_MS,
    }


def _load_frag_with_master(frag_id: int) -> dict[str, Any]:
    conn = _connect()
    try:
        row = conn.execute(
            f"SELECT rf.id, rf.demo_name, rf.server_time_ms, "
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
        frag_id, frag["demo_name"], window["start_ms"], window["end_ms"]
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


# ------------------------------------------------------------ editorial review

_VERDICTS = {"LOVE", "KEEP", "MAYBE", "DROP"}
_TIERS = {"S_PLUS", "S", "A", ""}


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
