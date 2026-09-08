"""Recorder-only highlight products, split from the match-wide data.

The database holds every kill in every match, 214,466 of them. That is the right
thing to store, but it is the wrong thing to cut a personal fragmovie from:
most of those kills belong to other people. The main Tr4sH/Stoneface reel needs
the kills the RECORDER made, which is a small fraction of the corpus.

Recorder identity comes from the protocol, not from names. The playerstate
stream only ever carries the player the demo followed, so the most frequent
client in it IS the recorder -- that holds regardless of colour codes, name
changes or clan tags. Aliases (Tr4sH / Trash / Stoneface) are used only to
CORROBORATE, never to decide, and disagreements are reported rather than
silently resolved.

Three products:

    recorder identity audit    EXACT / INFERRED / UNKNOWN per demo
    master_seek_recorder       ranked single frags by the recorder
    recorder sequences         capture-worthy WINDOWS, not isolated kills

The sequence builder is the point of the exercise: a wolfcam capture records a
span of time, so what matters is a window holding several strong kills, not one
kill in isolation.

    python engine/parser/recorder_products.py
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DEFAULT_DB = REPO / "creative_suite" / "database" / "frags_rebuilt.db"

ALIASES = ("tr4sh", "trash", "stoneface")
_COLOR = re.compile(r"\^\d")

SEQ_GAP_MS = 12000          # what one wolfcam capture window can hold
SEQ_MIN_KILLS = 2

TAG_WEIGHT = {
    "air_combo": 6.0, "quadkill": 6.0, "air_rocket": 5.0, "airshot": 4.0,
    "multikill": 4.0, "air_shaft": 3.5, "air_nade": 3.5, "rocket_rail": 3.0,
    "shaft_rail": 3.0, "shaft_rocket": 3.0, "big_flick": 2.5,
    "air_speed_combo": 2.5, "pixel_shot": 2.5, "very_fast_kill": 2.0,
    "high_acc_shaft": 2.0, "rocketjump_frag": 2.0, "airborne_kill": 1.5,
    "fast_kill": 1.0, "preshot": 1.5,
}
RAIL_MODS = {10}
ROCKET_MODS = {6, 7}


def strip_colors(s) -> str:
    return _COLOR.sub("", s or "").strip()


def is_alias(name) -> bool:
    return any(a in strip_colors(name).lower() for a in ALIASES)


def connect(db: Path):
    con = sqlite3.connect(str(db))
    con.row_factory = sqlite3.Row
    return con


# ---------------------------------------------------------------- identity
def identity_audit(con):
    """How each demo's recorder was established.

    EXACT     recorder_client came from the playerstate stream, which by
              protocol carries only the followed player
    INFERRED  no playerstate identity, but the roster carries a known alias
    UNKNOWN   neither -- reported, never dropped
    """
    rows = []
    for r in con.execute("""SELECT demo_id, name, recorder_client,
                                   recorder_name, accepted_frags, year
                            FROM demos"""):
        rc, rn = r["recorder_client"], r["recorder_name"] or ""
        if rc is not None:
            conf = "EXACT"
            method = "playerstate stream (protocol-level followed client)"
            alias_ok = is_alias(rn)
        elif is_alias(rn):
            conf, method, alias_ok = "INFERRED", "roster alias match", True
        else:
            conf, method, alias_ok = "UNKNOWN", "no playerstate, no alias", False
        rows.append({"demo_id": r["demo_id"], "demo": r["name"],
                     "year": r["year"], "recorder_client": rc,
                     "recorder_name": rn, "confidence": conf,
                     "method": method, "alias_corroborates": alias_ok,
                     "accepted_frags": r["accepted_frags"] or 0})
    return rows


# ------------------------------------------------------------------ ranking
def frag_score(r, prev_gap, next_gap, in_window):
    s, why = 0.0, []
    for tg in (r["tags"] or "").split(","):
        w = TAG_WEIGHT.get(tg)
        if w:
            s += w
            why.append(tg)
    if prev_gap is not None and prev_gap <= 4000:
        s += 2.5
        why.append("chain(-{}ms)".format(prev_gap))
    if next_gap is not None and next_gap <= 4000:
        s += 2.5
        why.append("chain(+{}ms)".format(next_gap))
    if in_window >= 3:
        s += in_window
        why.append("{}kills/12s".format(in_window))
    if r["mod"] in RAIL_MODS:
        s += 1.5
        why.append("rail")
    elif r["mod"] in ROCKET_MODS:
        s += 1.5
        why.append("rocket")
    return round(s, 2), why


def rank_frags(rows):
    by_demo = collections.defaultdict(list)
    for r in rows:
        by_demo[r["demo"]].append(r)
    out = []
    for demo, frs in by_demo.items():
        frs.sort(key=lambda z: z["server_time_ms"] or 0)
        times = [z["server_time_ms"] or 0 for z in frs]
        for i, r in enumerate(frs):
            t = times[i]
            pg = (t - times[i - 1]) if i > 0 else None
            ng = (times[i + 1] - t) if i + 1 < len(times) else None
            iw = sum(1 for x in times if 0 <= x - t <= SEQ_GAP_MS)
            s, why = frag_score(r, pg, ng, iw)
            out.append({**r, "ms_to_prev": pg, "ms_to_next": ng,
                        "kills_in_capture_window": iw,
                        "rank_score": s, "rank_reasons": ",".join(why[:8])})
    out.sort(key=lambda z: -z["rank_score"])
    return out


def build_sequences(ranked, clutch_index):
    """Group a recorder's kills into capture-worthy windows."""
    by_demo = collections.defaultdict(list)
    for r in ranked:
        by_demo[r["demo"]].append(r)

    seqs = []
    for demo, frs in by_demo.items():
        frs.sort(key=lambda z: z["server_time_ms"] or 0)
        cur = []
        for r in frs:
            if cur and (r["server_time_ms"] - cur[-1]["server_time_ms"]) > SEQ_GAP_MS:
                if len(cur) >= SEQ_MIN_KILLS:
                    seqs.append((demo, cur))
                cur = []
            cur.append(r)
        if len(cur) >= SEQ_MIN_KILLS:
            seqs.append((demo, cur))

    out = []
    for demo, grp in seqs:
        t0 = grp[0]["server_time_ms"]
        t1 = grp[-1]["server_time_ms"]
        span = max(1, t1 - t0)
        tags = set()
        for r in grp:
            tags.update(t for t in (r["tags"] or "").split(",") if t)
        score = sum(r["rank_score"] for r in grp)
        why = sorted(tags & set(TAG_WEIGHT), key=lambda t: -TAG_WEIGHT[t])[:6]
        # density: several kills inside one window is the thing worth capturing
        if len(grp) >= 3 and span <= SEQ_GAP_MS:
            score += 6.0
            why.append("{}kills/{:.1f}s".format(len(grp), span / 1000))
        if len({r["weapon_name"] for r in grp}) >= 3:
            score += 3.0
            why.append("weapon-combo")
        rounds = {r["round"] for r in grp if r["round"] is not None}
        key = (demo, min(rounds) if rounds else None)
        if key in clutch_index:
            score += 8.0
            why.append("clutch-overlap")
        out.append({
            "demo": demo, "year": grp[0].get("year"), "map": grp[0].get("map_name"),
            "round": min(rounds) if rounds else None,
            "start_ms": t0, "end_ms": t1,
            "start_clock": "{}:{:02d}".format(t0 // 60000, (t0 // 1000) % 60),
            "end_clock": "{}:{:02d}".format(t1 // 60000, (t1 // 1000) % 60),
            "span_s": round(span / 1000.0, 2),
            "kill_count": len(grp),
            "victims": ",".join(str(r["victim_name"]) for r in grp),
            "weapons": ",".join(str(r["weapon_name"]) for r in grp),
            "tags": ",".join(sorted(tags)),
            "score": round(score, 2),
            "ranking_reasons": ",".join(why[:8]),
        })
    out.sort(key=lambda z: -z["score"])
    return out


def write(path_stem: Path, rows, cols):
    with (path_stem.with_suffix(".csv")).open("w", newline="",
                                              encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    path_stem.with_suffix(".json").write_text(
        json.dumps({"total": len(rows), "items": rows}, indent=2),
        encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--out-dir", default=str(REPO / "output"))
    ap.add_argument("--top", type=int, default=20)
    a = ap.parse_args()

    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    con = connect(Path(a.db))

    # ---- identity audit -----------------------------------------------
    ident = identity_audit(con)
    conf = collections.Counter(r["confidence"] for r in ident)
    write(out / "recorder_identity_audit", ident,
          ["demo_id", "demo", "year", "recorder_client", "recorder_name",
           "confidence", "method", "alias_corroborates", "accepted_frags"])
    unknown = [r for r in ident if r["confidence"] == "UNKNOWN"]
    write(out / "recorder_identity_unresolved", unknown,
          ["demo_id", "demo", "year", "recorder_name", "accepted_frags"])

    raw_kills = con.execute("SELECT COUNT(*) FROM frags").fetchone()[0]
    total_kills = con.execute("SELECT COUNT(*) FROM frags_dedup").fetchone()[0]
    rec_kills = con.execute(
        "SELECT COUNT(*) FROM frags_dedup WHERE by_recorder=1").fetchone()[0]

    print("=" * 66)
    print("RECORDER IDENTITY AUDIT")
    print("=" * 66)
    print("  demos                    : {}".format(len(ident)))
    for k in ("EXACT", "INFERRED", "UNKNOWN"):
        print("  {:24} : {}".format(k, conf.get(k, 0)))
    ali = sum(1 for r in ident if r["alias_corroborates"])
    print("  alias corroborates       : {} of {} EXACT/INFERRED".format(
        ali, conf.get("EXACT", 0) + conf.get("INFERRED", 0)))
    print("")
    print("  raw frag rows              : {}".format(raw_kills))
    print("  deduplicated match kills   : {}  ({} snapshot repeats removed)"
          .format(total_kills, raw_kills - total_kills))
    print("  recorder-attacker kills    : {}".format(rec_kills))
    print("  non-recorder kills         : {}".format(total_kills - rec_kills))

    # ---- recorder frags ------------------------------------------------
    # frags_dedup, not frags: one row per real kill. The raw table re-emits a
    # kill once per snapshot the event entity survives (282 of 214,466 rows,
    # 0.13%), which would inflate any "kills in one window" ranking.
    #
    # recorder_is_alias, because "the recorder" of a downloaded pro demo is that
    # pro, not us. 1,620 recorder kills live in other players' demos and have no
    # place in a personal reel; they stay available in the all-match product.
    rows = [dict(r) for r in con.execute("""
        SELECT f.*, d.name AS demo, d.year, d.map_name
        FROM frags_dedup f JOIN demos d ON d.demo_id=f.demo_id
        WHERE f.by_recorder=1 AND d.recorder_is_alias=1""")]
    other = con.execute("""SELECT COUNT(*) FROM frags_dedup f JOIN demos d
                           ON d.demo_id=f.demo_id
                           WHERE f.by_recorder=1 AND d.recorder_is_alias=0"""
                        ).fetchone()[0]
    ranked = rank_frags(rows)

    # clutch overlap, if the clutch pass has run
    clutch_index = set()
    cp = out / "clutch_recorder.json"
    if not cp.exists():
        cp = out / "clutch_round_wins.json"
    if cp.exists():
        try:
            for c in json.loads(cp.read_text(encoding="utf-8")).get("items", []):
                clutch_index.add((c.get("demo"), c.get("round")))
        except Exception:
            pass

    cols = ["demo", "year", "map_name", "server_time_ms", "clock", "round",
            "attacker_client", "attacker_name", "victim_client", "victim_name",
            "mod", "weapon_name", "tags", "ms_to_prev", "ms_to_next",
            "kills_in_capture_window", "rank_score", "rank_reasons"]
    write(out / "master_seek_recorder", ranked, cols)

    per_year = collections.Counter(r["year"] for r in ranked)
    demos_contrib = len({r["demo"] for r in ranked})
    print("")
    print("=" * 66)
    print("RECORDER SEEK LIST")
    print("=" * 66)
    print("  recorder frags (alias demos) : {}   <- personal pool"
          .format(len(ranked)))
    print("  recorder frags in other players' demos: {} (excluded)".format(other))
    print("  demos contributing   : {}".format(demos_contrib))
    print("  by year              : {}".format(
        dict(sorted(per_year.items(), key=lambda z: str(z[0])))))

    # ---- sequences -----------------------------------------------------
    seqs = build_sequences(ranked, clutch_index)
    write(out / "recorder_sequences", seqs,
          ["demo", "year", "map", "round", "start_ms", "end_ms", "start_clock",
           "end_clock", "span_s", "kill_count", "victims", "weapons", "tags",
           "score", "ranking_reasons"])
    print("")
    print("=" * 66)
    print("RECORDER SEQUENCES  (capture windows, not isolated kills)")
    print("=" * 66)
    print("  sequences built : {}".format(len(seqs)))
    print("")
    print("  TOP {}:".format(a.top))
    print("    {:>6} {:34} {:>6} {:>6} {:>5} {:>4}  reasons".format(
        "score", "demo", "start", "span", "kills", "rnd"))
    for r in seqs[:a.top]:
        print("    {:>6.1f} {:34} {:>6} {:>5.1f}s {:>5} {:>4}  {}".format(
            r["score"], (r["demo"] or "")[:34], r["start_clock"], r["span_s"],
            r["kill_count"], r["round"] if r["round"] is not None else "",
            r["ranking_reasons"][:44]))
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
