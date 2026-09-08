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
        reject_if_live(db)          # BEFORE anything opens it
    else:
        tmp = Path(tempfile.mkdtemp(prefix="review-test-"))
        db = tmp / "editorial.db"
        if LIVE_DB.exists():
            backup_copy(LIVE_DB, db)

    from creative_suite.engine import creative_annotation as ca
    from creative_suite.engine import identity as idn
    from creative_suite.engine import production_usage as pu
    from creative_suite.engine import reconstruction_queue as rq
    from creative_suite.engine import review_corpus as rc
    from creative_suite.engine import review_proxy as rp
    from creative_suite.engine import review_tags as rt

    # EVERY module that can write a human row. This list being incomplete is
    # not a theoretical risk: the tag and workshop modules were added after
    # this launcher and were NOT redirected, so an automated mobile run wrote
    # three tags and a reconstruction request into the user's live database,
    # stamped HUMAN_USER. They were removed by hand. `assert_isolated` below
    # exists so the next addition fails loudly instead of quietly.
    ca.EDITORIAL_DB = db
    rc.EDITORIAL_DB = db
    rp.EDITORIAL_DB_PATH = db
    rt.EDITORIAL_DB = db
    rq.EDITORIAL_DB = db
    # Usage lifecycle and identity decisions are human production state too.
    # A rebuild is required to preserve them, so a test must not write them.
    pu.EDITORIAL_DB = db
    idn.EDITORIAL_DB = db

    real_record = rc.record

    def test_only_record(item_id, item_type, source_id, role, note=None,
                         provenance=rc.HUMAN_USER):
        # ONLY THE USER WRITES HUMAN CREATIVE TRUTH. This instance cannot,
        # by construction, whatever the router asks for.
        return real_record(item_id, item_type, source_id, role, note,
                           provenance=rc.TEST)

    rc.record = test_only_record

    _real_tag = rt.set_tag

    def test_only_tag(occurrence_id, tag, on=True, item_id="",
                      provenance=rt.HUMAN_USER):
        return _real_tag(occurrence_id, tag, on, item_id, rt.TEST)

    rt.set_tag = test_only_tag

    _real_request = rq.request

    def test_only_request(occurrence_id, item_id="", reason=rq.UNSPECIFIED,
                          note="", provenance=rq.HUMAN_USER):
        return _real_request(occurrence_id, item_id, reason, note, rq.TEST)

    rq.request = test_only_request

    def test_only_event_note(event_id, annotation, provenance=ca.HUMAN_USER):
        return _real_event_note(event_id, annotation, ca.TEST)

    _real_event_note = ca.set_event_annotation
    ca.set_event_annotation = test_only_event_note

    def test_only_round_note(content_hash, round_no, annotation,
                             provenance=ca.HUMAN_USER):
        return _real_round_note(content_hash, round_no, annotation, ca.TEST)

    _real_round_note = ca.set_round_annotation
    ca.set_round_annotation = test_only_round_note

    assert_isolated(db)

    import uvicorn
    from creative_suite.app import create_app

    print(f"TEST INSTANCE db={db} port={args.port}", flush=True)
    uvicorn.run(create_app(), host="127.0.0.1", port=args.port,
                log_level="warning")
    return 0


def _resolved(p: Path) -> str:
    """One canonical spelling of a path, for comparison.

    Windows makes this necessary rather than pedantic: `G:\QUAKE_LEGACY`,
    `g:\quake_legacy`, a short 8.3 name and a junction can all be the same
    file, and a string comparison says they are different.
    """
    try:
        r = p.resolve(strict=False)
    except OSError:
        r = p.absolute()
    return str(r).replace("/", "\\").casefold().rstrip("\\")


def reject_if_live(db: Path) -> None:
    """Refuse a database that is, or resolves to, the live one.

    `--db` used to be taken on trust: the launcher considered itself isolated
    because every module pointed at the SAME file, which is equally true when
    that file is the user's real editorial database. Isolation means "not
    live", not "consistent".
    """
    target = _resolved(db)
    forbidden = {_resolved(LIVE_DB)}
    # The side files are the same database by another name.
    for suffix in ("-wal", "-shm", "-journal"):
        forbidden.add(_resolved(LIVE_DB.with_name(LIVE_DB.name + suffix)))
    # And so is anything sitting in the live database directory.
    live_dir = _resolved(LIVE_DB.parent)
    if target in forbidden or _resolved(db.parent) == live_dir:
        raise SystemExit(
            f"REFUSING TO START: {db} is the live review database (or lives "
            f"beside it). A test instance that can reach it is a test "
            f"instance that can destroy the user's reviews.")


def backup_copy(src: Path, dest: Path) -> None:
    """A CONSISTENT copy, via SQLite's own backup API.

    Copying `.db`, `-wal` and `-shm` as three separate files is three reads
    at three different instants. In WAL mode recent commits live in `-wal`
    until a checkpoint, so the result can hold a half-applied transaction or
    miss commits outright -- and it opens without complaint either way.
    """
    import sqlite3
    source = sqlite3.connect(f"file:{src}?mode=ro", uri=True, timeout=60)
    try:
        target = sqlite3.connect(dest)
        try:
            source.backup(target)
        finally:
            target.close()
    finally:
        source.close()


LIVE_MODULE_ATTRS = (
    ("creative_suite.engine.creative_annotation", "EDITORIAL_DB"),
    ("creative_suite.engine.identity", "EDITORIAL_DB"),
    ("creative_suite.engine.production_usage", "EDITORIAL_DB"),
    ("creative_suite.engine.reconstruction_queue", "EDITORIAL_DB"),
    ("creative_suite.engine.review_corpus", "EDITORIAL_DB"),
    ("creative_suite.engine.review_proxy", "EDITORIAL_DB_PATH"),
    ("creative_suite.engine.review_tags", "EDITORIAL_DB"),
)


def assert_isolated(db: Path) -> None:
    """Refuse to serve if anything still points at the live database.

    A test instance that can reach the user's editorial database is a test
    instance that can destroy their reviews. Failing to start is a far
    smaller problem than discovering afterwards which rows were written.
    """
    import importlib
    reject_if_live(db)              # consistent AND not live
    wrong = []
    for name, attr in LIVE_MODULE_ATTRS:
        mod = importlib.import_module(name)
        got = Path(str(getattr(mod, attr)))
        if _resolved(got) != _resolved(db):
            wrong.append(f"{name}.{attr} -> {got}")
    if wrong:
        raise SystemExit("NOT ISOLATED, refusing to start: "
                         + "; ".join(wrong))


if __name__ == "__main__":
    raise SystemExit(main())
