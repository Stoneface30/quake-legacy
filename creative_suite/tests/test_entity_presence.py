"""Entity presence is a fact the demo carries, and absence has three meanings.

Before this, a per-player state row existed only when a delta arrived, so
nothing downstream could tell "outside the recorder's snapshot" from "present
and not moving" from "removed". These tests pin the semantics that make the
difference expressible.
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.parser import demo_parse as dp                        # noqa: E402

FIXTURE = Path("G:/QUAKE_LEGACY/demos/"
               "CA-pTnTr4sH-overkill-2012_01_29-19_42_42.dm_73")
FIXTURE_SHA = "a79940882e30b337f2d436207cabbe7cdb2542bec5688450c312823c3e428067"

pytestmark = pytest.mark.skipif(
    not FIXTURE.exists(),
    reason="the audited fixture demo is not on this machine")


@pytest.fixture(scope="module")
def parsed():
    if os.environ.get("DM73_SKIP_SLOW"):
        pytest.skip("slow decode")
    return dp.DM73Parser(str(FIXTURE)).parse()


def test_every_snapshot_reports_its_presence(parsed):
    """One presence row per snapshot, never fewer."""
    assert len(parsed["snapshot_presence"]) == parsed["snapshot_count"]


def test_a_present_player_always_has_a_state_row(parsed):
    """The row count must equal the presence count, not the delta count.

    Emitting a row only when a delta arrived is what made presence invisible.
    """
    rows = len(parsed["entities"])
    present = sum(x["players_present"] for x in parsed["snapshot_presence"])
    assert rows == present


def test_every_state_row_declares_how_it_got_its_values(parsed):
    """RECORDED or DELTA_INHERITED, never unlabelled."""
    labels = {r["state_provenance"] for r in parsed["entities"]}
    assert labels <= {"RECORDED", "DELTA_INHERITED"}
    assert labels, "no state rows at all"


def test_slot_reuse_produces_separate_spans(parsed):
    """A slot removed and re-added is two observation windows, not one.

    Splicing them would interpolate a player across a span in which the
    recording holds nothing about them (HL-6).
    """
    lifetimes = parsed["entity_lifetimes"]
    per_slot = {}
    for span in lifetimes:
        per_slot.setdefault(span["entity_num"], []).append(span)
    assert any(len(v) > 1 for v in per_slot.values()), \
        "this fixture is known to reuse slots; one span each means the " \
        "removal bit is being ignored"
    for spans in per_slot.values():
        spans.sort(key=lambda s: s["first_ms"])
        for a, b in zip(spans, spans[1:]):
            assert a["end_ms"] <= b["first_ms"], "spans must not overlap"


def test_every_span_says_why_it_ended(parsed):
    """A span that ended because the RECORDING stopped is not a removal."""
    reasons = {s["end_reason"] for s in parsed["entity_lifetimes"]}
    assert reasons <= {"EXPLICIT_REMOVAL", "RECORDING_ENDED"}
    assert None not in reasons


def test_the_recorder_never_appears_as_an_entity(parsed):
    """The server omits a client's own entity from its packet entities.

    Its absence from the entity stream is the protocol, not a coverage gap,
    and any metric that counts it as one is measuring the wrong thing.
    """
    snaps = parsed["snapshots"]
    povs = {}
    for s in snaps:
        c = s.get("client_num")
        if c is not None:
            povs[c] = povs.get(c, 0) + 1
    recorder = max(povs, key=povs.get)
    slots = {x["entity_num"] for x in parsed["entity_lifetimes"]}
    assert recorder not in slots


def test_presence_counts_never_exceed_the_roster(parsed):
    roster = [k for k, v in parsed["players"].items()
              if v.get("team") in ("RED", "BLUE")]
    peak = max(x["players_present"] for x in parsed["snapshot_presence"])
    assert peak <= len(roster)
