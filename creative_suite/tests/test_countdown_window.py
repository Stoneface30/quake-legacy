"""A frag in the opening seconds of a round opens on the countdown.

The pre-round freeze is the only moment in Clan Arena with a fixed, repeatable
shape, which is what makes it usable as an entry transition. A clip that starts
mid-sprint has nowhere to cut from.

The rule must only ever EXTEND a window. Buying a countdown by giving up
action would be a worse clip, not a better one.
"""
from creative_suite.engine import review_proxy as rp


def test_a_normal_frag_is_symmetric_around_the_kill():
    w = rp.capture_window(100_000, round_start_ms=50_000)
    assert w["start_ms"] == 100_000 - rp.WINDOW_PRE_MS
    assert w["end_ms"] == 100_000 + rp.WINDOW_POST_MS
    assert w["basis"] == "SYMMETRIC_AROUND_KILL"


def test_an_opening_frag_starts_on_the_countdown():
    round_start = 100_000
    kill = round_start + 2_000            # 2s into the round
    w = rp.capture_window(kill, round_start_ms=round_start)
    assert w["start_ms"] == round_start - rp.COUNTDOWN_LEAD_MS
    assert w["basis"] == "COUNTDOWN_LEAD_IN"
    # the kill itself is still fully covered
    assert w["end_ms"] == kill + rp.WINDOW_POST_MS


def test_the_countdown_never_shortens_a_window():
    """The lead-in extends backwards; it must not clip the front off."""
    round_start = 100_000
    for into_round in range(0, rp.EARLY_ROUND_MS + 1, 250):
        kill = round_start + into_round
        plain = kill - rp.WINDOW_PRE_MS
        w = rp.capture_window(kill, round_start_ms=round_start)
        assert w["start_ms"] <= plain, into_round
        assert w["end_ms"] == kill + rp.WINDOW_POST_MS


def test_a_late_frag_gets_no_countdown():
    round_start = 100_000
    kill = round_start + rp.EARLY_ROUND_MS + 1
    w = rp.capture_window(kill, round_start_ms=round_start)
    assert w["basis"] == "SYMMETRIC_AROUND_KILL"


def test_a_frag_before_its_round_start_is_not_treated_as_opening():
    """Negative time into the round is a boundary error, not an opener."""
    w = rp.capture_window(99_000, round_start_ms=100_000)
    assert w["basis"] == "SYMMETRIC_AROUND_KILL"


def test_no_round_start_means_no_countdown():
    w = rp.capture_window(100_000, round_start_ms=None)
    assert w["basis"] == "SYMMETRIC_AROUND_KILL"


def test_a_master_capture_window_wins():
    """A real capture already framed the moment; do not second-guess it."""
    w = rp.capture_window(100_000, round_start_ms=99_000,
                          master={"capture_start_ms": 1, "capture_end_ms": 2})
    assert w == {"start_ms": 1, "end_ms": 2, "basis": "MASTER_CAPTURE"}


def test_the_two_modules_agree_on_what_early_means():
    """review_proxy and round_context must not drift apart.

    One decides the clip window, the other decides the trait. A clip that
    opens on a countdown while the frag is not tagged an opener (or the
    reverse) is a contradiction the reviewer would have to resolve by eye.
    """
    from engine.parser import round_context as rc
    assert rp.EARLY_ROUND_MS == rc.EARLY_ROUND_MS
    assert rp.COUNTDOWN_LEAD_MS == rc.COUNTDOWN_LEAD_MS
