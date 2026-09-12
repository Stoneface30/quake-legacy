"""The WolfcamQL source PANTHEON builds against is pinned, verified and
bootstrapped -- exactly, or not at all (third_party/wolfcamql/SOURCE.json).

Every archive here is built in tmp_path; the "upstream" download is a
file:// URL. No test touches the network or the real tree."""
import hashlib
import io
import json
import tarfile
from pathlib import Path

import pytest


def _tar(tmp_path: Path, members: dict[str, bytes], name="src.tar.gz") -> Path:
    p = tmp_path / name
    with tarfile.open(p, "w:gz") as t:
        for n, data in members.items():
            info = tarfile.TarInfo(n); info.size = len(data)
            t.addfile(info, io.BytesIO(data))
    return p


def _manifest(tmp_path, arc: Path, **over) -> Path:
    m = {"name": "t", "version": "1", "archive": arc.name,
         "sha256": hashlib.sha256(arc.read_bytes()).hexdigest(),
         "size": arc.stat().st_size, "top_level_dir": "top",
         "extract_to": str(tmp_path / "out"), "mirrors": [],
         "local_fallback_env": "T_ARCHIVE"}
    m.update(over)
    p = tmp_path / "SOURCE.json"; p.write_text(json.dumps(m)); return p


def _tree(tmp_path, files: dict[str, bytes]) -> Path:
    p = tmp_path / "TREE.sha256"
    p.write_text("".join(f"{hashlib.sha256(d).hexdigest()}  {n}\n"
                         for n, d in sorted(files.items())))
    return p


def _upstream(tmp_path, monkeypatch, members, tree, extras=()) -> Path:
    """A manifest whose pinned archive is nowhere, so the bootstrap must take
    the upstream-by-commit path and verify the tree file by file."""
    monkeypatch.delenv("T_ARCHIVE", raising=False)
    up = _tar(tmp_path, members, name="upstream.tar.gz")
    return _manifest(tmp_path, up, archive="absent.tar.gz", sha256="f" * 64, size=1,
                     upstream_tarball=up.as_uri(), tree_manifest=str(_tree(tmp_path, tree)),
                     upstream_extras_ignored=list(extras))


def test_extracts_after_verifying(tmp_path, monkeypatch):
    from scripts import bootstrap_wolfcamql as B
    a = _tar(tmp_path, {"top/a.c": b"int x;"})
    monkeypatch.setenv("T_ARCHIVE", str(a))
    out = B.bootstrap(_manifest(tmp_path, a))
    assert (out / "top" / "a.c").read_bytes() == b"int x;"
    assert json.loads((out / ".bootstrap.json").read_text())["sha256"] == \
        hashlib.sha256(a.read_bytes()).hexdigest()


def test_a_wrong_checksum_fails_before_anything_is_extracted(tmp_path, monkeypatch):
    from scripts import bootstrap_wolfcamql as B
    a = _tar(tmp_path, {"top/a.c": b"int x;"})
    monkeypatch.setenv("T_ARCHIVE", str(a))
    with pytest.raises(B.ChecksumMismatch):
        B.bootstrap(_manifest(tmp_path, a, sha256="0" * 64))
    assert not (tmp_path / "out").exists()


def test_a_path_escaping_member_is_refused(tmp_path, monkeypatch):
    from scripts import bootstrap_wolfcamql as B
    a = _tar(tmp_path, {"top/../../evil.c": b"x"})
    monkeypatch.setenv("T_ARCHIVE", str(a))
    with pytest.raises(B.UnsafeArchive):
        B.bootstrap(_manifest(tmp_path, a))
    assert not (tmp_path / "evil.c").exists()


def test_an_existing_tree_is_adopted_only_if_it_matches(tmp_path, monkeypatch):
    from scripts import bootstrap_wolfcamql as B
    a = _tar(tmp_path, {"top/a.c": b"int x;"})
    monkeypatch.setenv("T_ARCHIVE", str(a))
    out = tmp_path / "out"; (out / "top").mkdir(parents=True)
    (out / "top" / "a.c").write_bytes(b"int y;")          # differs
    with pytest.raises(B.TreeMismatch):
        B.bootstrap(_manifest(tmp_path, a), adopt=True)
    (out / "top" / "a.c").write_bytes(b"int x;")          # matches
    B.bootstrap(_manifest(tmp_path, a), adopt=True)
    assert (out / ".bootstrap.json").exists()


def test_no_source_is_a_hard_failure(tmp_path, monkeypatch):
    from scripts import bootstrap_wolfcamql as B
    a = _tar(tmp_path, {"top/a.c": b"x"})
    monkeypatch.delenv("T_ARCHIVE", raising=False)
    m = _manifest(tmp_path, a); a.unlink()
    with pytest.raises(B.NoSource):
        B.bootstrap(m)


def test_upstream_by_commit_is_verified_file_by_file(tmp_path, monkeypatch):
    from scripts import bootstrap_wolfcamql as B
    m = _upstream(tmp_path, monkeypatch,
                  {"repo-73e2d70/a.c": b"int x;", "repo-73e2d70/track-svn.txt": b"svn",
                   "repo-73e2d70/pkg/readme": b"r"},
                  {"a.c": b"int x;"}, extras=["track-svn.txt", "pkg/"])
    out = B.bootstrap(m)
    assert (out / "top" / "a.c").read_bytes() == b"int x;"
    # packaging extras are dropped: the tree equals the pinned archive's
    assert not (out / "top" / "track-svn.txt").exists()
    assert not (out / "top" / "pkg").exists()
    assert json.loads((out / ".bootstrap.json").read_text())["source"].startswith("upstream")


def test_an_extra_listed_as_a_directory_may_be_a_plain_file(tmp_path, monkeypatch):
    """Found by the clean-clone proof: upstream `macwolfcambuild` is a file."""
    from scripts import bootstrap_wolfcamql as B
    m = _upstream(tmp_path, monkeypatch,
                  {"repo/a.c": b"int x;", "repo/macwolfcambuild": b"#!/bin/sh"},
                  {"a.c": b"int x;"}, extras=["macwolfcambuild/"])
    out = B.bootstrap(m)
    assert not (out / "top" / "macwolfcambuild").exists()


def test_one_altered_byte_upstream_is_refused(tmp_path, monkeypatch):
    from scripts import bootstrap_wolfcamql as B
    m = _upstream(tmp_path, monkeypatch, {"repo/a.c": b"int y;"}, {"a.c": b"int x;"})
    with pytest.raises(B.ChecksumMismatch):
        B.bootstrap(m)
    assert not (tmp_path / "out").exists()


def test_a_file_upstream_that_nobody_pinned_is_refused(tmp_path, monkeypatch):
    from scripts import bootstrap_wolfcamql as B
    m = _upstream(tmp_path, monkeypatch, {"repo/a.c": b"int x;", "repo/b.c": b"?"},
                  {"a.c": b"int x;"})
    with pytest.raises(B.TreeMismatch):
        B.bootstrap(m)
    assert not (tmp_path / "out").exists()


def test_a_pinned_file_missing_upstream_is_refused(tmp_path, monkeypatch):
    from scripts import bootstrap_wolfcamql as B
    m = _upstream(tmp_path, monkeypatch, {"repo/a.c": b"int x;"},
                  {"a.c": b"int x;", "b.c": b"int z;"})
    with pytest.raises(B.TreeMismatch):
        B.bootstrap(m)


def test_adopt_checks_the_tree_manifest_without_needing_the_archive(tmp_path, monkeypatch):
    from scripts import bootstrap_wolfcamql as B
    monkeypatch.delenv("T_ARCHIVE", raising=False)
    gone = _tar(tmp_path, {"top/a.c": b"int x;"}, name="gone.tar.gz")
    m = _manifest(tmp_path, gone, tree_manifest=str(_tree(tmp_path, {"a.c": b"int x;"})))
    gone.unlink()
    out = tmp_path / "out"; (out / "top").mkdir(parents=True)
    (out / "top" / "a.c").write_bytes(b"int x; ")         # one byte more
    with pytest.raises(B.TreeMismatch):
        B.bootstrap(m, adopt=True)
    (out / "top" / "a.c").write_bytes(b"int x;")
    B.bootstrap(m, adopt=True)
    assert (out / ".bootstrap.json").exists()
