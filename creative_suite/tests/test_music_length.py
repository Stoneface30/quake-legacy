"""Song length is a selection constraint, not something the mux discovers late.

Selection used to return exactly two tracks ranked on beat coincidence alone,
and the mux then trimmed whatever overflowed the body. When the first song
nearly covered the video by itself the second one played for a few seconds --
the user's report: "try to use correct song length / dont cut song too much and
no 5 sec song", and "overall its 1 or 2 song per video as target is 5/6 min".

These pin the three properties that report asks for: the video is covered, no
song appears as a stub, and no song is hacked down to a fragment of itself.
"""
from __future__ import annotations

import pytest

from creative_suite.engine import music_beatmatch as MB

XF = 2.0


def track(cid, dur, bpm=130.0, match=0.20):
    return {"content_id": cid, "path": "/lib/{}.mp3".format(cid), "name": cid,
            "duration_s": float(dur), "bpm": float(bpm), "rms_p90": 0.1,
            "match_pct": float(match)}


def covered(plan, body):
    """Playback the plan produces, accounting for the crossfade overlap."""
    return sum(c["play_s"] for c in plan) - XF * (len(plan) - 1)


class TestCoverage:
    def test_plan_covers_the_whole_video(self):
        # Running short is the one unrecoverable failure: it ends the video in
        # silence.
        for body in (240.0, 295.0, 350.0):
            plan = MB.plan_for_body([track("a", 300), track("b", 210),
                                     track("c", 180)], body, xfade_s=XF)
            assert plan, "no arrangement for {}s".format(body)
            assert covered(plan, body) >= body - 0.5

    def test_one_song_when_one_song_fits(self):
        plan = MB.plan_for_body([track("long", 310), track("b", 200)],
                                295.0, xfade_s=XF)
        assert len(plan) == 1
        assert plan[0]["play_s"] == pytest.approx(295.0)

    def test_two_songs_when_none_is_long_enough(self):
        plan = MB.plan_for_body([track("a", 200), track("b", 210)],
                                350.0, xfade_s=XF)
        assert len(plan) == 2
        assert covered(plan, 350.0) >= 349.5


class TestNoStubs:
    def test_never_returns_a_five_second_song(self):
        # The exact defect: song one nearly covers the body, so the remainder
        # left for song two is a few seconds. That pair must be REFUSED, not
        # trimmed into existence.
        plan = MB.plan_for_body([track("almost", 292), track("b", 200)],
                                295.0, xfade_s=XF)
        assert all(c["play_s"] >= MB.MIN_TRACK_PLAY_S for c in plan)

    def test_every_song_clears_the_floor_across_many_body_lengths(self):
        pool = [track("t{}".format(i), d, bpm=130.0)
                for i, d in enumerate((97, 150, 180, 200, 210, 257, 300, 363))]
        for body in range(200, 420, 7):
            plan = MB.plan_for_body(pool, float(body), xfade_s=XF)
            if not plan:
                continue
            assert min(c["play_s"] for c in plan) >= MB.MIN_TRACK_PLAY_S - 0.5, body

    def test_floor_is_a_musically_meaningful_run(self):
        assert MB.MIN_TRACK_PLAY_S >= 60.0


class TestTruncation:
    def test_never_discards_more_than_the_cut_ceiling(self):
        pool = [track("a", 200), track("b", 600)]
        plan = MB.plan_for_body(pool, 300.0, xfade_s=XF)
        for c in plan:
            kept = c["play_s"] / c["duration_s"]
            assert kept >= 1.0 - MB.MAX_CUT_FRACTION - 1e-6

    def test_a_wildly_long_song_is_not_used_as_a_solo_stub(self):
        # A 20-minute track "covers" a 5-minute video, but 75% of it is thrown
        # away. That is exactly the over-cutting the user objected to.
        plan = MB.plan_for_body([track("epic", 1200)], 300.0, xfade_s=XF)
        assert plan == []


class TestPairing:
    def test_pairs_stay_close_in_tempo(self):
        # "when a video has 2 songs use 2 song that are matching / bpm wise"
        pool = [track("a", 200, bpm=130.0), track("far", 210, bpm=95.0)]
        assert MB.plan_for_body(pool, 350.0, xfade_s=XF) == []
        pool.append(track("near", 210, bpm=133.0))
        plan = MB.plan_for_body(pool, 350.0, xfade_s=XF)
        assert len(plan) == 2
        assert {c["content_id"] for c in plan} == {"a", "near"}

    def test_beat_match_still_decides_between_valid_arrangements(self):
        # Structure gates; it must not override the musical choice. A much
        # better-matching pair beats a mediocre solo.
        pool = [track("solo", 310, match=0.10),
                track("p1", 200, bpm=130.0, match=0.40),
                track("p2", 210, bpm=130.0, match=0.40)]
        plan = MB.plan_for_body(pool, 295.0, xfade_s=XF)
        assert {c["content_id"] for c in plan} == {"p1", "p2"}

    def test_a_marginally_better_pair_does_not_beat_a_clean_solo(self):
        pool = [track("solo", 310, match=0.30),
                track("p1", 200, bpm=130.0, match=0.305),
                track("p2", 210, bpm=130.0, match=0.305)]
        plan = MB.plan_for_body(pool, 295.0, xfade_s=XF)
        assert len(plan) == 1 and plan[0]["content_id"] == "solo"


class TestDegenerate:
    def test_no_candidates_means_no_plan(self):
        assert MB.plan_for_body([], 295.0) == []

    def test_zero_body_means_no_plan(self):
        assert MB.plan_for_body([track("a", 300)], 0.0) == []

    def test_nothing_fits_returns_empty_rather_than_a_bad_plan(self):
        assert MB.plan_for_body([track("tiny", 90)], 295.0, xfade_s=XF) == []
