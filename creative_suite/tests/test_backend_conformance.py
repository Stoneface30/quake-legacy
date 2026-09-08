"""The A/B suite must be able to FAIL, and must not leak identity."""
from __future__ import annotations

import random

import pytest

from engine.pantheon import conformance as C
from engine.pantheon import offscreen as O


def _rgb(w, h, colour_at):
    out = bytearray()
    for y in range(h):
        for x in range(w):
            out.extend(colour_at(x, y))
    return bytes(out)


# -- the measures do what the verdict assumes -------------------------------

def test_a_camera_shift_barely_moves_the_colour_distribution():
    """The whole design rests on this: the two legs disagree about WHERE
    things are by a fraction of a frame, and the verdict must not read that
    as a visual difference."""
    w, h = 60, 40
    rng = random.Random(7)
    field = [[(rng.randrange(256), rng.randrange(256), rng.randrange(256))
              for _ in range(w + 4)] for _ in range(h)]
    a = _rgb(w, h, lambda x, y: field[y][x])
    shifted = _rgb(w, h, lambda x, y: field[y][x + 3])       # camera moved
    assert C._pixel_share(a, shifted, step=1) > 0.5, \
        "a shifted frame should look very different pixel by pixel"
    assert C._hist_distance(C._histogram(a), C._histogram(shifted)) < 0.05


def test_a_colour_change_moves_it_a_lot():
    w, h = 60, 40
    grey = _rgb(w, h, lambda x, y: (120, 120, 120))
    green = _rgb(w, h, lambda x, y: (120, 220, 120) if x < w // 3 else (120, 120, 120))
    # a third of the frame changes one channel: a third of that channel's
    # mass moves, which is a ninth of the three-channel total
    assert C._hist_distance(C._histogram(grey), C._histogram(green)) > 0.10


def test_the_green_share_finds_the_forced_enemy():
    w, h = 60, 40
    none = _rgb(w, h, lambda x, y: (120, 120, 120))
    some = _rgb(w, h, lambda x, y: (60, 235, 90) if x < w // 4 else (120, 120, 120))
    assert C._green_share(none) == 0
    assert 0.2 < C._green_share(some) < 0.3


def test_exposure_is_read_from_the_frame():
    w, h = 20, 20
    dark = _rgb(w, h, lambda x, y: (20, 20, 20))
    bright = _rgb(w, h, lambda x, y: (200, 200, 200))
    assert C._luma(bright) - C._luma(dark) > 150


# -- the verdict can fail ---------------------------------------------------

def _cmp(hist=0.0, luma=0.0, green=0.0, seconds=(2.3, 2.3)):
    return {"comparable": True,
            "per_frame": {"1.0": {"hist_distance": hist}},
            "max_hist_distance": hist, "median_hist_distance": hist,
            "max_luma_delta": luma, "median_luma_delta": luma,
            "max_green_delta": green, "median_green_delta": green,
            "max_pixel_share": 0.3, "median_pixel_share": 0.3,
            "seconds_a": seconds[0], "seconds_b": seconds[1],
            "frames_compared": 1,
            "alignment_frames": [0], "errors": [], "sampled": [1.0]}


def _run_with(monkeypatch, tmp_path, ab, control=None, repeats=3):
    """Drive run_case with the captures faked out -- no process is started,
    and conftest would refuse one anyway. `ab` is the reading for every
    A-against-B pair, `control` for every B-against-B pair."""
    monkeypatch.setattr(C, "pick", lambda case, seed=0: {
        "performance_id": "PERF:KILL:abc:1:5000", "demo_hash": "abc",
        "client": 1, "kind": "KILL", "t_ms": 50000, "map": "asylum",
        "weapon": "RAIL", "outcome": "KILL", "demo": str(tmp_path / "x.dm_73")})
    seen = []

    def fake_film(moment, *, label, desktop, staging, **kw):
        seen.append({"label": label, "desktop": desktop, **kw})
        return {"ok": True, "avi": str(tmp_path / f"{label}.avi"), "seconds": 1.0,
                "visible_windows": [], "stole_focus": False, "returncode": 0,
                "avis": {label: str(tmp_path / f"{label}.avi")}}

    monkeypatch.setattr(C, "film", fake_film)

    def fake_compare(a, b, *, span_s, cache=None):
        # A is the only clip whose name ends in _A; anything else is a B
        return ab if str(a).endswith("_A.avi") else (control or ab)

    monkeypatch.setattr(C, "compare", fake_compare)
    monkeypatch.setattr(C.M, "save_still", lambda *a, **k: None)
    case = C.Case("T", "why", "kind = 'KILL'")
    res = C.run_case(case, staging=tmp_path, out_dir=tmp_path, repeats=repeats)
    return res, seen


def test_a_washed_out_backend_is_reported_different(monkeypatch, tmp_path):
    res, _ = _run_with(monkeypatch, tmp_path, _cmp(luma=40.0), _cmp(luma=0.5))
    assert res.verdict == "DIFFERENT" and "exposure" in res.detail


def test_an_enemy_that_lost_its_green_is_reported_different(monkeypatch, tmp_path):
    res, _ = _run_with(monkeypatch, tmp_path, _cmp(green=0.09), _cmp(green=0.001))
    assert res.verdict == "DIFFERENT" and "enemy" in res.detail


def test_a_leg_that_filmed_a_shorter_clip_is_reported_different(monkeypatch, tmp_path):
    res, _ = _run_with(monkeypatch, tmp_path, _cmp(seconds=(2.3, 1.1)),
                       _cmp(seconds=(2.3, 2.31)))
    assert res.verdict == "DIFFERENT" and "length" in res.detail


def test_a_quiet_pair_is_equivalent(monkeypatch, tmp_path):
    res, _ = _run_with(monkeypatch, tmp_path, _cmp(hist=0.01, luma=0.5),
                       _cmp(hist=0.012, luma=0.7))
    assert res.verdict == "EQUIVALENT"


def test_a_reading_inside_the_backends_own_spread_passes(monkeypatch, tmp_path):
    """The whole point of filming B three times: A is allowed to differ by as
    much as the Bs differ from each other."""
    res, _ = _run_with(monkeypatch, tmp_path, _cmp(hist=0.03), _cmp(hist=0.05))
    assert res.verdict == "INCONCLUSIVE", \
        "a control past the tolerance means the case cannot decide"
    res, _ = _run_with(monkeypatch, tmp_path, _cmp(hist=0.015), _cmp(hist=0.018))
    assert res.verdict == "EQUIVALENT"


def test_a_backend_that_disagrees_with_itself_makes_the_case_undecidable(
        monkeypatch, tmp_path):
    """The death case measured this: 0.88 s of a dark, nearly frozen scene
    where the backend differed from itself past anything anyone would accept.
    Blaming the desktop for that would be a false finding."""
    res, _ = _run_with(monkeypatch, tmp_path, _cmp(hist=0.021), _cmp(hist=0.05))
    assert res.verdict == "INCONCLUSIVE" and "from itself" in res.detail


def test_without_a_control_the_verdict_says_so(monkeypatch, tmp_path):
    res, _ = _run_with(monkeypatch, tmp_path, _cmp(hist=0.01), repeats=1)
    assert res.verdict == "EQUIVALENT_NO_CONTROL"


def test_three_offscreen_captures_give_three_pairs_each_way(monkeypatch, tmp_path):
    res, seen = _run_with(monkeypatch, tmp_path, _cmp())
    assert [s["label"][-2:] for s in seen] == ["_A", "B1", "B2", "B3"]
    assert len(res.ab) == 3 and len(res.control) == 3


# -- the comparison is controlled -------------------------------------------

def test_the_legs_differ_only_in_the_desktop(monkeypatch, tmp_path):
    _, seen = _run_with(monkeypatch, tmp_path, _cmp())
    assert seen[0]["desktop"] is O.INTERACTIVE
    assert all(s["desktop"] == O.DESKTOP_NAME for s in seen[1:])
    # nothing else was allowed to vary
    rest = [{k: v for k, v in s.items() if k not in ("label", "desktop")}
            for s in seen]
    assert all(r == rest[0] for r in rest)


def test_a_leg_that_produced_nothing_is_not_a_pass(monkeypatch, tmp_path):
    monkeypatch.setattr(C, "pick", lambda case, seed=0: {
        "performance_id": "p", "demo_hash": "abc", "client": 1, "kind": "KILL",
        "t_ms": 50000, "map": "asylum", "weapon": None, "outcome": None,
        "demo": str(tmp_path / "x.dm_73")})
    monkeypatch.setattr(C, "film", lambda *a, **k: {
        "ok": False, "avi": None, "avis": {}, "missing": ["x"], "detail": "timeout"})
    res = C.run_case(C.Case("T", "w", "kind = 'KILL'"), staging=tmp_path,
                     out_dir=tmp_path)
    assert res.verdict == "A_PRODUCED_NOTHING"


# -- the public-repo rule ---------------------------------------------------

def test_a_case_record_names_nobody(monkeypatch, tmp_path):
    res, _ = _run_with(monkeypatch, tmp_path, _cmp())
    assert set(res.moment) == {"performance_id", "demo_hash", "client", "kind",
                               "t_ms", "map", "weapon", "outcome"}
    for key in ("name", "nick", "player", "steam"):
        assert not any(key in k.lower() for k in res.moment)


def test_every_case_is_drawn_from_after_the_seek_settle():
    """A moment near the head of a demo seeks before the first snapshot and
    the engine sits there until the timeout, producing nothing."""
    from creative_suite.engine import wolfcam_capture as wc
    assert C.MIN_T_MS > wc.SEEK_SETTLE_MS + C.PRE_MS


def test_the_ten_cases_are_the_ten_the_brief_asked_for():
    assert [c.name for c in C.CASES] == [
        "RAIL", "LG", "ROCKET", "GRENADE", "JUMP_PAD", "TELEPORT",
        "MULTI_PLAYER_ROUND", "LOW_LIGHT_MAP", "PROJECTILE_IMPACT", "DEATH"]
    for c in C.CASES:
        assert c.why, f"{c.name} does not say what it is for"


@pytest.mark.parametrize("case", C.CASES, ids=lambda c: c.name)
def test_every_case_resolves_to_a_real_moment(case):
    from engine.pantheon import store as S
    if not S.index_db().exists():
        pytest.skip("no performance index on this machine")
    got = C.pick(case)
    assert got is not None, f"{case.name} matches nothing in the index"
    assert got["t_ms"] >= C.MIN_T_MS
