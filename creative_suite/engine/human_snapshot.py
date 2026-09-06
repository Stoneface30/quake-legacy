"""A consistent snapshot of everything a human decided.

WHY THE BACKUP API AND NOT A FILE COPY. SQLite in WAL mode keeps recent
commits in `-wal` until a checkpoint. Copying `.db`, `-wal` and `-shm` as
three separate files is three reads at three different instants: the result
can hold a half-applied transaction, or miss commits entirely, and it will
still open without complaint. `sqlite3.Connection.backup()` takes one
consistent image under the database's own locking.

That mattered here for a reason worse than theory: the review test launcher
copied the three files by hand, and the same launcher was one missing
redirect away from writing into the original.

WHAT IS PROTECTED. Everything a person decided, and nothing a machine
derived. Verdicts, tags, GOLDEN, KEEP_CONTEXT, deletions, workshop requests,
notes at all three scopes, and the production usage lifecycle -- which is
human decision-making even though it looks like state.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_DIR = REPO_ROOT / "creative_suite" / "database"
EDITORIAL_DB = DB_DIR / "editorial.db"
SNAPSHOT_DIR = REPO_ROOT / "output" / "human_snapshots"

# Every table holding a human decision, and the column that identifies what
# the decision was about. `production_usage` is here because SHORTLISTED /
# ASSIGNED / USED is the director deciding what the film does with a moment,
# and a rebuild that detached it would lose real editorial work.
PROTECTED = (
    ("human_reviews", "item_id"),
    ("human_review_log", "item_id"),
    ("review_tags", "occurrence_id"),
    ("dismissed_occurrences", "occurrence_id"),
    ("reconstruction_requests", "occurrence_id"),
    ("round_annotations", "round_key"),
    ("scene_event_notes", "event_id"),
    ("production_usage", None),          # key column discovered at runtime
)


def _now_tag() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _tables(c: sqlite3.Connection) -> set[str]:
    return {r[0] for r in c.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}


def snapshot(src: Path = EDITORIAL_DB, out_dir: Path = SNAPSHOT_DIR
             ) -> dict[str, Any]:
    """One consistent image of the editorial database, plus a manifest."""
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = _now_tag()
    dest = out_dir / f"editorial-{tag}.db"

    source = sqlite3.connect(f"file:{src}?mode=ro", uri=True, timeout=60)
    try:
        target = sqlite3.connect(dest)
        try:
            source.backup(target)        # the whole point of this module
        finally:
            target.close()
    finally:
        source.close()

    manifest = {"taken_at": datetime.now(timezone.utc).isoformat(
        timespec="seconds"), "source": str(src), "snapshot": str(dest),
        "tables": {}}
    with sqlite3.connect(f"file:{dest}?mode=ro", uri=True) as c:
        c.row_factory = sqlite3.Row
        have = _tables(c)
        for name, _key in PROTECTED:
            if name not in have:
                manifest["tables"][name] = {"rows": 0, "absent": True}
                continue
            rows = [dict(r) for r in c.execute(f"SELECT * FROM {name}")]
            manifest["tables"][name] = {"rows": len(rows), "records": rows}
    mpath = out_dir / f"editorial-{tag}.manifest.json"
    mpath.write_text(json.dumps(manifest, indent=1, default=str),
                     encoding="utf-8")
    manifest["manifest_path"] = str(mpath)
    return manifest


def summarise(manifest: dict[str, Any]) -> dict[str, Any]:
    """The counts a human would check, without the row bodies."""
    return {t: d.get("rows", 0) for t, d in manifest["tables"].items()}


def latest(out_dir: Path = SNAPSHOT_DIR) -> Path | None:
    if not out_dir.exists():
        return None
    snaps = sorted(out_dir.glob("editorial-*.manifest.json"))
    return snaps[-1] if snaps else None


def reconcile(manifest_path: Path | None = None,
              live: Path = EDITORIAL_DB) -> dict[str, Any]:
    """Compare the live database against a snapshot, row by row.

    NEWER USER WORK IS NOT A DISCREPANCY. If the reviewer judged something
    while a repair was running, that row is ADDED, not missing -- and
    overwriting it with the snapshot would destroy exactly what the snapshot
    exists to protect. Only removals and changes are failures.
    """
    mpath = manifest_path or latest()
    if mpath is None:
        return {"ok": False, "reason": "no snapshot to reconcile against"}
    manifest = json.loads(Path(mpath).read_text(encoding="utf-8"))

    out: dict[str, Any] = {"snapshot": str(mpath), "tables": {}, "ok": True}
    with sqlite3.connect(f"file:{live}?mode=ro", uri=True) as c:
        c.row_factory = sqlite3.Row
        have = _tables(c)
        for name, _key in PROTECTED:
            before = manifest["tables"].get(name, {})
            if name not in have:
                if before.get("rows"):
                    out["tables"][name] = {"status": "TABLE_GONE"}
                    out["ok"] = False
                continue
            now = [dict(r) for r in c.execute(f"SELECT * FROM {name}")]
            b_rows = before.get("records", [])
            b_set = {json.dumps(r, sort_keys=True, default=str)
                     for r in b_rows}
            n_set = {json.dumps(r, sort_keys=True, default=str) for r in now}
            lost = b_set - n_set
            added = n_set - b_set
            out["tables"][name] = {
                "before": len(b_set), "now": len(n_set),
                "lost": len(lost), "added": len(added),
                "status": "EXACT" if not lost else "LOST_ROWS",
                "lost_rows": [json.loads(x) for x in sorted(lost)][:10],
            }
            if lost:
                out["ok"] = False
    return out
