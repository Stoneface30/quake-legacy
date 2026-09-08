"""Duplicate FL angles collapse to ONE, and the survivor is the fastest.

The corpus stores some third-person captures twice -- an original and a
re-export under another name. Playing both shows the viewer the same angle
twice in a row, which reads as a mistake rather than as coverage.

User 2026-08-31: "the FL are sometime twice so if both fl have same video just
use 1", then "the duplicate FL you can keep the fastest of the 2 same version
only". So identity is CONTENT, never the filename, and length breaks the tie --
the tighter export is the one without the dead air.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from creative_suite.engine import render_highlight as RH


class FakeCfg:
    ffmpeg_bin = "ffmpeg"


@pytest.fixture
def angles(tmp_path):
    made = []
    for name, body in (("a.avi", b"AAA"), ("a_copy.avi", b"AAA"),
                       ("b.avi", b"BBB")):
        q = tmp_path / name
        q.write_bytes(body)
        made.append(q)
    return made


def patch(monkeypatch, sigs, durs):
    monkeypatch.setattr(RH, "_angle_signature",
                        lambda q, cfg: sigs.get(Path(q).name))
    monkeypatch.setattr(RH, "probe_duration",
                        lambda q, cfg: durs[Path(q).name])
    RH._SIG_CACHE.clear()


class TestDedupe:
    def test_same_footage_collapses_to_one(self, angles, monkeypatch):
        patch(monkeypatch, {"a.avi": "S1", "a_copy.avi": "S1", "b.avi": "S2"},
              {"a.avi": 8.0, "a_copy.avi": 8.0, "b.avi": 5.0})
        kept = RH._dedupe_angles(angles, FakeCfg())
        assert len(kept) == 2
        assert {q.name for q in kept} == {"a.avi", "b.avi"}

    def test_the_fastest_of_a_duplicate_pair_survives(self, angles, monkeypatch):
        # same footage, different exports -- the SHORTER one is kept even though
        # the longer one comes first in the list
        patch(monkeypatch, {"a.avi": "S1", "a_copy.avi": "S1", "b.avi": "S2"},
              {"a.avi": 9.0, "a_copy.avi": 6.0, "b.avi": 5.0})
        kept = RH._dedupe_angles(angles, FakeCfg())
        assert {q.name for q in kept} == {"a_copy.avi", "b.avi"}

    def test_genuinely_different_angles_are_all_kept(self, angles, monkeypatch):
        # FL1/FL2/FL3 of one frag are different cameras, not duplicates
        patch(monkeypatch, {"a.avi": "S1", "a_copy.avi": "S2", "b.avi": "S3"},
              {"a.avi": 5.0, "a_copy.avi": 14.0, "b.avi": 18.0})
        assert len(RH._dedupe_angles(angles, FakeCfg())) == 3

    def test_order_is_preserved(self, angles, monkeypatch):
        patch(monkeypatch, {"a.avi": "S1", "a_copy.avi": "S2", "b.avi": "S3"},
              {"a.avi": 5.0, "a_copy.avi": 14.0, "b.avi": 18.0})
        assert [q.name for q in RH._dedupe_angles(angles, FakeCfg())] == \
            ["a.avi", "a_copy.avi", "b.avi"]

    def test_an_undecodable_clip_is_its_own_group(self, angles, monkeypatch):
        # signature None must not collapse everything that failed to decode
        monkeypatch.setattr(RH, "_angle_signature", lambda q, cfg: None)
        monkeypatch.setattr(RH, "probe_duration", lambda q, cfg: 5.0)
        RH._SIG_CACHE.clear()
        kept = RH._dedupe_angles(angles, FakeCfg())
        # a.avi and a_copy.avi are byte-identical, so they still collapse;
        # b.avi differs and must survive
        assert "b.avi" in {q.name for q in kept}
        assert len(kept) == 2

    def test_byte_identical_files_collapse_without_a_cfg(self, angles):
        # the no-cfg path still has to dedupe exact copies
        kept = RH._dedupe_angles(angles, None)
        assert len(kept) == 2

    def test_empty_input(self):
        assert RH._dedupe_angles([], FakeCfg()) == []
