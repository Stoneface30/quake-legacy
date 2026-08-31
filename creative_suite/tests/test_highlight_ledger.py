"""Tests for the episode ledger + unused-clip staging."""
from pathlib import Path
from types import SimpleNamespace

import pytest

from creative_suite.engine import highlight_ledger as L


def _frag(tmp, folder, pov, fls=()):
    d = tmp / "corpus" / folder
    d.mkdir(parents=True, exist_ok=True)
    p = d / pov
    p.write_bytes(b"x" * 2048)
    made = []
    for f in fls:
        q = d / f
        q.write_bytes(b"x" * 2048)
        made.append(q)
    return SimpleNamespace(fp=p, fls=made, tier="T1")


@pytest.fixture
def frags(tmp_path):
    return [
        _frag(tmp_path, "Demo (1)  - 10", "Demo (1)  - 10.avi", ["Demo (1FL1).avi"]),
        _frag(tmp_path, "Demo (2)  - 20", "Demo (2)  - 20.avi"),
        _frag(tmp_path, "Demo (3)  - 30", "Demo (3)  - 30.avi", ["Demo (3FL1).avi"]),
    ]


def test_nothing_used_initially(tmp_path, frags):
    assert L.load_used(4, root=tmp_path) == set()
    assert len(L.remaining(4, frags, root=tmp_path)) == 3


def test_mark_used_then_excluded(tmp_path, frags):
    L.mark_used(4, [frags[0].fp], episode=1, root=tmp_path)
    left = L.remaining(4, frags, root=tmp_path)
    assert [f.fp.name for f in left] == ["Demo (2)  - 20.avi", "Demo (3)  - 30.avi"]


def test_episodes_accumulate(tmp_path, frags):
    L.mark_used(4, [frags[0].fp], episode=1, root=tmp_path)
    L.mark_used(4, [frags[1].fp], episode=2, root=tmp_path)
    assert L.episode_count(4, root=tmp_path) == 2
    assert L.next_episode(4, root=tmp_path) == 3
    assert len(L.remaining(4, frags, root=tmp_path)) == 1


def test_rerendering_an_episode_replaces_it(tmp_path, frags):
    L.mark_used(4, [frags[0].fp], episode=1, root=tmp_path)
    L.mark_used(4, [frags[1].fp], episode=1, root=tmp_path)
    assert L.episode_count(4, root=tmp_path) == 1
    assert L.load_used(4, root=tmp_path) == {"Demo (2)  - 20/Demo (2)  - 20.avi"}


def test_keys_are_portable_not_absolute(tmp_path, frags):
    L.mark_used(4, [frags[0].fp], episode=1, root=tmp_path)
    key = next(iter(L.load_used(4, root=tmp_path)))
    assert not Path(key).is_absolute()
    assert key == "Demo (1)  - 10/Demo (1)  - 10.avi"


def test_parts_do_not_collide(tmp_path, frags):
    L.mark_used(4, [frags[0].fp], episode=1, root=tmp_path)
    assert L.load_used(5, root=tmp_path) == set()


def test_stage_unused_collects_leftovers_with_their_angles(tmp_path, frags):
    used = [frags[0].fp]
    n, folder = L.stage_unused(4, frags, used, root=tmp_path)
    staged = {p.name for p in folder.rglob("*.avi")}
    assert "Demo (2)  - 20.avi" in staged
    assert "Demo (3)  - 30.avi" in staged
    assert "Demo (3FL1).avi" in staged, "an angle must follow its POV"
    assert "Demo (1)  - 10.avi" not in staged, "used clip must not be staged"
    assert n == 3


def test_stage_unused_writes_manifest(tmp_path, frags):
    _, folder = L.stage_unused(4, frags, [frags[0].fp], root=tmp_path)
    txt = (folder / "MANIFEST.txt").read_text(encoding="utf-8")
    assert "does NOT touch the original" in txt
    assert "Demo (2)  - 20.avi" in txt


def test_staging_does_not_consume_extra_space(tmp_path, frags):
    """Hard links, not copies -- the corpus is far too large to duplicate."""
    _, folder = L.stage_unused(4, frags, [], root=tmp_path)
    src = frags[1].fp
    dst = folder / src.name
    assert dst.exists()
    assert dst.stat().st_ino == src.stat().st_ino or dst.stat().st_size == src.stat().st_size


def test_coverage_reports_progress(tmp_path, frags):
    L.mark_used(4, [frags[0].fp], episode=1, root=tmp_path)
    c = L.coverage(4, frags, root=tmp_path)
    assert (c.total, c.used, c.left, c.episodes) == (3, 1, 2, 1)
    assert c.pct == pytest.approx(33.33, abs=0.1)


def test_corrupt_ledger_refuses_rather_than_erasing(tmp_path, frags):
    p = L.ledger_path(4, root=tmp_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(RuntimeError):
        L.load_used(4, root=tmp_path)
