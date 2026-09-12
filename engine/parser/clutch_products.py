"""The clutch products the recognition taxonomy joins: a tracked producer.

`reclassify_v2`, `capture_windows`, `promotion_batch` and `review_package` read
`output/clutch_recorder.csv` (joined on `canonical_demo_hash`). No tracked code
wrote it: it was an "overnight artifact" (plans/2026-08-30-demo-v2-mining-
phase1). The corpus parser-v2 rebuild has to REGENERATE it from v2 data --
borrowing the v1 file would put obituary-derived v1 data into v2.

The definition was recovered and proven against the v1 files (2026-09-12):
  clutch_round_wins    `clutch_extract` over the corpus demos
  clutch_all_players   round wins joined to the demo's content hash, deduped
                       by (canonical_demo_hash, round, clutch_start_ms)
                       -- reproduces v1 1,794 / 1,794 exactly
  clutch_recorder      all_players filtered by the recorder's ALIAS NAME
                       (`clutch_extract.is_alias`) -- reproduces v1 1,746 /
                       1,746 exactly; the protocol-slot filter does NOT (15/48 off)

"RECORDER" IN clutch_recorder MEANS ALIAS-SELECTED, NOT THE RECORDER'S CLIENT
SLOT. Reproducing v1 proves how the old corpus was made, not that the alias
rule is the best truth, so both are kept: every clutch_all_players row carries
`is_recorder_alias` and `is_recorder_slot`, every clutch_recorder row carries
`selection_method=recorder_alias`, and clutch_selection.json counts the rows
the two methods disagree on (no names) -- the disagreements are data.

Everything is written under the DATA root's output/ (gitignored: names).

    python engine/parser/clutch_products.py [--workers 8]
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))

from engine.pantheon.store import data_root as _data_root  # noqa: E402

DATA = _data_root()
FRAGS_DB = DATA / "creative_suite" / "database" / "frags_rebuilt.db"
OUT_DIR = DATA / "output"

WIN_COLS = ["demo", "round", "map", "player_name", "player_client",
            "enemies_alive_at_start", "kills_during_clutch", "weapons",
            "clutch_start_ms", "clutch_end_ms", "duration_ms", "outcome",
            "rank_score"]
JOINED_COLS = WIN_COLS[:1] + ["canonical_demo_hash"] + WIN_COLS[1:]
ALL_COLS = JOINED_COLS + ["is_recorder_alias", "is_recorder_slot"]
RECORDER_COLS = JOINED_COLS + ["selection_method"]
SELECTION_METHOD = "recorder_alias"


def derive(wins: list[dict], name_to_hash: dict[str, str],
           recorder_of: dict[str, int | None] | None = None
           ) -> tuple[list[dict], list[dict], dict]:
    """(all_players, recorder, selection stats) from clutch round wins.
    Pure; unit-tested. `recorder_of` maps canonical hash -> recorder slot."""
    import clutch_extract as ce
    from engine.parser.capture_windows import dedupe_clutches
    recorder_of = recorder_of or {}
    joined = [dict(w, canonical_demo_hash=name_to_hash[w["demo"]])
              for w in wins if w["demo"] in name_to_hash]
    all_players = dedupe_clutches(joined)
    for r in all_players:
        slot = recorder_of.get(r["canonical_demo_hash"])
        r["is_recorder_alias"] = int(ce.is_alias(r.get("player_name")))
        r["is_recorder_slot"] = int(slot is not None and str(slot) == str(r["player_client"]))
    recorder = [dict(r, selection_method=SELECTION_METHOD)
                for r in all_players if r["is_recorder_alias"]]
    key = lambda r: [r["canonical_demo_hash"], int(r["round"]), int(r["player_client"])]
    stats = {
        "selection_method": SELECTION_METHOD,
        "all_players": len(all_players),
        "alias_and_slot": sum(1 for r in all_players
                              if r["is_recorder_alias"] and r["is_recorder_slot"]),
        "alias_only": [key(r) for r in all_players
                       if r["is_recorder_alias"] and not r["is_recorder_slot"]],
        "slot_only": [key(r) for r in all_players
                      if r["is_recorder_slot"] and not r["is_recorder_alias"]],
    }
    return all_players, recorder, stats


def _write(path: Path, rows: list[dict], cols: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    import clutch_extract as ce
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()

    con = sqlite3.connect(f"file:{FRAGS_DB.as_posix()}?mode=ro", uri=True)
    demos = con.execute("select name, coalesce(duplicate_of, content_hash), path, "
                        "recorder_client from demos where parse_error is null").fetchall()
    con.close()
    name_to_hash = {n: h for n, h, _p, _r in demos}
    recorder_of = {h: r for _n, h, _p, r in demos}
    paths = [DATA / "demos" / n for n, _h, _p, _r in demos]
    paths = [p for p in paths if p.is_file()]
    print(f"[clutch] {len(paths)} demos, {a.workers} workers", flush=True)

    wins, failed = [], 0
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for fut in as_completed([ex.submit(ce._worker, str(p)) for p in paths]):
            res = fut.result()
            if res.get("ok"):
                wins += res["rows"]
            else:
                failed += 1
                print(f"  [clutch] failed: {res.get('error')}", flush=True)
    wins.sort(key=lambda r: -r["rank_score"])
    all_players, recorder, stats = derive(wins, name_to_hash, recorder_of)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "clutch_round_wins.json").write_text(json.dumps(
        {"total": len(wins), "demos_scanned": len(paths), "demos_failed": failed,
         "items": wins}, indent=2), encoding="utf-8")
    _write(OUT_DIR / "clutch_round_wins.csv", wins, WIN_COLS)
    _write(OUT_DIR / "clutch_all_players.csv", all_players, ALL_COLS)
    _write(OUT_DIR / "clutch_recorder.csv", recorder, RECORDER_COLS)
    (OUT_DIR / "clutch_selection.json").write_text(json.dumps(stats, indent=1),
                                                    encoding="utf-8")
    print(f"[clutch] wins {len(wins)}  all_players {len(all_players)}  "
          f"recorder(alias) {len(recorder)}  alias&slot {stats['alias_and_slot']}  "
          f"alias-only {len(stats['alias_only'])}  slot-only {len(stats['slot_only'])}  "
          f"failed {failed}", flush=True)
    return 1 if failed and not wins else 0


if __name__ == "__main__":
    sys.exit(main())
