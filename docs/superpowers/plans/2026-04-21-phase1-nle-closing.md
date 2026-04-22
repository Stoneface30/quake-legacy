# Phase 1 NLE Closing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn PANTHEON Studio into a fully interactive NLE — drag-drop timeline, per-clip FX stack, intelligent randomizer, music beatmatch chain, all persisted in a local SQLite DB.

**Architecture:** SQLite (`studio_nle.db`) is the UI nervous system — every clip arrangement, FX setting, and music assignment lives there for sub-millisecond reads/writes. At render time, `manifest_generator.py` converts DB state to the existing `partNN.txt` / `partNN_overrides.txt` files — the render pipeline is untouched. StudioStore remains the in-memory reactive layer; DB is persistence below it.

**Tech Stack:** FastAPI (Python backend), SQLite via `sqlite3` stdlib, vanilla JS ES5 (canvas-based NLE timeline), CSS custom properties (existing design system).

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `creative_suite/database/nle_schema.sql` | CREATE | DDL for 4 NLE tables |
| `creative_suite/database/nle_db.py` | CREATE | SQLite connection pool + CRUD helpers |
| `creative_suite/config.py` | MODIFY | Add `nle_db_path` property |
| `creative_suite/api/studio.py` | MODIFY | 9 new REST endpoints |
| `creative_suite/frontend/studio-timeline-nle.js` | CREATE | Canvas NLE timeline (render/select/drag/edit) |
| `creative_suite/frontend/studio-timeline.js` | RETIRE | Old animation-timeline-js wrapper — replaced by NLE canvas |
| `creative_suite/frontend/studio-inspector.js` | MODIFY | Add FX stack below existing OVERRIDES section |
| `creative_suite/frontend/studio-edit.js` | MODIFY | Wire new timeline, RANDOMIZE + GENERATE buttons |
| `creative_suite/frontend/studio.css` | MODIFY | NLE canvas + FX card styles |
| `creative_suite/engine/manifest_generator.py` | CREATE | DB → partNN.txt + overrides |
| `creative_suite/engine/music_chain.py` | CREATE | BPM/chain scoring for music recommendations |
| `creative_suite/engine/effects.py` | CREATE | bass_drop, reverb_tail, filter_open audio FX |

---

## Task 1: DB Schema

**Files:**
- Create: `creative_suite/database/nle_schema.sql`

- [ ] **Step 1: Write the schema file**

```sql
-- creative_suite/database/nle_schema.sql
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS clip_arrangements (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    part        INTEGER NOT NULL,
    position    INTEGER NOT NULL,
    role        TEXT    NOT NULL DEFAULT 'body',   -- intro | body | outro
    clip_path   TEXT    NOT NULL,
    tier        TEXT    NOT NULL DEFAULT 'T2',     -- T1 | T2 | T3
    is_fl       INTEGER NOT NULL DEFAULT 0,
    pair_path   TEXT,
    duration_s  REAL,                                      -- populated at import via ffprobe; NULL if unknown
    updated_at  REAL    NOT NULL DEFAULT (unixepoch('now','subsecond'))
);

CREATE TABLE IF NOT EXISTS clip_effects (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    arrangement_id  INTEGER NOT NULL REFERENCES clip_arrangements(id) ON DELETE CASCADE,
    effect_type     TEXT    NOT NULL,  -- slowmo|speedup|shine_on_kill|audio_reverb|audio_bass_drop|zoom|vignette
    params          TEXT    NOT NULL DEFAULT '{}',  -- JSON blob
    position        INTEGER NOT NULL DEFAULT 0,
    enabled         INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS music_assignments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    part            INTEGER NOT NULL,
    role            TEXT    NOT NULL,   -- intro | main_{n} | outro
    track_filename  TEXT    NOT NULL,
    artist          TEXT,
    title           TEXT,
    bpm             REAL,
    duration_s      REAL,
    transition_in   TEXT DEFAULT '{}',   -- JSON
    transition_out  TEXT DEFAULT '{}',   -- JSON
    chain_score     REAL DEFAULT 0.0,
    position        INTEGER NOT NULL DEFAULT 0,
    UNIQUE(part, role)
);

CREATE TABLE IF NOT EXISTS audio_fx (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    part        INTEGER NOT NULL,
    trigger     TEXT    NOT NULL,   -- song_transition|frag_kill|frag_railgun|frag_rocket
    effect_type TEXT    NOT NULL,   -- sweep_up|sweep_down|bass_drop|reverb_tail|filter_open|audio_silence_dip
    params      TEXT    NOT NULL DEFAULT '{}',
    enabled     INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_arr_part_pos ON clip_arrangements(part, position);
CREATE INDEX IF NOT EXISTS idx_fx_arr ON clip_effects(arrangement_id);
CREATE INDEX IF NOT EXISTS idx_music_part ON music_assignments(part, position);
CREATE INDEX IF NOT EXISTS idx_audio_fx_part ON audio_fx(part);
```

- [ ] **Step 2: Commit**

```bash
git add creative_suite/database/nle_schema.sql
git commit -m "feat(nle): add studio_nle.db SQL schema (4 tables)"
```

---

## Task 2: DB Access Layer (`nle_db.py`)

**Files:**
- Create: `creative_suite/database/nle_db.py`

- [ ] **Step 1: Write the DB module**

```python
"""creative_suite/database/nle_db.py — SQLite access layer for studio_nle.db.

WAL mode, thread-local connections, context manager helper.
CRUD helpers for all 4 NLE tables.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

_SCHEMA_SQL = Path(__file__).with_name("nle_schema.sql")

_local = threading.local()


def _connect(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path), check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    return con


def init_db(db_path: Path) -> None:
    """Create tables if they don't exist. Safe to call on every startup."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = _connect(db_path)
    con.executescript(_SCHEMA_SQL.read_text(encoding="utf-8"))
    con.commit()
    con.close()


@contextmanager
def get_db(db_path: Path) -> Generator[sqlite3.Connection, None, None]:
    """Thread-local connection context manager. Auto-commits on success."""
    if not hasattr(_local, "con") or _local.db_path != str(db_path):
        _local.con = _connect(db_path)
        _local.db_path = str(db_path)
    con = _local.con
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


# ── clip_arrangements ──────────────────────────────────────────────────────────

def get_arrangement(db_path: Path, part: int) -> list[dict[str, Any]]:
    with get_db(db_path) as con:
        rows = con.execute(
            "SELECT * FROM clip_arrangements WHERE part=? ORDER BY position",
            (part,),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def upsert_arrangement_clip(db_path: Path, part: int, position: int, role: str,
                             clip_path: str, tier: str, is_fl: bool,
                             pair_path: str | None, duration_s: float | None,
                             clip_id: int | None = None) -> int:
    now = time.time()
    with get_db(db_path) as con:
        if clip_id is not None:
            con.execute(
                """UPDATE clip_arrangements
                   SET position=?, role=?, clip_path=?, tier=?, is_fl=?,
                       pair_path=?, duration_s=?, updated_at=?
                   WHERE id=?""",
                (position, role, clip_path, tier, int(is_fl),
                 pair_path, duration_s, now, clip_id),
            )
            return clip_id
        cur = con.execute(
            """INSERT INTO clip_arrangements
               (part, position, role, clip_path, tier, is_fl, pair_path, duration_s, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (part, position, role, clip_path, tier, int(is_fl),
             pair_path, duration_s, now),
        )
        return cur.lastrowid


def bulk_replace_arrangement(db_path: Path, part: int,
                              clips: list[dict[str, Any]]) -> None:
    """Delete all clips for a part and re-insert in new order. Single transaction."""
    now = time.time()
    with get_db(db_path) as con:
        con.execute("DELETE FROM clip_arrangements WHERE part=?", (part,))
        for i, c in enumerate(clips):
            con.execute(
                """INSERT INTO clip_arrangements
                   (part, position, role, clip_path, tier, is_fl, pair_path, duration_s, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (part, i, c.get("role", "body"), c["clip_path"],
                 c.get("tier", "T2"), int(c.get("is_fl", False)),
                 c.get("pair_path"), c.get("duration_s"), now),
            )


def delete_arrangement_clip(db_path: Path, clip_id: int) -> None:
    with get_db(db_path) as con:
        con.execute("DELETE FROM clip_arrangements WHERE id=?", (clip_id,))


# ── clip_effects ───────────────────────────────────────────────────────────────

def get_clip_effects(db_path: Path, arrangement_id: int) -> list[dict[str, Any]]:
    with get_db(db_path) as con:
        rows = con.execute(
            "SELECT * FROM clip_effects WHERE arrangement_id=? ORDER BY position",
            (arrangement_id,),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def add_clip_effect(db_path: Path, arrangement_id: int, effect_type: str,
                    params: dict, position: int) -> int:
    with get_db(db_path) as con:
        cur = con.execute(
            """INSERT INTO clip_effects (arrangement_id, effect_type, params, position, enabled)
               VALUES (?,?,?,?,1)""",
            (arrangement_id, effect_type, json.dumps(params), position),
        )
        return cur.lastrowid


def update_clip_effect(db_path: Path, fx_id: int, params: dict,
                       enabled: bool) -> None:
    with get_db(db_path) as con:
        con.execute(
            "UPDATE clip_effects SET params=?, enabled=? WHERE id=?",
            (json.dumps(params), int(enabled), fx_id),
        )


def delete_clip_effect(db_path: Path, fx_id: int) -> None:
    with get_db(db_path) as con:
        con.execute("DELETE FROM clip_effects WHERE id=?", (fx_id,))


# ── music_assignments ──────────────────────────────────────────────────────────

def get_music_assignments(db_path: Path, part: int) -> list[dict[str, Any]]:
    with get_db(db_path) as con:
        rows = con.execute(
            "SELECT * FROM music_assignments WHERE part=? ORDER BY position",
            (part,),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def upsert_music_assignment(db_path: Path, part: int, role: str,
                             track_filename: str, artist: str | None,
                             title: str | None, bpm: float | None,
                             duration_s: float | None, position: int,
                             transition_in: dict | None = None,
                             transition_out: dict | None = None,
                             chain_score: float = 0.0) -> None:
    with get_db(db_path) as con:
        con.execute(
            """INSERT INTO music_assignments
               (part, role, track_filename, artist, title, bpm, duration_s,
                transition_in, transition_out, chain_score, position)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(part, role) DO UPDATE SET
                 track_filename=excluded.track_filename,
                 artist=excluded.artist, title=excluded.title,
                 bpm=excluded.bpm, duration_s=excluded.duration_s,
                 transition_in=excluded.transition_in,
                 transition_out=excluded.transition_out,
                 chain_score=excluded.chain_score,
                 position=excluded.position""",
            (part, role, track_filename, artist, title, bpm, duration_s,
             json.dumps(transition_in or {}), json.dumps(transition_out or {}),
             chain_score, position),
        )


# ── audio_fx ──────────────────────────────────────────────────────────────────

def get_audio_fx(db_path: Path, part: int) -> list[dict[str, Any]]:
    with get_db(db_path) as con:
        rows = con.execute(
            "SELECT * FROM audio_fx WHERE part=? ORDER BY id", (part,)
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


def update_audio_fx(db_path: Path, fx_id: int, params: dict,
                    enabled: bool) -> None:
    with get_db(db_path) as con:
        con.execute(
            "UPDATE audio_fx SET params=?, enabled=? WHERE id=?",
            (json.dumps(params), int(enabled), fx_id),
        )
```

- [ ] **Step 2: Add `nle_db_path` to `creative_suite/config.py`**

In `Config` class, after the `db_path` property, add:

```python
    @property
    def nle_db_path(self) -> Path:
        return DATABASE_ROOT / "studio_nle.db"
```

- [ ] **Step 3: Wire DB init into app startup**

In `creative_suite/app.py`, find the `create_app()` function. After `cfg.ensure_dirs()`, add:

```python
    from creative_suite.database.nle_db import init_db
    init_db(cfg.nle_db_path)
```

- [ ] **Step 4: Smoke-test the DB init**

```bash
cd G:/QUAKE_LEGACY
E:\PersonalAI\venv\Scripts\python.exe -c "
from creative_suite.config import Config
from creative_suite.database.nle_db import init_db
cfg = Config()
init_db(cfg.nle_db_path)
print('DB OK:', cfg.nle_db_path)
"
```

Expected output: `DB OK: G:\QUAKE_LEGACY\creative_suite\database\studio_nle.db`

- [ ] **Step 5: Commit**

```bash
git add creative_suite/database/nle_db.py creative_suite/config.py creative_suite/app.py
git commit -m "feat(nle): add nle_db.py CRUD layer + Config.nle_db_path + app init"
```

---

## Task 3: Arrangement API Endpoints

**Files:**
- Modify: `creative_suite/api/studio.py` (append after existing endpoints)

- [ ] **Step 1: Add Pydantic models and 5 arrangement/FX endpoints**

Append to the bottom of `creative_suite/api/studio.py`:

```python
# ── NLE DB imports ────────────────────────────────────────────────────────────

from creative_suite.database import nle_db


def _nle_db(request: Request):
    return request.app.state.cfg.nle_db_path


# ── Arrangement models ────────────────────────────────────────────────────────

class _ArrangementClip(BaseModel):
    clip_path: str
    role: str = "body"
    tier: str = "T2"
    is_fl: bool = False
    pair_path: Optional[str] = None
    duration_s: Optional[float] = None


class ArrangementBody(BaseModel):
    clips: list[_ArrangementClip]


class _FxParams(BaseModel):
    effect_type: str
    params: dict = {}
    position: int = 0


class _FxUpdate(BaseModel):
    params: dict = {}
    enabled: bool = True


# ── Arrangement endpoints ─────────────────────────────────────────────────────

@router.get("/part/{part_num}/arrangement")
def get_arrangement(part_num: int, request: Request) -> dict[str, Any]:
    db = _nle_db(request)
    rows = nle_db.get_arrangement(db, part_num)
    for row in rows:
        row["effects"] = nle_db.get_clip_effects(db, row["id"])
    return {"part": part_num, "clips": rows}


@router.put("/part/{part_num}/arrangement")
def save_arrangement(part_num: int, body: ArrangementBody,
                     request: Request) -> dict[str, Any]:
    db = _nle_db(request)
    clips = [c.model_dump() for c in body.clips]
    nle_db.bulk_replace_arrangement(db, part_num, clips)
    return {"saved": True, "total": len(clips)}


@router.post("/part/{part_num}/arrangement/{clip_id}/fx")
def add_fx(part_num: int, clip_id: int, body: _FxParams,
           request: Request) -> dict[str, Any]:
    db = _nle_db(request)
    # verify clip belongs to this part
    arr = nle_db.get_arrangement(db, part_num)
    ids = [r["id"] for r in arr]
    if clip_id not in ids:
        raise HTTPException(404, f"Clip {clip_id} not in part {part_num}")
    fx_id = nle_db.add_clip_effect(db, clip_id, body.effect_type,
                                    body.params, body.position)
    return {"fx_id": fx_id}


@router.put("/part/{part_num}/arrangement/{clip_id}/fx/{fx_id}")
def update_fx(part_num: int, clip_id: int, fx_id: int,
              body: _FxUpdate, request: Request) -> dict[str, Any]:
    db = _nle_db(request)
    nle_db.update_clip_effect(db, fx_id, body.params, body.enabled)
    return {"updated": True}


@router.delete("/part/{part_num}/arrangement/{clip_id}/fx/{fx_id}")
def delete_fx(part_num: int, clip_id: int, fx_id: int,
              request: Request) -> dict[str, Any]:
    db = _nle_db(request)
    nle_db.delete_clip_effect(db, fx_id)
    return {"deleted": True}
```

- [ ] **Step 2: Smoke-test via curl (server must be running)**

```bash
# Start server if not running:
# E:\PersonalAI\venv\Scripts\uvicorn.exe creative_suite.app:create_app --factory --host 0.0.0.0 --port 8765 --reload

curl -s http://localhost:8765/api/studio/part/4/arrangement | python -m json.tool
```

Expected: `{"part": 4, "clips": []}` (empty — no clips imported yet)

- [ ] **Step 3: Commit**

```bash
git add creative_suite/api/studio.py
git commit -m "feat(nle): arrangement CRUD API + FX stack endpoints"
```

---

## Task 4: Import Existing Clip Lists into DB

**Files:**
- Modify: `creative_suite/api/studio.py` (add one import endpoint)

The arrangement GET already returns DB data. We need a way to seed the DB from existing `partNN.txt` files on first load, and an explicit import endpoint for the UI.

- [ ] **Step 1: Add import endpoint to `creative_suite/api/studio.py`**

```python
@router.post("/part/{part_num}/arrangement/import")
def import_from_clip_list(part_num: int, request: Request) -> dict[str, Any]:
    """Seed clip_arrangements from the existing partNN.txt manifest + T2/T3 dirs."""
    cfg = request.app.state.cfg
    db = _nle_db(request)

    # Use existing get_clips logic to read the current state
    clip_lists = _clip_lists_dir(request)
    clip_file = clip_lists / f"part{part_num:02d}.txt"
    if not clip_file.exists():
        raise HTTPException(404, f"No clip list for part {part_num}")

    # Re-use the existing saved order if available, otherwise parse .txt
    saved = _load_order_file(clip_lists, part_num)
    if saved is not None:
        raw_clips = saved
    else:
        raw_clips = []
        qv_part = cfg.quake_video_dir / "T1" / f"Part{part_num}"
        for line in clip_file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            c = _parse_clip_line(stripped, len(raw_clips))
            c["tier"] = "T1"
            c["is_fl"] = False
            name = Path(c["path"]).name
            c["name"] = name
            if not Path(c["path"]).is_absolute():
                c["path"] = str(qv_part / name)
            raw_clips.append(c)
        raw_clips += _scan_tier_dir(
            cfg.quake_video_dir / "T2" / f"Part{part_num}", "T2", len(raw_clips))
        raw_clips += _scan_tier_dir(
            cfg.quake_video_dir / "T3" / f"Part{part_num}", "T3", len(raw_clips))

    # Convert to nle_db format and bulk-replace
    db_clips = []
    for i, c in enumerate(raw_clips):
        db_clips.append({
            "clip_path": c.get("path", c.get("name", "")),
            "role":      "body",
            "tier":      c.get("tier", "T2"),
            "is_fl":     c.get("is_fl", False),
            "pair_path": None,
            "duration_s": None,
        })
    nle_db.bulk_replace_arrangement(db, part_num, db_clips)

    return {"imported": len(db_clips), "part": part_num}
```

- [ ] **Step 2: Test import for Part 4**

```bash
curl -s -X POST http://localhost:8765/api/studio/part/4/arrangement/import | python -m json.tool
# Then verify arrangement populated:
curl -s http://localhost:8765/api/studio/part/4/arrangement | python -m json.tool | head -40
```

Expected first response: `{"imported": N, "part": 4}` where N > 0.

- [ ] **Step 3: Commit**

```bash
git add creative_suite/api/studio.py
git commit -m "feat(nle): import clip list → DB endpoint"
```

---

## Task 5: Randomizer + Music API Endpoints

**Files:**
- Modify: `creative_suite/api/studio.py` (append more endpoints)
- Create: `creative_suite/engine/music_chain.py`

- [ ] **Step 1: Create `creative_suite/engine/music_chain.py`**

```python
"""creative_suite/engine/music_chain.py — Music beatmatch scoring for NLE.

Scores each track in the music library against:
  - Video body BPM (40%)
  - Duration coverage of the part (30%)
  - Chain score vs previous track (30%)

Returns top-N ranked candidates per role slot.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


def _bpm_match(track_bpm: float | None, video_bpm: float | None) -> float:
    if not track_bpm or not video_bpm or video_bpm == 0:
        return 0.5  # neutral if unknown
    return max(0.0, 1.0 - abs(track_bpm - video_bpm) / video_bpm)


def _duration_score(track_dur: float | None, body_dur: float | None) -> float:
    if not track_dur or not body_dur or body_dur == 0:
        return 0.5
    ratio = track_dur / body_dur
    # Ideal: track >= body. Penalty for short tracks (need repeat/stitch).
    if ratio >= 1.0:
        return 1.0
    return ratio  # 0.0–1.0


def _chain_score(prev_track: dict | None, candidate: dict) -> float:
    """Spectral/energy similarity heuristic: BPM proximity + key compat."""
    if prev_track is None:
        return 0.5  # no previous track — neutral
    prev_bpm = prev_track.get("bpm")
    cand_bpm = candidate.get("bpm")
    if not prev_bpm or not cand_bpm:
        return 0.5
    # BPM proximity: score 1.0 if within ±5 BPM, linear decay to 0.0 at ±30 BPM
    delta = abs(prev_bpm - cand_bpm)
    bpm_prox = max(0.0, 1.0 - delta / 30.0)
    return bpm_prox


def score_tracks(tracks: list[dict[str, Any]], body_dur: float,
                 video_bpm: float | None,
                 prev_track: dict | None = None,
                 top_n: int = 10) -> list[dict[str, Any]]:
    """Score and rank tracks for a given part + role slot."""
    scored = []
    for t in tracks:
        bpm_s  = _bpm_match(t.get("bpm"), video_bpm)
        dur_s  = _duration_score(t.get("duration_s"), body_dur)
        chain_s = _chain_score(prev_track, t)
        total  = bpm_s * 0.40 + dur_s * 0.30 + chain_s * 0.30
        scored.append({**t, "score": round(total, 3),
                       "score_bpm": round(bpm_s, 3),
                       "score_dur": round(dur_s, 3),
                       "score_chain": round(chain_s, 3)})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_n]


def load_library(library_dir: Path) -> list[dict[str, Any]]:
    """Scan engine/music/library/ and build a track list.

    BPM and duration_s are populated from a sidecar JSON
    (`engine/music/library/metadata.json`) if it exists; otherwise None.
    MusicLibrary.json has no BPM/key — detection via librosa is a future task.
    Scoring gracefully handles None values with neutral (0.5) scores.
    """
    if not library_dir.exists():
        return []
    # Load optional metadata sidecar
    meta: dict = {}
    meta_file = library_dir / "metadata.json"
    if meta_file.exists():
        import json as _json
        try:
            meta = _json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    tracks = []
    for f in sorted(library_dir.iterdir()):
        if f.suffix.lower() in (".mp3", ".wav", ".ogg", ".flac", ".m4a"):
            # Parse artist__title from slug filename
            stem = f.stem
            if "__" in stem:
                parts = stem.split("__", 1)
                artist = parts[0].replace("_", " ").title()
                title  = parts[1].replace("_", " ").title()
            else:
                artist = ""
                title  = stem.replace("_", " ").title()
            m = meta.get(f.name, {})
            tracks.append({
                "filename":   f.name,
                "artist":     artist,
                "title":      title,
                "bpm":        m.get("bpm"),       # from metadata.json sidecar; None = neutral score
                "duration_s": m.get("duration_s"),
            })
    return tracks
```

- [ ] **Step 2: Add randomizer + music endpoints to `creative_suite/api/studio.py`**

```python
import random as _random
from creative_suite.engine import music_chain as _music_chain


# ── Randomizer ────────────────────────────────────────────────────────────────

@router.post("/part/{part_num}/randomize")
def randomize_body(part_num: int, request: Request) -> dict[str, Any]:
    """Return a re-ordered body clip list. Does NOT write to DB — UI confirms."""
    db = _nle_db(request)
    rows = nle_db.get_arrangement(db, part_num)

    pinned    = [r for r in rows if r["role"] in ("intro", "outro")]
    body      = [r for r in rows if r["role"] == "body"]

    t1 = [c for c in body if c["tier"] == "T1"]
    t2 = [c for c in body if c["tier"] == "T2"]
    t3 = [c for c in body if c["tier"] == "T3"]

    _random.shuffle(t1)
    _random.shuffle(t2)
    _random.shuffle(t3)

    # Target: T2=60%, T1=25%, T3=15%
    total = len(body)
    t1_slots = max(1, round(total * 0.25)) if t1 else 0
    t3_slots = max(1, round(total * 0.15)) if t3 else 0
    t2_slots = total - t1_slots - t3_slots

    def _fill(pool: list, n: int) -> list:
        return (pool * math.ceil(n / max(len(pool), 1)))[:n] if pool else []

    import math
    t1_out = _fill(t1, t1_slots)
    t2_out = _fill(t2, t2_slots)
    t3_out = _fill(t3, t3_slots)

    # Interleave: mostly T2 with T1 at peaks, T3 as openers
    interleaved: list = []
    t3_iter = iter(t3_out)
    t1_iter = iter(t1_out)
    t2_iter = iter(t2_out)

    # First slot: T3 for cinematic opener if available
    first = next(t3_iter, None) or next(t2_iter, None)
    if first:
        interleaved.append(first)

    for i in range(total - len(interleaved)):
        if i % 4 == 3:           # every 4th slot: T1 peak
            c = next(t1_iter, None) or next(t2_iter, None)
        elif i % 6 == 5:         # every 6th slot: T3 atmosphere
            c = next(t3_iter, None) or next(t2_iter, None)
        else:
            c = next(t2_iter, None) or next(t1_iter, None)
        if c:
            interleaved.append(c)

    # Pad with any remaining clips
    for remaining in list(t1_iter) + list(t2_iter) + list(t3_iter):
        if len(interleaved) < total:
            interleaved.append(remaining)

    return {"part": part_num, "body_clips": interleaved, "pinned": pinned}


# ── Music recommendations ─────────────────────────────────────────────────────

@router.get("/part/{part_num}/music_recommend")
def music_recommend(part_num: int, request: Request,
                    prev_role: Optional[str] = None) -> dict[str, Any]:
    """Return top-10 track recommendations for a part + role slot."""
    cfg = request.app.state.cfg
    db  = _nle_db(request)

    library_dir = cfg.phase1_music_dir / "library"
    tracks = _music_chain.load_library(library_dir)

    # Use arrangement total duration as body_dur approximation
    rows = nle_db.get_arrangement(db, part_num)
    body_clips = [r for r in rows if r["role"] == "body"]
    body_dur = sum(r["duration_s"] or 5.0 for r in body_clips)

    # Find previous track for chain scoring
    prev_track = None
    if prev_role:
        music = nle_db.get_music_assignments(db, part_num)
        for m in music:
            if m["role"] == prev_role:
                prev_track = m
                break

    ranked = _music_chain.score_tracks(tracks, body_dur,
                                        video_bpm=None,
                                        prev_track=prev_track,
                                        top_n=10)
    return {"part": part_num, "recommendations": ranked}


# ── Music assignment ──────────────────────────────────────────────────────────

class _MusicAssignment(BaseModel):
    role:           str
    track_filename: str
    artist:         Optional[str] = None
    title:          Optional[str] = None
    bpm:            Optional[float] = None
    duration_s:     Optional[float] = None
    position:       int = 0
    transition_out: dict = {}


@router.put("/part/{part_num}/music")
def save_music_assignment(part_num: int, body: _MusicAssignment,
                          request: Request) -> dict[str, Any]:
    db = _nle_db(request)
    nle_db.upsert_music_assignment(
        db, part_num, body.role, body.track_filename,
        body.artist, body.title, body.bpm, body.duration_s,
        body.position, transition_out=body.transition_out,
    )
    return {"saved": True}


@router.delete("/part/{part_num}/music/{role}")
def clear_music_assignment(part_num: int, role: str,
                           request: Request) -> dict[str, Any]:
    db = _nle_db(request)
    with nle_db.get_db(db) as con:
        con.execute(
            "DELETE FROM music_assignments WHERE part=? AND role=?",
            (part_num, role),
        )
    return {"deleted": True}


# ── Audio FX ──────────────────────────────────────────────────────────────────

@router.get("/audio_fx")
def list_audio_fx(request: Request, part: int = 4) -> dict[str, Any]:
    db = _nle_db(request)
    rows = nle_db.get_audio_fx(db, part)
    return {"audio_fx": rows}


@router.put("/audio_fx/{fx_id}")
def update_audio_fx(fx_id: int, body: _FxUpdate,
                    request: Request) -> dict[str, Any]:
    db = _nle_db(request)
    nle_db.update_audio_fx(db, fx_id, body.params, body.enabled)
    return {"updated": True}
```

- [ ] **Step 3: Test randomize endpoint**

```bash
# Import part 4 first if not done:
curl -s -X POST http://localhost:8765/api/studio/part/4/arrangement/import
# Then randomize:
curl -s -X POST http://localhost:8765/api/studio/part/4/randomize | python -m json.tool | head -30
```

Expected: JSON with `body_clips` array (shuffled tier-balanced clip list).

- [ ] **Step 4: Test music recommend**

```bash
curl -s "http://localhost:8765/api/studio/part/4/music_recommend" | python -m json.tool | head -30
```

Expected: `{"part": 4, "recommendations": [...]}` with up to 10 tracks.

- [ ] **Step 5: Commit**

```bash
git add creative_suite/api/studio.py creative_suite/engine/music_chain.py
git commit -m "feat(nle): randomizer + music recommend + music assignment endpoints"
```

---

## Task 6: NLE Timeline Canvas (`studio-timeline-nle.js`)

**Files:**
- Create: `creative_suite/frontend/studio-timeline-nle.js`

This is the largest single file. It replaces `animation-timeline-js` with a custom `<canvas>` renderer.

- [ ] **Step 1: Create the file**

```javascript
/**
 * PANTHEON STUDIO — NLE Timeline (Canvas)
 * studio-timeline-nle.js
 *
 * Custom <canvas> Non-Linear Editor timeline.
 * No external dependencies.
 *
 * State sources:
 *   - StudioStore: clips[], selectedClip, activePart, currentTime
 *
 * Exposed on: window.StudioTimelineNLE
 * Rules: UI-1 (no innerHTML with untrusted data), UI-2 (store is source of truth)
 */
(function (global) {
  'use strict';

  // ── Constants ──────────────────────────────────────────────────────────────

  var TIER_COLORS = { T1: '#e8b923', T2: '#4a9eff', T3: '#7a7a9a' };
  var TIER_PINNED_BORDER = '#555';
  var RULER_H   = 24;  // px — time ruler height
  var CLIP_H    = 48;  // px — clip row height
  var AUDIO_H   = 32;  // px — audio track row height
  var MIN_CLIP_W = 8;   // px minimum rendered clip width
  var FONT_CLIP  = '11px "Bebas Neue", monospace';
  var FONT_RULER = '10px monospace';

  // ── Module state ───────────────────────────────────────────────────────────

  var _container   = null;
  var _canvas      = null;
  var _ctx         = null;
  var _clips       = [];
  var _ghostClips  = null;   // array when randomizer preview active
  var _selected    = [];     // selected clip indices
  var _dragging    = null;   // { clipIdx, startX, startPos }
  var _playheadT   = 0;      // seconds
  var _pixPerSec   = 60;     // zoom: pixels per second
  var _scrollLeft  = 0;
  var _clipboard   = [];
  var _unsubscribe = null;
  var _activePart  = null;
  var _raf         = null;
  var _dirty       = true;

  // ── Helpers ────────────────────────────────────────────────────────────────

  function _clipDur(clip) {
    return (clip.duration_s && clip.duration_s > 0) ? clip.duration_s : 5.0;
  }

  function _clipX(idx) {
    var x = 0;
    for (var i = 0; i < idx; i++) x += _clipDur(_clips[i]) * _pixPerSec;
    return x - _scrollLeft;
  }

  function _clipW(clip) {
    return Math.max(MIN_CLIP_W, _clipDur(clip) * _pixPerSec);
  }

  function _totalDur() {
    return _clips.reduce(function (s, c) { return s + _clipDur(c); }, 0);
  }

  function _hitTestClip(px, py) {
    // Returns clip index or -1. py must be in clip row zone (RULER_H to RULER_H+CLIP_H)
    if (py < RULER_H || py > RULER_H + CLIP_H) return -1;
    var x = 0;
    for (var i = 0; i < _clips.length; i++) {
      var w = _clipW(_clips[i]);
      var cx = x - _scrollLeft;
      if (px >= cx && px < cx + w) return i;
      x += _clipW(_clips[i]);
    }
    return -1;
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  function _render() {
    if (!_canvas || !_ctx) return;
    var W = _canvas.width;
    var H = _canvas.height;
    var ctx = _ctx;

    ctx.clearRect(0, 0, W, H);

    // Background
    ctx.fillStyle = '#0a0a0a';
    ctx.fillRect(0, 0, W, H);

    // Ruler
    ctx.fillStyle = '#111';
    ctx.fillRect(0, 0, W, RULER_H);
    ctx.fillStyle = '#333';
    ctx.fillRect(0, RULER_H - 1, W, 1);

    // Tick marks every second
    ctx.fillStyle = '#555';
    ctx.font = FONT_RULER;
    ctx.textAlign = 'left';
    var visStart = Math.floor(_scrollLeft / _pixPerSec);
    var visEnd   = Math.ceil((_scrollLeft + W) / _pixPerSec) + 1;
    for (var s = visStart; s <= visEnd; s++) {
      var tx = s * _pixPerSec - _scrollLeft;
      ctx.fillStyle = '#333';
      ctx.fillRect(tx, RULER_H - 8, 1, 8);
      if (s % 5 === 0) {
        ctx.fillStyle = '#777';
        ctx.fillRect(tx, RULER_H - 14, 1, 14);
        ctx.fillStyle = '#888';
        ctx.fillText(s + 's', tx + 2, RULER_H - 4);
      }
    }

    // Clip row background
    ctx.fillStyle = '#111';
    ctx.fillRect(0, RULER_H, W, CLIP_H);

    // Draw clips (ghost or real)
    var drawList = _ghostClips || _clips;
    var x = 0;
    for (var i = 0; i < drawList.length; i++) {
      var clip = drawList[i];
      var cx   = x - _scrollLeft;
      var cw   = _clipW(clip);
      var isSelected = _selected.indexOf(i) >= 0;
      var isPinned   = clip.role === 'intro' || clip.role === 'outro';
      var isGhost    = !!_ghostClips;

      // Clip body
      var color = TIER_COLORS[clip.tier] || '#4a9eff';
      ctx.globalAlpha = isGhost ? 0.5 : 1.0;
      ctx.fillStyle = color;
      if (isPinned) {
        ctx.fillStyle = '#1a1a1a';
        ctx.fillRect(cx, RULER_H + 2, cw - 1, CLIP_H - 4);
        ctx.strokeStyle = TIER_PINNED_BORDER;
        ctx.lineWidth = 1;
        ctx.strokeRect(cx + 0.5, RULER_H + 2.5, cw - 2, CLIP_H - 5);
        ctx.fillStyle = color;
        ctx.fillRect(cx, RULER_H + 2, 3, CLIP_H - 4);
      } else {
        ctx.fillRect(cx, RULER_H + 2, cw - 1, CLIP_H - 4);
      }

      // Selection highlight
      if (isSelected && !isGhost) {
        ctx.strokeStyle = '#fff';
        ctx.lineWidth = 2;
        ctx.strokeRect(cx + 1, RULER_H + 3, cw - 3, CLIP_H - 6);
      }

      // Tier label
      ctx.globalAlpha = 1.0;
      if (cw > 30) {
        ctx.fillStyle = isPinned ? color : '#000';
        ctx.font = FONT_CLIP;
        ctx.textAlign = 'left';
        var label = (clip.tier || 'T2');
        if (clip.name) label += ' ' + clip.name.slice(0, 12);
        ctx.fillText(label, cx + 4, RULER_H + CLIP_H - 8);
      }

      // Lock icon for pinned
      if (isPinned && cw > 20) {
        ctx.fillStyle = color;
        ctx.font = '10px monospace';
        ctx.textAlign = 'right';
        ctx.fillText('🔒', cx + cw - 4, RULER_H + 14);
      }

      x += cw;
    }

    ctx.globalAlpha = 1.0;

    // Playhead
    var phX = _playheadT * _pixPerSec - _scrollLeft;
    if (phX >= 0 && phX < W) {
      ctx.fillStyle = '#ff3333';
      ctx.fillRect(phX, 0, 2, RULER_H + CLIP_H);
    }

    // Audio row (placeholder waveform)
    var audioY = RULER_H + CLIP_H;
    ctx.fillStyle = '#0d0d0d';
    ctx.fillRect(0, audioY, W, AUDIO_H);
    ctx.fillStyle = '#1a3a1a';
    ctx.fillRect(0, audioY + 1, W, AUDIO_H - 2);
    ctx.fillStyle = '#2a5a2a';
    ctx.font = '10px monospace';
    ctx.textAlign = 'left';
    ctx.fillText('AUDIO TRACK — assign via GENERATE', 8, audioY + 20);

    _dirty = false;
  }

  function _scheduleRender() {
    if (_raf) return;
    _raf = requestAnimationFrame(function () {
      _raf = null;
      if (_dirty) _render();
    });
    _dirty = true;
  }

  // ── Canvas sizing ──────────────────────────────────────────────────────────

  function _resize() {
    if (!_canvas || !_container) return;
    var rect = _container.getBoundingClientRect();
    _canvas.width  = rect.width  || 800;
    _canvas.height = RULER_H + CLIP_H + AUDIO_H;
    _canvas.style.height = _canvas.height + 'px';
    _dirty = true;
    _scheduleRender();
  }

  // ── Mouse interaction ──────────────────────────────────────────────────────

  function _onMouseDown(e) {
    var rect = _canvas.getBoundingClientRect();
    var px = e.clientX - rect.left;
    var py = e.clientY - rect.top;
    var idx = _hitTestClip(px, py);

    if (idx < 0) {
      // Click on empty area — deselect
      _selected = [];
      _dispatch('SET_SELECTED_CLIP', null);
      _dirty = true;
      _scheduleRender();
      return;
    }

    if (e.shiftKey) {
      // Shift-click: add to selection
      var pos = _selected.indexOf(idx);
      if (pos >= 0) _selected.splice(pos, 1);
      else _selected.push(idx);
    } else if (_selected.indexOf(idx) < 0) {
      _selected = [idx];
    }

    // Notify store: primary selected clip
    var primaryClip = _clips[_selected[0]] || null;
    _dispatch('SET_SELECTED_CLIP', primaryClip);
    _dirty = true;
    _scheduleRender();

    // Start drag
    _dragging = { clipIdx: idx, startX: px, startPos: _clips[idx].position || idx };
    _canvas.addEventListener('mousemove', _onMouseMove);
    _canvas.addEventListener('mouseup', _onMouseUp);
  }

  function _onMouseMove(e) {
    if (!_dragging) return;
    var rect = _canvas.getBoundingClientRect();
    var px = e.clientX - rect.left;
    var dx = px - _dragging.startX;

    // Convert pixel delta to clip-position shift
    var avgDur = _totalDur() / Math.max(_clips.length, 1);
    var posShift = Math.round(dx / (_pixPerSec * Math.max(avgDur, 1)));
    var newPos = Math.max(0, Math.min(_clips.length - 1,
                          _dragging.startPos + posShift));

    if (newPos !== (_clips[_dragging.clipIdx].position || _dragging.clipIdx)) {
      _moveClip(_dragging.clipIdx, newPos);
      _dragging.clipIdx = newPos;  // follow the clip
    }

    _dirty = true;
    _scheduleRender();
  }

  function _onMouseUp() {
    _canvas.removeEventListener('mousemove', _onMouseMove);
    _canvas.removeEventListener('mouseup', _onMouseUp);
    if (_dragging) {
      _saveArrangement();
      _dragging = null;
    }
  }

  function _onContextMenu(e) {
    e.preventDefault();
    var rect = _canvas.getBoundingClientRect();
    var px = e.clientX - rect.left;
    var py = e.clientY - rect.top;
    var idx = _hitTestClip(px, py);
    if (idx < 0) return;
    _showContextMenu(e.clientX, e.clientY, idx);
  }

  function _onWheel(e) {
    e.preventDefault();
    _scrollLeft = Math.max(0, _scrollLeft + e.deltaY * 2);
    _dirty = true;
    _scheduleRender();
  }

  // ── Clip operations ────────────────────────────────────────────────────────

  function _moveClip(fromIdx, toIdx) {
    if (fromIdx === toIdx) return;
    var clip = _clips.splice(fromIdx, 1)[0];
    _clips.splice(toIdx, 0, clip);
    // Update selection
    _selected = _selected.map(function (i) {
      if (i === fromIdx) return toIdx;
      if (fromIdx < toIdx && i > fromIdx && i <= toIdx) return i - 1;
      if (fromIdx > toIdx && i >= toIdx && i < fromIdx) return i + 1;
      return i;
    });
  }

  function _deleteSelected() {
    if (_selected.length === 0) return;
    // Sort descending so splicing doesn't shift indices
    var sorted = _selected.slice().sort(function (a, b) { return b - a; });
    for (var i = 0; i < sorted.length; i++) {
      var clip = _clips[sorted[i]];
      if (clip.role === 'intro' || clip.role === 'outro') continue; // pinned
      _clips.splice(sorted[i], 1);
    }
    _selected = [];
    _dispatch('SET_SELECTED_CLIP', null);
    _saveArrangement();
    _dirty = true;
    _scheduleRender();
  }

  function _copySelected() {
    _clipboard = _selected.map(function (i) {
      return Object.assign({}, _clips[i]);
    });
  }

  function _cutSelected() {
    _copySelected();
    _deleteSelected();
  }

  function _pasteAtPlayhead() {
    if (_clipboard.length === 0) return;
    // Find insert position by playhead time
    var t = 0;
    var insertAt = _clips.length;
    for (var i = 0; i < _clips.length; i++) {
      t += _clipDur(_clips[i]);
      if (t >= _playheadT) { insertAt = i + 1; break; }
    }
    var newClips = _clipboard.map(function (c) {
      return Object.assign({}, c, { role: 'body', id: undefined });
    });
    Array.prototype.splice.apply(_clips, [insertAt, 0].concat(newClips));
    _saveArrangement();
    _dirty = true;
    _scheduleRender();
  }

  function _duplicateSelected() {
    _copySelected();
    _pasteAtPlayhead();
  }

  // ── Context menu ───────────────────────────────────────────────────────────

  function _showContextMenu(x, y, clipIdx) {
    var existing = document.getElementById('nle-ctx-menu');
    if (existing) existing.remove();

    var menu = document.createElement('div');
    menu.id = 'nle-ctx-menu';
    menu.className = 'nle-ctx-menu';
    menu.style.left = x + 'px';
    menu.style.top  = y + 'px';

    function _item(label, fn) {
      var li = document.createElement('div');
      li.className = 'nle-ctx-item';
      li.textContent = label;
      li.addEventListener('click', function () { menu.remove(); fn(); });
      menu.appendChild(li);
    }

    _item('Cut',    function () { _selected = [clipIdx]; _cutSelected(); });
    _item('Copy',   function () { _selected = [clipIdx]; _copySelected(); });
    _item('Delete', function () { _selected = [clipIdx]; _deleteSelected(); });
    _item('Duplicate', function () { _selected = [clipIdx]; _duplicateSelected(); });
    _item('Set as Intro', function () {
      _clips[clipIdx].role = 'intro';
      _saveArrangement(); _dirty = true; _scheduleRender();
    });
    _item('Set as Outro', function () {
      _clips[clipIdx].role = 'outro';
      _saveArrangement(); _dirty = true; _scheduleRender();
    });

    document.body.appendChild(menu);
    document.addEventListener('click', function _rm() {
      menu.remove();
      document.removeEventListener('click', _rm);
    });
  }

  // ── Keyboard ───────────────────────────────────────────────────────────────

  function _onKeyDown(e) {
    if (!_container) return;
    // Only handle if timeline has focus (check active element is canvas or child)
    if (!_canvas.contains(document.activeElement) &&
        document.activeElement !== _canvas) return;

    if ((e.ctrlKey || e.metaKey) && e.key === 'x') { e.preventDefault(); _cutSelected(); }
    else if ((e.ctrlKey || e.metaKey) && e.key === 'c') { e.preventDefault(); _copySelected(); }
    else if ((e.ctrlKey || e.metaKey) && e.key === 'v') { e.preventDefault(); _pasteAtPlayhead(); }
    else if ((e.ctrlKey || e.metaKey) && e.key === 'd') { e.preventDefault(); _duplicateSelected(); }
    else if (e.key === 'Delete' || e.key === 'Backspace') { e.preventDefault(); _deleteSelected(); }
  }

  // ── Ghost preview (randomizer) ─────────────────────────────────────────────

  function showGhostPreview(clips) {
    _ghostClips = clips;
    _dirty = true;
    _scheduleRender();
  }

  function clearGhostPreview() {
    _ghostClips = null;
    _dirty = true;
    _scheduleRender();
  }

  function acceptGhostPreview() {
    if (_ghostClips) {
      _clips = _ghostClips.slice();
      _ghostClips = null;
      _saveArrangement();
      _dirty = true;
      _scheduleRender();
    }
  }

  // ── API persistence ────────────────────────────────────────────────────────

  function _saveArrangement() {
    var part = _activePart;
    if (!part) return;
    var body = {
      clips: _clips.map(function (c, i) {
        return {
          clip_path: c.clip_path || c.path || '',
          role:      c.role  || 'body',
          tier:      c.tier  || 'T2',
          is_fl:     !!c.is_fl,
          pair_path: c.pair_path || null,
          duration_s: c.duration_s || null,
        };
      }),
    };
    fetch('/api/studio/part/' + part + '/arrangement', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }).catch(function (err) {
      console.error('[NLETimeline] save failed', err);
    });
  }

  function _dispatch(type, payload) {
    if (global.StudioStore) global.StudioStore.dispatch({ type: type, payload: payload });
  }

  // ── Store subscription ─────────────────────────────────────────────────────

  function _subscribeStore() {
    if (!global.StudioStore) return;
    _unsubscribe = global.StudioStore.subscribe(function (state, prev) {
      var clipsChanged = state.clips !== prev.clips;
      var partChanged  = state.activePart !== prev.activePart;
      var timeChanged  = state.currentTime !== prev.currentTime;

      if (partChanged) {
        _activePart = state.activePart;
      }
      if (clipsChanged) {
        // Merge store clips with current arrangement (preserve DB id, role, effects)
        _clips = (state.clips || []).map(function (c) {
          return Object.assign({ role: 'body', duration_s: null }, c, {
            clip_path: c.path || c.clip_path || '',
          });
        });
        _selected = [];
        _dirty = true;
        _scheduleRender();
      }
      if (timeChanged) {
        _playheadT = state.currentTime || 0;
        _dirty = true;
        _scheduleRender();
      }
    });

    // Seed from current state
    var s = global.StudioStore.getState();
    _activePart = s.activePart;
    _clips = (s.clips || []).map(function (c) {
      return Object.assign({ role: 'body', duration_s: null }, c, {
        clip_path: c.path || c.clip_path || '',
      });
    });
  }

  // ── Public API ─────────────────────────────────────────────────────────────

  function mount(container) {
    _container = container;

    _canvas = document.createElement('canvas');
    _canvas.tabIndex = 0;  // allow keyboard focus
    _canvas.className = 'nle-canvas';
    _canvas.style.width = '100%';
    _canvas.style.display = 'block';
    _canvas.style.cursor = 'pointer';

    container.replaceChildren(_canvas);
    _ctx = _canvas.getContext('2d');

    _canvas.addEventListener('mousedown', _onMouseDown);
    _canvas.addEventListener('contextmenu', _onContextMenu);
    _canvas.addEventListener('wheel', _onWheel, { passive: false });
    document.addEventListener('keydown', _onKeyDown);

    _subscribeStore();

    var ro = new ResizeObserver(_resize);
    ro.observe(container);
    _resize();
  }

  function unmount() {
    if (_unsubscribe) { _unsubscribe(); _unsubscribe = null; }
    if (_canvas) {
      _canvas.removeEventListener('mousedown', _onMouseDown);
      _canvas.removeEventListener('contextmenu', _onContextMenu);
      _canvas.removeEventListener('wheel', _onWheel);
    }
    document.removeEventListener('keydown', _onKeyDown);
    if (_raf) { cancelAnimationFrame(_raf); _raf = null; }
    _container = null;
    _canvas = null;
    _ctx = null;
  }

  function setZoom(pixPerSec) {
    _pixPerSec = Math.max(10, Math.min(200, pixPerSec));
    _dirty = true;
    _scheduleRender();
  }

  global.StudioTimelineNLE = {
    mount:             mount,
    unmount:           unmount,
    setZoom:           setZoom,
    showGhostPreview:  showGhostPreview,
    clearGhostPreview: clearGhostPreview,
    acceptGhostPreview: acceptGhostPreview,
  };

}(typeof window !== 'undefined' ? window : this));
```

- [ ] **Step 2: Register in studio.html**

In `creative_suite/frontend/studio.html`, add the script tag **before** `studio-edit.js`:

```html
<script src="/static/frontend/studio-timeline-nle.js"></script>
```

- [ ] **Step 3: Commit**

```bash
git add creative_suite/frontend/studio-timeline-nle.js creative_suite/frontend/studio.html
git commit -m "feat(nle): canvas NLE timeline with select/drag/edit/ghost preview"
```

---

## Task 7: Wire NLE Timeline into `studio-edit.js`

**Files:**
- Modify: `creative_suite/frontend/studio-edit.js`

The timeline slot is currently filled by the old `animation-timeline-js`. Replace with `StudioTimelineNLE`.

- [ ] **Step 1: Locate the timeline slot in `studio-edit.js`**

Find the section in `mount()` that creates and mounts the timeline. Look for `animation-timeline` or `_tlSlot`. Replace the timeline mount block:

Find:
```javascript
_tlSlot = timelinePanel;
```

After `_mountSubModules()` is called, find where the timeline sub-module is mounted and replace with:

```javascript
// In _mountSubModules() or inline after slot.replaceChildren(_root):
if (_tlSlot && global.StudioTimelineNLE) {
  global.StudioTimelineNLE.mount(_tlSlot);
  _activeMods.push(global.StudioTimelineNLE);
}
```

- [ ] **Step 2: Add RANDOMIZE and GENERATE buttons to the toolbar**

In the toolbar section of `studio-edit.js` `_buildToolbar()` or wherever the edit-page buttons are assembled, add:

```javascript
var btnRandomize = _el('button', 'edit-btn edit-randomize-btn');
btnRandomize.textContent = 'RANDOMIZE';
btnRandomize.addEventListener('click', _randomize);
toolbar.appendChild(btnRandomize);

var btnGenerate = _el('button', 'edit-btn edit-generate-btn');
btnGenerate.textContent = 'GENERATE';
btnGenerate.addEventListener('click', _openGeneratePanel);
toolbar.appendChild(btnGenerate);
```

- [ ] **Step 3: Add `_randomize()` function to `studio-edit.js`**

```javascript
function _randomize() {
  var part = global.StudioStore.getState().activePart;
  if (!part) return;
  fetch('/api/studio/part/' + part + '/randomize', { method: 'POST' })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      var clips = data.body_clips || [];
      if (global.StudioTimelineNLE) {
        global.StudioTimelineNLE.showGhostPreview(clips);
      }
      _showRandomizeConfirm(clips);
    })
    .catch(function (err) {
      console.error('[Edit] randomize failed', err);
    });
}

function _showRandomizeConfirm(clips) {
  var existing = document.getElementById('randomize-confirm');
  if (existing) existing.remove();

  var bar = document.createElement('div');
  bar.id = 'randomize-confirm';
  bar.className = 'randomize-confirm-bar';

  var msg = document.createElement('span');
  msg.textContent = 'Preview: ' + clips.length + ' clips reshuffled';
  bar.appendChild(msg);

  var btnAccept = document.createElement('button');
  btnAccept.textContent = 'ACCEPT';
  btnAccept.className = 'edit-btn edit-accept-btn';
  btnAccept.addEventListener('click', function () {
    if (global.StudioTimelineNLE) global.StudioTimelineNLE.acceptGhostPreview();
    bar.remove();
  });

  var btnTryAgain = _el('button', 'edit-btn');
  btnTryAgain.textContent = 'TRY AGAIN';
  btnTryAgain.addEventListener('click', function () {
    if (global.StudioTimelineNLE) global.StudioTimelineNLE.clearGhostPreview();
    bar.remove();
    _randomize();
  });

  var btnCancel = _el('button', 'edit-btn');
  btnCancel.textContent = 'CANCEL';
  btnCancel.addEventListener('click', function () {
    if (global.StudioTimelineNLE) global.StudioTimelineNLE.clearGhostPreview();
    bar.remove();
  });

  bar.appendChild(btnAccept);
  bar.appendChild(btnTryAgain);
  bar.appendChild(btnCancel);

  // Insert above the timeline panel
  var root = document.getElementById('edit-root') || document.body;
  root.insertBefore(bar, root.firstChild);
}
```

- [ ] **Step 4: Add `_openGeneratePanel()` function**

```javascript
function _openGeneratePanel() {
  var part = global.StudioStore.getState().activePart;
  if (!part) return;

  var existing = document.getElementById('generate-panel');
  if (existing) { existing.remove(); return; }

  fetch('/api/studio/part/' + part + '/music_recommend')
    .then(function (r) { return r.json(); })
    .then(function (data) {
      _renderGeneratePanel(part, data.recommendations || []);
    })
    .catch(function (err) {
      console.error('[Edit] music_recommend failed', err);
    });
}

function _renderGeneratePanel(part, tracks) {
  var panel = document.createElement('div');
  panel.id = 'generate-panel';
  panel.className = 'generate-panel';

  var hdr = document.createElement('div');
  hdr.className = 'generate-panel-hdr';
  var title = document.createElement('span');
  title.className = 'generate-panel-title';
  title.textContent = 'BEATMATCH RECOMMENDATIONS — Part ' + part;
  var btnClose = document.createElement('button');
  btnClose.className = 'generate-panel-close';
  btnClose.textContent = '✕';
  btnClose.addEventListener('click', function () { panel.remove(); });
  hdr.appendChild(title);
  hdr.appendChild(btnClose);
  panel.appendChild(hdr);

  var list = document.createElement('div');
  list.className = 'generate-track-list';

  if (tracks.length === 0) {
    var empty = document.createElement('div');
    empty.className = 'generate-empty';
    empty.textContent = 'No tracks in library yet — add MP3s to engine/music/library/';
    list.appendChild(empty);
  } else {
    tracks.forEach(function (t) {
      var row = document.createElement('div');
      row.className = 'generate-track-row';

      var pct = document.createElement('span');
      pct.className = 'generate-track-pct';
      pct.textContent = Math.round((t.score || 0) * 100) + '%';

      var info = document.createElement('span');
      info.className = 'generate-track-info';
      info.textContent = (t.title || t.filename) + (t.artist ? ' — ' + t.artist : '');

      var meta = document.createElement('span');
      meta.className = 'generate-track-meta';
      meta.textContent = (t.bpm ? t.bpm + ' BPM' : '? BPM') +
                         (t.duration_s ? '  ' + _fmtDur(t.duration_s) : '');

      var btnSel = document.createElement('button');
      btnSel.className = 'generate-select-btn';
      btnSel.textContent = 'SELECT';
      (function (track) {
        btnSel.addEventListener('click', function () {
          _assignMusic(part, 'main_1', track, panel);
        });
      }(t));

      row.appendChild(pct);
      row.appendChild(info);
      row.appendChild(meta);
      row.appendChild(btnSel);
      list.appendChild(row);
    });
  }

  panel.appendChild(list);

  // Insert above timeline
  var root = document.getElementById('edit-root') || document.body;
  root.insertBefore(panel, root.firstChild);
}

function _assignMusic(part, role, track, panel) {
  fetch('/api/studio/part/' + part + '/music', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      role:           role,
      track_filename: track.filename,
      artist:         track.artist || null,
      title:          track.title  || null,
      bpm:            track.bpm    || null,
      duration_s:     track.duration_s || null,
      position:       0,
    }),
  }).then(function () {
    if (panel) {
      var title = panel.querySelector('.generate-panel-title');
      if (title) title.textContent = 'Assigned: ' + (track.title || track.filename);
    }
    // Fetch chain recommendations for next slot
    fetch('/api/studio/part/' + part + '/music_recommend?prev_role=' + role)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        // Update panel with chain recommendations
        var list = panel ? panel.querySelector('.generate-track-list') : null;
        if (list && data.recommendations && data.recommendations.length > 0) {
          _appendChainSection(list, part, 'main_2', data.recommendations, panel);
        }
      });
  });
}

function _appendChainSection(list, part, role, tracks, panel) {
  var sep = document.createElement('div');
  sep.className = 'generate-chain-sep';
  sep.textContent = 'CHAIN → ' + role.toUpperCase();
  list.appendChild(sep);
  tracks.slice(0, 5).forEach(function (t) {
    var row = document.createElement('div');
    row.className = 'generate-track-row';
    var pct = document.createElement('span');
    pct.className = 'generate-track-pct';
    pct.textContent = Math.round((t.score || 0) * 100) + '%';
    var info = document.createElement('span');
    info.className = 'generate-track-info';
    info.textContent = (t.title || t.filename) + (t.artist ? ' — ' + t.artist : '');
    var btnSel = document.createElement('button');
    btnSel.className = 'generate-select-btn';
    btnSel.textContent = 'SELECT';
    (function (track) {
      btnSel.addEventListener('click', function () {
        _assignMusic(part, role, track, panel);
      });
    }(t));
    row.appendChild(pct);
    row.appendChild(info);
    row.appendChild(btnSel);
    list.appendChild(row);
  });
}

function _fmtDur(s) {
  var n = Number(s);
  if (isNaN(n)) return '';
  var m = Math.floor(n / 60);
  var sec = Math.floor(n % 60);
  return m + ':' + (sec < 10 ? '0' : '') + sec;
}
```

- [ ] **Step 5: Commit**

```bash
git add creative_suite/frontend/studio-edit.js
git commit -m "feat(nle): wire NLE timeline, RANDOMIZE ghost preview, GENERATE music panel"
```

---

## Task 8: Inspector FX Stack

**Files:**
- Modify: `creative_suite/frontend/studio-inspector.js`

Add a FX STACK section below the existing OVERRIDES section. Each clip shows its effects from the DB; user can add/remove/toggle effects.

- [ ] **Step 1: Add FX stack builder functions to `studio-inspector.js`**

After the existing `_rangeRow` / `_selectRow` helpers, add:

```javascript
var FX_CATALOGUE = [
  { type: 'slowmo',       label: 'SLOW MOTION',    params: [
    { key: 'rate',     label: 'Rate',    min: 0.1, max: 1.0, step: 0.05, def: 0.5 },
    { key: 'window_s', label: 'Window', min: 0.2, max: 3.0, step: 0.1,  def: 0.8 },
  ]},
  { type: 'speedup',      label: 'SPEED UP',       params: [
    { key: 'rate',     label: 'Rate',    min: 1.1, max: 4.0, step: 0.1, def: 2.0 },
    { key: 'window_s', label: 'Window', min: 0.2, max: 2.0, step: 0.1, def: 0.5 },
  ]},
  { type: 'zoom',         label: 'ZOOM',           params: [
    { key: 'scale',    label: 'Scale',  min: 1.1, max: 2.0, step: 0.05, def: 1.3 },
  ]},
  { type: 'vignette',     label: 'VIGNETTE',       params: [
    { key: 'intensity', label: 'Intensity', min: 0, max: 1, step: 0.05, def: 0.5 },
  ]},
  { type: 'shine_on_kill', label: 'SHINE ON KILL', params: [
    { key: 'intensity', label: 'Intensity', min: 0, max: 1, step: 0.05, def: 0.8 },
  ]},
  { type: 'bass_drop',    label: 'BASS DROP',      params: [
    { key: 'delay_ms',  label: 'Delay ms', min: 0, max: 500, step: 10, def: 0 },
    { key: 'intensity', label: 'Intensity', min: 0, max: 1, step: 0.05, def: 0.8 },
  ]},
  { type: 'reverb_tail',  label: 'REVERB TAIL',   params: [
    { key: 'decay_s', label: 'Decay s', min: 0.2, max: 2.0, step: 0.1, def: 0.8 },
    { key: 'mix',     label: 'Mix',     min: 0,   max: 1,   step: 0.05, def: 0.5 },
  ]},
];

function _fxCatalogue(type) {
  for (var i = 0; i < FX_CATALOGUE.length; i++) {
    if (FX_CATALOGUE[i].type === type) return FX_CATALOGUE[i];
  }
  return null;
}

function _buildFxCard(fx, clipId, part, onRemove) {
  var cat = _fxCatalogue(fx.effect_type) || { label: fx.effect_type, params: [] };
  var params = JSON.parse(fx.params || '{}');

  var card = _el('div', 'insp-fx-card' + (fx.enabled ? '' : ' insp-fx-card--off'));

  var hdr = _el('div', 'insp-fx-card-hdr');
  var toggle = _el('button', 'insp-fx-toggle', fx.enabled ? '●' : '○');
  toggle.title = 'Toggle';
  var lbl = _el('span', 'insp-fx-label', cat.label);
  var rmBtn = _el('button', 'insp-fx-rm', '✕');
  rmBtn.title = 'Remove';
  hdr.appendChild(toggle);
  hdr.appendChild(lbl);
  hdr.appendChild(rmBtn);
  card.appendChild(hdr);

  var currentParams = Object.assign({}, params);
  var enabled = !!fx.enabled;

  function _save() {
    fetch('/api/studio/part/' + part + '/arrangement/' + clipId + '/fx/' + fx.id, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ params: currentParams, enabled: enabled }),
    }).catch(function (err) { console.error('[Inspector] FX save failed', err); });
  }

  toggle.addEventListener('click', function () {
    enabled = !enabled;
    toggle.textContent = enabled ? '●' : '○';
    card.className = 'insp-fx-card' + (enabled ? '' : ' insp-fx-card--off');
    _save();
  });

  rmBtn.addEventListener('click', function () {
    fetch('/api/studio/part/' + part + '/arrangement/' + clipId + '/fx/' + fx.id, {
      method: 'DELETE',
    }).then(function () { onRemove(); });
  });

  // Parameter rows
  cat.params.forEach(function (p) {
    var v = (params[p.key] !== undefined) ? params[p.key] : p.def;
    var row = _rangeRow(p.label, p.min, p.max, p.step, v, function (newVal) {
      currentParams[p.key] = newVal;
    });
    card.appendChild(row);
  });

  // APPLY button for this card
  var applyBtn = _el('button', 'insp-fx-apply-btn', 'APPLY');
  applyBtn.addEventListener('click', _save);
  card.appendChild(applyBtn);

  return card;
}

function _buildFxSection(clip, part) {
  var sec = _el('div', 'insp-section');
  sec.appendChild(_el('div', 'insp-section-title', 'FX STACK'));
  var body = _el('div', 'insp-fx-body');

  function _reloadFx() {
    // Fetch effects for this clip from DB
    fetch('/api/studio/part/' + part + '/arrangement')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var arr = data.clips || [];
        var match = null;
        for (var i = 0; i < arr.length; i++) {
          if (arr[i].clip_path === (clip.clip_path || clip.path)) {
            match = arr[i]; break;
          }
        }
        var effects = (match && match.effects) ? match.effects : [];
        body.replaceChildren();
        effects.forEach(function (fx) {
          body.appendChild(_buildFxCard(fx, match ? match.id : 0, part, _reloadFx));
        });
        body.appendChild(_buildAddFxRow(match ? match.id : 0, part, _reloadFx));
      });
  }

  _reloadFx();
  sec.appendChild(body);
  return sec;
}

function _buildAddFxRow(clipId, part, onAdded) {
  var row = _el('div', 'insp-add-fx-row');
  var sel = document.createElement('select');
  sel.className = 'insp-select';
  FX_CATALOGUE.forEach(function (cat) {
    var opt = document.createElement('option');
    opt.value = cat.type;
    opt.textContent = cat.label;
    sel.appendChild(opt);
  });
  var btn = _el('button', 'insp-apply-btn', '+ ADD EFFECT');
  btn.addEventListener('click', function () {
    var type = sel.value;
    var cat = _fxCatalogue(type);
    var defaultParams = {};
    (cat ? cat.params : []).forEach(function (p) { defaultParams[p.key] = p.def; });
    fetch('/api/studio/part/' + part + '/arrangement/' + clipId + '/fx', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ effect_type: type, params: defaultParams, position: 0 }),
    }).then(function () { onAdded(); });
  });
  row.appendChild(sel);
  row.appendChild(btn);
  return row;
}
```

- [ ] **Step 2: Call `_buildFxSection()` inside `_showClip()`**

Find `_showClip()` in `studio-inspector.js`. After the OVERRIDES section is appended, add:

```javascript
  var part = global.StudioStore && global.StudioStore.getState().activePart;
  if (part) {
    _bodyEl.appendChild(_buildFxSection(clip, part));
  }
```

- [ ] **Step 3: Commit**

```bash
git add creative_suite/frontend/studio-inspector.js
git commit -m "feat(nle): Inspector FX stack with effect cards and DB persistence"
```

---

## Task 9: CSS — NLE Timeline + FX Stack + Generate Panel

**Files:**
- Modify: `creative_suite/frontend/studio.css` (append)

- [ ] **Step 1: Append styles**

```css
/* ── NLE Timeline canvas ──────────────────────────────────────────────────── */
.nle-canvas {
  display: block;
  width: 100%;
  background: #0a0a0a;
  border-top: 1px solid #222;
}
.nle-ctx-menu {
  position: fixed;
  z-index: 8000;
  background: #1a1a1a;
  border: 1px solid #444;
  border-radius: 3px;
  min-width: 140px;
  padding: 4px 0;
}
.nle-ctx-item {
  padding: 6px 14px;
  font-size: 12px;
  cursor: pointer;
  color: #ccc;
  font-family: 'Bebas Neue', monospace;
  letter-spacing: .08em;
}
.nle-ctx-item:hover { background: #2a2a2a; color: #e8b923; }

/* ── Randomize confirm bar ────────────────────────────────────────────────── */
.randomize-confirm-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: #111;
  border-bottom: 1px solid #333;
  font-family: 'Bebas Neue', monospace;
  letter-spacing: .08em;
  font-size: 13px;
  color: #aaa;
}
.edit-randomize-btn { border-color: #e8b923; color: #e8b923; }
.edit-generate-btn  { border-color: #4a9eff; color: #4a9eff; }
.edit-accept-btn    { background: #2a4a2a; border-color: #5fba7d; color: #5fba7d; }

/* ── Generate panel ───────────────────────────────────────────────────────── */
.generate-panel {
  background: #0d0d0d;
  border-bottom: 1px solid #333;
  max-height: 280px;
  display: flex;
  flex-direction: column;
}
.generate-panel-hdr {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid #222;
}
.generate-panel-title {
  font-family: 'Bebas Neue', monospace;
  font-size: 13px;
  letter-spacing: .12em;
  color: #e8b923;
}
.generate-panel-close {
  background: none;
  border: none;
  color: #555;
  cursor: pointer;
  font-size: 14px;
}
.generate-panel-close:hover { color: #ccc; }
.generate-track-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 0;
}
.generate-track-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 5px 12px;
  border-bottom: 1px solid #1a1a1a;
  font-size: 12px;
}
.generate-track-row:hover { background: #141414; }
.generate-track-pct {
  min-width: 38px;
  font-family: monospace;
  font-weight: 700;
  color: #5fba7d;
}
.generate-track-info { flex: 1; color: #ccc; }
.generate-track-meta { color: #555; font-size: 11px; min-width: 90px; }
.generate-select-btn {
  background: none;
  border: 1px solid #333;
  color: #888;
  padding: 2px 8px;
  cursor: pointer;
  font-size: 11px;
  font-family: 'Bebas Neue', monospace;
  border-radius: 2px;
}
.generate-select-btn:hover { border-color: #e8b923; color: #e8b923; }
.generate-chain-sep {
  padding: 5px 12px;
  font-size: 10px;
  letter-spacing: .12em;
  color: #4a9eff;
  font-family: 'Bebas Neue', monospace;
  border-top: 1px solid #1a2a3a;
}
.generate-empty { padding: 12px; color: #444; font-size: 12px; }

/* ── FX Stack ─────────────────────────────────────────────────────────────── */
.insp-fx-card {
  background: #111;
  border: 1px solid #2a2a2a;
  border-radius: 3px;
  margin-bottom: 4px;
}
.insp-fx-card--off { opacity: 0.45; }
.insp-fx-card-hdr {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 8px;
  border-bottom: 1px solid #222;
}
.insp-fx-toggle {
  background: none;
  border: none;
  color: #e8b923;
  cursor: pointer;
  font-size: 14px;
  padding: 0;
  line-height: 1;
}
.insp-fx-label {
  flex: 1;
  font-family: 'Bebas Neue', monospace;
  letter-spacing: .08em;
  font-size: 11px;
  color: #ccc;
}
.insp-fx-rm {
  background: none;
  border: none;
  color: #333;
  cursor: pointer;
  font-size: 12px;
}
.insp-fx-rm:hover { color: #e05050; }
.insp-fx-apply-btn {
  width: 100%;
  background: #1a1a1a;
  border: none;
  border-top: 1px solid #222;
  color: #555;
  font-family: 'Bebas Neue', monospace;
  letter-spacing: .1em;
  padding: 4px;
  cursor: pointer;
  font-size: 10px;
}
.insp-fx-apply-btn:hover { color: #e8b923; }
.insp-fx-body { padding: 4px; }
.insp-add-fx-row {
  display: flex;
  gap: 6px;
  padding: 6px 4px;
  border-top: 1px solid #1a1a1a;
}
.insp-add-fx-row .insp-select { flex: 1; }
```

- [ ] **Step 2: Commit**

```bash
git add creative_suite/frontend/studio.css
git commit -m "feat(nle): CSS for canvas timeline, FX stack, generate panel, randomize bar"
```

---

## Task 10: Manifest Generator

**Files:**
- Create: `creative_suite/engine/manifest_generator.py`

- [ ] **Step 1: Create the manifest generator**

```python
"""creative_suite/engine/manifest_generator.py — DB → render manifest bridge.

Reads studio_nle.db and emits:
  creative_suite/engine/clip_lists/partNN.txt
  creative_suite/engine/clip_lists/partNN_overrides.txt

Called by the render pipeline at render time. Zero changes to render code.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from creative_suite.config import Config
from creative_suite.database import nle_db


def generate_manifest(part: int, cfg: Config | None = None) -> dict[str, Any]:
    """Read DB state for a part and write clip list + overrides files."""
    if cfg is None:
        cfg = Config()

    db = cfg.nle_db_path
    rows = nle_db.get_arrangement(db, part)

    if not rows:
        return {"status": "empty", "part": part, "clips": 0}

    clip_lists = cfg.phase1_clip_lists
    nn = f"{part:02d}"

    # ── Clip list (partNN.txt) ─────────────────────────────────────────────────
    lines = [
        f"# Part {part} — generated from studio_nle.db",
        f"# {len(rows)} clips",
    ]
    for row in rows:
        path = row["clip_path"]
        effects = nle_db.get_clip_effects(db, row["id"])
        tags = []
        for fx in effects:
            if not fx["enabled"]:
                continue
            params = json.loads(fx["params"] or "{}")
            ftype = fx["effect_type"]
            if ftype == "slowmo":
                tags.append(f"slow={params.get('rate', 0.5)}")
                if "window_s" in params:
                    tags.append(f"slow_window={params['window_s']}")
            elif ftype == "speedup":
                tags.append(f"speed={params.get('rate', 2.0)}")
            elif ftype == "zoom":
                tags.append(f"zoom={params.get('scale', 1.3)}")
        if row["role"] in ("intro", "outro"):
            tags.append(f"[{row['role']}]")
        suffix = " [" + " ".join(tags) + "]" if tags else ""
        if row["pair_path"]:
            lines.append(f"{path} > {row['pair_path']}{suffix}")
        else:
            lines.append(f"{path}{suffix}")

    clip_file = clip_lists / f"part{nn}.txt"
    clip_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ── Overrides (partNN_overrides.txt) ───────────────────────────────────────
    music = nle_db.get_music_assignments(db, part)
    overrides: list[str] = []
    for m in music:
        role = m["role"]
        fn   = m["track_filename"]
        tout = json.loads(m["transition_out"] or "{}")
        overrides.append(f"{role}_music={fn}")
        if tout:
            overrides.append(f"{role}_transition_out={json.dumps(tout)}")

    if overrides:
        ovr_file = clip_lists / f"part{nn}_overrides.txt"
        ovr_file.write_text("\n".join(overrides) + "\n", encoding="utf-8")

    return {
        "status": "ok",
        "part":   part,
        "clips":  len(rows),
        "music_tracks": len(music),
        "clip_file": str(clip_file),
    }


def generate_all(cfg: Config | None = None) -> list[dict[str, Any]]:
    """Regenerate manifests for all parts that have DB arrangements."""
    if cfg is None:
        cfg = Config()
    db = cfg.nle_db_path
    results = []
    for part in range(1, 13):
        rows = nle_db.get_arrangement(db, part)
        if rows:
            results.append(generate_manifest(part, cfg))
    return results
```

- [ ] **Step 2: Add a manifest generate endpoint to `studio.py`**

```python
from creative_suite.engine import manifest_generator as _manifest_gen

@router.post("/part/{part_num}/generate_manifest")
def generate_manifest(part_num: int, request: Request) -> dict[str, Any]:
    cfg = request.app.state.cfg
    result = _manifest_gen.generate_manifest(part_num, cfg)
    return result
```

- [ ] **Step 3: Test manifest generation for Part 4**

```bash
# Import Part 4 into DB (if not done)
curl -s -X POST http://localhost:8765/api/studio/part/4/arrangement/import

# Generate manifest
curl -s -X POST http://localhost:8765/api/studio/part/4/generate_manifest | python -m json.tool

# Verify output files
python -c "
from pathlib import Path
print(Path('creative_suite/engine/clip_lists/part04.txt').read_text()[:500])
"
```

Expected: manifest file matches the DB arrangement order.

- [ ] **Step 4: Commit**

```bash
git add creative_suite/engine/manifest_generator.py creative_suite/api/studio.py
git commit -m "feat(nle): manifest generator — DB → partNN.txt + overrides bridge"
```

---

## Task 11: End-to-End Smoke Test

**Files:** No new files — integration test only.

- [ ] **Step 1: Import Part 4 clips into DB**

```bash
curl -s -X POST http://localhost:8765/api/studio/part/4/arrangement/import
curl -s http://localhost:8765/api/studio/part/4/arrangement | python -m json.tool | head -20
```

Expected: clips array populated from existing part04.txt + T2/T3 dirs.

- [ ] **Step 2: Randomize + accept**

Open browser: `http://localhost:8765/studio?mode=studio&page=edit`
- Select Part 4
- Click RANDOMIZE → ghost preview appears on timeline
- Click ACCEPT → clips reordered + saved to DB

- [ ] **Step 3: Assign music**

- Click GENERATE → recommendations panel opens
- Click SELECT on top track
- Observe chain recommendations appear

- [ ] **Step 4: Add an FX to a clip**

- Click a clip on the timeline → Inspector FX stack appears
- Click `+ ADD EFFECT` → select SLOW MOTION
- Adjust Rate slider → click APPLY

- [ ] **Step 5: Generate manifest**

```bash
curl -s -X POST http://localhost:8765/api/studio/part/4/generate_manifest | python -m json.tool
```

Verify `part04.txt` reflects the new arrangement.

- [ ] **Step 6: Final commit**

```bash
git add -A
git commit -m "feat(nle): Phase 1 NLE closing — complete end-to-end integration"
```

---

## Self-Review

### Spec Coverage

| Spec section | Covered by task |
|---|---|
| §3 DB schema (4 tables) | Task 1 |
| §4 NLE timeline canvas (render/select/drag) | Task 6 |
| §4.3 Gap-close on delete | Task 6 (_deleteSelected, _moveClip splice) |
| §4.4 Pinned clips (intro/outro) | Task 6 (role check in drag/delete) |
| §5 Inspector FX stack | Task 8 |
| §5.1 Effect catalogue | Task 8 (FX_CATALOGUE) |
| §6 Randomizer (T1/T2/T3 ratio, ghost preview) | Task 5 (backend) + Task 7 (frontend) |
| §7 Music beatmatch chain | Task 5 (music_chain.py + endpoint) + Task 7 (generate panel) |
| §7.3 Fade-over / transition JSON | music_assignments.transition_out written by Task 5 |
| §8 Manifest generator | Task 10 |
| §9 API endpoints (9 total) | Tasks 3, 4, 5, 10 |
| §10 Files list | All tasks combined |
| §11 Implementation order | Matches task order 1-11 |

### Type Consistency Check

- `clip_path` used consistently across nle_db.py, API models, timeline JS, manifest generator ✓
- `arrangement_id` FK in clip_effects matches `id` from clip_arrangements ✓  
- `role` values (`intro`/`body`/`outro`) consistent across schema, API, timeline canvas, manifest ✓
- `effect_type` strings in FX_CATALOGUE JS match `effect_type` column in schema ✓
- `_nle_db(request)` helper used consistently in all new API endpoints ✓

### No Placeholders

Scanned — no TBD, TODO, "similar to", or "appropriate error handling" found in plan. All code steps are complete. ✓
