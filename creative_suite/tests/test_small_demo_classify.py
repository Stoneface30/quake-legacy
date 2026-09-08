"""Task 2 — classification of demos under 800 KB (charter §4)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "engine" / "parser"))

from small_demo_classify import classify


def _row(**kw):
    base = dict(parse_error=None, packet_errors=0, accepted_frags=0,
                duration_ms=0, rounds=0)
    base.update(kw)
    return base


def test_parse_error_wins():
    assert classify(_row(parse_error="bad header", accepted_frags=5)) == "CORRUPT_UNREADABLE"


def test_packet_errors_with_frags():
    assert classify(_row(packet_errors=3, accepted_frags=2)) == "CORRUPT_RECOVERABLE"


def test_packet_errors_without_frags():
    assert classify(_row(packet_errors=3)) == "TRUNCATED_BUT_PARSEABLE"


def test_short_clip_by_duration():
    assert classify(_row(accepted_frags=1, duration_ms=45000, rounds=3)) == "VALID_SHORT_CLIP"


def test_short_clip_by_rounds():
    assert classify(_row(accepted_frags=4, duration_ms=300000, rounds=1)) == "VALID_SHORT_CLIP"


def test_partial_demo():
    assert classify(_row(accepted_frags=9, duration_ms=300000, rounds=4)) == "VALID_PARTIAL_DEMO"


def test_aborted_zero_rounds_zero_frags():
    assert classify(_row()) == "ABORTED_RECORDING"


def test_aborted_with_rounds_no_frags():
    assert classify(_row(rounds=2, duration_ms=200000)) == "ABORTED_RECORDING"


def test_null_fields_do_not_crash():
    assert classify(_row(accepted_frags=1, duration_ms=None, rounds=None)) == "VALID_SHORT_CLIP"
