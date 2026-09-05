"""Run the REAL review service against an isolated copy of its database.

WHY THIS EXISTS. A browser test has to press the real buttons against the
real server, or it proves nothing about the phone. But the reviewer's
database holds the user's genuine HUMAN_USER verdicts, and an automated test
that can write there is an automated test that can destroy them.

So: same application, same routers, same review.html, same media files on
disk, same HTTP -- and a COPY of editorial.db, with `record` forced to TEST
provenance. Two independent protections, neither of which changes production
code:

  * every write lands in a throwaway file
  * every verdict it could still write is stamped TEST, never HUMAN_USER

Nothing is monkeypatched inside the app itself; only the module-level
database constants and one storage function, before the app is imported.

    python scripts/review_test_instance.py --port 8767
"""
from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

LIVE_DB = REPO_ROOT / "creative_suite" / "database" / "editorial.db"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8767)
    ap.add_argument("--db", default="", help="reuse an existing copy")
    args = ap.parse_args()

    if args.db:
        db = Path(args.db)
    else:
        tmp = Path(tempfile.mkdtemp(prefix="review-test-"))
        db = tmp / "editorial.db"
        if LIVE_DB.exists():
            # WAL and SHM too, or the copy can miss recent commits entirely
            # and the queue would look empty for reasons nothing explains.
            shutil.copy2(LIVE_DB, db)
            for suffix in ("-wal", "-shm"):
                side = LIVE_DB.with_name(LIVE_DB.name + suffix)
                if side.exists():
                    shutil.copy2(side, db.with_name(db.name + suffix))

    from creative_suite.engine import creative_annotation as ca
    from creative_suite.engine import review_corpus as rc
    from creative_suite.engine import review_proxy as rp

    ca.EDITORIAL_DB = db
    rc.EDITORIAL_DB = db
    rp.EDITORIAL_DB_PATH = db

    real_record = rc.record

    def test_only_record(item_id, item_type, source_id, role, note=None,
                         provenance=rc.HUMAN_USER):
        # ONLY THE USER WRITES HUMAN CREATIVE TRUTH. This instance cannot,
        # by construction, whatever the router asks for.
        return real_record(item_id, item_type, source_id, role, note,
                           provenance=rc.TEST)

    rc.record = test_only_record

    def test_only_event_note(event_id, annotation, provenance=ca.HUMAN_USER):
        return _real_event_note(event_id, annotation, ca.TEST)

    _real_event_note = ca.set_event_annotation
    ca.set_event_annotation = test_only_event_note

    def test_only_round_note(content_hash, round_no, annotation,
                             provenance=ca.HUMAN_USER):
        return _real_round_note(content_hash, round_no, annotation, ca.TEST)

    _real_round_note = ca.set_round_annotation
    ca.set_round_annotation = test_only_round_note

    import uvicorn
    from creative_suite.app import create_app

    print(f"TEST INSTANCE db={db} port={args.port}", flush=True)
    uvicorn.run(create_app(), host="127.0.0.1", port=args.port,
                log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
