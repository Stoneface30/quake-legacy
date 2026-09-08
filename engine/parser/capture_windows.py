"""Recorder capture windows for V2 clip generation (charter §5, §6, §9, §17).

Groups the ranked recorder kills (master_seek_recorder.csv) into capture
windows with generous context, extends windows to cover whole clutches
(clutch_recorder.csv, joined on canonical demo hash), keeps every kill offset
for hit-to-beat, and emits ranked top-20/50/100 lists plus the full set.
Top-100 candidates are inserted into demo_v2.db as promotion CANDIDATEs.

Usage:
    python -u engine/parser/capture_windows.py
"""
from __future__ import annotations

import csv
import json
import sqlite3
import sys
from pathlib import Path

# DATA, not code: under a worktree these differ, and opening a
# database beneath the wrong one silently CREATES an empty file
# rather than failing. See engine.pantheon.store.
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()
FRAGS_DB = REPO_ROOT / "creative_suite" / "database" / "frags_rebuilt.db"
SEEK_CSV = REPO_ROOT / "output" / "master_seek_recorder.csv"
CLUTCH_CSV = REPO_ROOT / "output" / "clutch_recorder.csv"
OUT_DIR = REPO_ROOT / "output" / "demo_v2"

CHAIN_GAP_MS = 5_000
PRE_MS = 5_000
POST_MS = 3_000
POST_CLUTCH_MS = 4_000

ACTION_TAGS = {"airshot", "air_rocket", "airborne_kill", "rocketjump_frag",
               "air_combo", "big_flick", "high_acc_shaft"}


def dedupe_clutches(clutches: list[dict]) -> list[dict]:
    """Drop clutch rows duplicated across duplicate demo files."""
    seen, out = set(), []
    for c in clutches:
        key = (c["canonical_demo_hash"], int(c["round"]), int(c["clutch_start_ms"]))
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out


def _chain(kills: list[dict]) -> list[list[dict]]:
    kills = sorted(kills, key=lambda k: int(k["server_time_ms"]))
    groups, cur = [], [kills[0]]
    for k in kills[1:]:
        if int(k["server_time_ms"]) - int(cur[-1]["server_time_ms"]) <= CHAIN_GAP_MS:
            cur.append(k)
        else:
            groups.append(cur)
            cur = [k]
    groups.append(cur)
    return groups


def _mk_window(group: list[dict]) -> dict:
    """Window bounds with dynamic context (charter: capture generously).

    Single frag: 5 s pre / 4 s post. Multikill (3+): 6 s pre / 5 s post so the
    setup and the aftermath both survive. Clutch extension widens further.
    """
    times = [int(k["server_time_ms"]) for k in group]
    pre = PRE_MS + (1000 if len(group) >= 3 else 0)
    post = (POST_MS + 1000) if len(group) < 3 else (POST_MS + 2000)
    return {
        "kills": group,
        "capture_start_ms": times[0] - pre,
        "capture_end_ms": times[-1] + post,
        "clutch": None,
    }


def _finalize(w: dict, demo_hash: str | None) -> dict:
    group = sorted(w["kills"], key=lambda k: int(k["server_time_ms"]))
    start = max(0, w["capture_start_ms"])
    end = w["capture_end_ms"]
    best = max(group, key=lambda k: float(k["rank_score"]))
    scores = sorted((float(k["rank_score"]) for k in group), reverse=True)
    score = scores[0] + 0.5 * sum(scores[1:])
    clutch = w["clutch"]
    if clutch:
        score += 2.0 * int(clutch["enemies_alive_at_start"])
    tags = sorted({t for k in group for t in (k.get("tags") or "").split(",") if t})
    return {
        "demo": group[0]["demo"],
        "canonical_demo_hash": demo_hash,
        "map": group[0].get("map_name", ""),
        "round": int(best["round"]) if best.get("round") not in (None, "") else None,
        "server_time_ms": int(best["server_time_ms"]),
        "clock_start": _clock(best, start),
        "clock_end": _clock(best, end),
        "capture_start_ms": start,
        "capture_end_ms": end,
        "duration_s": round((end - start) / 1000.0, 2),
        "n_kills": len(group),
        "weapon": best.get("weapon_name", ""),
        "weapons": ",".join(sorted({k.get("weapon_name", "") for k in group})),
        "tags": ",".join(tags),
        "frag_offsets_ms": json.dumps(
            [int(k["server_time_ms"]) - start for k in group]),
        "score": round(score, 2),
        "clutch_context": json.dumps({
            "enemies_alive_at_start": int(clutch["enemies_alive_at_start"]),
            "kills_during_clutch": int(clutch["kills_during_clutch"]),
            "weapons": clutch["weapons"],
            "outcome": clutch["outcome"],
            "clutch_rank_score": float(clutch["rank_score"]),
        }) if clutch else None,
    }


def _clock(ref_kill: dict, t_ms: int) -> str:
    """Render demo clock at t_ms using the reference kill's clock anchor.

    CA clocks count DOWN, so clock = ref_clock + (ref_time - t) in seconds.
    Falls back to raw seconds if the anchor clock is unparsable.
    """
    ref_t = int(ref_kill["server_time_ms"])
    raw = ref_kill.get("clock") or ""
    try:
        mm, ss = raw.split(":")
        ref_clock_s = int(mm) * 60 + int(ss)
    except ValueError:
        s = max(0, t_ms) // 1000
        return f"~{s // 60}:{s % 60:02d}"
    clock_s = max(0, ref_clock_s + (ref_t - t_ms) // 1000)
    return f"{clock_s // 60}:{clock_s % 60:02d}"


def build_windows(kills: list[dict], clutches: list[dict] | None = None,
                  demo_hash: str | None = None) -> list[dict]:
    """Build finalized capture windows for one demo's recorder kills."""
    if not kills:
        return []
    windows = [_mk_window(g) for g in _chain(kills)]

    for c in clutches or []:
        if demo_hash is None or c["canonical_demo_hash"] != demo_hash:
            continue
        cs, ce = int(c["clutch_start_ms"]), int(c["clutch_end_ms"])
        for w in windows:
            if any(cs <= int(k["server_time_ms"]) <= ce for k in w["kills"]):
                w["capture_start_ms"] = min(w["capture_start_ms"], cs - PRE_MS)
                w["capture_end_ms"] = max(w["capture_end_ms"], ce + POST_CLUTCH_MS)
                w["clutch"] = c

    # Post-extension re-merge of overlapping windows (single pass over sorted)
    windows.sort(key=lambda w: w["capture_start_ms"])
    merged = [windows[0]]
    for w in windows[1:]:
        prev = merged[-1]
        if w["capture_start_ms"] <= prev["capture_end_ms"]:
            prev["kills"].extend(w["kills"])
            prev["capture_start_ms"] = min(prev["capture_start_ms"], w["capture_start_ms"])
            prev["capture_end_ms"] = max(prev["capture_end_ms"], w["capture_end_ms"])
            prev["clutch"] = prev["clutch"] or w["clutch"]
        else:
            merged.append(w)

    return [_finalize(w, demo_hash) for w in merged]


MIN_SHARED_TUPLES = 3


def build_match_groups(demo_frags: dict[str, list[tuple]]) -> dict[str, int]:
    """Group demo files that recorded the SAME server match.

    Evidence: two recordings of one match contain identical
    (map, server_time_ms, attacker_client, victim_client, mod) kill tuples —
    for ALL players, not just the recorder. Unrelated matches colliding on
    MIN_SHARED_TUPLES exact millisecond+clients+mod tuples is not a real
    scenario, while same-map serverTime coincidences alone are (servers
    restart serverTime). Union-find over shared-tuple demo pairs.

    demo_frags: demo name -> list of kill tuples.
    Returns demo name -> match_group_id.
    """
    parent: dict[str, str] = {d: d for d in demo_frags}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    tuple_owners: dict[tuple, list[str]] = {}
    for demo, tuples in demo_frags.items():
        for t in tuples:
            tuple_owners.setdefault(t, []).append(demo)

    pair_counts: dict[tuple[str, str], int] = {}
    for owners in tuple_owners.values():
        if len(owners) < 2:
            continue
        owners = sorted(set(owners))
        for i in range(len(owners)):
            for j in range(i + 1, len(owners)):
                pair = (owners[i], owners[j])
                pair_counts[pair] = pair_counts.get(pair, 0) + 1

    for (a, b), n in pair_counts.items():
        if n >= MIN_SHARED_TUPLES:
            union(a, b)

    roots: dict[str, int] = {}
    out: dict[str, int] = {}
    for d in demo_frags:
        r = find(d)
        out[d] = roots.setdefault(r, len(roots))
    return out


def dedupe_windows(windows: list[dict], match_group: dict[str, int]) -> list[dict]:
    """Collapse duplicate MOMENTS — only within one match group.

    Two windows are the same moment iff their demos recorded the same match
    (match_group) AND they share at least one kill serverTime (kill times are
    server-authoritative, identical across copies of a match). Windows from
    unrelated matches are NEVER merged, even if map+serverTime coincide.
    Keeps the higher score (fuller chain), then the descriptively named demo.
    """
    import json as _json

    def kill_times(w: dict) -> set[int]:
        offs = _json.loads(w["frag_offsets_ms"])
        return {w["capture_start_ms"] + o for o in offs}

    by_group: dict[int, list[dict]] = {}
    ungrouped: list[dict] = []
    for w in windows:
        g = match_group.get(w["demo"])
        if g is None:
            ungrouped.append(w)
        else:
            by_group.setdefault(g, []).append(w)

    out: list[dict] = list(ungrouped)
    for group in by_group.values():
        demos = {w["demo"] for w in group}
        if len(demos) == 1:
            out.extend(group)
            continue
        kept: list[tuple[set[int], dict]] = []
        for w in sorted(group, key=lambda w: (-w["score"],
                                              w["demo"].startswith("Demo ("))):
            kt = kill_times(w)
            if any(kt & other_kt for other_kt, _ in kept):
                continue
            kept.append((kt, w))
        out.extend(w for _, w in kept)
    return out


def assign_classes(windows: list[dict]) -> None:
    """Complete taxonomy — every window gets an explicit class.

    Premium: CLUTCH_PREMIUM / T1_NEW (P99) / T2_NEW (P95) / ACTION_PREMIUM
    (action tag). Remainder: NORMAL (score >= median — solid but unremarkable
    recorder kills) or LOW_SCORE (below median — context/killfeed value only).
    Class counts always sum to the unique-window total.
    """
    scores = sorted((w["score"] for w in windows), reverse=True)
    if not scores:
        return
    p99 = scores[max(0, len(scores) // 100 - 1)]
    p95 = scores[max(0, len(scores) * 5 // 100 - 1)]
    p50 = scores[len(scores) // 2]
    for w in windows:
        if w["clutch_context"]:
            w["class"] = "CLUTCH_PREMIUM"
        elif w["score"] >= p99:
            w["class"] = "T1_NEW"
        elif w["score"] >= p95:
            w["class"] = "T2_NEW"
        elif set((w["tags"] or "").split(",")) & ACTION_TAGS:
            w["class"] = "ACTION_PREMIUM"
        elif w["score"] >= p50:
            w["class"] = "NORMAL"
        else:
            w["class"] = "LOW_SCORE"


def load_demo_frag_tuples(conn) -> dict[str, list[tuple]]:
    """All kill tuples per demo (every player) for match fingerprinting."""
    demo_frags: dict[str, list[tuple]] = {}
    for demo, mp, t, a, v, mod in conn.execute(
            "SELECT f.demo_name, d.map_name, f.server_time_ms, f.attacker_client,"
            " f.victim_client, f.mod FROM frags f JOIN demos d ON d.demo_id=f.demo_id"):
        demo_frags.setdefault(demo, []).append((mp, t, a, v, mod))
    return demo_frags


def prepare() -> tuple[list[dict], dict[str, int], dict[str, tuple]]:
    """Everything up to (but excluding) dedup: pre-dedup windows,
    match groups, and demo info map."""
    conn = sqlite3.connect(f"file:{FRAGS_DB}?mode=ro", uri=True)
    demo_info = {}
    for name, h, size, rc, dup in conn.execute(
            "SELECT name, content_hash, size_bytes, recorder_client, duplicate_of FROM demos"):
        demo_info[name] = (dup or h, size, rc)
    demo_frags = load_demo_frag_tuples(conn)
    conn.close()
    match_group = build_match_groups(demo_frags)

    with open(SEEK_CSV, newline="", encoding="utf-8") as f:
        seek = list(csv.DictReader(f))
    with open(CLUTCH_CSV, newline="", encoding="utf-8") as f:
        clutches = dedupe_clutches(list(csv.DictReader(f)))

    clutch_by_hash: dict[str, list[dict]] = {}
    for c in clutches:
        clutch_by_hash.setdefault(c["canonical_demo_hash"], []).append(c)

    by_demo: dict[str, list[dict]] = {}
    for k in seek:
        by_demo.setdefault(k["demo"], []).append(k)

    windows: list[dict] = []
    for demo, kills in by_demo.items():
        h = demo_info.get(demo, (None, None, None))[0]
        windows.extend(build_windows(kills, clutch_by_hash.get(h, []), h))

    for w in windows:
        w["match_group"] = match_group.get(w["demo"])
    return windows, match_group, demo_info


def run() -> dict:
    windows, match_group, demo_info = prepare()
    windows = dedupe_windows(windows, match_group)
    assign_classes(windows)
    windows.sort(key=lambda w: w["score"], reverse=True)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fields = list(dict.fromkeys([*windows[0].keys()])) if windows else []

    def write_csv(path: Path, rows: list[dict]):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)

    write_csv(OUT_DIR / "capture_windows_full.csv", windows)
    with open(OUT_DIR / "capture_windows_full.json", "w", encoding="utf-8") as f:
        json.dump(windows, f, indent=1)
    for n in (20, 50, 100):
        write_csv(OUT_DIR / f"capture_windows_top{n}.csv", windows[:n])

    # NOTE: promotion-candidate DB rows are owned by promotion_batch.py,
    # which applies overlap removal and diversity before inserting.

    counts = {}
    for w in windows:
        counts[w["class"]] = counts.get(w["class"], 0) + 1
    return {"windows": len(windows), "class_counts": counts,
            "top_score": windows[0]["score"] if windows else 0}


if __name__ == "__main__":
    s = run()
    print(f"windows: {s['windows']}  top_score: {s['top_score']}")
    for k, v in sorted(s["class_counts"].items(), key=lambda kv: -kv[1]):
        print(f"  {k:16s} {v}")
