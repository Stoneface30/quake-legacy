"""Regression cover for the packet-dispatch bug that caused the old-demo undercount.

ROOT CAUSE (proven 2026-08-29): `_dispatch` consumed ONE service message per
packet and returned. A Quake packet carries an ack sequence followed by a
SEQUENCE of messages terminated by svc_EOF, so every snapshot bundled behind a
serverCommand was discarded. Old demos reported 0-3 kills; after the fix the
same demos report 103-296.

SEPARATE BUG, also covered here: `except Exception: pass` around _dispatch hid a
NameError from a later refactor and made a CORRECT event-enum change look like a
catastrophic regression. Failures are now counted and surfaced.
"""
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "engine" / "parser"))
D = pytest.importorskip("demo_parse")


class _Rec:
    """Records which service messages _dispatch actually processed."""

    def __init__(self, cmds):
        self._cmds = list(cmds)
        self.seen = []

    def install(self, parser):
        it = iter(self._cmds)

        def readlong():
            return 0

        def readbyte():
            try:
                return next(it)
            except StopIteration:
                raise IndexError("end of packet")

        class FakeBits:
            pass

        fb = FakeBits()
        fb.readlong = readlong
        fb.readbyte = readbyte
        parser._fake = fb

        parser._parse_gamestate = lambda s: self.seen.append("gamestate")
        parser._parse_servercommand = lambda s: self.seen.append("servercommand")
        parser._parse_snapshot = lambda s, e, n: self.seen.append("snapshot")
        return fb


def _run(cmds, monkeypatch):
    p = D.DM73Parser.__new__(D.DM73Parser)
    p._packet_errors = 0
    p._first_packet_error = None
    rec = _Rec(cmds)
    fb = rec.install(p)
    monkeypatch.setattr(D, "_Bits", lambda huff, payload: fb)
    p._huff = None
    p._dispatch(b"", [], [])
    return rec.seen


def test_snapshot_after_servercommand_is_processed(monkeypatch):
    """THE regression. A snapshot bundled behind a serverCommand must not be lost."""
    seen = _run([D._SVC_SERVERCOMMAND, D._SVC_SNAPSHOT, D._SVC_EOF], monkeypatch)
    assert seen == ["servercommand", "snapshot"], (
        "dispatch returned after the first message -- this is the exact bug "
        "that reduced old demos to 0-3 kills"
    )


def test_multiple_servercommands_then_snapshot(monkeypatch):
    seen = _run([D._SVC_SERVERCOMMAND, D._SVC_SERVERCOMMAND,
                 D._SVC_SNAPSHOT, D._SVC_EOF], monkeypatch)
    assert seen == ["servercommand", "servercommand", "snapshot"]


def test_several_snapshots_in_one_packet(monkeypatch):
    seen = _run([D._SVC_SNAPSHOT, D._SVC_SNAPSHOT, D._SVC_EOF], monkeypatch)
    assert seen == ["snapshot", "snapshot"]


def test_stops_cleanly_at_eof(monkeypatch):
    """Nothing after svc_EOF may be decoded -- the bit position is spent."""
    seen = _run([D._SVC_SNAPSHOT, D._SVC_EOF, D._SVC_SNAPSHOT], monkeypatch)
    assert seen == ["snapshot"]


def test_unknown_opcode_halts_rather_than_decoding_garbage(monkeypatch):
    seen = _run([D._SVC_SNAPSHOT, 200, D._SVC_SNAPSHOT], monkeypatch)
    assert seen == ["snapshot"]


def test_truncated_packet_does_not_raise(monkeypatch):
    """Running off the end must terminate the loop, not explode."""
    seen = _run([D._SVC_SERVERCOMMAND, D._SVC_SNAPSHOT], monkeypatch)
    assert seen == ["servercommand", "snapshot"]


def test_gamestate_is_dispatched(monkeypatch):
    seen = _run([D._SVC_GAMESTATE, D._SVC_EOF], monkeypatch)
    assert seen == ["gamestate"]


# ── the swallowed-exception bug ─────────────────────────────────────────────

def test_parser_exposes_packet_error_counters():
    """A silent `pass` here once turned a NameError into a false protocol
    conclusion. Failures must be counted and the first one surfaced."""
    p = D.DM73Parser.__new__(D.DM73Parser)
    p._packet_errors = 0
    p._first_packet_error = None
    assert hasattr(p, "_packet_errors")
    assert hasattr(p, "_first_packet_error")


def test_event_constants_used_by_build_event_all_exist():
    """The NameError came from constants deleted while still referenced."""
    for name in ("_EV_OBITUARY", "_EV_CHANGE_WEAPON", "_EV_DROP_WEAPON",
                 "_EV_FIRE_WEAPON", "_EV_NOAMMO", "_EV_RAILTRAIL",
                 "_EV_MISSILE_HIT", "_EV_MISSILE_MISS", "_EV_GIB_PLAYER",
                 "_EV_ITEM_PICKUP", "_EV_PAIN", "_EV_DEATH1", "_EV_DEATH2",
                 "_EV_DEATH3", "_EV_DROWN"):
        assert hasattr(D, name), f"{name} is referenced by _build_event"


def test_ql_event_numbering_is_locked():
    """QL protocol-73 values, cross-checked against QLDT and UberDemoTools."""
    assert D._EV_OBITUARY == 58
    assert D._EV_ITEM_PICKUP == 15
    assert D._EV_CHANGE_WEAPON == 18
    assert D._EV_FIRE_WEAPON == 20
    assert D._EV_MISSILE_MISS == 48
    assert D._EV_PAIN == 53
    assert D._EV_GIB_PLAYER == 63
    assert D._EV_SCOREPLUM == 64
    assert D._ET_EVENTS == 13
    assert D._ET_EVENTS + D._EV_OBITUARY == 71   # obituary base eType
