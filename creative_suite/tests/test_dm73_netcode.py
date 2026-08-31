"""Netcode regression tests for the dm_73 demo parser.

Guards the areamask framing bug found 2026-08-29: _parse_snapshot read
`areamaskLen + 1` bytes on the belief that "QL stores count-1". It does not --
the repo's own spec (docs/reference/dm73-format-deep-dive.md:348) says
`areamask byte[areamaskLen]`, matching Q3's CL_ParseSnapshot.

The extra byte desynced the bitstream at the head of every snapshot, so the
playerstate and all entity deltas after it decoded as garbage and ran off the
end of the payload. parse() swallows those with a bare `except Exception: pass`,
so the failure was invisible: 73.6% of packets in a real demo were dropped
silently while the parser still reported success.
"""
import struct
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
DEMOS = REPO / "demos"
sys.path.insert(0, str(REPO / "engine" / "parser"))

demo_parse = pytest.importorskip("demo_parse")


def _a_demo() -> Path:
    if not DEMOS.is_dir():
        pytest.skip("demo corpus not present")
    for f in sorted(DEMOS.glob("*.dm_73")):
        return f
    pytest.skip("no .dm_73 demos found")


def _packet_stats(path: Path) -> tuple[int, int]:
    """(ok, failed) over every packet in the demo."""
    p = demo_parse.DM73Parser(path)
    ok = fail = 0
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
                p._dispatch(payload, [], [])
                ok += 1
            except Exception:
                fail += 1
    return ok, fail


def test_snapshot_framing_does_not_desync():
    """The whole demo must decode with zero dropped packets.

    A non-zero failure count means the bitstream is desyncing -- almost always a
    framing/field-table error, not corrupt input.
    """
    demo = _a_demo()
    ok, fail = _packet_stats(demo)
    assert ok > 0, "parsed nothing at all"
    assert fail == 0, (
        f"{fail} of {ok + fail} packets failed to decode "
        f"({fail * 100 / (ok + fail):.1f}%) -- bitstream desync in {demo.name}"
    )


def test_areamask_reads_exactly_areamasklen():
    """Pin the framing constant against the format spec."""
    src = (REPO / "engine" / "parser" / "demo_parse.py").read_text(encoding="utf-8")
    assert "for _ in range(area_len + 1)" not in src, (
        "areamask must consume exactly areamaskLen bytes "
        "(dm73-format-deep-dive.md:348, Q3 CL_ParseSnapshot)"
    )
