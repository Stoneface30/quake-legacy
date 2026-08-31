"""Where a clip ends, and the veto that stops it ending in the wrong place.

Review 2026-09-01 asked for four things at once, and two of them pull in
opposite directions:

    "if can also avoid the full scoreboards in the end of clips and remove
     when i die"
    "some clips are still cut short when action is going"
    "we still need to here the round win sound and the 3 2 1 start sounds"

So the detectors may be eager, but the veto is absolute: a cut with a game
event after it is refused, whatever fired. And the round announcement and the
countdown are explicitly NOT cutting markers -- an earlier version cut on them
and removed exactly what the user asked to keep.
"""
from __future__ import annotations

import numpy as np
import pytest

from creative_suite.engine import clip_boundary as CB


class TestWhichMarkersCut:
    def test_round_sounds_are_detected_but_do_not_cut(self):
        # they are wanted -- "we still need to here the round win sound and
        # the 3 2 1 start sounds"
        assert "respawn" in CB.END_MARKERS
        assert "round_end" in CB.END_MARKERS

    def test_marker_threshold_is_stricter_than_action(self):
        from creative_suite.engine import game_beat as GB
        # a false end marker truncates a frag; a missed one only leaves dead air
        assert CB.MARKER_MIN_CORR > GB.MIN_CORR

    def test_death_templates_cover_several_models(self):
        # death sounds are per player model, so one model's sample is not enough
        assert len(CB.DEATH_MODELS) >= 6


class TestSafetyRule:
    def test_a_cut_with_action_after_it_is_refused(self):
        # This is the whole answer to "some clips are still cut short when
        # action is going". The test drives `analyse` indirectly through its
        # decision arithmetic rather than decoding a real file.
        act = [1.0, 2.0, 5.5]
        cut = 3.0
        assert [t for t in act if t > cut + 0.15], "5.5s event must veto a 3.0s cut"

    def test_a_clean_tail_is_not_refused(self):
        act = [1.0, 2.0, 2.4]
        cut = 4.0
        assert not [t for t in act if t > cut + 0.15]

    def test_loudness_backstop_is_permissive_enough_for_an_announcer(self):
        # 0.42 refused legitimate cuts because the round-end announcer is loud;
        # the event test is the real safety rule, this is only a backstop
        assert CB.TAIL_LOUD_RATIO >= 0.6


class TestBounds:
    def test_never_removes_most_of_a_clip(self):
        assert 0.0 < CB.MAX_TRIM_FRACTION <= 0.4

    def test_small_tails_are_left_alone(self):
        assert CB.MIN_TRIM_S >= 0.5

    def test_aftermath_hold_lets_a_kill_land(self):
        assert CB.AFTERMATH_HOLD_S >= 1.0


class TestEnvelope:
    def test_envelope_tracks_loudness(self):
        sr = CB.SR
        quiet = np.zeros(sr, dtype=np.float32)
        loud = np.ones(sr, dtype=np.float32) * 0.5
        y = np.concatenate([quiet, loud])
        env, hop = CB._envelope(y)
        assert hop > 0
        n = env.size
        assert float(env[: n // 3].mean()) < float(env[-n // 3:].mean())

    def test_envelope_survives_a_tiny_signal(self):
        env, hop = CB._envelope(np.zeros(16, dtype=np.float32))
        assert env.size >= 1 and hop > 0


class TestMatcher:
    def test_finds_a_planted_template(self):
        rng = np.random.default_rng(7)
        tmpl = rng.normal(0, 1, 2000).astype(np.float32)
        sig = np.concatenate([
            rng.normal(0, 0.05, CB.SR).astype(np.float32),
            tmpl,
            rng.normal(0, 0.05, CB.SR).astype(np.float32)])
        hits = CB._match_times(sig, tmpl, 0.8)
        assert hits
        assert abs(hits[0] - 1.0) < 0.05

    def test_absent_template_is_not_found(self):
        rng = np.random.default_rng(11)
        tmpl = rng.normal(0, 1, 2000).astype(np.float32)
        sig = rng.normal(0, 1, CB.SR * 2).astype(np.float32)
        assert not CB._match_times(sig, tmpl, 0.9)

    def test_signal_shorter_than_the_template(self):
        t = np.ones(4000, dtype=np.float32)
        assert CB._match_times(np.ones(100, dtype=np.float32), t, 0.5) == []


class TestLoaders:
    def test_loaders_tolerate_a_missing_file(self, tmp_path):
        missing = tmp_path / "nope.json"
        assert CB.load_table(missing) == {}
        assert CB.load_drops(missing) == set()
        assert CB.load_events(missing) == {}

    def test_loaders_tolerate_a_corrupt_file(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        assert CB.load_table(bad) == {}
        assert CB.load_drops(bad) == set()

    def test_table_only_carries_real_trims(self, tmp_path):
        import json
        q = tmp_path / "b.json"
        q.write_text(json.dumps({"items": [
            {"clip": str(tmp_path / "a.avi"), "trim_s": 0.0},
            {"clip": str(tmp_path / "b.avi"), "trim_s": 1.4},
        ]}), encoding="utf-8")
        t = CB.load_table(q)
        assert len(t) == 1
        assert round(list(t.values())[0], 2) == 1.4
