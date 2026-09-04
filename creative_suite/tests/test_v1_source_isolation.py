"""V1 is reference history. V2 media is generated from game truth.

A V1 render is a finished editorial decision -- trimmed, graded, speed-ramped,
cut to music that is no longer the plan. Reviewing one and calling it a moment
would be judging an old edit and recording that verdict against a canonical
occurrence. These tests keep the two apart structurally rather than by
convention.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from creative_suite.engine import media_provenance as mp     # noqa: E402

REPO = mp.REPO_ROOT

# Every module that can turn a path into playable media.
MEDIA_PATH_MODULES = (
    "creative_suite/engine/review_proxy.py",
    "creative_suite/engine/public_clip_export.py",
    "creative_suite/engine/round_story.py",
    "creative_suite/engine/movement_moments.py",
    "creative_suite/api/review.py",
)


def test_v1_render_directories_are_legacy_and_v2_cache_is_not():
    """`output/` holds V1 Part renders at its root AND the V2 proxy cache
    underneath, so the rule cannot be "output is legacy". This is the split."""
    assert mp.is_legacy(REPO / "QUAKE VIDEO" / "T1" / "Part1" / "a.avi")
    assert mp.is_legacy(REPO / "output" / "Part4_highlight.mp4")
    assert mp.is_legacy(REPO / "FRAGMOVIE VIDEOS" / "IntroPart2.mp4")
    assert not mp.is_legacy(REPO / "output" / "demo_v2" / "review_proxies" / "k.mp4")
    assert not mp.is_legacy(REPO / "demos" / "x.dm_73")


def test_only_a_raw_demo_may_become_a_capture():
    mp.assert_demo_source(REPO / "demos" / "x.dm_73")
    for bad in (REPO / "QUAKE VIDEO" / "T2" / "b.avi",
                REPO / "output" / "Part7_highlight.mp4",
                REPO / "output" / "demo_v2" / "review_proxies" / "k.mp4",
                REPO / "docs" / "stray.dm_73"):
        with pytest.raises(mp.LegacySourceRefused):
            mp.assert_demo_source(bad)


def test_the_v2_staging_area_is_a_legitimate_source():
    """Wolfcam captures from a staged copy, and 83 real demos live under
    output/demo_v2/_wolfcam_staging. That is V2 machinery, not V1 output."""
    staged = (REPO / "output" / "demo_v2" / "_wolfcam_staging" /
              "wolfcam-ql" / "demos" / "x.dm_73")
    assert not mp.is_legacy(staged)
    mp.assert_demo_source(staged)


def test_a_fixture_outside_the_repository_is_not_refused():
    """The rule is about V1 output, not about location. V1 contains ZERO
    .dm_73 files, so demanding every source sit under demos/ refused honest
    cases -- test fixtures among them -- while protecting nothing extra."""
    mp.assert_demo_source(Path("C:/elsewhere/fixture.dm_73"))


def test_there_is_no_authoritative_provenance_for_a_v1_render():
    """The refusal has a name so it can be reported; it is not a value any
    asset may hold."""
    assert mp.V1_RENDER_SOURCE not in mp.AUTHORITATIVE
    assert set(mp.AUTHORITATIVE) == {
        "RAW_DEMO_CAPTURE", "DERIVED_ROUND_CAPTURE",
        "RECONSTRUCTED_CURRENT", "SYNTHETIC_CURRENT"}


def test_no_media_module_references_a_v1_directory():
    """No lookup, and no fallback, may name V1 output. Checked as source
    text because the failure mode is a path someone adds later."""
    banned = ("QUAKE VIDEO", "FRAGMOVIE VIDEOS", "_highlight",
              "render_part_v6", "clip_lists")
    offenders = []
    for rel in MEDIA_PATH_MODULES:
        src = (REPO / rel).read_text(encoding="utf-8")
        for b in banned:
            if b in src:
                offenders.append(f"{rel}: {b}")
    assert not offenders, f"V2 media path reaches V1 output: {offenders}"


def test_no_media_module_globs_for_clips():
    """A glob over a media directory is how a fallback silently acquires V1
    footage. There is none, and there should stay none."""
    offenders = []
    for rel in MEDIA_PATH_MODULES:
        src = (REPO / rel).read_text(encoding="utf-8")
        for pat in (".glob(", ".rglob(", ".iterdir("):
            if pat in src:
                offenders.append(f"{rel}: {pat}")
    # public_clip_export lists its own export directory, which is V2 output.
    offenders = [o for o in offenders if "public_clip_export" not in o]
    assert not offenders, f"media lookup uses a directory scan: {offenders}"


def test_the_proxy_source_is_guarded_where_it_is_used():
    """demo_source() returns whatever a database row holds. A row is not a
    guarantee, so the check lives at the point of use."""
    src = (REPO / "creative_suite/engine/review_proxy.py").read_text(encoding="utf-8")
    assert src.count("assert_demo_source") >= 2, \
        "guard both the request and the capture"
    exp = (REPO / "creative_suite/engine/public_clip_export.py").read_text(encoding="utf-8")
    assert "assert_demo_source" in exp


@pytest.mark.parametrize("db,table,col", [
    ("frags_rebuilt.db", "demos", "path"),
])
def test_every_stored_demo_path_is_a_raw_demo(db, table, col):
    """The corpus itself, not just the code. 4,292 rows at time of writing."""
    p = REPO / "creative_suite" / "database" / db
    if not p.exists():
        pytest.skip(f"{db} not present")
    c = sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True)
    bad = [r[0] for r in c.execute(f"SELECT {col} FROM {table}")
           if mp.is_legacy(r[0]) or not str(r[0]).lower().endswith(".dm_73")]
    assert not bad, f"{len(bad)} stored paths are not raw demos, e.g. {bad[:2]}"


def test_no_cached_proxy_was_built_from_v1_media():
    """Every cached clip must live in the V2 cache and name a demo the corpus
    knows. Audited at 63 rows; nothing needed invalidating."""
    ed = REPO / "creative_suite" / "database" / "editorial.db"
    fr = REPO / "creative_suite" / "database" / "frags_rebuilt.db"
    if not (ed.exists() and fr.exists()):
        pytest.skip("databases not present")
    c = sqlite3.connect(f"file:{ed.as_posix()}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    rows = c.execute("SELECT demo_name, mp4_path FROM review_proxies").fetchall()
    d = sqlite3.connect(f"file:{fr.as_posix()}?mode=ro", uri=True)
    known = {n for (n,) in d.execute("SELECT name FROM demos")}
    for r in rows:
        if r["mp4_path"]:
            assert not mp.is_legacy(r["mp4_path"]), r["mp4_path"]
        assert r["demo_name"] in known, r["demo_name"]
