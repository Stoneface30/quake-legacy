"""Command line for the THE_PANTHEON export seam.

Three ways to choose what crosses, and no way to choose everything:

    python -m creative_suite.engine.export_cli status
    python -m creative_suite.engine.export_cli ids ql_abc... ql_def...
    python -m creative_suite.engine.export_cli query --actor NaikoMarie --limit 10
    python -m creative_suite.engine.export_cli query --mine --weapon ROCKET --limit 5

`--limit` is capped by MAX_BATCH and an oversized ask is refused rather than
trimmed. There is deliberately no `--all`: the metadata for every attributed
kill is queryable here, and that is a different thing from having exported
the media for it.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from creative_suite.engine import public_clip_export as px   # noqa: E402
from creative_suite.engine import review_corpus as rc        # noqa: E402


def _select(args) -> list[px.ExportCandidate]:
    where = ["killer_class = 'PLAYER'"]
    params: list[object] = []
    if args.mine:
        where.append("is_recorder_killer = 1")
    if args.clan:
        norms = sorted(rc.roster_norms())
        where.append(f"killer_name_norm IN ({','.join('?' * len(norms))})")
        params.extend(norms)
    if args.actor:
        where.append("killer_name_norm = ?")
        params.append(args.actor.strip().lower())
    if args.weapon:
        where.append("mod_name = ?")
        params.append(args.weapon.upper())
    if args.map:
        where.append("LOWER(map) = ?")
        params.append(args.map.lower())
    if args.telefrag:
        where.append("death_cause = 'TELEFRAG'")
    cands = px.candidates_from_kill_events(
        where=" AND ".join(f"k.{w}" if not w.startswith("LOWER") else w
                           for w in where),
        params=params, limit=args.limit)
    return px.attach_machine_scores(cands)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="export_cli")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="what is already in the exchange directory")

    q = sub.add_parser("query", help="select by attribute and export")
    q.add_argument("--mine", action="store_true", help="the recorder's own kills")
    q.add_argument("--clan", action="store_true", help="anyone on the pTn roster")
    q.add_argument("--actor", help="one normalized actor name")
    q.add_argument("--weapon", help="MOD name, e.g. ROCKET or RAILGUN")
    q.add_argument("--map")
    q.add_argument("--telefrag", action="store_true")
    q.add_argument("--limit", type=int, default=10)
    q.add_argument("--note", help="a source note; THE_PANTHEON reveals it "
                                  "only after voting")
    q.add_argument("--dry-run", action="store_true",
                   help="print what would be exported and capture nothing")

    i = sub.add_parser("ids", help="export specific external_source_ids")
    i.add_argument("ids", nargs="+")
    i.add_argument("--note")
    i.add_argument("--dry-run", action="store_true")

    a = ap.parse_args(argv)

    if a.cmd == "status":
        print(json.dumps(px.export_summary(), indent=2))
        return 0

    if a.cmd == "ids":
        # Resolve public ids back to rows. The mapping lives here and only
        # here -- that is the point of the id being a digest.
        every = px.candidates_from_kill_events(limit=1_000_000)
        want = set(a.ids)
        cands = px.attach_machine_scores(
            [c for c in every if c.external_source_id in want])
        missing = want - {c.external_source_id for c in cands}
        if missing:
            print(f"unknown ids: {sorted(missing)}", file=sys.stderr)
    else:
        cands = _select(a)

    if not cands:
        print("nothing matched", file=sys.stderr)
        return 1

    if a.dry_run:
        for c in cands:
            print(f"{c.external_source_id}  {c.map_name or '?':16s} "
                  f"{c.weapon or '?':14s} actor={c.actor_display_name or '?':16s} "
                  f"pov={'own' if c.is_actor_pov else 'observed'} "
                  f"score={c.machine_score if c.machine_score is not None else '-'}")
        print(f"\n{len(cands)} candidates, nothing captured (--dry-run)")
        return 0

    try:
        out = px.export(cands, note=getattr(a, "note", None))
    except px.ExportRefused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=2))
    return 0 if out["failed"] == 0 else 3


if __name__ == "__main__":
    raise SystemExit(main())
