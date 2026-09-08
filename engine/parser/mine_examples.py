"""Mine the demo corpus for N examples of every frag type we recognise.

Purpose (user 2026-08-29): "try to use the demo to get 2 frag from each type we
want to recognize so we can finetune it and optimize it."

Scans demos until it has N examples of each tag, then writes a review manifest:
demo, exact server time, round, weapon, the tag and the evidence string that
produced it. That manifest is what you seek to in WolfcamQL to confirm whether
a detector is right -- it is the tuning loop for `frag_classify.py`.

    python engine/parser/mine_examples.py --want 2 --max-demos 40
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))

import demo_parse  # noqa: E402
import frag_classify as fc  # noqa: E402

# Every tag the classifier can emit, so a type with ZERO examples is visible
# rather than silently absent.
ALL_TAGS = [
    "airshot", "air_rocket", "air_nade", "air_shaft", "air_combo",
    "airborne_kill", "rocketjump_frag", "air_speed_combo",
    "fast_kill", "very_fast_kill",
    "multikill", "quadkill",
    "rocket_rail", "shaft_rail", "shaft_rocket", "rocket_shaft",
    "big_flick", "pixel_shot", "preshot", "high_acc_shaft",
]


def mine(demos: list[Path], want: int, mine_only: bool) -> dict:
    found: dict[str, list[dict]] = defaultdict(list)
    scanned = 0

    for d in demos:
        if all(len(found[t]) >= want for t in ALL_TAGS):
            break
        try:
            parsed = demo_parse.DM73Parser(d).parse()
        except Exception as exc:
            print(f"  [skip] {d.name}: {exc}", flush=True)
            continue
        scanned += 1
        me = fc.demo_taker(parsed) if mine_only else None
        frags = fc.classify(parsed, player=me)

        for f in frags:
            for tag in f.tags:
                if len(found[tag.name]) >= want:
                    continue
                found[tag.name].append({
                    "tag": tag.name,
                    "confidence": tag.confidence,
                    "evidence": tag.detail,
                    "demo": d.name,
                    "server_time_ms": f.time_ms,
                    "clock": f"{f.time_ms // 60000}:{(f.time_ms // 1000) % 60:02d}",
                    "round": f.round,
                    "weapon": f.weapon_name,
                    "killer": f.killer_name,
                    "victim": f.victim_name,
                    "score": round(f.score, 1),
                    "all_tags": f.tag_names,
                    "killer_speed_ups": (round(f.killer_speed)
                                         if f.killer_speed else None),
                    "accuracy_pct": f.lg_accuracy,
                })
        if not frags:
            # No kills at all in a full match means the entity field table does
            # not match this demo's protocol build -- not that the demo is dull.
            print(f"  [!!] {d.name[:44]:44} ZERO kills decoded "
                  f"({len(parsed.get('events', []))} events) -- field-table "
                  f"mismatch", flush=True)
        got = sum(1 for t in ALL_TAGS if found[t])
        print(f"  [{scanned}] {d.name[:44]:44} types covered {got}/{len(ALL_TAGS)}",
              flush=True)

    return {"scanned": scanned, "want": want,
            "examples": {t: found[t] for t in ALL_TAGS}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--want", type=int, default=2)
    ap.add_argument("--max-demos", type=int, default=40)
    ap.add_argument("--all-players", action="store_true",
                    help="include kills by anyone (default: demo taker only)")
    ap.add_argument("--min-bytes", type=int, default=1_000_000,
                    help="skip single-frag clips (user: <1MB is one action)")
    ap.add_argument("--out", default="output/frag_examples.json")
    a = ap.parse_args()

    # Deduplicate by CONTENT. The corpus holds many byte-identical copies under
    # different names -- the four largest "different" demos were one file, so
    # sorting by size scanned the same demo four times and coverage never moved.
    import hashlib

    seen: set[str] = set()
    demos: list[Path] = []
    for q in sorted((ROOT / "demos").glob("*.dm_73"),
                    key=lambda z: -z.stat().st_size):
        if q.stat().st_size < a.min_bytes:
            continue                      # sub-MB files are single-frag clips
        try:
            h = hashlib.md5(q.read_bytes()).hexdigest()
        except OSError:
            continue
        if h in seen:
            continue
        seen.add(h)
        demos.append(q)
        if len(demos) >= a.max_demos:
            break
    print(f"mining {len(demos)} demo(s) for {a.want} example(s) of each type")
    res = mine(demos, a.want, mine_only=not a.all_players)

    out = ROOT / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=2), encoding="utf-8")

    print(f"\nscanned {res['scanned']} demo(s) -> {out}\n")
    print(f"{'type':20} {'found':>6}   example")
    missing = []
    for t in ALL_TAGS:
        ex = res["examples"][t]
        if not ex:
            missing.append(t)
            print(f"{t:20} {0:>6}   -- none found --")
            continue
        e = ex[0]
        print(f"{t:20} {len(ex):>6}   {e['demo'][:34]:34} @{e['clock']} "
              f"{e['weapon']:10} {e['evidence'][:40]}")
    if missing:
        print(f"\nNOT FOUND in this sample ({len(missing)}): {', '.join(missing)}")
        print("Either genuinely rare, or the detector is too strict -- that is "
              "exactly what this manifest is for.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
