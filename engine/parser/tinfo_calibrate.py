"""Calibrate decoded obituaries against the server's own `tinfo` health feed.

`tinfo` is a teammate-status servercommand: a count, then groups of six ints
(clientNum, location, health, armor, weapon, powerup). It covers TEAMMATES ONLY,
so it can never be the production frag source -- but that is exactly what makes
it useful as an INDEPENDENT signal. A teammate's health crossing from >0 to 0 is
the server telling us someone died, decoded by a completely different code path
from the entity stream.

    TINFO_DEATH_PROXY   health > 0 -> 0 for one client

Two directions are measured, and they answer different questions:

    precision   of the proxies, how many line up with an obituary we decoded
    recall      of our decoder, how many obituaries for tinfo-visible victims
                the proxies also saw

A proxy is matched only to an obituary for the SAME victim. Matching on time
alone would pair unrelated deaths in a busy round and manufacture a good score.

This is a DIAGNOSTIC. It never feeds frags.db.

    python engine/parser/tinfo_calibrate.py <demo> [--window 3000]
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import demo_parse as D  # noqa: E402

TINFO_FIELDS = 6          # clientNum, location, health, armor, weapon, powerup
DEFAULT_WINDOW_MS = 3000


def collect(path: Path):
    """Every tinfo sample and every obituary, on one pass of the demo."""
    p = D.DM73Parser(path)
    samples = []      # {time, client, health, armor, weapon}
    raw_seen = []

    original = p._parse_servercommand

    def cap(s):
        # Read the command ourselves, then hand a fresh view to the real parser
        # is not possible (the bit cursor has moved), so we fully replace it.
        try:
            s.readlong()
            raw = s.readstring()
        except Exception:
            return
        if not raw.startswith("tinfo"):
            return
        tok = raw.split()[1:]
        if not tok:
            return
        try:
            n = int(tok[0])
        except ValueError:
            return
        body = tok[1:]
        if n <= 0 or len(body) < n * TINFO_FIELDS:
            return
        if len(raw_seen) < 3:
            raw_seen.append(raw[:200])
        for i in range(n):
            g = body[i * TINFO_FIELDS:(i + 1) * TINFO_FIELDS]
            try:
                cid, loc, hp, ar, wp = (int(g[0]), int(g[1]), int(g[2]),
                                        int(g[3]), int(g[4]))
            except (ValueError, IndexError):
                continue
            samples.append({"time": p._last_server_time, "client": cid,
                            "health": hp, "armor": ar, "weapon": wp,
                            "location": loc})

    p._parse_servercommand = cap
    parsed = p.parse()

    obits = [e for e in parsed.get("events", []) if e.get("type") == "obituary"]
    return samples, obits, raw_seen, parsed


def death_proxies(samples):
    """health > 0 -> 0 transitions, per client, in time order."""
    last = {}
    out = []
    for s in sorted(samples, key=lambda z: z["time"]):
        cid = s["client"]
        prev = last.get(cid)
        if prev is not None and prev > 0 and s["health"] <= 0:
            out.append({"time": s["time"], "victim": cid,
                        "prev_health": prev, "new_health": s["health"],
                        "armor": s["armor"], "weapon": s["weapon"]})
        last[cid] = s["health"]
    return out


def classify_unmatched(proxy, obits, samples, rounds):
    """Why a proxy has no obituary. 'unknown' is an honest answer."""
    t = proxy["time"]
    for r in rounds or []:
        st, en = r.get("start_ms"), r.get("end_ms")
        if st is not None and abs(t - st) <= 2000:
            return "round_reset"
        if en is not None and abs(t - en) <= 2000:
            return "round_end"
    later = [s for s in samples
             if s["client"] == proxy["victim"] and 0 < s["time"] - t <= 6000]
    if later and any(s["health"] > 0 for s in later):
        return "respawn_or_state_transition"
    if not later:
        return "disconnect_or_left_tinfo_scope"
    same = [o for o in obits
            if abs(int(o.get("server_time_ms") or 0) - t) <= 8000]
    if same:
        return "obituary_present_but_outside_window"
    return "unknown"


def calibrate(path: Path, window_ms: int) -> dict:
    samples, obits, raw_seen, parsed = collect(path)
    proxies = death_proxies(samples)
    rounds = parsed.get("rounds", [])

    obit_by_victim = {}
    for o in obits:
        obit_by_victim.setdefault(o.get("victim_client"), []).append(o)

    matched, unmatched = [], []
    for pr in proxies:
        cands = obit_by_victim.get(pr["victim"], [])
        best, bestd = None, None
        for o in cands:
            d = int(o.get("server_time_ms") or 0) - pr["time"]
            if abs(d) <= window_ms and (bestd is None or abs(d) < abs(bestd)):
                best, bestd = o, d
        if best is not None:
            matched.append({**pr, "obituary_time": int(best.get("server_time_ms") or 0),
                            "attacker": best.get("killer_client"),
                            "MOD": best.get("weapon"),
                            "delta_ms": bestd})
        else:
            unmatched.append({**pr,
                              "reason": classify_unmatched(pr, obits, samples, rounds)})

    # Reverse direction: of the obituaries whose victim EVER appears in tinfo,
    # how many did a proxy also see? That is our decoder's recall on this slice.
    tinfo_clients = {s["client"] for s in samples}
    eligible = [o for o in obits if o.get("victim_client") in tinfo_clients]
    proxy_times = {}
    for pr in proxies:
        proxy_times.setdefault(pr["victim"], []).append(pr["time"])
    rev_hit = 0
    for o in eligible:
        t = int(o.get("server_time_ms") or 0)
        if any(abs(t - pt) <= window_ms
               for pt in proxy_times.get(o.get("victim_client"), [])):
            rev_hit += 1

    deltas = sorted(abs(m["delta_ms"]) for m in matched)

    def pct(p):
        if not deltas:
            return None
        k = min(len(deltas) - 1, int(round(p / 100.0 * (len(deltas) - 1))))
        return deltas[k]

    reasons = {}
    for u in unmatched:
        reasons[u["reason"]] = reasons.get(u["reason"], 0) + 1

    return {
        "demo": path.name,
        "tinfo_samples": len(samples),
        "tinfo_clients": sorted(tinfo_clients),
        "raw_samples": raw_seen,
        "obituaries": len(obits),
        "proxies_total": len(proxies),
        "matched_same_victim": len(matched),
        "unmatched": len(unmatched),
        "precision": (len(matched) / len(proxies)) if proxies else None,
        "eligible_obituaries": len(eligible),
        "tinfo_matched_obituaries": rev_hit,
        "tinfo_recall": (rev_hit / len(eligible)) if eligible else None,
        "delta_ms": {
            "min": deltas[0] if deltas else None,
            "median": statistics.median(deltas) if deltas else None,
            "p90": pct(90), "p95": pct(95), "p99": pct(99),
            "max": deltas[-1] if deltas else None,
        },
        "unmatched_reasons": reasons,
        "matched_rows": matched[:60],
        "unmatched_rows": unmatched[:60],
    }


def report(res: dict) -> None:
    print("\n" + "=" * 78)
    print(res["demo"])
    print("=" * 78)
    print("  tinfo samples          : {}  (clients {})".format(
        res["tinfo_samples"], res["tinfo_clients"]))
    for r in res["raw_samples"]:
        print("      {}".format(r))
    print("  obituaries decoded     : {}".format(res["obituaries"]))
    print("  TINFO_DEATH_PROXY      : {}".format(res["proxies_total"]))
    print("    matched same victim  : {}".format(res["matched_same_victim"]))
    print("    unmatched            : {}".format(res["unmatched"]))
    if res["precision"] is not None:
        print("    proxy precision      : {:.1%}".format(res["precision"]))
    d = res["delta_ms"]
    if d["median"] is not None:
        print("  proxy->obituary lag ms : min {} median {} p90 {} p95 {} "
              "p99 {} max {}".format(d["min"], d["median"], d["p90"],
                                     d["p95"], d["p99"], d["max"]))
    print("  eligible obituaries    : {}".format(res["eligible_obituaries"]))
    print("    seen by tinfo        : {}".format(res["tinfo_matched_obituaries"]))
    if res["tinfo_recall"] is not None:
        print("    tinfo recall         : {:.1%}".format(res["tinfo_recall"]))
    if res["unmatched_reasons"]:
        print("  unmatched classified   :")
        for k, v in sorted(res["unmatched_reasons"].items(), key=lambda z: -z[1]):
            print("      {:38} {}".format(k, v))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("demos", nargs="+")
    ap.add_argument("--window", type=int, default=DEFAULT_WINDOW_MS)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    D._get_huff()
    allres = []
    for d in a.demos:
        res = calibrate(Path(d), a.window)
        report(res)
        allres.append(res)
    if a.json:
        Path(a.json).write_text(json.dumps(allres, indent=2), encoding="utf-8")
        print("\nwrote {}".format(a.json))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
