"""Review API: queue, verdict, note, media.

The media problem is the whole design. A proxy takes about forty seconds of
wolfcam to produce, and there are 36,607 frags, so pre-rendering the corpus
is roughly six hundred hours. Nothing here waits for that. A background
filler walks the queue in the user's chosen order and renders ahead; the UI
shows what is ready and says plainly what is not, and a verdict is never
blocked on a render -- a moment can be judged from its metadata alone if the
user already knows the shot.
"""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from creative_suite.engine import review_corpus as rc
from creative_suite.engine import review_proxy

router = APIRouter(prefix="/api/review", tags=["review"])

FRONTEND = Path(__file__).resolve().parents[1] / "frontend"

# How far ahead the filler renders. Deep enough that a reviewer working at a
# sensible pace stays ahead of the worker, shallow enough that changing
# order does not waste an hour of rendering.
PREFETCH = 12
_lock = threading.Lock()
_state: dict[str, Any] = {"order": rc.ORDER_WORST_FIRST, "cursor": 0}


class Verdict(BaseModel):
    item_id: str
    role: str
    note: str | None = None
    # No provenance field. The API is the user's hand; anything else writing
    # a verdict goes through review_corpus.record() and states what it is.


class Note(BaseModel):
    item_id: str
    note: str


@router.get("/corpora")
def get_corpora():
    """What can be reviewed, and for what cannot, exactly what is missing."""
    return {
        "corpora": [rc.corpus_status(c) for c in rc.CORPORA],
        "item_types": [
            {"item_type": t, "total": rc.count_items(t),
             "available": (rc.count_items(t) > 0
                           and t not in rc.NOT_A_REVIEW_MOMENT),
             # A family can have plenty of rows and still not be reviewable.
             # Saying which, and why, beats an empty or a misleading queue.
             "withheld_because": rc.NOT_A_REVIEW_MOMENT.get(t)}
            for t in rc.ITEM_TYPES
        ],
    }


@router.get("/progress")
def get_progress(item_type: str = rc.FRAG, corpus: str | None = None):
    if corpus:
        item_type = rc.CORPUS_ITEM_TYPE.get(corpus, item_type)
    return rc.progress(item_type, corpus=corpus)


@router.get("/queue")
def get_queue(order: str = rc.ORDER_WORST_FIRST, offset: int = 0,
              limit: int = Query(30, le=200), item_type: str = rc.FRAG,
              unreviewed_only: bool = False, corpus: str | None = None,
              weapon: str | None = None, map: str | None = None,
              trait: str | None = None, death_cause: str | None = None,
              actor: str | None = None, opponent: str | None = None,
              pov: str | None = None, merge: str | None = None,
              min_round_kills: int | None = None,
              funny: str | None = None):
    # Named parameters, not a query string the browser composes. The filter
    # whitelist lives in review_corpus and refuses anything it does not know.
    filters = {k: v for k, v in
               {"weapon": weapon, "map": map, "trait": trait,
                "death_cause": death_cause, "actor": actor,
                "opponent": opponent, "pov": pov, "merge": merge,
                "min_round_kills": min_round_kills,
                "funny": funny}.items() if v}
    try:
        items = rc.queue(order=order, limit=limit, offset=offset,
                         item_type=item_type, unreviewed_only=unreviewed_only,
                         corpus=corpus, filters=filters)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if corpus:
        item_type = rc.CORPUS_ITEM_TYPE.get(corpus, item_type)
    with _lock:
        _state["order"] = order
        _state["cursor"] = offset
    _prefetch(items[:PREFETCH],
              key=f"{corpus}|{item_type}|{order}|{sorted(filters.items())}")
    return {"order": order, "offset": offset, "item_type": item_type,
            "corpus": corpus,
            "filters": filters,
            "total": rc.count_items(item_type, corpus=corpus,
                                    filters=filters),
            "items": [i.to_dict() for i in items]}


@router.get("/item/{item_id}")
def get_item(item_id: str):
    it = rc.item(item_id)
    if it is None:
        raise HTTPException(404, f"no such item: {item_id}")
    return it.to_dict()


@router.post("/verdict")
def post_verdict(v: Verdict):
    it = rc.item(v.item_id)
    if it is None:
        raise HTTPException(404, f"no such item: {v.item_id}")
    try:
        out = rc.record(v.item_id, it.item_type, it.source_id, v.role, v.note,
                        provenance=rc.HUMAN_USER)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {**out, "progress": rc.progress(it.item_type)}


@router.post("/note")
def post_note(n: Note):
    return rc.annotate(n.item_id, n.note)


@router.post("/undo")
def post_undo():
    out = rc.undo_last()
    if out is None:
        raise HTTPException(404, "nothing to undo")
    return {**out, "progress": rc.progress()}


@router.get("/pool/{role}")
def get_pool(role: str, item_type: str | None = None,
             weapon: str | None = None, limit: int = Query(200, le=1000)):
    try:
        return {"role": role,
                "items": rc.pool(role, item_type, weapon, limit)}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/notes")
def get_notes(q: str, limit: int = Query(100, le=500)):
    return {"query": q, "items": rc.search_notes(q, limit)}


# ── media ───────────────────────────────────────────────────────────────────

def _proxy_for(it: rc.ReviewItem) -> dict[str, Any]:
    """Ask the existing proxy cache for this item's clip window."""
    try:
        return review_proxy.request_proxy(
            frag_id=it.source_id, demo_name=it.demo_name,
            start_ms=it.start_ms, end_ms=it.end_ms)
    except TypeError:
        # older signature: (frag) -- fall back to state only
        return review_proxy.get_state(it.source_id)
    except Exception as e:            # a media failure must not stop review
        return {"state": "ERROR", "error": f"{type(e).__name__}: {e}"}


_active_queue: dict[str, Any] = {"key": None}


def _prefetch(items: list[rc.ReviewItem], key: str | None = None) -> None:
    """Render ahead of the queue the user is ACTUALLY on.

    The worker used to keep draining whatever it had been given, so changing
    filter left it rendering forty clips nobody was going to watch while the
    new queue rendered behind them. The key is the active selection; work
    queued under a stale one is abandoned rather than finished.
    """
    with _lock:
        if key is not None:
            _active_queue["key"] = key
        current = _active_queue["key"]
    for it in items:
        with _lock:
            if _active_queue["key"] != current:
                return             # the user moved on; stop spending wolfcam
        try:
            _proxy_for(it)
        except Exception:
            pass                       # best effort, never blocks the queue


@router.get("/media/{item_id}")
def get_media(item_id: str):
    it = rc.item(item_id)
    if it is None:
        raise HTTPException(404, f"no such item: {item_id}")
    st = _proxy_for(it)
    path = st.get("mp4_path")
    if st.get("state") == "READY" and path and Path(path).exists():
        return FileResponse(path, media_type="video/mp4")
    # Not an error: the clip is being made, or could not be. The reviewer is
    # told which, and can still judge and move on.
    raise HTTPException(
        status_code=425 if st.get("state") not in ("ERROR", "FAILED") else 404,
        detail={"state": st.get("state", "PENDING"),
                "error": st.get("error"),
                "hint": "clip is rendering; verdicts do not wait for it"})


@router.get("/media_state/{item_id}")
def get_media_state(item_id: str):
    it = rc.item(item_id)
    if it is None:
        raise HTTPException(404, f"no such item: {item_id}")
    st = _proxy_for(it)
    return {"item_id": item_id, "state": st.get("state", "PENDING"),
            "error": st.get("error"),
            "ready": bool(st.get("state") == "READY" and st.get("mp4_path")
                          and Path(str(st.get("mp4_path"))).exists())}


@router.get("/ui", response_class=HTMLResponse)
def ui():
    p = FRONTEND / "review.html"
    if not p.exists():
        raise HTTPException(404, "review.html missing")
    return HTMLResponse(p.read_text(encoding="utf-8"))


# ── identity review ─────────────────────────────────────────────────────────
# A different question from the five-button creative review, so it gets its
# own endpoints and its own small page. "Is this recorder me?" is a matter of
# fact the user knows and the code cannot infer.

class IdentityDecision(BaseModel):
    name_norm: str
    user_state: str | None = None
    ptn_state: str | None = None
    alias_of: str | None = None
    note: str | None = None


@router.get("/identity/status")
def identity_status():
    from creative_suite.engine import identity as idn
    return idn.status()


@router.get("/identity/recorders")
def identity_recorders(limit: int = Query(200, le=500)):
    from creative_suite.engine import identity as idn
    return {"candidates": idn.recorder_candidates(limit=limit),
            "user_states": list(idn.USER_STATES),
            "ptn_states": list(idn.PTN_STATES)}


@router.get("/identity/ptn")
def identity_ptn(min_lines: int = 20):
    from creative_suite.engine import identity as idn
    return {"candidates": idn.ptn_candidates(min_lines=min_lines),
            "user_supplied": list(idn.USER_SUPPLIED_PTN),
            "primary": idn.PRIMARY_USER,
            "user_defined_aliases": idn.USER_DEFINED_ALIASES}


@router.post("/identity/decide")
def identity_decide(d: IdentityDecision):
    from creative_suite.engine import identity as idn
    try:
        return idn.decide(d.name_norm, d.user_state, d.ptn_state,
                          d.alias_of, d.note, decided_by=idn.BY_USER)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/identity/ui", response_class=HTMLResponse)
def identity_ui():
    p = FRONTEND / "identity.html"
    if not p.exists():
        raise HTTPException(404, "identity.html missing")
    return HTMLResponse(p.read_text(encoding="utf-8"))


# ── round context ───────────────────────────────────────────────────────────
# A frag is the fast review unit; a round is the context it lived in. The
# round is offered, never forced -- no autoplay, no replacing the +/-3s clip.

class UsageUpdate(BaseModel):
    occurrence_id: int
    state: str
    detail: str = ""


@router.get("/round/{item_id}")
def get_round(item_id: str):
    from creative_suite.engine import round_story as rs
    it = rc.item(item_id)
    if it is None:
        raise HTTPException(404, f"no such item: {item_id}")
    if it.round_no is None:
        return {"item_id": item_id, "available": False,
                "reason": "this moment has no round attributed"}
    ctx = rs.round_context(it.content_hash, it.round_no)
    if ctx is None:
        return {"item_id": item_id, "available": False,
                "reason": "no observed events in that round"}
    start, end = rs.round_window(ctx)
    d = ctx.to_dict()
    d.pop("content_hash", None)          # private provenance, never to the UI
    return {"item_id": item_id, "available": True,
            "round": d, "media_start_ms": start, "media_end_ms": end,
            "media_duration_s": round((end - start) / 1000.0, 1)}


@router.get("/usage/{occurrence_id}")
def get_usage(occurrence_id: int):
    from creative_suite.engine import production_usage as pu
    return pu.states([occurrence_id])[occurrence_id]


@router.post("/usage")
def post_usage(u: UsageUpdate):
    from creative_suite.engine import production_usage as pu
    try:
        return pu.set_state(u.occurrence_id, u.state, u.detail)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/usage_summary")
def usage_summary():
    from creative_suite.engine import production_usage as pu
    return pu.summary()


@router.get("/media/round/{item_id}")
def get_round_media(item_id: str):
    """The whole round, rendered on demand only.

    Never pre-rendered: full-round media is minutes of wolfcam per round and
    the user asks for it on a small fraction of moments.
    """
    from creative_suite.engine import round_story as rs
    it = rc.item(item_id)
    if it is None or it.round_no is None:
        raise HTTPException(404, f"no round for {item_id}")
    ctx = rs.round_context(it.content_hash, it.round_no)
    if ctx is None:
        raise HTTPException(404, "no observed events in that round")
    start, end = rs.round_window(ctx)
    try:
        st = review_proxy.request_proxy(frag_id=it.source_id,
                                        demo_name=it.demo_name,
                                        start_ms=start, end_ms=end)
    except Exception as e:                                     # noqa: BLE001
        raise HTTPException(503, f"{type(e).__name__}: {e}")
    path = st.get("mp4_path")
    if st.get("state") == "READY" and path and Path(path).exists():
        return FileResponse(path, media_type="video/mp4")
    raise HTTPException(
        status_code=425,
        detail={"state": st.get("state", "PENDING"),
                "hint": "the full round is rendering; this is on-demand only"})


@router.get("/traits")
def get_traits(limit: int = Query(40, le=120)):
    """The machine traits actually present, with counts.

    Never a hardcoded list: offering a filter for a trait nobody has gives
    the user an empty result that reads as "this never happened".
    """
    return {"traits": rc.trait_vocabulary(limit=limit),
            "note": rc.TRAIT_NOTE}


@router.get("/facets")
def get_facets(corpus: str = rc.DEFAULT_CORPUS):
    """Values worth offering as filters, drawn from the data itself."""
    it = rc.CORPUS_ITEM_TYPE.get(corpus, rc.USER_FRAG)
    with rc._rec() as c:
        weapons = [r[0] for r in c.execute(
            "SELECT mod_name FROM kill_occurrences_v1 WHERE mod_name IS NOT NULL "
            "GROUP BY 1 ORDER BY COUNT(*) DESC LIMIT 16")]
        maps = [r[0] for r in c.execute(
            "SELECT map FROM kill_occurrences_v1 WHERE map IS NOT NULL "
            "GROUP BY 1 ORDER BY COUNT(*) DESC LIMIT 20")]
        causes = [r[0] for r in c.execute(
            "SELECT death_cause FROM kill_occurrences_v1 GROUP BY 1 "
            "ORDER BY COUNT(*) DESC")]
    funny: list[str] = []
    with rc._rec() as c:
        if c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND "
                     "name='funny_runs_v1'").fetchone():
            import json as _j
            r = c.execute("SELECT by_signal FROM funny_runs_v1").fetchone()
            if r:
                funny = [k for k, _ in sorted(_j.loads(r["by_signal"]).items(),
                                              key=lambda kv: -kv[1])]
    return {"corpus": corpus, "item_type": it, "weapons": weapons,
            "maps": maps, "death_causes": causes, "funny_signals": funny,
            "funny_note": ("a discovery label, not a quality class -- a flyby "
                           "may well be FEATURE material"),
            "roles": list(rc.ROLES), "role_labels": rc.ROLE_LABEL,
            "traits": rc.trait_vocabulary(limit=40),
            "trait_note": rc.TRAIT_NOTE}


# ── session persistence ─────────────────────────────────────────────────────
# Reviewing 33,316 moments is not one sitting. Losing your place to a browser
# refresh, a server restart or closing a laptop is the kind of friction that
# ends a curation habit, so where the user was is persisted server-side --
# not in the browser, because the point is to survive the browser.

class SessionState(BaseModel):
    corpus: str | None = None
    item_type: str | None = None
    order: str | None = None
    filters: dict[str, Any] | None = None
    offset: int | None = None
    last_item_id: str | None = None


_SESSION_SCHEMA = """
CREATE TABLE IF NOT EXISTS review_session (
    who        TEXT PRIMARY KEY,
    state      TEXT NOT NULL,
    updated_at TEXT NOT NULL);
"""


def _session_conn():
    import sqlite3 as _s
    c = _s.connect(rc.EDITORIAL_DB, timeout=30)
    c.row_factory = _s.Row
    c.executescript(_SESSION_SCHEMA)
    return c


def _who(request: Request) -> str:
    """The Access identity when there is one, otherwise the local operator.

    Keyed per person so a shared link never resumes into somebody else's
    position -- and so a future second reviewer does not inherit this one's.
    """
    return getattr(request.state, "access_email", None) or "LOCAL"


@router.get("/session")
def get_session(request: Request):
    import json as _j
    with _session_conn() as c:
        r = c.execute("SELECT * FROM review_session WHERE who=?",
                      (_who(request),)).fetchone()
    if r is None:
        return {"found": False, "corpus": rc.DEFAULT_CORPUS,
                "order": rc.ORDER_WORST_FIRST, "filters": {}, "offset": 0}
    return {"found": True, "updated_at": r["updated_at"], **_j.loads(r["state"])}


@router.post("/session")
def post_session(s: SessionState, request: Request):
    import json as _j
    from datetime import datetime, timezone
    state = {k: v for k, v in s.model_dump().items() if v is not None}
    with _session_conn() as c:
        c.execute(
            "INSERT INTO review_session(who, state, updated_at) VALUES (?,?,?) "
            "ON CONFLICT(who) DO UPDATE SET state=excluded.state, "
            "updated_at=excluded.updated_at",
            (_who(request), _j.dumps(state),
             datetime.now(timezone.utc).isoformat(timespec="seconds")))
    return {"saved": True, **state}
