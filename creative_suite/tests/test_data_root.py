"""Where the code lives and where the data lives are different questions.

THE BUG THIS PINS. Every reviewer module resolved its databases with
`Path(__file__).resolve().parents[2]` -- the checkout the code was loaded
from. In the main checkout that is also where the data is, so it was right
by coincidence and invisible for as long as there was one checkout.

In a worktree it is wrong, and it fails in the worst available way: SQLite
CREATES whatever file you open. A clean integration worktree therefore did
not raise. It made an empty review database, reported zero human verdicts,
and skipped 212 tests while passing. Data loss and a healthy system are
indistinguishable at that moment.

It got worse when the fix was partial. Repointing fifteen modules and
leaving `identity.py` gave the reviewer the real corpus and an EMPTY
identity store, so "who is the user" came back smaller and the corpus
quietly lost 250 frags -- plausible numbers that were wrong, which is more
dangerous than an error.

THE TEST THAT MATTERS is the last one: both checkouts must report the same
counts from the same data.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

CODE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CODE_ROOT))

from engine.pantheon import store


# ── A + B: both checkouts resolve the same authoritative root ───────────────

def test_the_data_root_is_the_project_not_the_worktree():
    """A worktree under `.claude/worktrees/` shares the project's corpus --
    the databases are gitignored, so they exist exactly once."""
    data = store.data_root()
    parts = CODE_ROOT.parts
    if ".claude" in parts and "worktrees" in parts:
        expected = Path(*parts[:parts.index(".claude")])
        assert data == expected, f"worktree resolved {data}, wanted {expected}"
        assert data != CODE_ROOT, "code root and data root collapsed"
    else:
        assert data == CODE_ROOT


def test_an_explicit_root_overrides_everything(monkeypatch, tmp_path):
    """C: a test that wants an isolated database says so. Nothing infers
    "this is a worktree, therefore a test"."""
    monkeypatch.setenv(store.ENV_ROOT, str(tmp_path))
    assert store.data_root() == tmp_path


# ── D: a missing authoritative root fails closed ────────────────────────────

def test_a_missing_data_root_raises_rather_than_inventing_one(monkeypatch,
                                                              tmp_path):
    """FAIL CLOSED. Returning a path that does not exist is how an empty
    database gets created and believed."""
    monkeypatch.setenv(store.ENV_ROOT, str(tmp_path / "nowhere"))
    with pytest.raises(store.AuthoritativeDataRootNotResolved):
        store.require_database_dir()


def test_a_present_data_root_is_returned():
    d = store.require_database_dir()
    assert d.is_dir() and d.name == "database"


# ── E: importing the reviewer creates no databases ──────────────────────────

REVIEW_MODULES = (
    "creative_suite.engine.review_corpus",
    "creative_suite.engine.review_proxy",
    "creative_suite.engine.identity",
    "creative_suite.engine.review_tags",
    "creative_suite.engine.round_bounds",
    "creative_suite.engine.action_stats",
    "engine.parser.demo_lineage",
)


@pytest.mark.parametrize("mod", REVIEW_MODULES)
def test_review_modules_read_the_shared_root(mod):
    """`identity.py` is in this list deliberately: leaving it behind was the
    partial fix that produced quietly wrong corpus counts."""
    import importlib
    m = importlib.import_module(mod)
    root = getattr(m, "REPO_ROOT", None)
    assert root is not None, f"{mod} has no root"
    assert Path(root) == store.data_root(), \
        f"{mod} resolves {root}, not {store.data_root()}"


def test_importing_the_reviewer_creates_no_stub_database(tmp_path):
    """A fresh checkout that merely IMPORTS the reviewer must not leave a
    database behind. Import-time file creation is what made the empty store
    look like a working one."""
    fake = tmp_path / "checkout"
    (fake / "creative_suite" / "database").mkdir(parents=True)
    env = dict(os.environ, QUAKE_LEGACY_ROOT=str(fake),
               PYTHONPATH=str(CODE_ROOT))
    subprocess.run(
        [sys.executable, "-c",
         "import creative_suite.engine.review_corpus, "
         "creative_suite.engine.identity, creative_suite.engine.review_proxy"],
        cwd=str(CODE_ROOT), env=env, check=True, timeout=180,
        capture_output=True)
    made = sorted(p.name for p in (fake / "creative_suite" / "database").glob("*.db"))
    assert made == [], f"importing the reviewer created {made}"


# ── the one that would have caught all of it ────────────────────────────────

def test_both_checkouts_report_the_same_corpus():
    """THE REAL TEST. Same data, two checkouts, identical counts.

    When this was written the worktree said 32,862 offered and the main
    checkout said 33,102 -- same database, same review_corpus.py, a 250-frag
    difference that came entirely from an empty identity store.
    """
    main = store.data_root()
    if main == CODE_ROOT:
        pytest.skip("only meaningful from a worktree")
    from creative_suite.engine import review_corpus as rc
    here = rc.progress("USER_FRAG")

    env = dict(os.environ, PYTHONPATH=str(main))
    out = subprocess.run(
        [sys.executable, "-c",
         "from creative_suite.engine import review_corpus as rc;"
         "p = rc.progress('USER_FRAG');"
         "print(p['reviewed'], p['total'], p.get('canonical_total'))"],
        cwd=str(main), env=env, capture_output=True, text=True, timeout=600)
    assert out.returncode == 0, out.stderr[-400:]
    a, b, c = out.stdout.split()
    assert (int(a), int(b), int(c)) == (
        here["reviewed"], here["total"], here["canonical_total"]), \
        f"main says {out.stdout.strip()}, worktree says {here['reviewed']} " \
        f"{here['total']} {here['canonical_total']}"
