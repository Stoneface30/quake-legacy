"""Round-first mining over the WHOLE CA corpus, with the recorder known up front.

Why this exists: the V2 validation quarantined 414 of 430 rounds, and every one
of the 414 had recorder_client = None. The resolver inferred the recorder from
events inside the round window, and most rounds carry no such event -- so a
perfectly good round was thrown away for lack of a label the demo record
already had (frags_rebuilt.demos.recorder_client, known for 4,066 CA demos).

Rules (from the user's review):
  * a round starts exactly 5 s before the fight goes live (never before the
    announcement), so the countdown is on screen;
  * it ends at the EARLIEST of recorder death, the authoritative round end,
    the next round's announcement, or the end of the demo -- never into the
    next round;
  * one item per round, carrying every trait that fired inside it;
  * sorted by gametype, then weapon lane, then score;
  * scoring from the calibrated model: hero traits count, support traits count
    but cannot make a hero round, retired traits score zero.

Engine facts used (verified against source earlier this week): CS 661 carries
\\time\\<scheduled start>\\round\\<N>; CS 662 > 0 is play running, -1 is play
over; values keep a trailing quote + newline; the round-end command is logged
against the PREVIOUS snapshot so the decisive kill lands ~25 ms later, hence
a small grace after the end command.
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
REC = DB / "frag_recognition.db"
FR = DB / "frags_rebuilt.db"
SH = DB / "frag_shapes.db"
HERE = ROOT / "output/demo_v2/round_review_v2"
MODEL = ROOT / "output/demo_v2/calibration_v2/calibration_model.json"
REGISTRY = HERE / "trait_registry_v2.json"
ANSWERS = ROOT / "output/demo_v2/calibration_answers.json"

COUNTDOWN_LEAD_MS = 5000
END_GRACE_MS = 200            # decisive kill lands ~25 ms after the end cmd
DEATH_TAIL_MS = 750           # let the death itself read on screen
MIN_BYTES = 512_000
TOP_MOMENT_WEIGHTS = (1.0, 0.60, 0.35)
TRAIT_SCALE = 20.0

LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 0


def norm(v):
    return (v or "").replace('"', "").replace("\n", "").replace("\r", "").strip()


def ro(path):
    c = sqlite3.connect("file:%s?mode=ro" % path.as_posix(), uri=True, timeout=120)
    c.row_factory = sqlite3.Row
    return c


# ── calibration ────────────────────────────────────────────────────────────
model = json.loads(MODEL.read_text(encoding="utf-8"))
tw = model["trait_weights"]
registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
family_of = {t: fam for fam, ts in registry["families"].items() for t in ts}
policy_of = {t: pol for pol, ts in registry["policies"].items() for t in ts}


def trait_value(name):
    pol = policy_of.get(name) or (tw.get(name) or {}).get("policy")
    if pol not in ("hero", "support"):
        return 0.0, pol or "unregistered"
    return float(tw[name]["shrunk_mean"]) * TRAIT_SCALE, pol


# ── the user's written notes, per trait ────────────────────────────────────
notes = collections.defaultdict(list)
try:
    ans = json.loads(ANSWERS.read_text(encoding="utf-8"))
    for k, v in ans.items():
        if k.startswith("v_") and str(v).strip():
            trait = k[2:].rsplit("__", 1)[0]
            notes[trait].append(str(v).strip())
except (OSError, ValueError):
    pass
FLAGS = {
    "NO_KILL": re.compile(r"\bno (kill|frag)\b|nothing happ|no shot|nothing here", re.I),
    "NOT_ME": re.compile(r"\bnot me\b|someone else|spec(c|ing)|swapping", re.I),
    "WRONG_WEAPON": re.compile(r"just (a )?rail|not sure splash|just a shaft|just .* kill", re.I),
    "SEEN": re.compile(r"\bseen\b|already", re.I),
    "MODIFIER_ONLY": re.compile(r"if not with other|only with|filler|combined", re.I),
}
note_flags = {t: {f: sum(1 for x in xs if rx.search(x)) for f, rx in FLAGS.items()}
              for t, xs in notes.items()}

# ── demos in scope ─────────────────────────────────────────────────────────
fr = ro(FR)
demos = {}
for r in fr.execute("SELECT content_hash, name, gametype, recorder_client, "
                    "size_bytes, map_name FROM demos WHERE duplicate_of IS NULL "
                    "AND path IS NOT NULL"):
    demos[r["content_hash"]] = dict(r)
fr.close()

rec = ro(REC)
scope = [h for h, d in demos.items()
         if (d["gametype"] or "").upper() == "CA" and d["recorder_client"] is not None
         and (d["size_bytes"] or 0) >= MIN_BYTES]
out_of_scope = collections.Counter(
    "not_CA" if (d["gametype"] or "").upper() != "CA" else
    "no_recorder" if d["recorder_client"] is None else "under_512KB"
    for h, d in demos.items() if h not in set(scope))
if LIMIT:
    scope = scope[:LIMIT]
scope_set = set(scope)
print("CA demos in scope: %d  (out of scope: %s)" % (len(scope), dict(out_of_scope)),
      flush=True)

# ── bulk reads ─────────────────────────────────────────────────────────────
rs = collections.defaultdict(list)
for r in rec.execute("SELECT content_hash, server_time_ms, cs, value FROM "
                     "round_state_v1 WHERE cs IN (661, 662) ORDER BY "
                     "content_hash, server_time_ms"):
    if r["content_hash"] in scope_set:
        rs[r["content_hash"]].append((r["server_time_ms"], r["cs"], norm(r["value"])))

demo_end = {}
for r in rec.execute("SELECT content_hash, MAX(server_time_ms) m FROM "
                     "gamestate_facts_v2 WHERE fact='DEMO_END' GROUP BY 1"):
    demo_end[r["content_hash"]] = r["m"]
last_seen = collections.defaultdict(int)
for r in rec.execute("SELECT content_hash, MAX(server_time_ms) m FROM "
                     "round_state_v1 GROUP BY 1"):
    last_seen[r["content_hash"]] = max(last_seen[r["content_hash"]], r["m"] or 0)

kills = collections.defaultdict(list)     # recorder's kills
deaths = collections.defaultdict(list)    # recorder's deaths
for r in rec.execute("SELECT content_hash, server_time_ms, mod_name, victim_client, "
                     "killer_client, is_recorder_killer, is_recorder_victim "
                     "FROM kill_events_v1 WHERE is_best_observation=1"):
    h = r["content_hash"]
    if h not in scope_set:
        continue
    last_seen[h] = max(last_seen[h], r["server_time_ms"])
    if r["is_recorder_killer"]:
        kills[h].append(r)
    if r["is_recorder_victim"]:
        deaths[h].append(r["server_time_ms"])

traits_at = collections.defaultdict(list)  # (hash, ms) -> recognised classes
frag_meta = {}
for r in rec.execute("SELECT id, content_hash, server_time_ms, classes, weapon_name "
                     "FROM recognized_frags WHERE classes IS NOT NULL"):
    if r["content_hash"] not in scope_set:
        continue
    try:
        cls = json.loads(r["classes"] or "[]")
    except (TypeError, ValueError):
        continue
    names = [c.get("name") if isinstance(c, dict) else str(c) for c in cls]
    traits_at[(r["content_hash"], r["server_time_ms"])].extend(n for n in names if n)
    frag_meta[(r["content_hash"], r["server_time_ms"])] = (r["id"], r["weapon_name"])

shapes_at = collections.defaultdict(list)
try:
    sh = ro(SH)
    for r in sh.execute("SELECT content_hash, server_time_ms, shape, actor FROM frag_shapes_v1"):
        h = r["content_hash"]
        if h in scope_set and r["actor"] == demos[h]["recorder_client"]:
            shapes_at[(h, r["server_time_ms"])].append(r["shape"])
except sqlite3.Error:
    pass


# ── rounds ─────────────────────────────────────────────────────────────────
def rounds_for(h):
    """Collapse repeated configstrings; one entry per announced round."""
    out, cur = [], None
    for t, cs, v in rs.get(h, ()):
        if cs == 661:
            m = re.search(r"round\\(-?\d+)", v)
            st = re.search(r"time\\(-?\d+)", v)
            if not m or int(m.group(1)) <= 0:
                continue
            n = int(m.group(1))
            if cur and cur["round"] == n:
                continue
            cur = {"round": n, "announce": t,
                   "scheduled": int(st.group(1)) if st else None,
                   "fight": None, "end": None}
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
    dend = demo_end.get(h) or last_seen.get(h) or 0
    rlist = rounds_for(h)
    if not rlist:
        quarantine["NO_ROUND_CONFIGSTRINGS"] += 1
        continue
    for i, r in enumerate(rlist):
        nxt = rlist[i + 1]["announce"] if i + 1 < len(rlist) else None
        fight = r["fight"] or r["scheduled"]
        if fight is None:
            quarantine["NO_FIGHT_START"] += 1
            continue
        if r["announce"] > fight:
            quarantine["ANNOUNCE_AFTER_FIGHT"] += 1
            continue
        start = max(r["announce"], fight - COUNTDOWN_LEAD_MS)
        caps = [x for x in (nxt, dend) if x]
        round_end = (r["end"] + END_GRACE_MS) if r["end"] else None
        hard_end = min([x for x in (round_end, *caps) if x] or [dend])
        if hard_end <= fight:
            quarantine["END_BEFORE_FIGHT"] += 1
            continue
        died = [t for t in deaths.get(h, ()) if fight <= t <= hard_end]
        if died:
            end = min(min(died) + DEATH_TAIL_MS, hard_end)
            reason = "RECORDER_DEATH"
        elif round_end and round_end == hard_end:
            end, reason = hard_end, "ROUND_END"
        elif nxt and nxt == hard_end:
            end, reason = hard_end, "NEXT_ROUND_ANNOUNCED"
        else:
            end, reason = hard_end, "DEMO_END"

        # every recorder action inside the window
        moments = []
        for k in kills.get(h, ()):
            t = k["server_time_ms"]
            if not (fight <= t <= end):
                continue
            names = list(dict.fromkeys(traits_at.get((h, t), []) + shapes_at.get((h, t), [])))
            best = {}
            for nm in names:
                val, pol = trait_value(nm)
                fam = family_of.get(nm, "trait:" + nm)
                if fam not in best or val > best[fam][0]:
                    best[fam] = (val, pol, nm)
            # SUPPORT TRAITS ARE MODIFIERS, NOT HEADLINES (user review:
            # "drop if not with other traits", weak traits become modifiers).
            # Calibration shrinks every trait toward the global mean, so a
            # support trait was worth ~49 against ~55-62 for a hero trait, and
            # three of them in different families outscored a real hero moment:
            # the #1 round was 1012 points on two kills of DODGE_AND_KILL +
            # FAST_WEAPON_SWITCH + ESCAPE_TURNAROUND. Now a moment is worth its
            # strongest hero trait, plus 15% of each support trait (capped at
            # three), and a moment with no hero trait at all counts 25%.
            heroes = sorted((v for v, p, _ in best.values() if p == "hero" and v > 0),
                            reverse=True)
            supports = sorted((v for v, p, _ in best.values() if p == "support" and v > 0),
                              reverse=True)[:3]
            if heroes:
                total = heroes[0] + 0.35 * sum(heroes[1:3]) + 0.15 * sum(supports)
            else:
                total = 0.25 * (supports[0] if supports else 0.0) + 0.05 * sum(supports[1:])
            moments.append({
                "t": t, "weapon": k["mod_name"], "traits": names,
                "value": round(total, 2),
                "hero": any(p == "hero" and v > 0 for v, p, _ in best.values()),
                "frag_id": (frag_meta.get((h, t)) or (None,))[0]})
        # shapes that are not kills (e.g. recorder-owned action shapes)
        vals = sorted((m["value"] for m in moments), reverse=True)
        score = sum(w * v for w, v in zip(TOP_MOMENT_WEIGHTS, vals))
        weapons = collections.Counter(
            (m["weapon"] or "UNKNOWN").replace("_SPLASH", "") for m in moments)
        lane = ("NONE" if not weapons else
                weapons.most_common(1)[0][0] if len(weapons) == 1 or
                weapons.most_common(1)[0][1] > sum(weapons.values()) / 2
                else "MULTI_WEAPON")
        units.append({
            "content_hash": h, "demo_name": d["name"], "map": d["map_name"],
            "gametype": "CA", "round": r["round"],
            "start_ms": start, "fight_ms": fight, "end_ms": end,
            "countdown_lead_ms": fight - start, "end_reason": reason,
            "partial": reason == "DEMO_END",
            "kills": len(moments), "has_hero": any(m["hero"] for m in moments),
            "score": round(score, 2), "lane": lane,
            "weapons": dict(weapons),
            "traits": sorted({n for m in moments for n in m["traits"]}),
            "moments": moments})

# ── roles: from the score distribution, never a flat default ───────────────
scored = sorted((u for u in units if u["kills"]), key=lambda u: -u["score"])
n = len(scored)
for i, u in enumerate(scored):
    q = i / max(n, 1)
    if u["has_hero"] and q < 0.05:
        u["role"] = "HERO_ROUND"
    elif q < 0.20 and u["score"] > 0:
        u["role"] = "STRONG_ROUND"
    elif q < 0.50 and u["score"] > 0:
        u["role"] = "FILLER_ROUND"
    elif u["score"] > 0:
        u["role"] = "TRANSITION_OR_BLOOPER"
    else:
        u["role"] = "LOW_VALUE"
for u in units:
    u.setdefault("role", "NO_RECORDER_ACTION")

lane_rank = collections.defaultdict(int)
ordered = sorted(units, key=lambda u: (u["gametype"], u["lane"], -u["score"]))
for u in ordered:
    lane_rank[u["lane"]] += 1
    u["lane_rank"] = lane_rank[u["lane"]]

# ── outputs ────────────────────────────────────────────────────────────────
best = sorted(units, key=lambda u: -u["score"])
with open(HERE / "rounds_ranked.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["rank", "role", "score", "lane", "lane_rank", "kills", "has_hero",
                "end_reason", "countdown_lead_ms", "start_ms", "fight_ms", "end_ms",
                "round", "map", "demo_name", "traits"])
    for i, u in enumerate(best, 1):
        w.writerow([i, u["role"], u["score"], u["lane"], u["lane_rank"], u["kills"],
                    u["has_hero"], u["end_reason"], u["countdown_lead_ms"],
                    u["start_ms"], u["fight_ms"], u["end_ms"], u["round"], u["map"],
                    u["demo_name"], " | ".join(u["traits"])])
(HERE / "rounds_ranked.json").write_text(json.dumps(best, indent=1), encoding="utf-8")

trait_rows = []
for t in sorted(set(policy_of) | set(tw)):
    val, pol = trait_value(t)
    trait_rows.append({
        "trait": t, "policy": pol, "weight": round(val, 2),
        "rated_n": (tw.get(t) or {}).get("rated_n", 0),
        "raw_mean": round((tw.get(t) or {}).get("raw_mean", 0) or 0, 2),
        "rounds_with_trait": sum(1 for u in units if t in u["traits"]),
        "notes": len(notes.get(t, [])),
        **{"flag_" + k.lower(): v for k, v in note_flags.get(t, {}).items()},
        "sample_notes": " || ".join(notes.get(t, [])[:3])})
trait_rows.sort(key=lambda r: ({"hero": 0, "support": 1}.get(r["policy"], 2), -r["weight"]))
with open(HERE / "traits_ranked.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(trait_rows[0]))
    w.writeheader()
    w.writerows(trait_rows)

roles = collections.Counter(u["role"] for u in units)
ends = collections.Counter(u["end_reason"] for u in units)
lanes = collections.Counter(u["lane"] for u in units if u["kills"])
summary = {
    "demos_in_scope": len(scope), "out_of_scope": dict(out_of_scope),
    "rounds_built": len(units), "quarantined": dict(quarantine),
    "rounds_with_recorder_kills": n, "roles": dict(roles),
    "end_reasons": dict(ends), "lanes": dict(lanes),
    "countdown_lead_exact_5s": sum(1 for u in units if u["countdown_lead_ms"] == 5000),
    "calibration_hash": model.get("calibration_hash"),
}
(HERE / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
print(json.dumps(summary, indent=1))
