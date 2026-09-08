"""Regression: title-card backdrops must resolve against the REPO root.

pick_intro_backdrop_fls() built its search path from config.ROOT, which is
`<repo>/creative_suite` after the Plan-1 restructure. The clip corpus lives at
`<repo>/QUAKE VIDEO`, so the glob matched nothing, silently returned [], and
every title card rendered over black -- a direct violation of Rule P1-Y
("renders over desaturated FL gameplay backdrop ... NEVER over black").
"""
from creative_suite.engine import title_card
from creative_suite.engine.config import REPO_ROOT, Config


def test_backdrop_search_uses_repo_root(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    fl_dir = root / "QUAKE VIDEO" / "T3" / "Part4" / "grp"
    fl_dir.mkdir(parents=True)
    (fl_dir / "Demo (1FL1).avi").write_bytes(b"x")
    (fl_dir / "Demo (1).avi").write_bytes(b"x")

    cfg = Config()
    cfg.clips_root = root / "QUAKE VIDEO"
    monkeypatch.setattr(title_card, "REPO_ROOT", root, raising=False)

    found = title_card.pick_intro_backdrop_fls(4, cfg, count=4)
    assert [p.name for p in found] == ["Demo (1FL1).avi"], (
        "must find nested FL clips under the repo-root corpus"
    )


def test_repo_root_is_the_repo_not_creative_suite():
    assert (REPO_ROOT / "creative_suite").is_dir()
    assert REPO_ROOT.name != "creative_suite"
