"""Round-trip tests for the .dm_73 writer.

THE CONTRACT. The project's own `DM73Parser` is the semantic unit test. A
writer validated against its own idea of the format proves nothing; validated
against the reader that consumes 4,292 real demos, it proves the encoding is
the one this project already trusts. Every layer here is written, parsed back,
and compared as STATE -- never as a byte count.

WolfcamQL remains the external validator. Passing this file is necessary and
not sufficient.
"""
from __future__ import annotations

import random

import pytest

from engine.parser import dm73_write as W
from engine.parser.demo_parse import (
    _ES_BITS, _FLOAT_INT_BIAS, _PS_BITS, _Bits, DM73Parser, _get_huff)


@pytest.fixture(scope="module")
def huff():
    return _get_huff()


# ══ PINNED: the bit layer ═══════════════════════════════════════════════════
# Everything above this is undebuggable if one bit is misplaced. These are
# exhaustive on purpose and must not be relaxed to make a refactor pass.

def test_every_symbol_round_trips(huff):
    """All 256. The Huffman tree is static -- `receive` never calls
    `add_ref` -- so the writer's code table and the reader's tree walk are the
    same structure read two ways."""
    bad = []
    for sym in range(256):
        w = W.BitWriter()
        w.writebyte(sym)
        if _Bits(huff, w.bytes()).readbyte() != sym:
            bad.append(sym)
    assert not bad, f"symbols failed to round-trip: {bad}"


@pytest.mark.parametrize("n", list(range(1, 33)))
def test_every_bit_width_round_trips(huff, n: int):
    """`writebits` must split the low `n & 7` bits raw and the rest as whole
    Huffman bytes, exactly as `readbits` recombines them."""
    rng = random.Random(1000 + n)
    for _ in range(40):
        v = rng.getrandbits(n)
        w = W.BitWriter()
        w.writebits(v, n)
        assert _Bits(huff, w.bytes()).readbits(n) == v, (n, v)


def test_mixed_primitive_stream_stays_aligned(huff):
    """Alignment is the failure mode that matters: one bad width silently
    shifts everything after it and the damage shows up somewhere unrelated."""
    w = W.BitWriter()
    w.writebyte(7)
    w.writebits(1, 1)
    w.writebits(1023, 10)
    w.writeshort(4242)
    w.writelong(-123456)
    w.writestring("CA-explainer")
    w.writefloat(1234.5)
    w.writebits(5, 3)
    r = _Bits(huff, w.bytes())
    assert r.readbyte() == 7
    assert r.readbits(1) == 1
    assert r.readbits(10) == 1023
    assert r.readshort() == 4242
    assert r.readlong() == -123456
    assert r.readstring() == "CA-explainer"
    assert round(r.readfloat(), 1) == 1234.5
    assert r.readbits(3) == 5


def test_writer_and_reader_agree_on_byte_alignment(huff):
    """A sub-byte write followed by a symbol must not pad. If the writer
    aligned and the reader did not, short streams would still pass -- so this
    checks the bit cursor after a deliberately ragged sequence."""
    w = W.BitWriter()
    for width, value in ((3, 5), (1, 1), (5, 17), (8, 200), (2, 3)):
        w.writebits(value, width)
    r = _Bits(huff, w.bytes())
    assert [r.readbits(wd) for wd, _ in ((3, 0), (1, 0), (5, 0), (8, 0), (2, 0))] \
        == [5, 1, 17, 200, 3]


# ══ delta encodings ═════════════════════════════════════════════════════════

def test_entity_and_playerstate_use_different_integer_encodings():
    """An entity integer carries a non-zero prefix bit; a playerstate integer
    does not. Confusing them desyncs the rest of the packet, so the two paths
    are deliberately separate functions."""
    src = __import__("inspect").getsource(W.write_playerstate_delta)
    assert "no prefix" in src or "direct" in src


def test_entity_delta_round_trips_every_field_type(huff):
    """One float and one integer field of each width present in the table."""
    parser = DM73Parser.__new__(DM73Parser)
    state = {}
    rng = random.Random(4)
    for i, bits in enumerate(_ES_BITS):
        if bits == 0:
            state[i] = float(rng.randint(-2000, 2000))       # small-int form
        else:
            state[i] = rng.randint(1, (1 << bits) - 1)
    w = W.BitWriter()
    W.write_entity_delta(w, {}, state)
    got = parser._read_entity_delta(_Bits(huff, w.bytes()))
    assert got == state


def test_entity_delta_round_trips_a_true_float(huff):
    """Values that are not small integers take the full 32-bit path."""
    parser = DM73Parser.__new__(DM73Parser)
    state = {W.ES_POS_X: 1234.5, W.ES_POS_Y: -8191.25, W.ES_POS_Z: 0.125}
    w = W.BitWriter()
    W.write_entity_delta(w, {}, state)
    got = parser._read_entity_delta(_Bits(huff, w.bytes()))
    assert got == pytest.approx(state)


def test_entity_removal_and_no_change_forms(huff):
    parser = DM73Parser.__new__(DM73Parser)
    w = W.BitWriter()
    W.write_entity_delta(w, {}, None)
    assert parser._read_entity_delta(_Bits(huff, w.bytes())) is None

    w = W.BitWriter()
    W.write_entity_delta(w, {W.ES_ETYPE: 1}, {W.ES_ETYPE: 1})
    assert parser._read_entity_delta(_Bits(huff, w.bytes())) == {}


def test_playerstate_delta_round_trips(huff):
    parser = DM73Parser.__new__(DM73Parser)
    parser._ps_state = {}
    parser._ps_events = []
    parser._ps_prev_seq = None
    ps = {W.PS_ORIGIN_X: 1024.0, W.PS_ORIGIN_Y: -512.0, W.PS_ORIGIN_Z: 96.0,
          W.PS_VEL_X: 320.0, W.PS_VEL_Y: -64.0, W.PS_VEL_Z: 12.0,
          W.PS_YAW: 135.0, W.PS_PITCH: -10.0,
          W.PS_CLIENTNUM: 3, W.PS_WEAPON: 7, W.PS_GROUND: 1023}
    w = W.BitWriter()
    W.write_playerstate_delta(w, {}, ps,
                              stats={W.STAT_HEALTH: 175, W.STAT_ARMOR: 50})
    snap = parser._read_playerstate(_Bits(huff, w.bytes()))
    assert snap["client_num"] == 3
    assert snap["weapon"] == 7
    assert (snap["origin_x"], snap["origin_y"], snap["origin_z"]) == (1024.0, -512.0, 96.0)
    assert (snap["vel_x"], snap["vel_y"], snap["vel_z"]) == (320.0, -64.0, 12.0)
    assert snap["angle_yaw"] == 135.0
    assert snap["health"] == 175
    assert snap["armor"] == 50
    assert snap["airborne"] is True            # groundEntityNum 1023


# ══ whole-file layers ═══════════════════════════════════════════════════════

def _ca_configstrings(n_players: int = 8) -> dict[int, str]:
    cs = {W.CS_SERVERINFO: W.serverinfo("campgrounds", gametype=4,
                                        hostname="PANTHEON SYNTHETIC EXPLAINER"),
          W.CS_SYSTEMINFO: W.systeminfo()}
    for i in range(n_players):
        team = 1 if i < n_players // 2 else 2
        label = "RED" if team == 1 else "BLUE"
        cs[W.CS_PLAYERS + i] = W.player_configstring(
            f"{label}_{i % (n_players // 2) + 1}", team=team)
    return cs


def test_gamestate_round_trips_map_gametype_and_teams(tmp_path):
    d = W.DemoWriter()
    d.write_gamestate(_ca_configstrings())
    out = DM73Parser(d.save(tmp_path / "gs.dm_73")).parse()
    assert out["map"] == "campgrounds"
    assert out["gametype"] == "CA"
    assert out["packet_errors"] == 0
    assert len(out["players"]) == 8
    assert [out["players"][i]["team"] for i in range(8)] == \
        ["RED"] * 4 + ["BLUE"] * 4
    assert out["players"][0]["name"] == "RED_1"
    assert out["players"][7]["name"] == "BLUE_4"


def test_info_string_rejects_an_embedded_separator():
    with pytest.raises(ValueError):
        W.info_string([("n", "bad" + W.SEP + "name")])


def test_snapshot_stream_round_trips_position_and_time(tmp_path):
    """serverTime progression and per-frame position, read back as state."""
    d = W.DemoWriter()
    d.write_gamestate(_ca_configstrings())
    times, xs = [], []
    for f in range(12):
        t = 5000 + f * 50
        x = 900.0 + f * 24
        times.append(t)
        xs.append(x)
        ps = {W.PS_CLIENTNUM: 2, W.PS_ORIGIN_X: x, W.PS_ORIGIN_Y: -300.0,
              W.PS_ORIGIN_Z: 64.0, W.PS_VEL_X: 480.0, W.PS_YAW: 45.0,
              W.PS_WEAPON: 6, W.PS_GROUND: 1023}
        ents = {c: {W.ES_ETYPE: W.ET_PLAYER, W.ES_CLIENTNUM: c,
                    W.ES_POS_X: x + c * 40, W.ES_POS_Y: -300.0 + c * 20,
                    W.ES_POS_Z: 64.0} for c in range(8)}
        d.write_snapshot(t, ps, ents,
                         stats={W.STAT_HEALTH: 200, W.STAT_ARMOR: 100})
    out = DM73Parser(d.save(tmp_path / "snaps.dm_73")).parse()
    assert out["packet_errors"] == 0
    assert out["snapshot_count"] == 12
    assert [s["server_time_ms"] for s in out["snapshots"]] == times
    assert [s["origin_x"] for s in out["snapshots"]] == xs
    assert {s["client_num"] for s in out["snapshots"]} == {2}
    assert {s["health"] for s in out["snapshots"]} == {200}
    assert {s["airborne"] for s in out["snapshots"]} == {True}


def test_areamask_length_is_written_without_the_plus_one(tmp_path):
    """The reader takes exactly `areamaskLen` bytes. A writer that emitted an
    extra one would desync every snapshot -- the same defect, mirrored, that
    once swallowed 73.6% of packets on the read side."""
    d = W.DemoWriter()
    d.write_gamestate(_ca_configstrings())
    for f in range(4):
        d.write_snapshot(1000 + f * 50,
                         {W.PS_CLIENTNUM: 1, W.PS_ORIGIN_X: 10.0 + f},
                         {0: {W.ES_ETYPE: W.ET_PLAYER}},
                         areamask=bytes([0xFF, 0x0F, 0x00, 0x7A]))
    out = DM73Parser(d.save(tmp_path / "area.dm_73")).parse()
    assert out["packet_errors"] == 0
    assert out["snapshot_count"] == 4
    assert [s["origin_x"] for s in out["snapshots"]] == [10.0, 11.0, 12.0, 13.0]


def test_server_command_text_survives(tmp_path):
    d = W.DemoWriter()
    d.write_gamestate(_ca_configstrings())
    d.write_server_command(1, 'print "SYNTHETIC EXPLAINER"')
    out = DM73Parser(d.save(tmp_path / "cmd.dm_73")).parse()
    assert out["packet_errors"] == 0
    assert any("SYNTHETIC EXPLAINER" in t["text"] for t in out["server_text"])


# ══ field indices: the parser is the only authority ═════════════════════════

def test_entity_field_indices_come_from_the_parser():
    """These were invented once and every test still passed, because the tests
    compared the invented indices against themselves. The engine got players
    whose eType landed in eFlags and whose position landed in velocity, and
    drew nothing. Bind them to `demo_parse` so that cannot recur."""
    from engine.parser import demo_parse as dp
    assert (W.ES_POS_X, W.ES_POS_Y, W.ES_POS_Z) == (dp._F_POS_X, dp._F_POS_Y,
                                                    dp._F_POS_Z) == (1, 2, 5)
    assert W.ES_ETYPE == dp._F_ETYPE == 12
    assert W.ES_CLIENTNUM == dp._F_CLIENT == 21
    assert W.ES_GROUND == dp._F_GROUND == 16
    assert W.ES_EVENT == dp._F_EVENT == 10
    assert W.ES_OTHER_ENT == dp._F_VICTIM == 19
    assert W.ES_OTHER_ENT2 == dp._F_KILLER == 31
    assert W.EV_OBITUARY == dp._EV_OBITUARY == 58
    assert W.ET_EVENTS == dp._ET_EVENTS == 13


# ══ the padding class of failure ════════════════════════════════════════════

def test_every_packet_carries_slack_after_svc_eof():
    """Q3 derives its cursor from the BIT position as (bit >> 3) + 1 and
    refuses a read where readcount > cursize, so a payload whose bits end
    exactly on a byte boundary leaves the cursor one byte past the buffer and
    the next MSG_ReadByte returns -1. Wolfcam reported that as
    "Illegible server message -1" on 13 of 162 packets and died in
    CL_PeekSnapshot. It was intermittent because it depends on total bit
    length, not content -- so the guard is structural, not a sample."""
    assert W.DemoWriter.TAIL_PAD >= 1
    d = W.DemoWriter()
    d.write_gamestate(_ca_configstrings())
    for f in range(30):
        d.write_snapshot(1000 + f * 50,
                         {W.PS_CLIENTNUM: 0, W.PS_ORIGIN_X: 1.0 + f},
                         {1: {W.ES_ETYPE: W.ET_PLAYER, W.ES_CLIENTNUM: 1,
                              W.ES_POS_X: float(f)}})
    for pkt in d._packets:
        assert pkt.payload[-W.DemoWriter.TAIL_PAD:] == bytes(W.DemoWriter.TAIL_PAD)


# ══ obituary ════════════════════════════════════════════════════════════════

def test_obituary_matches_the_shape_the_engine_emits():
    """Real obituary deltas in the corpus look like
    {1: x, 2: y, 5: z, 12: 71, 14: mod, 19: victim, 31: killer}."""
    e = W.obituary_entity(killer=1, victim=5, mod=7, pos=(10.0, 20.0, 30.0))
    assert e[W.ES_ETYPE] == 71                      # ET_EVENTS + EV_OBITUARY
    assert e[W.ES_EVENTPARM] == 7
    assert e[W.ES_OTHER_ENT] == 5
    assert e[W.ES_OTHER_ENT2] == 1


def test_obituary_round_trips_killer_victim_mod_and_time(tmp_path):
    d = W.DemoWriter()
    d.write_gamestate(_ca_configstrings())
    kill_t = 3000
    for f in range(60):          # t runs to 3950, so kill_t is actually reached
        t = 1000 + f * 50
        ents = {c: {W.ES_ETYPE: W.ET_PLAYER, W.ES_CLIENTNUM: c,
                    W.ES_POS_X: 100.0 + c, W.ES_POS_Y: 40.0, W.ES_POS_Z: 50.0}
                for c in range(1, 8)}
        if t == kill_t:
            ents[512] = W.obituary_entity(killer=1, victim=5, mod=7,
                                          pos=(120.0, 40.0, 50.0))
        d.write_snapshot(t, {W.PS_CLIENTNUM: 0, W.PS_ORIGIN_X: float(f)}, ents)
    out = DM73Parser(d.save(tmp_path / "obit.dm_73")).parse()
    assert out["packet_errors"] == 0
    obits = [e for e in out["events"] if e["type"] == "obituary"]
    assert len(obits) == 1
    e = obits[0]
    assert e["killer_client"] == 1
    assert e["victim_client"] == 5
    assert e["weapon"] == 7
    assert e["server_time_ms"] == kill_t
    assert e["killer_team"] == "RED"
    assert e["victim_team"] == "BLUE"


def test_two_deaths_in_the_same_slot_need_the_toggle_bit(tmp_path):
    """The parser compares the RAW eType and drops a repeat, which is exactly
    what EV_EVENT_BIT1/BIT2 exist to prevent. Without a flipped toggle the
    second death silently never happened."""
    d = W.DemoWriter()
    d.write_gamestate(_ca_configstrings())
    for f in range(60):
        t = 1000 + f * 50
        ents = {1: {W.ES_ETYPE: W.ET_PLAYER, W.ES_CLIENTNUM: 1,
                    W.ES_POS_X: 10.0}}
        if t == 2000:
            ents[512] = W.obituary_entity(1, 5, 7, (1.0, 2.0, 3.0), toggle=0)
        if t == 3000:
            ents[512] = W.obituary_entity(1, 6, 7, (1.0, 2.0, 3.0), toggle=0x100)
        d.write_snapshot(t, {W.PS_CLIENTNUM: 0, W.PS_ORIGIN_X: float(f)}, ents)
    out = DM73Parser(d.save(tmp_path / "two.dm_73")).parse()
    obits = [e for e in out["events"] if e["type"] == "obituary"]
    assert len(obits) == 2, "the toggle bit is what distinguishes them"
    assert [e["victim_client"] for e in obits] == [5, 6]


def test_configstring_update_rides_a_server_command(tmp_path):
    """svc_configstring only appears inside the gamestate; a mid-demo change
    arrives as `cs <index> "<value>"`, which is what CA alive counts use."""
    d = W.DemoWriter()
    d.write_gamestate(_ca_configstrings())
    d.write_configstring(1, 664, "3")
    out = DM73Parser(d.save(tmp_path / "cs.dm_73")).parse()
    assert out["packet_errors"] == 0
