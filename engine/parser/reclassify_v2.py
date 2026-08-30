"""Taxonomy v2 as a RECLASSIFICATION pass over cached recognition rows.

Hard rule (user, 2026-08-30): never full-rescan the corpus for taxonomy
changes. This pass derives every v2 label computable from persisted v1
attributes + existing databases/CSVs, updates rows in place, and exports
mode-weighted top lists. Runtime: seconds-to-minutes, zero demo IO.

Adds from cache:
  attacker/victim speed percentiles + FAST/VERY_FAST/EXTREME_SPEED labels
  SPEED_TARGET_FRAG · RAPID_MULTIKILL (chain kills/s) · stationary penalty
  CLUTCH_1V2/1V3/1V4_PLUS (clutch_recorder.csv join by hash + time window)
  mode split MAIN_CA / SIDE_DUEL / SIDE_OTHER (demos.gametype join)
Genuinely missing (needs targeted extraction, NOT here): recorder
health/armor, view-angle timeseries, LG tick series, projectile paths,
LOS/visibility geometry (stage-2 handles candidates).
"""
from __future__ import annotations

import csv
import json
import re
import sqlite3
from bisect import bisect_left
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RECOG_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"
FRAGS_DB = REPO_ROOT / "creative_suite" / "database" / "frags_rebuilt.db"
CLUTCH_CSV = REPO_ROOT / "output" / "clutch_recorder.csv"
NORMS = REPO_ROOT / "output" / "demo_v2" / "recognition" / "norms.json"
OUT_DIR = REPO_ROOT / "output" / "demo_v2" / "recognition"

CHAIN_GAP_MS = 3000
RECLASS_MARK = "db_reclass_v2"

# Reasons this module appends (stripped before every recompute so the pass
# is IDEMPOTENT — running twice must not double scores; the original
# implementation double-added on rerun, repaired 2026-08-30).
_REASON_RE = re.compile(
    r"^([+-] (extreme-speed p|very-fast p|high-speed p|fast target p|"
    r"stationary target|rapid chain |1v\d clutch |near-death |critical |"
    r"low hp |survived \d+dmg burst|true flick |extreme flick |clean flick |"
    r"tracking sweep |aim transition |clean snap|geo direct |geo near-direct |"
    r"air rocket geo |temporal prediction |rarity|pixel shot |tiny gap |"
    r"reaction |corner prefire |"
    r"lg pressure |lg dodge |damage burst ))")

# Legacy weights of the two buggy runs (for the one-time score repair).
_OLD_HEALTH = {"near": 10, "crit": 6, "low": 3, "ctx": 0.5, "burst": 2}


def pctile(sorted_vals: list[float], v: float) -> float:
    if not sorted_vals:
        return 0.0
    return round(100.0 * bisect_left(sorted_vals, v) / len(sorted_vals), 1)


def load_norm_samples(conn) -> dict[str, list[float]]:
    """Percentile bases from the cached rows themselves (sorted samples)."""
    ks, vs = [], []
    for (attrs,) in conn.execute("SELECT attributes FROM recognized_frags"):
        a = json.loads(attrs or "{}")
        if a.get("killer_speed") is not None:
            ks.append(float(a["killer_speed"]))
        if a.get("victim_speed") is not None:
            vs.append(float(a["victim_speed"]))
    return {"killer_speed": sorted(ks), "victim_speed": sorted(vs)}


def mode_of(gametype: str | None) -> str:
    g = (gametype or "").upper()
    if "CLAN" in g or g == "CA":
        return "MAIN_CA"
    if "DUEL" in g:
        return "SIDE_DUEL"
    return "SIDE_OTHER"


def run() -> dict:
    conn = sqlite3.connect(RECOG_DB)
    conn.row_factory = sqlite3.Row

    fconn = sqlite3.connect(f"file:{FRAGS_DB}?mode=ro", uri=True)
    demo_meta = {name: (gt, dup or h) for name, gt, h, dup in fconn.execute(
        "SELECT name, gametype, content_hash, duplicate_of FROM demos")}
    fconn.close()

    clutches: dict[str, list[dict]] = {}
    with open(CLUTCH_CSV, newline="", encoding="utf-8") as f:
        for c in csv.DictReader(f):
            clutches.setdefault(c["canonical_demo_hash"], []).append(c)

    samples = load_norm_samples(conn)

    # stage-2 geometric visibility (own table; merged into attributes here)
    stage2: dict[tuple, dict] = {}
    try:
        for row in conn.execute("SELECT * FROM stage2_visibility"):
            d = dict(zip([c[0] for c in conn.execute(
                "SELECT * FROM stage2_visibility LIMIT 0").description], row))
            key = (d.get("demo_name"), d.get("server_time_ms"))
            stage2[key] = d
    except sqlite3.OperationalError:
        pass  # table not built yet

    # label archive frequencies for rarity (first pass, read-only)
    from collections import Counter
    label_freq: Counter = Counter()
    total_rows = 0
    for (cl,) in conn.execute("SELECT classes FROM recognized_frags"):
        total_rows += 1
        for x in json.loads(cl or "[]"):
            label_freq[x["name"] if isinstance(x, dict) else x] += 1
    rows = [dict(r) for r in conn.execute(
        "SELECT id, demo_name, server_time_ms, classes, attributes, reasons,"
        " speed_score, movement_score, clutch_score, drama_score,"
        " penalty_score, highlight_score, multikill_score"
        " FROM recognized_frags")]

    # chain grouping per demo for kills/s
    by_demo: dict[str, list[dict]] = {}
    for r in rows:
        by_demo.setdefault(r["demo_name"], []).append(r)
    chain_kps: dict[int, float] = {}
    chain_len: dict[int, int] = {}
    for demo, rs in by_demo.items():
        rs.sort(key=lambda r: r["server_time_ms"])
        i = 0
        while i < len(rs):
            j = i
            while (j + 1 < len(rs) and
                   rs[j + 1]["server_time_ms"] - rs[j]["server_time_ms"]
                   <= CHAIN_GAP_MS):
                j += 1
            n = j - i + 1
            dur_s = max(0.5, (rs[j]["server_time_ms"]
                              - rs[i]["server_time_ms"]) / 1000.0)
            for k in range(i, j + 1):
                chain_len[rs[k]["id"]] = n
                chain_kps[rs[k]["id"]] = n / dur_s if n > 1 else 0.0
            i = j + 1

    stats = {"reused": len(rows), "labels_added": 0, "ca": 0, "duel": 0,
             "other": 0, "clutch_labeled": 0, "repaired_legacy": 0}
    up = []
    for r in rows:
        a = json.loads(r["attributes"] or "{}")
        classes = json.loads(r["classes"] or "[]")
        reasons = json.loads(r["reasons"] or "[]")

        # ── idempotency: remove everything this module added previously ──
        classes = [c for c in classes
                   if not (isinstance(c, dict)
                           and c.get("source") == RECLASS_MARK)]
        reasons = [x for x in reasons if not _REASON_RE.match(x)]
        prev = a.pop("_reclass_delta", None)
        if prev is not None:
            r["speed_score"] = (r["speed_score"] or 0) - prev.get("speed", 0)
            r["movement_score"] = (r["movement_score"] or 0) - prev.get("move", 0)
            r["clutch_score"] = (r["clutch_score"] or 0) - prev.get("clutch", 0)
            r["drama_score"] = (r["drama_score"] or 0) - prev.get("drama", 0)
            r["penalty_score"] = (r["penalty_score"] or 0) - prev.get("pen", 0)
            r["highlight_score"] = (r["highlight_score"] or 0) - prev.get("total", 0)

        have = {c["name"] if isinstance(c, dict) else c for c in classes}
        add_speed = add_move = add_clutch = add_drama = 0.0
        add_pen = 0.0

        def add(name, conf, detail=""):
            if name in have:
                return
            classes.append({"name": name, "confidence": conf,
                            "detail": detail, "source": RECLASS_MARK})
            have.add(name)
            stats["labels_added"] += 1

        gt, h = demo_meta.get(r["demo_name"], (None, None))
        mode = mode_of(gt)
        a["mode_pool"] = mode
        stats[{"MAIN_CA": "ca", "SIDE_DUEL": "duel",
               "SIDE_OTHER": "other"}[mode]] += 1

        ks = a.get("killer_speed")
        if ks is not None:
            p = pctile(samples["killer_speed"], float(ks))
            a["attacker_speed_percentile"] = p
            if p >= 99:
                add("EXTREME_SPEED", "CONFIRMED", f"p{p}")
                add_speed += 14
                reasons.append(f"+ extreme-speed p{p} (+14)")
            elif p >= 97:
                add("VERY_FAST_FRAG", "CONFIRMED", f"p{p}")
                add_speed += 8
                reasons.append(f"+ very-fast p{p} (+8)")
            elif p >= 90:
                add("HIGH_SPEED_FRAG", "CONFIRMED", f"p{p}")
                add_speed += 4
                reasons.append(f"+ high-speed p{p} (+4)")
        vs = a.get("victim_speed")
        if vs is not None:
            pv = pctile(samples["victim_speed"], float(vs))
            a["victim_speed_percentile"] = pv
            if pv >= 97:
                add("SPEED_TARGET_FRAG", "CONFIRMED", f"victim p{pv}")
                add_move += 5
                reasons.append(f"+ fast target p{pv} (+5)")
            elif float(vs) < 40:
                add_pen -= 3
                reasons.append("- stationary target (-3)")

        kps = chain_kps.get(r["id"], 0.0)
        if kps >= 1.5 and chain_len.get(r["id"], 1) >= 3:
            add("RAPID_MULTIKILL", "CONFIRMED",
                f"{chain_len[r['id']]} kills @ {kps:.1f}/s")
            add_move += 6
            reasons.append(f"+ rapid chain {kps:.1f} kills/s (+6)")

        if h and h in clutches:
            t = r["server_time_ms"]
            for c in clutches[h]:
                if int(c["clutch_start_ms"]) <= t <= int(c["clutch_end_ms"]):
                    n = int(c["enemies_alive_at_start"])
                    label = ("CLUTCH_1V4_PLUS" if n >= 4 else
                             "CLUTCH_1V3" if n == 3 else
                             "CLUTCH_1V2" if n == 2 else None)
                    if label:
                        add(label, "CONFIRMED", f"1v{n} {c['outcome']}")
                        add_clutch += 6 + 4 * (n - 2)
                        add_drama += 3
                        reasons.append(f"+ 1v{n} clutch (+{6 + 4*(n-2)})")
                        stats["clutch_labeled"] += 1
                    break

        # true-aim quality (targeted view timeseries; complete movement curve)
        fd = a.get("flick_deg_v2", a.get("flick_true_deg"))
        if fd is not None:
            fms = a.get("flick_ms_v2", a.get("flick_true_ms")) or 0
            dps = a.get("flick_dps_v2", a.get("flick_peak_dps")) or 0
            settle = a.get("settle_deg")
            rev = a.get("flick_reversals")
            # a flick ENDS at the shot, so final-100ms stillness is the wrong
            # cleanliness test; low reversal count = clean snap
            clean = rev is not None and rev <= 1
            # physical sanity: >2500 deg/s smoothed or >250deg net is a
            # teleport/respawn view snap, not aim
            humanly = (dps or 0) <= 2500 and fd <= 250
            clean = clean and humanly
            # label contract: EXTREME_FLICK is a strict SUBSET of
            # CLEAN_FLICK (both always applied together).
            if fd >= 90 and fms <= 350 and dps >= 350 and clean:
                add("CLEAN_FLICK", "CONFIRMED", f"{fd}deg/{fms}ms")
                add("EXTREME_FLICK", "CONFIRMED",
                    f"{fd}deg/{fms}ms peak {dps}dps rev {rev}")
                add_move += 9
                reasons.append(f"+ extreme flick {fd}deg @ {dps}dps (+9)")
            elif fd >= 50 and fms <= 300 and clean:
                add("CLEAN_FLICK", "CONFIRMED",
                    f"{fd}deg/{fms}ms rev {rev}")
                add_move += 4
                reasons.append(f"+ clean flick {fd}deg/{fms}ms (+4)")
            elif fd >= 80 and fms >= 400 and humanly and (rev or 0) <= 3:
                # impressive aim that is NOT a snap: sustained engaged sweep
                # (the honest home of the downgraded 106deg event)
                add("AGGRESSIVE_TRACKING_SWEEP", "CONFIRMED",
                    f"{fd}deg over {fms}ms, rev {rev}")
                add_move += 4
                reasons.append(f"+ tracking sweep {fd}deg/{fms}ms (+4)")
            elif fd >= 120 and humanly:
                add("LARGE_AIM_TRANSITION", "HIGH", f"{fd}deg/{fms}ms")
                add_move += 2
                reasons.append(f"+ aim transition {fd}deg (+2)")
            if fd >= 80 and humanly and                     (a.get("attacker_speed_percentile") or 0) >= 90:
                add("HIGH_SPEED_AIM_TRANSITION", "CONFIRMED",
                    f"{fd}deg at p{a.get('attacker_speed_percentile')}")
            if clean and (rev == 0) and fd >= 40:
                add_move += 2
                reasons.append("+ clean snap (+2)")

        # LG engagement labels (targeted LG extraction; damage-flow model)
        cr = a.get("lg_contact_rate")
        if cr is not None:
            if cr >= 2.0:
                add("LG_HIGH_PRESSURE", "CONFIRMED", f"{cr}/s contact")
                add_move += 5
                reasons.append(f"+ lg pressure {cr}/s (+5)")
            dr = a.get("lg_dodge_rating") or 0
            inr = a.get("lg_incoming_hit_ratio")
            ticks = a.get("lg_incoming_fire_ticks") or 0
            if dr >= 20 and ticks >= 60 and (inr is not None and inr <= 0.10):
                add("LG_DODGE_MASTER", "CONFIRMED",
                    f"rating {dr}, ate {inr:.0%} of {ticks} ticks")
                add_move += 7
                reasons.append(f"+ lg dodge {inr:.0%}/{ticks}t (+7)")
            burst = a.get("lg_damage_burst_3s") or 0
            if burst >= 100:   # ~p99 of bucket-floor distribution
                add("DAMAGE_BURST", "CONFIRMED", f"{burst}dmg/3s")
                add_move += 4
                reasons.append(f"+ damage burst {burst}/3s (+4)")

        # projectile geometry labels (targeted reconstruction cache)
        pg = a.get("projectile_direct_geometry")
        if pg == "DIRECT_CONFIRMED":
            add("DIRECT_CONFIRMED_GEO", "CONFIRMED",
                f"expansion {a.get('projectile_direct_expansion_u')}u")
            add_move += 6
            reasons.append("+ geo direct (body hit) (+6)")
        elif pg in ("DIRECT_LIKELY", "NEAR_DIRECT"):
            add("NEAR_DIRECT", "HIGH",
                f"expansion {a.get('projectile_direct_expansion_u')}u")
            add_move += 3
            reasons.append("+ geo near-direct (+3)")
        if (a.get("projectile_victim_airborne")
                and abs(a.get("projectile_victim_vertical_speed") or 0) >= 250):
            add("AIR_ROCKET_GEO", "CONFIRMED",
                f"victim vz {a.get('projectile_victim_vertical_speed')}")
            add_move += 5
            reasons.append(
                f"+ air rocket geo (vz {a.get('projectile_victim_vertical_speed')}) (+5)")
        if ((a.get("victim_travel_during_flight") or 0) >= 300
                and (a.get("projectile_flight_ms") or 0) >= 600):
            add("PREDICTION_TEMPORAL", "HIGH",
                f"{a.get('victim_travel_during_flight')}u during "
                f"{a.get('projectile_flight_ms')}ms flight")
            add_move += 4
            reasons.append("+ temporal prediction (+4)")

        # stage-2 pixel/visibility evidence
        s2 = stage2.get((r["demo_name"], r["server_time_ms"]))
        if s2:
            for k in ("visible_fraction", "los_open_duration_ms",
                      "angular_size_deg", "corner_prefire"):
                if s2.get(k) is not None:
                    a["los_" + k if not k.startswith("los") else k] = s2[k]
            vf = s2.get("visible_fraction")
            ang = s2.get("angular_size_deg")
            los = s2.get("los_open_duration_ms")
            if vf is not None and 0 < vf <= 0.25 and (ang or 99) <= 3.0:
                add("PIXEL_SHOT_GEO", "HIGH",   # render proof upgrades to CONFIRMED
                    f"visible {vf:.0%}, {ang}deg target")
                add_move += 8
                reasons.append(f"+ pixel shot {vf:.0%} exposure (+8)")
                if vf <= 0.12:
                    add("TINY_GAP_SHOT", "CONFIRMED", f"visible {vf:.0%}")
                    add_move += 3
                    reasons.append(f"+ tiny gap {vf:.0%} (+3)")
            if (los is not None and los <= 250 and (vf or 0) >= 0.5):
                add("REACTION_SHOT", "CONFIRMED", f"LOS open {los}ms")
                add_move += 5
                reasons.append(f"+ reaction {los}ms LOS (+5)")
            if s2.get("corner_prefire"):
                add("CORNER_PREFIRE_CONFIRMED", "CONFIRMED",
                    "hidden at t-200ms, visible at kill")
                add_move += 4
                reasons.append("+ corner prefire (+4)")

        # rarity: multi-dimensional archive-relative scarcity (small,
        # additive; never replaces skill evidence)
        rare = sum(1 for x in have
                   if 0 < label_freq.get(x, 0) <= total_rows * 0.002)
        semi = sum(1 for x in have
                   if total_rows * 0.002 < label_freq.get(x, 0)
                   <= total_rows * 0.01)
        rarity = min(8.0, rare * 3.0 + semi * 1.0)
        if rarity >= 3.0:
            add_move += rarity
            reasons.append(f"+ rarity({rare}x ultra,{semi}x rare) (+{rarity})")

        # health drama (targeted extraction; context-weighted: the same HP
        # means more with more enemies alive — mandate: 20HP cleanup != 20HP 1v3)
        h = a.get("health_at_frag")
        if h is not None:
            enemies = 1
            if "CLUTCH_1V4_PLUS" in have:
                enemies = 4
            elif "CLUTCH_1V3" in have:
                enemies = 3
            elif "CLUTCH_1V2" in have:
                enemies = 2
            ctx = 1.0 + 0.25 * (enemies - 1)
            if h <= 5:
                add("LAST_HP_CANDIDATE", "CONFIRMED", f"{h}hp")
                bonus = round(5 * ctx, 1)
                add_drama += bonus
                reasons.append(f"+ near-death {h}hp x1v{enemies} (+{bonus})")
            elif h <= 15:
                add("CRITICAL_HP_FRAG", "CONFIRMED", f"{h}hp")
                bonus = round(1.5 * ctx, 1)
                add_drama += bonus
                reasons.append(f"+ critical {h}hp x1v{enemies} (+{bonus})")
            elif h <= 35:
                add("LOW_HP_FRAG", "CONFIRMED", f"{h}hp")
                bonus = round(1.5 * ctx, 1)
                add_drama += bonus
                reasons.append(f"+ low hp {h} x1v{enemies} (+{bonus})")
            drop = a.get("biggest_drop_10s") or 0
            if drop >= 60:
                add("HEAVY_DAMAGE_SURVIVED", "CONFIRMED", f"-{drop}hp burst")
                add_drama += 1
                reasons.append(f"+ survived {drop}dmg burst (+1)")

        # ── one-time legacy repair: the first two (non-idempotent) runs
        # added the non-health delta TWICE and the old-weight health delta
        # once, with nothing recorded. Reconstruct deterministically from
        # the same attributes and subtract, recovering the v1 base. ──
        if prev is None:
            legacy_h = 0.0
            hh = a.get("health_at_frag")
            if hh is not None:
                en = (4 if "CLUTCH_1V4_PLUS" in have else
                      3 if "CLUTCH_1V3" in have else
                      2 if "CLUTCH_1V2" in have else 1)
                octx = 1.0 + _OLD_HEALTH["ctx"] * (en - 1)
                if hh <= 5:
                    legacy_h += round(_OLD_HEALTH["near"] * octx, 1)
                elif hh <= 15:
                    legacy_h += round(_OLD_HEALTH["crit"] * octx, 1)
                elif hh <= 35:
                    legacy_h += round(_OLD_HEALTH["low"] * octx, 1)
                if (a.get("biggest_drop_10s") or 0) >= 60:
                    legacy_h += _OLD_HEALTH["burst"]
            nonhealth = add_speed + add_move + add_clutch + add_pen                 + (3.0 if (add_clutch > 0) else 0.0)  # old clutch drama +3
            r["speed_score"] = (r["speed_score"] or 0) - 2 * add_speed
            r["movement_score"] = (r["movement_score"] or 0) - 2 * add_move
            r["clutch_score"] = (r["clutch_score"] or 0) - 2 * add_clutch
            r["drama_score"] = ((r["drama_score"] or 0)
                                - 2 * (3.0 if add_clutch > 0 else 0.0)
                                - (0.0 if hh is None else legacy_h))
            r["penalty_score"] = (r["penalty_score"] or 0) - 2 * add_pen
            r["highlight_score"] = ((r["highlight_score"] or 0)
                                    - 2 * nonhealth - legacy_h)
            stats["repaired_legacy"] += 1

        delta = add_speed + add_move + add_clutch + add_drama + add_pen
        a["_reclass_delta"] = {"speed": add_speed, "move": add_move,
                               "clutch": add_clutch, "drama": add_drama,
                               "pen": add_pen, "total": delta}
        up.append((json.dumps(classes), json.dumps(a), json.dumps(reasons),
                   (r["speed_score"] or 0) + add_speed,
                   (r["movement_score"] or 0) + add_move,
                   (r["clutch_score"] or 0) + add_clutch,
                   (r["drama_score"] or 0) + add_drama,
                   (r["penalty_score"] or 0) + add_pen,
                   (r["highlight_score"] or 0) + delta,
                   2, r["id"]))

    conn.executemany(
        "UPDATE recognized_frags SET classes=?, attributes=?, reasons=?,"
        " speed_score=?, movement_score=?, clutch_score=?, drama_score=?,"
        " penalty_score=?, highlight_score=?, recognition_version=?"
        " WHERE id=?", up)
    conn.commit()

    # mode-weighted top lists (match-group dedup via canonical hash grouping)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    conn.row_factory = sqlite3.Row
    all_rows = [dict(r) for r in conn.execute(
        "SELECT demo_name, server_time_ms, weapon_name, classes, attributes,"
        " highlight_score, reasons FROM recognized_frags"
        " ORDER BY highlight_score DESC")]
    pools = {"top_overall_ca": [], "top_duel": [], "top_other": []}
    seen_moments = set()
    for r in all_rows:
        a = json.loads(r["attributes"] or "{}")
        gt, h = demo_meta.get(r["demo_name"], (None, None))
        key = (h, r["server_time_ms"])
        if key in seen_moments:
            continue
        seen_moments.add(key)
        pool = {"MAIN_CA": "top_overall_ca", "SIDE_DUEL": "top_duel",
                "SIDE_OTHER": "top_other"}[a.get("mode_pool", "SIDE_OTHER")]
        if len(pools[pool]) < 100:
            pools[pool].append(r)
    for name, rs in pools.items():
        with open(OUT_DIR / f"{name}.csv", "w", newline="",
                  encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["rank", "score", "demo", "server_time_ms", "weapon",
                        "classes", "reasons"])
            for i, r in enumerate(rs, 1):
                cl = [c["name"] if isinstance(c, dict) else c
                      for c in json.loads(r["classes"] or "[]")]
                w.writerow([i, r["highlight_score"], r["demo_name"],
                            r["server_time_ms"], r["weapon_name"],
                            "|".join(cl),
                            " ".join(json.loads(r["reasons"] or "[]"))])
    conn.close()
    stats["pools"] = {k: len(v) for k, v in pools.items()}
    return stats


if __name__ == "__main__":
    import time
    t0 = time.time()
    s = run()
    print(json.dumps(s, indent=1))
    print(f"elapsed {time.time() - t0:.1f}s")
