"""Gate G1: the engine's own decoder (host/pantheon_demo_feed.c, run through
`pantheon_cgame.exe --dump-snapshots`) and DM73Parser agree on everything
cgame is handed -- every playerstate field, every entity field, the
configstring set at every snapshot, the command stream, the gamestate.

Two independent decoders agreeing is the proof; neither is trusted alone.
The field tables on both sides are generated from msg.c. Skips cleanly without
the corpus or the exe. Demos are named by content hash only (public repo).
"""
from __future__ import annotations

import math
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from engine.pantheon import store as S
from engine.pantheon.pantheon_capture import host_exe

# protocol 73: campgrounds 2012 (short), overkill 2012 (long: wraps the ring)
G1_HASHES = ("4db16c445bcaafce", "a22d726b7679b8c7")
RING_HASH = "a22d726b7679b8c7"
PARSE_RING = 8192                      # PACKET_BACKUP * MAX_SNAPSHOT_ENTITIES

_FNV_BASIS, _FNV_PRIME, _MASK = 1469598103934665603, 1099511628211, (1 << 64) - 1


def _demo(prefix: str) -> Path:
    if not S.FRAGS_DB.exists():
        pytest.skip("no corpus catalogue")
    con = sqlite3.connect(f"file:{S.FRAGS_DB.as_posix()}?mode=ro", uri=True)
    row = con.execute("select path from demos where content_hash like ? limit 1",
                      (prefix + "%",)).fetchone()
    con.close()
    if not row or not Path(row[0]).exists():
        pytest.skip(f"demo {prefix} not on this machine")
    return Path(row[0])


def _host_args() -> list[str]:
    if not host_exe().exists():
        pytest.skip("pantheon_cgame.exe not built")
    base = S.PROJECT_ROOT / "output" / "demo_v2" / "_wolfcam_staging"
    if not base.exists():
        pytest.skip("no engine basepath on this machine")
    return [str(host_exe()), "--basepath", str(base), "--game", "baseq3"]


# ---- the C side ------------------------------------------------------------

def _unescape(s: str) -> str:
    out, i = [], 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            out.append({"\\": "\\", "n": "\n", "r": "\r", "t": "\t"}.get(s[i + 1], s[i + 1]))
            i += 2
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


def _c_dump(demo: Path) -> dict:
    raw = subprocess.run(_host_args() + ["--dump-snapshots", str(demo)],
                         capture_output=True, timeout=900, check=True).stdout
    d = {"F": {}, "G": [], "Q": [], "invalid": set(), "S": {}, "P": {}, "E": {}, "C": {}}
    for line in raw.decode("latin-1").split("\n"):
        f = line.rstrip("\r").split("\t")
        k = f[0]
        if k == "F":
            d["F"][f[1]] = f[2:]
        elif k == "G":
            d["G"].append((int(f[1]), int(f[2]), f[3], f[4], int(f[5])))
        elif k == "Q":
            d["Q"].append((int(f[1]), _unescape("\t".join(f[2:]))))
        elif k == "D" and f[4] == "0":
            d["invalid"].add(int(f[2]))
        elif k == "S":
            d["S"][int(f[2])] = tuple(int(x) for x in (f[1], f[3], f[4], f[5], f[6]))
        elif k == "P":
            d["P"][int(f[1])] = f[2:]
        elif k == "E":
            d["E"].setdefault(int(f[1]), {})[int(f[2])] = f[3:]
        elif k == "C":
            d["C"][int(f[1])] = (f[2], f[3])
    return d


# ---- the Python side ---------------------------------------------------------

def _cs_record(h: int, i: int, v: str) -> int:
    for b in str(i).encode() + b"\0" + v.encode("latin-1") + b"\0":
        h = ((h ^ b) * _FNV_PRIME) & _MASK
    return h


def _cs_set_hash(cs: dict) -> str:
    h = _FNV_BASIS
    for i in sorted(cs):
        if cs[i]:
            h = _cs_record(h, i, cs[i])
    return "%016x" % h


def _ps_values(ps: dict) -> list:
    return ([ps.get(i, 0) for i in range(48)] +
            [ps.get(f"{p}{j}", 0) for p in "spaw" for j in range(16)])


def _same(c: str, py, is_float: bool) -> bool:
    py = py or 0
    if is_float:
        return math.isclose(float(c), float(py), rel_tol=1e-6, abs_tol=1e-6)
    return int(c) & 0xFFFFFFFF == int(py) & 0xFFFFFFFF


def _compare(demo: Path) -> tuple[dict, dict]:
    from engine.parser.demo_parse import DM73Parser, server_command_cs
    from engine.parser import netfields_generated as NF

    c = _c_dump(demo)
    py = DM73Parser(demo, capture_entities=True).parse()
    ps_float = [b.strip() == "0" for _i, _n, b, _s in NF.PLAYERSTATE_Q3] + [False] * 64
    es_float = [b.strip() == "0" for _i, _n, b, _s in NF.ENTITYSTATE_QLDM73]
    # Both sides name the same fields in the same order.
    assert c["F"]["P"][:48] == [n for _i, n, _b, _s in NF.PLAYERSTATE_Q3]
    assert c["F"]["E"] == [n for _i, n, _b, _s in NF.ENTITYSTATE_QLDM73]

    bad: dict[str, list] = {}
    def miss(kind, *what):
        bad.setdefault(kind, []).append(what)

    cs, bigcs, prev, touched = {}, [""], {}, set()
    seq_now, py_g, py_q, py_only = None, [], [], []
    set_hash = None
    for rec in py["g1_log"]:
        if rec[0] == "G":
            cs = {k: v for k, v in rec[1].items()}
            prev, touched, set_hash = dict(cs), set(), _cs_set_hash(cs)
            seq_now = rec[4]
            py_g.append((rec[2], rec[3], "73", set_hash, rec[4]))
        elif rec[0] == "Q":
            py_q.append((rec[1], rec[2]))
            seq_now = rec[1]
            _argv, change = server_command_cs(bigcs, rec[2])
            if change is not None and 0 <= change[0] < 1024:
                cs[change[0]] = change[1]
                touched.add(change[0])
        else:
            _k, t, flags, msg, ps, ents = rec
            if t not in c["S"]:
                py_only.append(t)
                continue
            c_msg, c_flags, c_seq, c_n, _pen = c["S"][t]
            if (msg, flags, seq_now, len(ents)) != (c_msg, c_flags, c_seq, c_n):
                miss("snapshot header", t, (msg, flags, seq_now, len(ents)), c["S"][t][:4])
            for name, cv, pv, fl in zip(c["F"]["P"], c["P"][t], _ps_values(ps), ps_float):
                if not _same(cv, pv, fl):
                    miss("playerstate", t, name, cv, pv)
            c_ents = c["E"].get(t, {})
            if set(c_ents) != set(ents):
                miss("entity presence", t, sorted(set(c_ents) ^ set(ents)))
            for num in set(c_ents) & set(ents):
                for i, (cv, fl) in enumerate(zip(c_ents[num], es_float)):
                    if not _same(cv, ents[num].get(i), fl):
                        miss("entity field", t, num, c["F"]["E"][i], cv, ents[num].get(i))
            changed = sorted(i for i in touched if cs.get(i, "") != prev.get(i, ""))
            if changed:
                set_hash = _cs_set_hash(cs)
            for i in touched:
                prev[i] = cs.get(i, "")
            touched = set()
            c_hash, c_changed = c["C"][t]
            if set_hash != c_hash:
                miss("configstring set", t, set_hash, c_hash)
            if (",".join(map(str, changed)) or "-") != c_changed:
                miss("configstrings changed", t, changed, c_changed)
    if py_g != c["G"]:
        miss("gamestate", py_g, c["G"])
    if py_q != c["Q"]:
        first = next((i for i, (a, b) in enumerate(zip(py_q, c["Q"])) if a != b),
                     min(len(py_q), len(c["Q"])))
        miss("command stream", len(py_q), len(c["Q"]), first,
             py_q[first:first + 1], c["Q"][first:first + 1])
    # A snapshot the engine refuses (delta from a frame it never held) may
    # exist in DM73Parser; it must be one the C reader parsed AND marked invalid.
    for t in py_only:
        if t not in c["invalid"]:
            miss("snapshot only in DM73Parser", t)
    py_times = {r[1] for r in py["g1_log"] if r[0] == "S"}
    for t in set(c["S"]) - py_times:
        miss("snapshot only in the C reader", t)
    return c, bad


@pytest.mark.parametrize("prefix", G1_HASHES)
def test_g1_every_field_agrees(prefix):
    c, bad = _compare(_demo(prefix))
    assert c["S"], "the C reader produced no snapshots"
    report = {k: (len(v), v[:5]) for k, v in bad.items()}
    assert not bad, report


def test_g1_exercises_the_parse_entity_ring():
    """A short fixture cannot pass G1 without crossing the 8192-slot mask."""
    c = _c_dump(_demo(RING_HASH))
    pens = [(pen, n) for (_m, _f, _s, n, pen) in c["S"].values()]
    assert max(p for p, _n in pens) > 3 * PARSE_RING
    assert any(p % PARSE_RING + n > PARSE_RING for p, n in pens), \
        "no snapshot straddles the parse-entity ring boundary"


def test_command_ring_wraps_like_wolfcam():
    out = subprocess.run(_host_args() + ["--self-test-rings"], capture_output=True,
                         text=True, timeout=300)
    assert "RINGS OK" in out.stdout and out.returncode == 0, out.stdout[-2000:]


def test_signed_playerstate_fields_follow_the_generated_table():
    from engine.parser import demo_parse, netfields_generated as NF
    assert demo_parse._PS_SIGNED == {i for i, _n, _b, s in NF.PLAYERSTATE_Q3 if s}


def test_the_c_field_tables_are_current():
    root = Path(__file__).resolve().parents[2]
    if not (root / "engine" / "pantheon_renderer" / "wolfcamql-11.3-src").exists():
        pytest.skip("WolfcamQL source not bootstrapped")
    r = subprocess.run([sys.executable, "-m", "engine.parser.gen_netfields", "--check"],
                       cwd=root, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr


def test_an_unsupported_protocol_fails_rather_than_compares():
    """The dump refuses anything but protocol 73 (exit 3). Proven on the
    source: the check exists and returns non-zero, never skips."""
    src = (Path(__file__).resolve().parents[2] / "engine" / "pantheon_renderer" /
           "host" / "pantheon_frame.c").read_text(encoding="utf-8")
    block = src[src.index("if (s_dumpSnapshots) {"):]
    block = block[:block.index("G1_PrintFieldNames();") + 2000]
    assert 'strcmp(proto, "73")' in block and "return 3;" in block
