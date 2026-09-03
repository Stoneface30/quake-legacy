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

from fastapi import APIRouter, HTTPException, Query
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
             "available": rc.count_items(t) > 0}
            for t in rc.ITEM_TYPES
        ],
    }


@router.get("/progress")
def get_progress(item_type: str = rc.FRAG, corpus: str | None = None):
    if corpus:
        item_type = rc.CORPUS_ITEM_TYPE.get(corpus, item_type)
    return rc.progress(item_type)


@router.get("/queue")
def get_queue(order: str = rc.ORDER_WORST_FIRST, offset: int = 0,
              limit: int = Query(30, le=200), item_type: str = rc.FRAG,
              unreviewed_only: bool = False, corpus: str | None = None):
    try:
        items = rc.queue(order=order, limit=limit, offset=offset,
                         item_type=item_type, unreviewed_only=unreviewed_only,
                         corpus=corpus)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if corpus:
        item_type = rc.CORPUS_ITEM_TYPE.get(corpus, item_type)
    with _lock:
        _state["order"] = order
        _state["cursor"] = offset
    _prefetch(items[:PREFETCH])
    return {"order": order, "offset": offset, "item_type": item_type,
            "corpus": corpus,
            "total": rc.count_items(item_type, corpus=corpus),
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


def _prefetch(items: list[rc.ReviewItem]) -> None:
    for it in items:
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
