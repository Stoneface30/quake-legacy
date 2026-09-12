"""Make the WolfcamQL source PANTHEON builds against exist -- exactly, or not at all.

Reads third_party/wolfcamql/SOURCE.json. Sources, in order:

  1. the pinned archive: the local fallback env var, the download cache, then
     each mirror -- size and SHA-256 verified BEFORE anything is extracted;
  2. upstream by commit (`upstream_tarball`): GitHub's generated tarballs are
     not byte-stable, but file contents at a commit are, so the download is
     extracted into a staging directory and verified file by file against
     `tree_manifest`. A missing file, an altered byte or a file nobody pinned
     (other than `upstream_extras_ignored`) refuses the whole tree.

Members that would escape the target are refused. A mismatch is a hard
failure: PANTHEON is never built against bytes nobody pinned.

    python scripts/bootstrap_wolfcamql.py            # extract if absent
    python scripts/bootstrap_wolfcamql.py --adopt    # verify an existing tree, then stamp it
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "third_party" / "wolfcamql" / "SOURCE.json"
CACHE = ROOT / ".cache" / "third_party"          # gitignored


class ChecksumMismatch(RuntimeError): ...
class UnsafeArchive(RuntimeError): ...
class TreeMismatch(RuntimeError): ...
class NoSource(RuntimeError): ...


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _resolve(p: str) -> Path:
    return Path(p) if Path(p).is_absolute() else ROOT / p


def _verify(path: Path, m: dict) -> Path:
    if path.stat().st_size != m["size"] or _sha(path) != m["sha256"]:
        raise ChecksumMismatch(f"{path}: expected {m['sha256']} ({m['size']} bytes)")
    return path


def _download(url: str, dest: Path) -> None:
    with urllib.request.urlopen(url, timeout=60) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f)


def _pinned_archive(m: dict) -> Path | None:
    """The pinned archive, verified -- or None if no copy is reachable."""
    env = os.getenv(m.get("local_fallback_env", ""))
    if env and Path(env).exists():
        return _verify(Path(env), m)
    cached = CACHE / m["sha256"] / m["archive"]
    if cached.exists():
        return _verify(cached, m)
    for url in m.get("mirrors", []):
        cached.parent.mkdir(parents=True, exist_ok=True)
        tmp = cached.with_suffix(".part")
        try:
            _download(url, tmp)
            _verify(tmp, m)
        except ChecksumMismatch:
            tmp.unlink(missing_ok=True)
            raise
        except OSError:
            tmp.unlink(missing_ok=True)
            continue
        tmp.replace(cached)
        return cached
    return None


def _read_tree(m: dict) -> dict[str, str] | None:
    if not m.get("tree_manifest"):
        return None
    tree = {}
    for line in _resolve(m["tree_manifest"]).read_text(encoding="utf-8").splitlines():
        if line.strip():
            sha, rel = line.split("  ", 1)
            tree[rel] = sha
    return tree


def _safe_members(t: tarfile.TarFile, top: str | None):
    """Every member under ONE top directory (`top`, or whichever single one the
    archive has), no absolute paths, no `..`, no links or devices."""
    members = t.getmembers()
    tops = {Path(mem.name).parts[0] for mem in members if Path(mem.name).parts}
    for mem in members:
        p = Path(mem.name)
        if p.is_absolute() or ".." in p.parts or mem.issym() or mem.islnk() or mem.isdev():
            raise UnsafeArchive(f"refusing member {mem.name!r}")
    if top is not None and tops - {top}:
        raise UnsafeArchive(f"members outside {top!r}: {sorted(tops - {top})}")
    if len(tops) != 1:
        raise UnsafeArchive(f"expected one top directory, found {sorted(tops)}")
    return tops.pop(), members


def _extract(archive: Path, top: str | None, into: Path) -> Path:
    with tarfile.open(archive, "r:gz") as t:
        name, members = _safe_members(t, top)
        kw = {"filter": "data"} if hasattr(tarfile, "data_filter") else {}
        t.extractall(into, members=members, **kw)
    return into / name


def _is_extra(rel: str, extras) -> bool:
    """`name/` covers a directory's contents AND a plain file of that name:
    upstream `macwolfcambuild` is a file, though the listing reads like a dir."""
    return any(rel == e.rstrip("/") or (e.endswith("/") and rel.startswith(e))
               for e in extras)


def _check_tree(tree_dir: Path, tree: dict[str, str], *, extras=(), exact: bool,
                altered=ChecksumMismatch) -> None:
    for rel, sha in tree.items():
        f = tree_dir / rel
        if not f.is_file():
            raise TreeMismatch(f"{f}: pinned in the tree manifest, missing")
        if _sha(f) != sha:
            raise altered(f"{f}: expected {sha}")
    if exact:
        for f in tree_dir.rglob("*"):
            rel = f.relative_to(tree_dir).as_posix()
            if f.is_file() and rel not in tree and not _is_extra(rel, extras):
                raise TreeMismatch(f"{f}: not in the tree manifest")


def _adopt(m: dict, out: Path, tree: dict[str, str] | None) -> str:
    """Verify a tree already on disk. With a tree manifest the archive is not
    needed; without one, compare against the pinned archive."""
    if tree is not None:
        _check_tree(out / m["top_level_dir"], tree, exact=False, altered=TreeMismatch)
        return "adopted:tree_manifest"
    archive = _pinned_archive(m)
    if archive is None:
        raise NoSource(f"cannot adopt {out}: no tree manifest and no copy of {m['archive']}")
    with tarfile.open(archive, "r:gz") as t:
        _, members = _safe_members(t, m["top_level_dir"])
        for mem in members:
            if mem.isfile():
                disk = out / mem.name
                if not disk.exists() or disk.read_bytes() != t.extractfile(mem).read():
                    raise TreeMismatch(f"{disk} differs from the pinned archive")
    return "adopted:archive"


def bootstrap(manifest: Path = MANIFEST, *, adopt: bool = False) -> Path:
    m = json.loads(Path(manifest).read_text(encoding="utf-8"))
    out = _resolve(m["extract_to"])
    stamp = out / ".bootstrap.json"
    if stamp.exists() and json.loads(stamp.read_text())["sha256"] == m["sha256"]:
        return out
    tree = _read_tree(m)

    if adopt and out.exists():
        source = _adopt(m, out, tree)
    else:
        if out.exists() and any(out.iterdir()):
            raise TreeMismatch(f"{out} exists without a stamp; rerun with --adopt to verify it")
        archive = _pinned_archive(m)                # verified before anything else
        upstream = m.get("upstream_tarball") if tree is not None else None
        if archive is None and not upstream:
            raise NoSource(f"no verified copy of {m['archive']}: set "
                           f"{m.get('local_fallback_env')}, add a mirror, or pin "
                           f"upstream_tarball + tree_manifest in {manifest}")
        out.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(dir=out.parent))
        try:
            content = staging / "content"
            if archive is not None:
                _extract(archive, m["top_level_dir"], content)
                source = "archive"
            else:
                dl = staging / "upstream.tar.gz"
                try:
                    _download(upstream, dl)
                except OSError as e:
                    raise NoSource(f"upstream {upstream}: {e}") from e
                top = _extract(dl, None, staging / "x")
                extras = m.get("upstream_extras_ignored", [])
                _check_tree(top, tree, extras=extras, exact=True)
                for e in extras:                    # the tree equals the archive's
                    p = top / e.rstrip("/")
                    if p.is_dir():
                        shutil.rmtree(p)
                    elif p.exists():
                        p.unlink()
                content.mkdir()
                top.rename(content / m["top_level_dir"])
                source = f"upstream:{m.get('upstream_commit') or upstream}"
            if out.exists():
                out.rmdir()
            shutil.move(str(content), str(out))
        finally:
            shutil.rmtree(staging, ignore_errors=True)

    stamp.write_text(json.dumps({"sha256": m["sha256"], "archive": m["archive"],
                                 "version": m["version"], "source": source}, indent=2))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--adopt", action="store_true")
    a = ap.parse_args()
    try:
        print(bootstrap(adopt=a.adopt))
    except (ChecksumMismatch, UnsafeArchive, TreeMismatch, NoSource) as e:
        print(f"bootstrap_wolfcamql: {e}", file=sys.stderr)
        sys.exit(2)
