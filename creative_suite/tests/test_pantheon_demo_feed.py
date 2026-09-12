"""G1: the C demo reader and DM73Parser agree on every snapshot and on every
player and missile in it. Two independent decoders agreeing is the proof;
neither is trusted alone. Skips cleanly without the corpus or the exe.

Demos are named by content hash only (public repo: no file names)."""
from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path

import pytest

from engine.pantheon import store as S
from engine.pantheon.pantheon_capture import host_exe

# protocol 73: campgrounds 2012, overkill 2012
G1_HASHES = ("4db16c445bcaafce", "a22d726b7679b8c7")


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


def _c_dump(demo: Path):
    out = subprocess.run(_host_args() + ["--dump-snapshots", str(demo)],
                         capture_output=True, text=True, timeout=900, check=True).stdout
    snaps, ents = {}, {}
    for line in out.splitlines():
        f = line.split("\t")
        if f[0] == "S" and len(f) == 7:
            snaps[int(f[2])] = tuple(map(float, f[3:6]))
        elif f[0] == "E" and len(f) == 7:
            ents.setdefault(int(f[1]), {})[int(f[2])] = (int(f[3]), *map(float, f[4:7]))
    return snaps, ents


def _close(a, b, tol=0.5):
    return all(abs(float(x or 0) - float(y)) <= tol for x, y in zip(a, b))


@pytest.mark.parametrize("prefix", G1_HASHES)
def test_c_reader_agrees_with_dm73parser_on_every_snapshot(prefix):
    from engine.parser.demo_parse import DM73Parser
    demo = _demo(prefix)
    parser = DM73Parser(demo, capture_entities=True)
    py = parser.parse()
    c_snaps, c_ents = _c_dump(demo)
    assert c_snaps, "the C reader produced no snapshots"
    # DM73Parser keeps snapshots whose delta base it never saw; the engine
    # (and so the C reader) drops them as invalid. Expected gaps: counted,
    # bounded, reported -- not hidden.
    expected_gaps = parser._missing_delta_refs

    bad, missing = [], []
    for s in py["snapshots"]:
        t = int(s["server_time_ms"])
        if t not in c_snaps:
            missing.append(t)
            continue
        if not _close((s["origin_x"], s["origin_y"], s["origin_z"]), c_snaps[t]):
            bad.append((t, "ps.origin", c_snaps[t]))
        want = py["entities_by_time"].get(t, {})
        got = c_ents.get(t, {})
        for num in set(want) | set(got):
            if num not in got or num not in want:
                bad.append((t, "entity presence", num, num in want, num in got))
            elif want[num][0] != got[num][0] or not _close(want[num][1:], got[num][1:]):
                bad.append((t, "entity", num, want[num], got[num]))
    assert len(missing) <= expected_gaps, (len(missing), expected_gaps, missing[:10])
    assert not bad, (len(bad), bad[:15])
