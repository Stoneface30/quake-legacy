"""CLUTCH_ROUND_WIN extraction — last player standing who wins the round.

A clutch is the most watchable thing in Clan Arena: our player alone against
live opponents, and the round still ends in our favour. This finds them from
the obituary stream.

Two data realities shape the implementation.

ROUND BOUNDARIES ARE OFF BY ONE KILL. The parser's round counter increments
before the round-ending obituary is recorded, so every round's final kill lands
in the NEXT bucket. Measured on CA-<player>-asylum-2012_11_11: kills per round
alternate 4,1,3,1,5,1,4,1... -- the odd buckets are real rounds and each even
bucket holds exactly the trailing kill of the round before it. Buckets are
merged back before any clutch logic runs; without that, every round would look
like it ended with our player dead or alone for one kill.

IDENTITY COMES FROM THE CLIENT SLOT. Name text is matched only as a fallback,
because names carry colour codes (`^6T^3R^64^3S^6H^7`) and change between
demos. `frag_classify.demo_taker` recovers the recorder, which is the player
whose demo this is.

    python engine/parser/clutch_extract.py --db creative_suite/database/frags_rebuilt.db
    python engine/parser/clutch_extract.py --demos demos/CA-*.dm_73
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import re
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))

ALIASES = ("tr4sh", "trash", "stoneface")
_COLOR = re.compile(r"\^\d")

# A bucket holding this many kills or fewer, immediately after a populated
# bucket, is the previous round's trailing kill rather than a round of its own.
TRAILING_BUCKET_MAX = 1


def strip_colors(s) -> str:
    return _COLOR.sub("", s or "").strip()


def is_alias(name) -> bool:
    n = strip_colors(name).lower()
    return any(a in n for a in ALIASES)


def merged_rounds(obits):
    """Group obituaries into real rounds, repairing the off-by-one counter."""
    buckets = defaultdict(list)
    for e in obits:
        buckets[e.get("round") or 0].append(e)
    keys = sorted(buckets)

    rounds = []
    for k in keys:
        rows = sorted(buckets[k], key=lambda e: e.get("server_time_ms") or 0)
        if (rounds and len(rows) <= TRAILING_BUCKET_MAX
                and len(rounds[-1]) > TRAILING_BUCKET_MAX):
            rounds[-1].extend(rows)          # trailing kill of the round before
        else:
            rounds.append(rows)
    for r in rounds:
        r.sort(key=lambda e: e.get("server_time_ms") or 0)
    return [r for r in rounds if r]


def teams_of(players):
    """client -> team, ignoring spectators (they never contribute to a round)."""
    out = {}
    if isinstance(players, dict):
        for cid, info in players.items():
            t = (info or {}).get("team", "")
            if t and t.upper() != "SPECTATOR":
                out[int(cid)] = t.upper()
    return out


def analyse_round(rows, teams, me):
    """Return a clutch record for this round, or None.

    A clutch starts at the moment our player is the last one alive on their
    team while at least one opponent is still up, and counts only if the round
    then ends with our side winning.
    """
    if me is None or me not in teams:
        return None
    my_team = teams[me]
    mates = {c for c, t in teams.items() if t == my_team}
    foes = {c for c, t in teams.items() if t != my_team}
    if not mates or not foes:
        return None

    alive_mates = set(mates)
    alive_foes = set(foes)
    start_ms = None
    foes_at_start = 0
    kills, weapons = [], []

    for e in rows:
        v = e.get("victim_client")
        k = e.get("killer_client")
        t = e.get("server_time_ms") or 0

        if start_ms is not None and k == me and v in alive_foes:
            kills.append({"t": t, "victim": v,
                          "victim_name": strip_colors(e.get("victim_name")),
                          "weapon": e.get("weapon_name")})
            weapons.append(e.get("weapon_name"))

        alive_mates.discard(v)
        alive_foes.discard(v)

        if (start_ms is None and me in alive_mates
                and alive_mates == {me} and alive_foes):
            start_ms = t
            foes_at_start = len(alive_foes)

    if start_ms is None:
        return None
    if me not in alive_mates:                 # we died -- not a clutch win
        return None
    if alive_foes:                            # opponents still up at round end
        return None

    end_ms = rows[-1].get("server_time_ms") or start_ms
    return {
        "clutch_start_ms": start_ms,
        "clutch_end_ms": end_ms,
        "duration_ms": max(0, end_ms - start_ms),
        "enemies_alive_at_start": foes_at_start,
        "kills_during_clutch": len(kills),
        "weapons": ",".join(w for w in weapons if w),
        "kill_detail": kills,
        "outcome": "WIN",
    }


def score(rec):
    """Rank what actually watches well: outnumbered, fast, varied."""
    s = 0.0
    s += {1: 2.0, 2: 6.0, 3: 11.0}.get(rec["enemies_alive_at_start"],
                                       14.0 if rec["enemies_alive_at_start"] >= 4
                                       else 0.0)
    s += 2.0 * rec["kills_during_clutch"]
    if rec["duration_ms"] and rec["kills_during_clutch"] >= 2:
        per = rec["duration_ms"] / rec["kills_during_clutch"]
        if per < 3000:
            s += 4.0
        elif per < 6000:
            s += 2.0
    if len(set(w for w in rec["weapons"].split(",") if w)) >= 3:
        s += 2.0
    return round(s, 2)


def from_demo(path: Path):
    import demo_parse as D
    import frag_classify as fc
    res = D.DM73Parser(path).parse()
    obits = [e for e in res.get("events", []) if e.get("type") == "obituary"]
    if not obits:
        return []
    teams = teams_of(res.get("players"))
    me = fc.demo_taker(res)
    if me is None:
        players = res.get("players") or {}
        for cid, info in (players.items() if isinstance(players, dict) else []):
            if is_alias((info or {}).get("name")):
                me = int(cid)
                break
    if me is None:
        return []

    players = res.get("players") or {}
    my_name = strip_colors((players.get(me) or {}).get("name")
                           if isinstance(players, dict) else "")

    out = []
    for i, rows in enumerate(merged_rounds(obits), 1):
        rec = analyse_round(rows, teams, me)
        if not rec:
            continue
        rec.update({"demo": path.name, "round": i, "player_client": me,
                    "player_name": my_name,
                    "map": res.get("map"), "gametype": res.get("gametype")})
        rec["rank_score"] = score(rec)
        out.append(rec)
    return out


def _worker(path_str):
    """Scan one demo in a separate process. Errors are returned, not raised."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import demo_parse as D
    D._get_huff()
    try:
        return {"ok": True, "rows": from_demo(Path(path_str))}
    except Exception as exc:                         # noqa: BLE001
        return {"ok": False, "demo": Path(path_str).name,
                "error": "{}: {}".format(type(exc).__name__, exc)[:200]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--demos", nargs="*", default=None)
    ap.add_argument("--glob", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out-dir", default=str(REPO / "output"))
    ap.add_argument("--workers", type=int,
                    default=max(2, (os.cpu_count() or 4) // 2))
    a = ap.parse_args()

    import demo_parse as D
    D._get_huff()

    paths = []
    if a.demos:
        for d in a.demos:
            paths += [Path(x) for x in glob.glob(d)]
    elif a.glob:
        paths = [Path(x) for x in glob.glob(a.glob)]
    else:
        paths = sorted((REPO / "demos").glob("*.dm_73"))
    if a.limit:
        paths = paths[:a.limit]

    print("[clutch] scanning {} demo(s) with {} workers".format(
        len(paths), a.workers), flush=True)
    all_rows = []
    failed = 0
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(_worker, str(q)): q for q in paths}
        for i, fut in enumerate(as_completed(futs), 1):
            try:
                res = fut.result()
            except Exception as exc:                 # noqa: BLE001
                failed += 1
                print("  [clutch] worker died: {}".format(exc), flush=True)
                continue
            if res.get("ok"):
                all_rows += res["rows"]
            else:
                failed += 1
            if i % 250 == 0:
                print("  [clutch] {}/{}  {} found".format(i, len(paths),
                                                          len(all_rows)),
                      flush=True)

    all_rows.sort(key=lambda r: -r["rank_score"])
    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "clutch_round_wins.json").write_text(
        json.dumps({"total": len(all_rows), "demos_scanned": len(paths),
                    "demos_failed": failed, "items": all_rows}, indent=2),
        encoding="utf-8")
    cols = ["demo", "round", "map", "player_name", "player_client",
            "enemies_alive_at_start", "kills_during_clutch", "weapons",
            "clutch_start_ms", "clutch_end_ms", "duration_ms", "outcome",
            "rank_score"]
    with (out_dir / "clutch_round_wins.csv").open("w", newline="",
                                                  encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in all_rows:
            w.writerow(r)

    print("")
    print("[clutch] {} CLUTCH_ROUND_WIN across {} demo(s), {} failed".format(
        len(all_rows), len(paths), failed))
    print("  {}".format(out_dir / "clutch_round_wins.csv"))
    print("  {}".format(out_dir / "clutch_round_wins.json"))
    if all_rows:
        print("")
        print("  top 20:")
        print("    {:>6} {:34} {:>5} {:>4} {:>6} {:>7}  weapons".format(
            "score", "demo", "round", "1vN", "kills", "dur s"))
        for r in all_rows[:20]:
            print("    {:>6.1f} {:34} {:>5} {:>4} {:>6} {:>7.1f}  {}".format(
                r["rank_score"], r["demo"][:34], r["round"],
                r["enemies_alive_at_start"], r["kills_during_clutch"],
                r["duration_ms"] / 1000.0, r["weapons"][:40]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
