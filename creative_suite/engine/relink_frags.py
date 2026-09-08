"""Re-attach review clips to frags after a re-derivation renumbered them.

`recognized_frags.id` is an auto-assigned rowid and the recognition scan
deletes and reinserts a demo's rows, so every rescanned demo gets NEW frag
ids. Review proxies are keyed on `frag_id`. That combination does not orphan a
clip -- it silently points it at a DIFFERENT frag, which is worse, because the
review looks fine and is wrong.

The defence is an identity that survives renumbering. A kill is identified by
its demo (content hash), the server time it happened, and who died; none of
those change when the row is rewritten. `frag_identity_map.json` is written
BEFORE a rescan and consumed here after it.

This only ever rewrites `review_proxies.frag_id`. It does not touch
HUMAN_USER review state, and it refuses to guess: a frag whose identity no
longer resolves is reported, not reassigned to something nearby.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REC_DB = REPO_ROOT / "creative_suite/database/frag_recognition.db"
ED_DB = REPO_ROOT / "creative_suite/database/editorial.db"
MAP = REPO_ROOT / "creative_suite/database/frag_identity_map.json"

# A kill can shift by a snapshot between derivations; more than this and it is
# a different moment, not the same one renumbered.
TIME_TOLERANCE_MS = 400


def load_map(path=None) -> list[dict]:
    with open(path or MAP, encoding="utf-8") as f:
        return json.load(f)["frags"]


def resolve(rec, entry) -> int | None:
    """The current frag id for a frozen identity, or None if it is gone."""
    row = rec.execute(
        "SELECT id FROM recognized_frags WHERE content_hash=? AND "
        "ABS(server_time_ms-?)<=? AND victim_client IS ? "
        "ORDER BY ABS(server_time_ms-?) LIMIT 1",
        (entry["content_hash"], entry["server_time_ms"], TIME_TOLERANCE_MS,
         entry["victim_client"], entry["server_time_ms"])).fetchone()
    if row:
        return row[0]
    # Victim may be recorded differently after a taxonomy change; fall back to
    # demo + time alone, which is still specific to one kill.
    row = rec.execute(
        "SELECT id FROM recognized_frags WHERE content_hash=? AND "
        "ABS(server_time_ms-?)<=? ORDER BY ABS(server_time_ms-?) LIMIT 1",
        (entry["content_hash"], entry["server_time_ms"], TIME_TOLERANCE_MS,
         entry["server_time_ms"])).fetchone()
    return row[0] if row else None


def relink(dry_run=True, rec_db=None, ed_db=None, map_path=None):
    rec = sqlite3.connect("file:%s?mode=ro" % (rec_db or REC_DB), uri=True,
                          timeout=60)
    ed = sqlite3.connect(str(ed_db or ED_DB), timeout=60)

    entries = load_map(map_path)
    unchanged = moved = lost = 0
    changes, missing = [], []
    for e in entries:
        now = resolve(rec, e)
        if now is None:
            lost += 1
            missing.append(e)
            continue
        if now == e["frag_id"]:
            unchanged += 1
            continue
        moved += 1
        changes.append((e["frag_id"], now, e["mp4_path"]))

    if not dry_run:
        for old, new, path in changes:
            # Move only the proxy row that owns this clip file. Matching on
            # the path as well as the id stops a re-run from dragging along
            # some other proxy that happens to share the old id.
            ed.execute("UPDATE review_proxies SET frag_id=? WHERE frag_id=? "
                       "AND mp4_path=?", (new, old, path))
        ed.commit()
    ed.close()
    return {"total": len(entries), "unchanged": unchanged, "moved": moved,
            "lost": lost, "changes": changes, "missing": missing,
            "applied": not dry_run}


def verify(rec_db=None, ed_db=None, map_path=None) -> dict:
    """Check the DATABASE, not the map.

    `relink` compares the current frag against the id frozen in the map, so
    re-running it after a successful apply reports the same "renumbered"
    count forever -- the map is a record of what WAS, and never changes. That
    made a working fix look like it had not applied. This asks the only
    question that matters: does the proxy row holding this clip file now
    point at a frag that IS this kill?
    """
    rec = sqlite3.connect("file:%s?mode=ro" % (rec_db or REC_DB), uri=True,
                          timeout=60)
    ed = sqlite3.connect("file:%s?mode=ro" % (ed_db or ED_DB), uri=True,
                         timeout=60)
    ok = wrong = orphan = 0
    for e in load_map(map_path):
        row = ed.execute("SELECT frag_id FROM review_proxies WHERE mp4_path=? "
                         "LIMIT 1", (e["mp4_path"],)).fetchone()
        if not row:
            orphan += 1
            continue
        r = rec.execute("SELECT content_hash, server_time_ms FROM "
                        "recognized_frags WHERE id=?", (row[0],)).fetchone()
        same_demo = r and r[0] == e["content_hash"]
        close = r and abs(r[1] - e["server_time_ms"]) <= TIME_TOLERANCE_MS
        if same_demo and close:
            ok += 1
        else:
            wrong += 1
    return {"correct": ok, "wrong": wrong, "no_proxy_row": orphan}


if __name__ == "__main__":
    import sys
    dry = "--apply" not in sys.argv
    r = relink(dry_run=dry)
    print("%s: %d frags -- %d unchanged, %d renumbered, %d unresolvable"
          % ("DRY RUN" if dry else "APPLIED", r["total"], r["unchanged"],
             r["moved"], r["lost"]))
    for old, new, _p in r["changes"][:15]:
        print("   FRAG:%s -> FRAG:%s" % (old, new))
    for e in r["missing"][:10]:
        print("   LOST  %s t=%s (clip kept on disk)"
              % (e["content_hash"][:12], e["server_time_ms"]))
    v = verify()
    print("verified against the database: %d correct, %d wrong, %d no proxy row"
          % (v["correct"], v["wrong"], v["no_proxy_row"]))
