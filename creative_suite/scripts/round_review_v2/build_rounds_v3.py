"""Round / action mining with trait rules v3 (the recorder's notes applied).

Differences from build_rounds.py (v2), each one from a written note:
  * policy comes from trait_rules_v3.R, not the calibration policy list;
    weights stay the calibrated shrunk means (x20);
  * every gametype with a known recorder is mined -- CA as rounds, the rest
    as action units (recorder kills chained <= 6 s) -- and each gametype
    (plus CTF instagib) is its own lane, ranked on its own; TDM/FFA x0.5;
  * gauntlet and telefrag kills never carry aim / precision / movement /
    health traits; a telefrag goes to the TELEFRAG lane and scores nothing;
  * series multiplier: each extra kill chained within 6 s adds 25% (cap 2x);
  * CLUTCH_1VN becomes CLUTCH_1V2/1V3/1V4_PLUS only when the recorder won
    the round or killed at least twice while last alive; otherwise dropped;
  * RAIL_CONSECUTIVE is HERO at >= 3 rails, SUPPORT at 2;
  * UPSHOT_KILL is HERO only for LG / rocket, SUPPORT otherwise;
  * LOW_HEALTH_WIN only when that kill won the round;
  * LG_HIGH_ACCURACY is rebuilt from the LG contact rate (the demo carries
    no beam-hit count, so this is the honest proxy): >= p97 HERO, >= p90
    SUPPORT; LG_TRACKING needs >= 60 damage in 3 s (not a finishing tick);
  * SAVED_BY_RECORDER on every kill the recorder also saved as a small demo;
  * LANE traits (telefrag, blooper, transition, effect) are collected per
    round as tags and never scored.
Outputs go to round_review_v2/v3/ so the v2 page stays untouched.
"""
from __future__ import annotations

import collections
import csv
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path("G:/QUAKE_LEGACY")
DB = ROOT / "creative_suite/database"
REC, FR, SH = DB / "frag_recognition.db", DB / "frags_rebuilt.db", DB / "frag_shapes.db"
HERE = ROOT / "output/demo_v2/round_review_v2"
OUT = HERE / "v3"
OUT.mkdir(exist_ok=True)
MODEL = ROOT / "output/demo_v2/calibration_v2/calibration_model.json"
sys.path.insert(0, str(HERE))
from trait_rules_v3 import R                                  # noqa: E402

COUNTDOWN_LEAD_MS, END_GRACE_MS, DEATH_TAIL_MS = 5000, 200, 750
MIN_BYTES = 512_000
CHAIN_MS = 6000
TOP_MOMENT_WEIGHTS = (1.0, 0.60, 0.35)
SCALE = 20.0
DISCOUNT = {"TDM": 0.5, "FFA": 0.5}
NOT_FOR_MELEE = {"aim", "precision", "movement", "health"}


def norm(v):
    return (v or "").replace('"', "").replace("\n", "").replace("\r", "").strip()


def ro(p):
    c = sqlite3.connect("file:%s?mode=ro" % p.as_posix(), uri=True, timeout=120)
    c.row_factory = sqlite3.Row
    return c


# ── policy ─────────────────────────────────────────────────────────────────
tw = json.loads(MODEL.read_text(encoding="utf-8"))["trait_weights"]
POL, LANES, GROUP = {}, {}, {}
for t, (grp, newp, _rule, _why) in R.items():
    POL[t] = newp.split()[0].split(":")[0]
    LANES[t] = re.findall(r"LANE:(\w+)", newp)
    GROUP[t] = grp


def weight(t):
    m = (tw.get(t) or {}).get("shrunk_mean")
    return float(m if m is not None else 3.0) * SCALE


# ── demos in scope: every gametype, recorder known, full-size ──────────────
fr = ro(FR)
demos = {r["content_hash"]: dict(r) for r in fr.execute(
    "SELECT content_hash, name, gametype, recorder_client, size_bytes, map_name "
    "FROM demos WHERE duplicate_of IS NULL AND path IS NOT NULL")}
fr.close()
scope = [h for h, d in demos.items()
         if d["recorder_client"] is not None and (d["size_bytes"] or 0) >= MIN_BYTES]
scope_set = set(scope)

rec = ro(REC)
kills, deaths, last_seen = (collections.defaultdict(list), collections.defaultdict(list),
                            collections.defaultdict(int))
occ_hashes = collections.defaultdict(set)
best_of_occ = {}
for r in rec.execute("SELECT content_hash, server_time_ms, mod_name, victim_client, "
                     "is_recorder_killer, is_recorder_victim, occurrence_id, "
                     "is_best_observation FROM kill_events_v1"):
    h = r["content_hash"]
    occ_hashes[r["occurrence_id"]].add(h)
    if not r["is_best_observation"]:
        continue
    best_of_occ[r["occurrence_id"]] = (h, r["server_time_ms"], r["is_recorder_killer"],
                                       r["is_recorder_victim"])
    if h not in scope_set:
        continue
    last_seen[h] = max(last_seen[h], r["server_time_ms"])
    if r["is_recorder_killer"]:
        kills[h].append(dict(r))
    if r["is_recorder_victim"]:
        deaths[h].append(r["server_time_ms"])

# SAVED_BY_RECORDER: a best observation whose occurrence also lives in a small demo
small = {h for h, d in demos.items() if (d["size_bytes"] or 0) < MIN_BYTES}
saved = {(v[0], v[1]) for oc, v in best_of_occ.items()
         if v[2] and occ_hashes[oc] & small and v[0] not in small}

# instagib: CTF demo whose recorder kills are >= 80% railgun
def gametype_lane(h):
    g = (demos[h]["gametype"] or "OTHER").upper()
    if g == "CTF":
        ks = kills.get(h, ())
        if ks and sum(1 for k in ks if k["mod_name"] == "RAILGUN") >= 0.8 * len(ks):
            return "CTF_INSTAGIB"
    return g


rs = collections.defaultdict(list)
for r in rec.execute("SELECT content_hash, server_time_ms, cs, value FROM round_state_v1 "
                     "WHERE cs IN (661, 662) ORDER BY content_hash, server_time_ms"):
    if r["content_hash"] in scope_set:
        rs[r["content_hash"]].append((r["server_time_ms"], r["cs"], norm(r["value"])))
demo_end = {r[0]: r[1] for r in rec.execute(
    "SELECT content_hash, MAX(server_time_ms) FROM gamestate_facts_v2 "
    "WHERE fact='DEMO_END' GROUP BY 1")}

frag = {}                      # (hash, t) -> {names:{name:detail}, attrs, weapon}
for r in rec.execute("SELECT content_hash, server_time_ms, classes, attributes, "
                     "weapon_name, id FROM recognized_frags WHERE classes IS NOT NULL"):
    if r["content_hash"] not in scope_set:
        continue
    try:
        cls = json.loads(r["classes"] or "[]")
        at = json.loads(r["attributes"] or "{}")
    except (TypeError, ValueError):
        continue
    frag[(r["content_hash"], r["server_time_ms"])] = {
        "names": {(c.get("name") if isinstance(c, dict) else str(c)):
                  (c.get("detail", "") if isinstance(c, dict) else "") for c in cls},
        "attrs": at, "id": r["id"]}

shapes_at = collections.defaultdict(list)
for r in ro(SH).execute("SELECT content_hash, server_time_ms, shape, actor FROM frag_shapes_v1"):
    h = r["content_hash"]
    if h in scope_set and r["actor"] == demos[h]["recorder_client"]:
        shapes_at[(h, r["server_time_ms"])].append(r["shape"])

# lane events from the funny table (recorder deaths / recorder telefrags)
FUNNY_LANE = {"HERO_THEN_DEATH": "TRANSITION", "KILL_THEN_DEATH_FAST": "TRANSITION",
              "FROM_THE_GRAVE": "TRANSITION", "ENVIRONMENTAL_DEATH": "BLOOPER",
              "SELF_DAMAGE_DEATH": "BLOOPER", "INSTANT_TRADE": "BLOOPER",
              "REFRAG": "BLOOPER", "TELEFRAG": "TELEFRAG"}
funny_at = collections.defaultdict(set)      # (hash) -> {(t, lane)}
funny_trait = collections.defaultdict(set)   # (hash, t) -> support traits
for oc, sig in rec.execute("SELECT occurrence_id, signals FROM funny_candidates_v1"):
    b = best_of_occ.get(oc)
    if not b or b[0] not in scope_set or not (b[2] or b[3]):
        continue                      # not the recorder's kill or death
    try:
        sigs = json.loads(sig) if sig and sig[:1] == "[" else [sig]
    except ValueError:
        sigs = [sig]
    for s in sigs:
        if s in FUNNY_LANE:
            funny_at[b[0]].add((b[1], FUNNY_LANE[s]))
        elif s in ("GAUNTLET_KILL",) and b[2]:
            funny_trait[(b[0], b[1])].add(s)
        elif s == "CHAT_REACTION_NEARBY" and b[2]:
            funny_trait[(b[0], b[1])].add(s)

# LG contact-rate percentiles for the rebuilt LG_HIGH_ACCURACY
lg_rates = sorted(f["attrs"]["lg_contact_rate"] for f in frag.values()
                  if f["attrs"].get("lg_contact_rate") is not None)


def lg_pct(v):
    if not lg_rates:
        return 0.0
    import bisect
    return 100.0 * bisect.bisect_right(lg_rates, v) / len(lg_rates)


unregistered = collections.Counter()


def score_moment(h, k, won_round):
    t, mod = k["server_time_ms"], (k["mod_name"] or "")
    f = frag.get((h, t), {"names": {}, "attrs": {}, "id": None})
    names = dict(f["names"])
    for s in shapes_at.get((h, t), []) + sorted(funny_trait.get((h, t), ())):
        names.setdefault(s, "")
    if (h, t) in saved:
        names["SAVED_BY_RECORDER"] = ""
    a = f["attrs"]
    lanes, kept = set(), {}
    melee = mod == "GAUNTLET"
    tele = mod == "TELEFRAG" or "TELEFRAG" in names
    for n, det in names.items():
        if n not in POL:
            unregistered[n] += 1
            continue
        pol = POL[n]
        lanes.update(LANES[n])
        if pol in ("RETIRE", "BASE", "LANE"):
            continue
        if (melee or tele) and GROUP[n] in NOT_FOR_MELEE:
            continue
        if n == "RAIL_CONSECUTIVE":
            m = re.search(r"(\d+) rails", det)
            pol = "HERO" if m and int(m.group(1)) >= 3 else "SUPPORT"
        elif n == "UPSHOT_KILL" and not mod.startswith(("LIGHTNING", "ROCKET")):
            pol = "SUPPORT"
        elif n == "LOW_HEALTH_WIN" and "ROUND_WINNING_FRAG" not in names:
            continue
        elif n == "LG_TRACKING" and (a.get("lg_damage_burst_3s") or 0) < 60:
            continue
        elif n == "LG_HIGH_ACCURACY":
            p = lg_pct(a["lg_contact_rate"]) if a.get("lg_contact_rate") is not None else 0
            if p < 90:
                continue
            pol = "HERO" if p >= 97 else "SUPPORT"
        elif n == "CLUTCH_1VN":
            m = re.search(r"1v(\d+)", det)
            if not (m and won_round):
                continue
            nn = int(m.group(1))
            n, pol = ("CLUTCH_1V4_PLUS" if nn >= 4 else "CLUTCH_1V%d" % nn), "HERO"
            if nn < 2:
                continue
        kept[n] = pol
    if tele:
        lanes.add("TELEFRAG")
        return {"t": t, "weapon": mod, "traits": sorted(kept), "value": 0.0,
                "hero": False, "lanes": sorted(lanes), "frag_id": f["id"]}
    # LG_HIGH_ACCURACY may also come purely from the attribute
    if mod.startswith("LIGHTNING") and a.get("lg_contact_rate") is not None \
            and "LG_HIGH_ACCURACY" not in kept:
        p = lg_pct(a["lg_contact_rate"])
        if p >= 90:
            kept["LG_HIGH_ACCURACY"] = "HERO" if p >= 97 else "SUPPORT"
    heroes = sorted((weight(n) for n, p in kept.items() if p == "HERO"), reverse=True)
    sups = sorted((weight(n) for n, p in kept.items() if p == "SUPPORT"), reverse=True)[:3]
    base = 10.0                                    # every own kill is worth something
    if heroes:
        total = base + heroes[0] + 0.35 * sum(heroes[1:3]) + 0.15 * sum(sups)
    else:
        total = base + 0.25 * (sups[0] if sups else 0.0) + 0.05 * sum(sups[1:])
    return {"t": t, "weapon": mod, "traits": sorted(kept), "value": round(total, 2),
            "hero": bool(heroes), "lanes": sorted(lanes), "frag_id": f["id"]}


def finish(moments):
    """Series multiplier, then top-3 weighting."""
    moments.sort(key=lambda m: m["t"])
    chain = 1
    for i, m in enumerate(moments):
        chain = chain + 1 if i and m["t"] - moments[i - 1]["t"] <= CHAIN_MS and m["value"] else 1
        m["chain"] = chain
        m["value"] = round(m["value"] * min(2.0, 1 + 0.25 * (chain - 1)), 2)
    vals = sorted((m["value"] for m in moments), reverse=True)
    return round(sum(w * v for w, v in zip(TOP_MOMENT_WEIGHTS, vals)), 2)


def weapon_lane(moments):
    w = collections.Counter((m["weapon"] or "UNKNOWN").replace("_SPLASH", "")
                            for m in moments if m["value"])
    if not w:
        return "NONE"
    top, c = w.most_common(1)[0]
    return top if len(w) == 1 or c > sum(w.values()) / 2 else "MULTI_WEAPON"


def rounds_for(h):
    out, cur = [], None
    for t, cs, v in rs.get(h, ()):
        if cs == 661:
            m, st = re.search(r"round\\(-?\d+)", v), re.search(r"time\\(-?\d+)", v)
            if not m or int(m.group(1)) <= 0:
                continue
            if cur and cur["round"] == int(m.group(1)):
                continue
            cur = {"round": int(m.group(1)), "announce": t,
                   "scheduled": int(st.group(1)) if st else None, "fight": None, "end": None}
            out.append(cur)
        elif cs == 662 and cur is not None:
            try:
                x = int(v.split()[0])
            except (ValueError, IndexError):
                continue
            if x > 0 and cur["fight"] is None:
                cur["fight"] = t
            elif x < 0 and cur["end"] is None and cur["fight"] is not None:
                cur["end"] = t
    return out


units, quarantine = [], collections.Counter()
for h in scope:
    d = demos[h]
    glane = gametype_lane(h)
    dend = demo_end.get(h) or last_seen.get(h) or 0
    windows = []
    if glane == "CA":
        rl = rounds_for(h)
        if not rl:
            quarantine["NO_ROUND_CONFIGSTRINGS"] += 1
        for i, r in enumerate(rl):
            nxt = rl[i + 1]["announce"] if i + 1 < len(rl) else None
            fight = r["fight"] or r["scheduled"]
            if fight is None or r["announce"] > fight:
                quarantine["BAD_ROUND_START"] += 1
                continue
            start = max(r["announce"], fight - COUNTDOWN_LEAD_MS)
            round_end = (r["end"] + END_GRACE_MS) if r["end"] else None
            hard_end = min([x for x in (round_end, nxt, dend) if x] or [dend])
            if hard_end <= fight:
                quarantine["END_BEFORE_FIGHT"] += 1
                continue
            died = [t for t in deaths.get(h, ()) if fight <= t <= hard_end]
            if died:
                end, reason = min(min(died) + DEATH_TAIL_MS, hard_end), "RECORDER_DEATH"
            elif round_end and round_end == hard_end:
                end, reason = hard_end, "ROUND_END"
            elif nxt and nxt == hard_end:
                end, reason = hard_end, "NEXT_ROUND_ANNOUNCED"
            else:
                end, reason = hard_end, "DEMO_END"
            windows.append((r["round"], start, fight, end, reason))
    else:
        ks = sorted(k["server_time_ms"] for k in kills.get(h, ()))
        i = 0
        while i < len(ks):
            j = i
            while j + 1 < len(ks) and ks[j + 1] - ks[j] <= CHAIN_MS:
                j += 1
            windows.append((len(windows) + 1, max(0, ks[i] - 5000), ks[i],
                            min(ks[j] + 3000, dend or ks[j] + 3000), "ACTION_UNIT"))
            i = j + 1
    for rnd, start, fight, end, reason in windows:
        inside = [k for k in kills.get(h, ()) if fight <= k["server_time_ms"] <= end]
        won = reason != "RECORDER_DEATH" and glane == "CA" and any(
            "ROUND_WINNING_FRAG" in frag.get((h, k["server_time_ms"]), {"names": {}})["names"]
            for k in inside)
        # >= 2 kills while last alive also counts as a won clutch
        lastalive = sum(1 for k in inside if "CLUTCH_1VN" in
                        frag.get((h, k["server_time_ms"]), {"names": {}})["names"])
        moments = [score_moment(h, k, won or lastalive >= 2) for k in inside]
        score = finish(moments) * DISCOUNT.get(glane, 1.0)
        lanes = sorted({l for m in moments for l in m["lanes"]} |
                       {l for t, l in funny_at.get(h, ()) if start <= t <= end})
        units.append({
            "content_hash": h, "demo_name": d["name"], "map": d["map_name"],
            "gametype": glane, "round": rnd, "start_ms": start, "fight_ms": fight,
            "end_ms": end, "countdown_lead_ms": fight - start, "end_reason": reason,
            "partial": reason == "DEMO_END", "kills": len(moments),
            "has_hero": any(m["hero"] for m in moments), "score": round(score, 2),
            "lane": weapon_lane(moments), "tags": lanes,
            "saved_by_recorder": any("SAVED_BY_RECORDER" in m["traits"] for m in moments),
            "traits": sorted({n for m in moments for n in m["traits"]}),
            "moments": moments})

# roles per gametype lane
for g in {u["gametype"] for u in units}:
    sc = sorted((u for u in units if u["gametype"] == g and u["kills"]), key=lambda u: -u["score"])
    for i, u in enumerate(sc):
        q = i / max(len(sc), 1)
        u["role"] = ("HERO_ROUND" if u["has_hero"] and q < 0.05 else
                     "STRONG_ROUND" if q < 0.20 else "FILLER_ROUND" if q < 0.50 else
                     "TRANSITION_OR_BLOOPER")
for u in units:
    u.setdefault("role", "NO_RECORDER_ACTION")

best = sorted(units, key=lambda u: (u["gametype"] != "CA", -u["score"]))
(OUT / "rounds_ranked.json").write_text(json.dumps(best, indent=1), encoding="utf-8")
with open(OUT / "rounds_ranked.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["gametype", "role", "score", "lane", "kills", "has_hero", "saved",
                "end_reason", "start_ms", "end_ms", "round", "map", "demo_name", "tags", "traits"])
    for u in best:
        w.writerow([u["gametype"], u["role"], u["score"], u["lane"], u["kills"], u["has_hero"],
                    u["saved_by_recorder"], u["end_reason"], u["start_ms"], u["end_ms"],
                    u["round"], u["map"], u["demo_name"], "|".join(u["tags"]),
                    " | ".join(u["traits"])])

tcount = collections.Counter(n for u in units for m in u["moments"] for n in m["traits"])
summary = {
    "demos_in_scope": len(scope), "units": len(units), "quarantined": dict(quarantine),
    "by_gametype": dict(collections.Counter(u["gametype"] for u in units)),
    "roles": {g: dict(collections.Counter(u["role"] for u in units if u["gametype"] == g))
              for g in sorted({u["gametype"] for u in units})},
    "tags": dict(collections.Counter(t for u in units for t in u["tags"])),
    "saved_by_recorder_units": sum(1 for u in units if u["saved_by_recorder"]),
    "trait_moments": dict(tcount.most_common()),
    "v3_traits_never_fired": sorted(t for t, p in POL.items()
                                    if p in ("HERO", "SUPPORT") and not tcount[t]),
    "unregistered_names": dict(unregistered.most_common(40)),
}
(OUT / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
print(json.dumps({k: v for k, v in summary.items() if k != "trait_moments"}, indent=1))
