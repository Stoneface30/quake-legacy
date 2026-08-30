"""Ranked frag seek-list for WolfcamQL capture -- PROVEN demos only.

Section 11 of the 2026-08-29 brief. Emits the capture manifest for demos whose
obituary extraction we trust, without waiting on the 2010-2011 protocol
question.

SCOPE, stated plainly: this is NOT the whole corpus. A demo qualifies only if
its obituary stream passes `looks_trustworthy()` -- enough obituaries to be a
real kill feed rather than the 0-3 stragglers the older builds yield. Every
output file is labelled accordingly.

Ranking rewards what actually cuts well: rapid multi-kills, consecutive frags,
rocket/rail work, late-round sequences, and several kills inside one capture
window.

    python engine/parser/seek_list.py --max-demos 40 --top 40
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

import demo_parse as D  # noqa: E402
import frag_classify as fc  # noqa: E402

# A demo with only a handful of obituaries is an old-build casualty, not a
# quiet match. Measured: trustworthy demos yield 60+, the broken ones 0-3.
MIN_OBITS_TRUSTED = 20

CHAIN_MS = 4000        # two frags this close read as one sequence
CAPTURE_MS = 12000     # a single wolfcam capture window


def looks_trustworthy(parsed: dict) -> tuple[bool, str]:
    obits = [e for e in parsed.get("events", []) if e.get("type") == "obituary"]
    n = len(obits)
    if n < MIN_OBITS_TRUSTED:
        return False, f"only {n} obituaries -- build not proven"
    return True, f"{n} obituaries"


def rank(frags: list, me: int | None) -> list[dict]:
    """Score each frag on how well it would cut."""
    out: list[dict] = []
    times = [f.time_ms for f in frags]

    for i, f in enumerate(frags):
        prev_gap = f.time_ms - times[i - 1] if i > 0 else None
        next_gap = times[i + 1] - f.time_ms if i + 1 < len(times) else None
        in_window = sum(1 for t in times
                        if 0 <= t - f.time_ms <= CAPTURE_MS)

        score = f.score          # tag-derived (airshot, multikill, combos...)
        reasons = list(f.tag_names)

        if prev_gap is not None and prev_gap <= CHAIN_MS:
            score += 2.5
            reasons.append(f"chain(-{prev_gap}ms)")
        if next_gap is not None and next_gap <= CHAIN_MS:
            score += 2.5
            reasons.append(f"chain(+{next_gap}ms)")
        if in_window >= 3:
            score += in_window
            reasons.append(f"{in_window}kills/{CAPTURE_MS//1000}s")
        if f.weapon in (fc.RAIL | fc.ROCKET):
            score += 1.5
            reasons.append("rail/rocket")
        if me is not None and f.killer == me:
            score += 1.0
            reasons.append("recorder-frag")

        out.append({
            "server_time_ms": f.time_ms,
            "timestamp": f"{f.time_ms // 60000}:{(f.time_ms // 1000) % 60:02d}",
            "seekclock": f"{f.time_ms // 60000}:{(f.time_ms // 1000) % 60:02d}",
            "round": f.round,
            "attacker": f.killer, "attacker_name": f.killer_name,
            "victim": f.victim, "victim_name": f.victim_name,
            "MOD": f.weapon, "weapon": f.weapon_name,
            "kills_in_capture_window": in_window,
            "ms_to_prev_frag": prev_gap,
            "ms_to_next_frag": next_gap,
            "rank_score": round(score, 2),
            "rank_reasons": reasons,
            "tags": f.tag_names,
        })
    return out


def build(max_demos: int, min_bytes: int) -> dict:
    seen: set[str] = set()
    entries: list[dict] = []
    trusted: list[str] = []
    rejected: list[dict] = []

    demos = sorted((ROOT / "demos").glob("*.dm_73"),
                   key=lambda z: -z.stat().st_size)
    for q in demos:
        if len(trusted) >= max_demos:
            break
        if q.stat().st_size < min_bytes:
            continue
        try:
            h = hashlib.md5(q.read_bytes()).hexdigest()
        except OSError:
            continue
        if h in seen:
            continue
        seen.add(h)

        try:
            parsed = D.DM73Parser(q).parse()
        except Exception as exc:
            rejected.append({"demo": q.name, "why": f"parse failed: {exc}"})
            continue

        ok, why = looks_trustworthy(parsed)
        if not ok:
            rejected.append({"demo": q.name, "why": why})
            continue

        trusted.append(q.name)
        me = fc.demo_taker(parsed)
        frags = fc.classify(parsed)
        for row in rank(frags, me):
            row["demo"] = q.name
            row["recorder_client"] = me
            entries.append(row)

    entries.sort(key=lambda r: -r["rank_score"])
    return {
        "label": "PROVEN SEEK LIST -- trusted-build demos only, NOT the full corpus",
        "trusted_demos": trusted,
        "rejected_demos": rejected,
        "min_obituaries_to_trust": MIN_OBITS_TRUSTED,
        "total_candidates": len(entries),
        "candidates": entries,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-demos", type=int, default=40)
    ap.add_argument("--min-bytes", type=int, default=700_000)
    ap.add_argument("--top", type=int, default=40)
    a = ap.parse_args()

    D._get_huff()
    res = build(a.max_demos, a.min_bytes)

    out_dir = ROOT / "output"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "seek_list_2012.json").write_text(
        json.dumps(res, indent=2), encoding="utf-8")

    csv_path = out_dir / "seek_list_2012.csv"
    cols = ["demo", "server_time_ms", "timestamp", "round", "attacker",
            "attacker_name", "victim", "victim_name", "MOD", "weapon",
            "kills_in_capture_window", "ms_to_prev_frag", "ms_to_next_frag",
            "rank_score", "recorder_client"]
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for row in res["candidates"]:
            w.writerow(row)

    print(res["label"])
    print(f"trusted demos : {len(res['trusted_demos'])}")
    print(f"rejected      : {len(res['rejected_demos'])} "
          f"(fewer than {MIN_OBITS_TRUSTED} obituaries -- unproven build)")
    print(f"candidates    : {res['total_candidates']}")
    print(f"\nwrote {csv_path}\n      {out_dir / 'seek_list_2012.json'}\n")
    print(f"top {a.top} capture candidates:")
    print(f"  {'score':>6} {'demo':30} {'clock':>7} {'rnd':>4} "
          f"{'weapon':11} {'atk':>4} {'vic':>4}  reasons")
    for r in res["candidates"][:a.top]:
        print(f"  {r['rank_score']:>6.1f} {r['demo'][:30]:30} "
              f"{r['timestamp']:>7} {r['round']:>4} {r['weapon'][:11]:11} "
              f"{r['attacker']:>4} {r['victim']:>4}  "
              f"{', '.join(r['rank_reasons'][:4])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
