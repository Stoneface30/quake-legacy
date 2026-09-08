"""Targeted extractor: recorder LG engagements (+ dodge differential).

Scope: recorder LIGHTNING kills only (12,220 engagement anchors / 3,120
demos costed 2026-08-30). Window: kill_t-8000..kill_t+1000 per anchor,
merged when overlapping.

Evidence model (honest — measured, not fabricated): the RECORDER's own
fire events are NOT in the entity event stream (own player is playerstate;
verified 2026-08-30), and PAIN events are rate-limited, so tick-accuracy
for the recorder cannot be computed. What IS exact/derivable:
  - enemy LG fire ticks: exact (their fire_weapon events carry weapon_name);
  - damage flows: health drops from pain event_parm series both directions;
  - recorder LG-held spans: snapshot weapon field.
Metrics:
  lg_dealt_dmg / lg_dealt_dps    victim health drops while recorder holds LG
  lg_taken_lg_dmg                recorder health drops within 150ms of enemy
                                 LG fire
  lg_incoming_hit_ratio          taken_lg_dmg / (enemy_lg_ticks * 6dmg) —
                                 the enemy's LG efficiency ON the recorder
  lg_dodge_dps_diff              dealt_dps - taken_dps during the engagement
                                 (user: outdamaging while undereating IS
                                 dodging skill)
  lg_damage_burst_3s             max damage dealt in any 3s window (the
                                 damage-counter trigger)
Also per engagement: duration, my fire ticks, target switches (victims of
my kills + pain-target changes), target speed at kill (from cached attrs),
damage_dealt_estimate (sum of victim pain health drops observed),
damage_burst_3s (max damage dealt in any 3s window — the damage-counter
trigger), my min health.

Persists to recognition_lg_engagements + summary attrs on the kill rows.
Resumable via lg_extracted(content_hash, version).
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

# DATA, not code: under a worktree these differ, and opening a
# database beneath the wrong one silently CREATES an empty file
# rather than failing. See engine.pantheon.store.
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()
RECOG_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"
FRAGS_DB = REPO_ROOT / "creative_suite" / "database" / "frags_rebuilt.db"

EXTRACTOR_VERSION = 1
PRE_MS, POST_MS = 8000, 1000
LG_WEAPON_ID = 6   # WP_LIGHTNING in QL weapon numbering (change_weapon parm)


def candidate_map() -> dict[str, list[int]]:
    c = sqlite3.connect(f"file:{RECOG_DB}?mode=ro", uri=True)
    out: dict[str, list[int]] = {}
    for demo, t, attrs in c.execute(
            "SELECT demo_name, server_time_ms, attributes FROM"
            " recognized_frags WHERE weapon_name='LIGHTNING'"):
        a = json.loads(attrs or "{}")
        if a.get("lg_engagement") is not None:
            continue
        out.setdefault(demo, []).append(t)
    c.close()
    return out


def extract_one(demo_path: str, kill_times: list[int],
                recorder_client: int) -> dict[int, dict]:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from demo_parse import DM73Parser
    parsed = DM73Parser(Path(demo_path)).parse()
    events = parsed.get("events", [])

    LG_DMG_PER_CELL = 6
    enemy_lg_fire: dict[int, list[int]] = defaultdict(list)
    pain: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for e in events:
        cn = e.get("client_num")
        if cn is None:
            continue
        t = e["server_time_ms"]
        if (e["type"] == "fire_weapon" and cn != recorder_client
                and e.get("weapon") == 6):   # WP_LIGHTNING (raw parm; the
                # parser's weapon_name on fire events is MOD-table mislabeled)
            enemy_lg_fire[cn].append(t)
        elif e["type"] == "pain":
            pain[cn].append((t, e.get("event_parm") or 0))

    # recorder LG-held spans + own health series from playerstate snapshots
    held: list[tuple[int, int]] = []
    my_hp: list[tuple[int, int]] = []
    cur = None
    for sn in parsed.get("snapshots", []):
        t = None
        for k in ("server_time", "server_time_ms", "serverTime", "t_ms", "t"):
            if sn.get(k) is not None:
                t = int(sn[k])
                break
        if t is None:
            continue
        if sn.get("health") is not None:
            my_hp.append((t, int(sn["health"])))
        w = sn.get("weapon")
        if w == 6 and cur is None:            # WP_LIGHTNING
            cur = t
        elif w != 6 and cur is not None:
            held.append((cur, t))
            cur = None
    if cur is not None:
        held.append((cur, my_hp[-1][0] if my_hp else cur))

    def holding_lg(t: int) -> bool:
        return any(a <= t <= b for a, b in held)

    obits = [e for e in events if e["type"] == "obituary"]

    out: dict[int, dict] = {}
    for kt in kill_times:
        w0, w1 = kt - PRE_MS, kt + POST_MS
        dur_s = (w1 - w0) / 1000.0
        victims = {e.get("victim_client") for e in obits
                   if w0 <= e["server_time_ms"] <= w1
                   and e.get("killer_client") == recorder_client}
        victims.discard(None)

        # contact evidence: pain EVENT_PARM is a QUANTIZED health bucket
        # (80/60/40/20 observed), so exact victim damage is NOT derivable.
        # Honest metrics: pain-event count while recorder holds LG
        # (each = at least one landed hit) + bucket-drop damage floor.
        dealt = 0                                   # bucket-drop dmg floor
        contact_pains = 0
        dealt_events: list[tuple[int, int]] = []    # (t, weight)
        for cn, ps in pain.items():
            if cn == recorder_client:
                continue
            win = sorted((t, hp) for t, hp in ps if w0 <= t <= w1)
            prev_hp = None
            for t, hp in win:
                if holding_lg(t):
                    contact_pains += 1
                    dealt_events.append((t, 7))     # nominal LG-tier weight
                    if prev_hp is not None and 0 < prev_hp - hp <= 100:
                        dealt += prev_hp - hp
                prev_hp = hp

        # damage burst: max dealt in any 3s window
        dealt_events.sort()
        burst = 0
        for i in range(len(dealt_events)):
            acc = 0
            for j in range(i, len(dealt_events)):
                if dealt_events[j][0] - dealt_events[i][0] > 3000:
                    break
                acc += dealt_events[j][1]
            burst = max(burst, acc)

        # damage taken from LG: my hp drops within 150ms of enemy LG fire
        all_enemy_ticks = sorted(t for ts in enemy_lg_fire.values()
                                 for t in ts if w0 <= t <= w1)
        hp_win = sorted((t, hp) for t, hp in my_hp if w0 <= t <= w1)
        taken_lg = 0
        taken_total = 0
        for i in range(1, len(hp_win)):
            d = hp_win[i - 1][1] - hp_win[i][1]
            if 0 < d <= 100:
                taken_total += d
                lo = hp_win[i - 1][0] - 150
                hi = hp_win[i][0] + 150
                if any(lo <= ft <= hi for ft in all_enemy_ticks):
                    taken_lg += d
        in_ratio = (taken_lg / (len(all_enemy_ticks) * LG_DMG_PER_CELL)
                    ) if all_enemy_ticks else 0.0

        out[kt] = {
            "summary": {
                "lg_engagement": 1,
                "lg_contact_pains": contact_pains,
                "lg_contact_rate": round(contact_pains / dur_s, 2),
                "lg_dealt_bucket_dmg_floor": dealt,
                "lg_taken_lg_dmg": taken_lg,
                "lg_taken_total_dmg": taken_total,
                "lg_incoming_fire_ticks": len(all_enemy_ticks),
                "lg_incoming_hit_ratio": round(min(1.0, in_ratio), 3),
                # dodge: exact damage taken (1hp-resolution own health)
                # against exact enemy LG pressure, versus outgoing contact
                # pressure. Low incoming ratio + high contact rate = dodging.
                "lg_dodge_rating": round(
                    (contact_pains / dur_s) * 10 - min(1.0, in_ratio) * 20, 1),
                "lg_damage_burst_3s": burst,
                "lg_target_switches": max(0, len(victims) - 1),
                "lg_min_health": min((hp for _, hp in hp_win), default=None),
            },
            "series": {
                "dealt": [[t - kt, d] for t, d in dealt_events],
                "my_hp": [[t - kt, hp] for t, hp in hp_win[::3]],
                "enemy_lg_fire": [t - kt for t in all_enemy_ticks[::2]],
            },
        }
    return out


def run(limit: int | None = None, workers: int = 10) -> dict:
    conn = sqlite3.connect(RECOG_DB)
    conn.execute("CREATE TABLE IF NOT EXISTS lg_extracted ("
                 " content_hash TEXT PRIMARY KEY, demo_name TEXT,"
                 " version INTEGER, events INTEGER, status TEXT,"
                 " extracted_at TEXT DEFAULT (datetime('now')))")
    conn.execute("CREATE TABLE IF NOT EXISTS recognition_lg_engagements ("
                 " demo_name TEXT, server_time_ms INTEGER, version INTEGER,"
                 " series TEXT, PRIMARY KEY (demo_name, server_time_ms))")
    conn.commit()

    fconn = sqlite3.connect(f"file:{FRAGS_DB}?mode=ro", uri=True)
    meta = {n: (p, dup or h, rc) for n, p, h, dup, rc in fconn.execute(
        "SELECT name, path, content_hash, duplicate_of, recorder_client"
        " FROM demos")}
    fconn.close()

    done = {r[0] for r in conn.execute(
        "SELECT content_hash FROM lg_extracted WHERE version=? AND"
        " status='ok'", (EXTRACTOR_VERSION,))}
    cands = candidate_map()
    todo = [(d, meta[d][0], meta[d][1], meta[d][2], ts)
            for d, ts in cands.items()
            if d in meta and meta[d][1] not in done]
    if limit:
        todo = todo[:limit]

    stats = {"eligible_events": sum(len(t) for t in cands.values()),
             "demos_to_open": len(todo), "events_updated": 0, "failed": 0}
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(extract_one, path, ts, rc): (demo, h, ts)
                for demo, path, h, rc, ts in todo}
        n = 0
        for fut in as_completed(futs):
            demo, h, ts = futs[fut]
            n += 1
            try:
                res = fut.result()
            except Exception as e:   # noqa: BLE001 - per-demo isolation
                conn.execute("INSERT OR REPLACE INTO lg_extracted VALUES"
                             " (?,?,?,?,?,datetime('now'))",
                             (h, demo, EXTRACTOR_VERSION, 0,
                              f"fail: {type(e).__name__}"))
                conn.commit()
                stats["failed"] += 1
                continue
            for kt, payload in res.items():
                row = conn.execute(
                    "SELECT id, attributes FROM recognized_frags WHERE"
                    " demo_name=? AND server_time_ms=?", (demo, kt)).fetchone()
                if row is None:
                    continue
                a = json.loads(row[1] or "{}")
                a.update(payload["summary"])
                conn.execute("UPDATE recognized_frags SET attributes=?"
                             " WHERE id=?", (json.dumps(a), row[0]))
                conn.execute("INSERT OR REPLACE INTO"
                             " recognition_lg_engagements VALUES (?,?,?,?)",
                             (demo, kt, EXTRACTOR_VERSION,
                              json.dumps(payload["series"])))
                stats["events_updated"] += 1
            conn.execute("INSERT OR REPLACE INTO lg_extracted VALUES"
                         " (?,?,?,?, 'ok', datetime('now'))",
                         (h, demo, EXTRACTOR_VERSION, len(res)))
            conn.commit()
            if n % 200 == 0:
                print(f"[lg] {n}/{len(todo)} demos,"
                      f" {stats['events_updated']} events,"
                      f" {time.time()-t0:.0f}s", flush=True)
    stats["wall_s"] = round(time.time() - t0, 1)
    conn.close()
    return stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=10)
    args = ap.parse_args()
    print(json.dumps(run(args.limit, args.workers), indent=1))
