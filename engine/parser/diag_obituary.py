"""Obituary decoding diagnostic for dm_73 -- evidence before any fix.

Written to the brief of 2026-08-29, which correctly called out that earlier
diagnostics conflated four different things. This tool keeps them separate at
all times:

    wire ordinal        the netfield index on the wire (0..52)
    semantic field      what that ordinal MEANS in the active profile
    raw eType           the entity's reconstructed eType byte
    normalized event    (raw_eType & ~EV_EVENT_BITS) - ET_EVENTS
    the `event` field   ordinal 10, a DIFFERENT field from eType

Obituary recognition per QLDT's old dm_73 decoder:

    (eType & ~EV_EVENT_BITS) == ET_EVENTS + EV_OBITUARY_QL
    ET_EVENTS = 13,  EV_OBITUARY_QL = 58   =>  base eType == 71

    eventParm       -> means of death
    otherEntityNum  -> victim   (ordinal 19)
    otherEntityNum2 -> attacker (ordinal 31)

INVARIANT enforced here: a delta reporting `lastField = N` can never transmit a
changed ordinal >= N. Earlier reporting appeared to show ordinal 31 present
while per-delta maxima sat at 24 -- but those were an AGGREGATE over all deltas
compared against a maximum from a different delta. That comparison is invalid,
and this tool never makes it: every count below is per-delta.

    python engine/parser/diag_obituary.py <demo> [<demo> ...]
"""
from __future__ import annotations

import argparse
import collections
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import demo_parse as D  # noqa: E402

EV_EVENT_BITS = 0x300
ET_EVENTS = 13
EV_OBITUARY_QL = 58
OBITUARY_BASE_ETYPE = ET_EVENTS + EV_OBITUARY_QL      # 71

SEMANTIC = {
    9: "pos.gravity", 10: "event", 12: "eType", 14: "eventParm",
    16: "groundEntityNum", 18: "eFlags", 19: "otherEntityNum(victim)",
    20: "weapon", 21: "clientNum", 31: "otherEntityNum2(attacker)",
}


class Probe:
    """Re-decodes a demo while recording per-delta facts, never aggregates."""

    def __init__(self, path: Path):
        self.path = path
        self.lastfield_hist = collections.Counter()
        self.max_lastfield = 0
        self.changed_ordinal_hist = collections.Counter()
        self.raw_etype_hist = collections.Counter()
        self.norm_event_hist = collections.Counter()
        self.event_field_hist = collections.Counter()
        self.violations: list[str] = []
        self.obit_candidates: list[dict] = []
        self.deltas = 0
        self.state: dict[int, dict] = {}

    def run(self) -> None:
        p = D.DM73Parser(self.path)
        real_delta = p._read_entity_delta

        def tapped(s):
            """Wrap the real reader so we can see lastField and the ordinals."""
            bit0 = s._bit
            removed = s.readbits(1)
            if removed:
                return None
            if s.readbits(1) == 0:
                return {}
            last = s.readbyte()
            out: dict = {}
            changed: list[int] = []
            for i in range(min(last, len(D._ES_BITS))):
                if s.readbits(1):
                    changed.append(i)
                    bits = D._ES_BITS[i]
                    if bits == 0:
                        if s.readbits(1):
                            if s.readbits(1) == 0:
                                t = s.readbits(D._FLOAT_INT_BITS)
                                out[i] = float(t - D._FLOAT_INT_BIAS)
                            else:
                                out[i] = s.readfloat()
                    else:
                        if s.readbits(1):
                            out[i] = s.readbits(bits)

            self.deltas += 1
            self.lastfield_hist[last] += 1
            self.max_lastfield = max(self.max_lastfield, last)
            for c in changed:
                self.changed_ordinal_hist[c] += 1
                # THE invariant. A violation here is a decoder bug, not data.
                if c >= last:
                    self.violations.append(
                        f"ordinal {c} changed but lastField={last}")
            out["__last"] = last
            out["__changed"] = changed
            return out

        p._read_entity_delta = tapped
        p.parse()

    def note_entity(self, num: int, delta: dict, server_time: int) -> None:
        pass


def analyse(path: Path, show: int) -> dict:
    """Walk the demo, reconstruct entity state, and hunt obituaries properly."""
    huff = D._get_huff()
    parser = D.DM73Parser(path)

    lastfield_hist = collections.Counter()
    changed_hist = collections.Counter()
    raw_etype_hist = collections.Counter()
    norm_hist = collections.Counter()
    event_field_hist = collections.Counter()
    violations = 0
    deltas = 0
    obits: list[dict] = []
    state: dict[int, dict] = {}
    server_time = 0

    with open(path, "rb") as fh:
        while True:
            hdr = fh.read(8)
            if len(hdr) < 8:
                break
            seq, length = struct.unpack("<ii", hdr)
            if seq == -1 or length <= 0:
                break
            payload = fh.read(length)
            if len(payload) < length:
                break
            try:
                s = D._Bits(huff, payload)
                s.readlong()
                cmd = s.readbyte()
                if cmd != D._SVC_SNAPSHOT:
                    continue
                server_time = s.readlong()
                delta_num = s.readbyte()
                s.readbyte()                       # snapFlags
                if delta_num == 0:
                    state = {}
                area_len = s.readbyte()
                for _ in range(area_len):
                    s.readbyte()
                _read_playerstate_skip(s, parser)

                while True:
                    num = s.readbits(D._GENTITYNUM_BITS)
                    if num == 1023:
                        break
                    if s.readbits(1):              # removed
                        state.pop(num, None)
                        continue
                    if s.readbits(1) == 0:         # unchanged
                        continue
                    last = s.readbyte()
                    lastfield_hist[last] += 1
                    deltas += 1
                    d: dict = {}
                    for i in range(min(last, len(D._ES_BITS))):
                        if s.readbits(1):
                            changed_hist[i] += 1
                            if i >= last:
                                violations += 1
                            bits = D._ES_BITS[i]
                            if bits == 0:
                                if s.readbits(1):
                                    if s.readbits(1) == 0:
                                        t = s.readbits(D._FLOAT_INT_BITS)
                                        d[i] = float(t - D._FLOAT_INT_BIAS)
                                    else:
                                        d[i] = s.readfloat()
                            else:
                                if s.readbits(1):
                                    d[i] = s.readbits(bits)

                    # RECONSTRUCTED state, not the delta alone.
                    ent = state.setdefault(num, {})
                    ent.update(d)

                    raw_et = ent.get(D._F_ETYPE)
                    if raw_et is not None:
                        raw_etype_hist[raw_et] += 1
                        base = raw_et & ~EV_EVENT_BITS
                        norm_hist[base] += 1
                        if base == OBITUARY_BASE_ETYPE:
                            obits.append({
                                "time": server_time, "entity": num,
                                "raw_eType": raw_et, "base_eType": base,
                                "event": ent.get(D._F_EVENT),
                                "MOD": ent.get(D._F_EVPARM),
                                "victim": ent.get(D._F_VICTIM),
                                "attacker": ent.get(D._F_KILLER),
                                "lastField": last,
                                "changed": sorted(d),
                            })
                    evf = ent.get(D._F_EVENT)
                    if evf is not None:
                        event_field_hist[evf & ~EV_EVENT_BITS] += 1
            except Exception:
                continue

    return {
        "deltas": deltas,
        "lastfield_hist": lastfield_hist,
        "max_lastfield": max(lastfield_hist) if lastfield_hist else 0,
        "changed_hist": changed_hist,
        "raw_etype_hist": raw_etype_hist,
        "norm_hist": norm_hist,
        "event_field_hist": event_field_hist,
        "violations": violations,
        "obits": obits,
    }


def _read_playerstate_skip(s, parser) -> None:
    """Consume the playerstate so entity parsing starts at the right bit."""
    parser._read_playerstate(s)


def report(path: Path, show: int) -> None:
    r = analyse(path, show)
    print(f"\n{'=' * 74}\n{path.name}\n{'=' * 74}")
    print(f"  entity deltas              : {r['deltas']}")
    print(f"  lastField max              : {r['max_lastfield']}")
    print(f"  lastField histogram (top)  : "
          f"{dict(r['lastfield_hist'].most_common(8))}")
    print(f"  INVARIANT violations       : {r['violations']}  "
          f"(changedOrdinal >= lastField)")
    print(f"  deltas transmitting ord 31 : {r['changed_hist'].get(31, 0)}  "
          f"({SEMANTIC[31]})")
    print(f"  deltas transmitting ord 19 : {r['changed_hist'].get(19, 0)}  "
          f"({SEMANTIC[19]})")
    print(f"  deltas transmitting ord 14 : {r['changed_hist'].get(14, 0)}  "
          f"({SEMANTIC[14]})")
    print(f"  raw eType histogram (top)  : "
          f"{dict(r['raw_etype_hist'].most_common(8))}")
    print(f"  base eType (& ~0x300) top  : {dict(r['norm_hist'].most_common(8))}")
    print(f"  base eType == {OBITUARY_BASE_ETYPE} count     : "
          f"{r['norm_hist'].get(OBITUARY_BASE_ETYPE, 0)}   <-- obituary entities")
    print(f"  `event` field (ord 10) top : "
          f"{dict(r['event_field_hist'].most_common(8))}")
    print(f"  RAW obituary candidates    : {len(r['obits'])}")

    if r["obits"]:
        print(f"\n  first {min(show, len(r['obits']))} raw obituary candidates:")
        print(f"  {'time':>9} {'ent':>5} {'rawET':>6} {'baseET':>7} "
              f"{'MOD':>4} {'victim':>7} {'attacker':>9} {'lastF':>6}  changed")
        for o in r["obits"][:show]:
            print(f"  {o['time']:>9} {o['entity']:>5} {o['raw_eType']:>6} "
                  f"{o['base_eType']:>7} {str(o['MOD']):>4} "
                  f"{str(o['victim']):>7} {str(o['attacker']):>9} "
                  f"{o['lastField']:>6}  {o['changed']}")
    else:
        print("\n  NO obituary entities found. Fields carrying attacker "
              "(ord 31) were transmitted "
              f"{r['changed_hist'].get(31, 0)} time(s).")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("demos", nargs="+")
    ap.add_argument("--show", type=int, default=20)
    a = ap.parse_args()
    for d in a.demos:
        report(Path(d), a.show)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
