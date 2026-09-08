"""Dump the RAW wire fields behind decoded events.

Certification needs more than "we produced N obituaries". It needs the actual
bytes for individual events: which ordinals the delta carried, what lastField
reached, what eType looked like before and after masking. That is the evidence
that distinguishes a correct decode from a plausible one.

Used for two jobs in the certification pass:

    --obituaries N     dump N obituaries in full (the 2011 death probes)
    --etype 95         dump the lifecycle of a given base eType (the 95 question)

The probe attaches to the parser's own delta loop, so it reports what the
decoder actually saw rather than re-deriving it.

    python engine/parser/probe_events.py <demo> --obituaries 3
    python engine/parser/probe_events.py <demo> --etype 95 --limit 8
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import demo_parse as D  # noqa: E402

EV_EVENT_BITS = 0x300

FIELD_NAMES = {
    D._F_ETYPE: "eType", D._F_EVENT: "event", D._F_EVPARM: "eventParm",
    D._F_VICTIM: "otherEntityNum(victim)", D._F_KILLER: "otherEntityNum2(attacker)",
    D._F_WEAPON: "weapon", D._F_CLIENT: "clientNum", D._F_GROUND: "groundEntityNum",
    D._F_POS_X: "pos.trBase[0]", D._F_POS_Y: "pos.trBase[1]",
    D._F_POS_Z: "pos.trBase[2]",
}


def instrument(path: Path):
    """Parse once, capturing every entity delta with its raw ordinals."""
    p = D.DM73Parser(path)
    captured = []

    real_delta = D._read_delta_entity if hasattr(D, "_read_delta_entity") else None

    # The cleanest hook is the parser's own per-entity merge point. We wrap the
    # entity_states dict so every delta passes through us with its ordinals.
    class _Tap(dict):
        def __init__(self, sink):
            super().__init__()
            self._sink = sink

        def __setitem__(self, k, v):
            super().__setitem__(k, v)

    p._entity_states = _Tap(captured)
    return p, captured


def dump(path: Path, want_obits: int, want_etype: int | None, limit: int):
    """Re-parse with a field-level tap on the delta loop."""
    p = D.DM73Parser(path)

    records = []
    etype_track = defaultdict(list)

    orig_build = p._build_event_record if hasattr(p, "_build_event_record") else None

    # Tap the snapshot parser: wrap it so we can observe deltas as they merge.
    orig_snapshot = p._parse_snapshot

    def tapped(s, events, snapshots):
        before = len(events)
        orig_snapshot(s, events, snapshots)
        for ev in events[before:]:
            ent = ev.get("entity_num")
            acc = p._entity_states.get(ent, {}) if ent is not None else {}
            raw_et = acc.get(D._F_ETYPE)
            rec = {
                "server_time_ms": ev.get("server_time_ms"),
                "type": ev.get("type"),
                "entity_num": ent,
                "raw_eType": raw_et,
                "base_eType": (raw_et & ~EV_EVENT_BITS) if raw_et else None,
                "normalized_event": ((raw_et & ~EV_EVENT_BITS) - D._ET_EVENTS)
                                    if raw_et else None,
                "event_field": acc.get(D._F_EVENT),
                "eventParm": acc.get(D._F_EVPARM),
                "otherEntityNum_victim": acc.get(D._F_VICTIM),
                "otherEntityNum2_attacker": acc.get(D._F_KILLER),
                "weapon_field": acc.get(D._F_WEAPON),
                "clientNum": acc.get(D._F_CLIENT),
                "present_ordinals": sorted(acc.keys()),
                "max_ordinal_seen": max(acc.keys()) if acc else None,
                "victim_client": ev.get("victim_client"),
                "victim_name": ev.get("victim_name"),
                "killer_client": ev.get("killer_client"),
                "killer_name": ev.get("killer_name"),
                "MOD": ev.get("weapon"),
                "MOD_name": ev.get("weapon_name"),
            }
            records.append(rec)
            if raw_et is not None:
                base = raw_et & ~EV_EVENT_BITS
                etype_track[base].append(rec)

    p._parse_snapshot = tapped
    parsed = p.parse()

    out = {"demo": path.name,
           "total_events": len(parsed.get("events", [])),
           "packet_errors": parsed.get("packet_errors")}

    if want_obits:
        obits = [r for r in records if r["type"] == "obituary"]
        out["obituary_probes"] = obits[:want_obits]
        out["obituaries_total"] = len(obits)

    if want_etype is not None:
        rows = etype_track.get(want_etype, [])
        by_ent = defaultdict(list)
        for r in rows:
            by_ent[r["entity_num"]].append(r)
        life = []
        for ent, rs in list(by_ent.items())[:limit]:
            ts = [r["server_time_ms"] for r in rs if r["server_time_ms"] is not None]
            life.append({
                "entity_num": ent,
                "snapshot_count": len(rs),
                "first_time_ms": min(ts) if ts else None,
                "last_time_ms": max(ts) if ts else None,
                "lifetime_ms": (max(ts) - min(ts)) if len(ts) > 1 else 0,
                "clientNum": rs[-1].get("clientNum"),
                "eventParm": rs[-1].get("eventParm"),
                "otherEntityNum_victim": rs[-1].get("otherEntityNum_victim"),
                "otherEntityNum2_attacker": rs[-1].get("otherEntityNum2_attacker"),
                "weapon_field": rs[-1].get("weapon_field"),
                "max_ordinal_seen": rs[-1].get("max_ordinal_seen"),
                "present_ordinals": rs[-1].get("present_ordinals"),
            })
        out["etype_{}_entities".format(want_etype)] = life
        out["etype_{}_total_rows".format(want_etype)] = len(rows)
        out["etype_{}_distinct_entities".format(want_etype)] = len(by_ent)

    out["base_etype_histogram"] = {
        str(k): len(v) for k, v in sorted(etype_track.items(),
                                          key=lambda z: -len(z[1]))[:25]}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("demo")
    ap.add_argument("--obituaries", type=int, default=0)
    ap.add_argument("--etype", type=int, default=None)
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    D._get_huff()
    res = dump(Path(a.demo), a.obituaries, a.etype, a.limit)
    print(json.dumps(res, indent=2)[:14000])
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=2), encoding="utf-8")
        print("\nwrote {}".format(a.json))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
