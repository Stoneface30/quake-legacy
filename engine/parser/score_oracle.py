"""Independent kill oracle from `scores` servercommands.

Answers section 7 of the 2026-08-29 brief. `kills == obit71` only proves our
FILTER keeps everything our DETECTOR finds -- it measures precision, not recall.
This module supplies an independent signal: the server's own scoreboard.

Method: track each client's score across every `scores` update. A positive
delta is evidence of a kill event the server counted. Compare those against the
obituary entities we decode.

    score-implied increments  vs  matched obit71  vs  UNMATCHED

If a demo shows dozens of score increments and 0-3 obituary entities, our
extraction is objectively incomplete -- and the unmatched timestamps become the
probes for section 9 (inspect every network change at a known kill time).

CAUTION built in: in Clan Arena `score` is not necessarily a frag counter. The
report prints the raw per-client field vector so the mapping can be judged
rather than assumed, and never claims attacker/victim from a delta alone.

    python engine/parser/score_oracle.py <demo> [--window 3000]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import demo_parse as D  # noqa: E402
import frag_classify as fc  # noqa: E402


def collect_scoreboards(path: Path) -> tuple[list[dict], list[str]]:
    """Every `scores` update as {time, rows:[[int,...]]}, plus raw samples."""
    p = D.DM73Parser(path)
    boards: list[dict] = []
    samples: list[str] = []

    def cap(s):
        try:
            s.readlong()
            raw = s.readstring()
        except Exception:
            return
        if not raw.startswith("scores "):
            return
        if len(samples) < 3:
            samples.append(raw[:240])
        tok = raw.split()[1:]
        try:
            n = int(tok[0])
            rest = tok[3:]
        except (ValueError, IndexError):
            return
        if n <= 0 or not rest or len(rest) % n:
            return
        w = len(rest) // n
        rows = []
        for i in range(n):
            try:
                rows.append([int(x) for x in rest[i * w:(i + 1) * w]])
            except ValueError:
                return
        boards.append({"time": p._last_server_time, "rows": rows, "width": w})

    p._parse_servercommand = cap
    p.parse()
    return boards, samples


def score_deltas(boards: list[dict], field: int = 1) -> list[dict]:
    """Positive changes in the chosen per-client field, in time order."""
    last: dict[int, int] = {}
    out: list[dict] = []
    for b in boards:
        for row in b["rows"]:
            if len(row) <= field:
                continue
            cid, val = row[0], row[field]
            prev = last.get(cid)
            if prev is not None and val > prev:
                out.append({"time": b["time"], "client": cid,
                            "old": prev, "new": val, "delta": val - prev})
            last[cid] = val
    return out


def analyse(path: Path, window_ms: int, field: int) -> dict:
    boards, samples = collect_scoreboards(path)
    parsed = D.DM73Parser(path).parse()
    obits = [e for e in parsed.get("events", []) if e.get("type") == "obituary"]
    obit_times = sorted(int(e.get("server_time_ms") or 0) for e in obits)

    deltas = score_deltas(boards, field)
    matched, unmatched = [], []
    for d in deltas:
        near = min((abs(t - d["time"]) for t in obit_times), default=None)
        d["nearest_obit_ms"] = near
        (matched if near is not None and near <= window_ms
         else unmatched).append(d)

    return {
        "boards": len(boards),
        "width": boards[0]["width"] if boards else 0,
        "samples": samples,
        "deltas": deltas,
        "matched": matched,
        "unmatched": unmatched,
        "raw_obit": len(obits),
        "filtered": len(fc.classify(parsed)),
        "obit_times": obit_times,
        "rows_sample": boards[0]["rows"][:3] if boards else [],
    }


def report(path: Path, window_ms: int, field: int, show: int) -> None:
    r = analyse(path, window_ms, field)
    print(f"\n{'=' * 78}\n{path.name}\n{'=' * 78}")
    print(f"  scores updates           : {r['boards']}  "
          f"(per-client field width {r['width']})")
    if r["rows_sample"]:
        print(f"  first rows (judge the mapping, do not assume it):")
        for row in r["rows_sample"]:
            print(f"      {row}")
    print(f"  raw obit71 detected      : {r['raw_obit']}")
    print(f"  filtered obituaries      : {r['filtered']}")
    print(f"  score increments (fld {field}) : {len(r['deltas'])}")
    print(f"    matched to an obituary : {len(r['matched'])}  "
          f"(within {window_ms} ms)")
    print(f"    UNMATCHED              : {len(r['unmatched'])}  "
          f"<-- kills with no obituary entity")

    if r["deltas"]:
        recall = len(r["matched"]) / len(r["deltas"]) * 100
        print(f"  implied detector recall  : {recall:.0f}%")

    if r["unmatched"]:
        print(f"\n  first {min(show, len(r['unmatched']))} unmatched increments "
              f"(probes for snapshot inspection):")
        print(f"  {'time':>10} {'clock':>8} {'client':>7} {'old':>5} "
              f"{'new':>5} {'d':>3} {'nearest obit':>13}")
        for d in r["unmatched"][:show]:
            t = d["time"]
            near = d["nearest_obit_ms"]
            print(f"  {t:>10} {t // 60000:>4}:{(t // 1000) % 60:02d} "
                  f"{d['client']:>7} {d['old']:>5} {d['new']:>5} "
                  f"{d['delta']:>3} "
                  f"{'-' if near is None else str(near) + ' ms':>13}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("demos", nargs="+")
    ap.add_argument("--window", type=int, default=3000)
    ap.add_argument("--field", type=int, default=1,
                    help="per-client row index to track (1 = score)")
    ap.add_argument("--show", type=int, default=12)
    a = ap.parse_args()
    for d in a.demos:
        report(Path(d), a.window, a.field, a.show)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
