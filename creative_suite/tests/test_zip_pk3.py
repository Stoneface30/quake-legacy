"""Task 8.2 — pk3 zip writer round-trip.

A pk3 is plain ZIP with .pk3 extension. The Quake engine scans baseq3
alphabetically and loads pk3s in order, so `zzz_photorealistic.pk3` MUST
land after `pak00.pk3` to override. That's a file-naming concern, not a
zip-internal concern.

Internal paths matter a LOT though:
  - Case-sensitive on Linux but not on Windows. Both engines normalize,
    but wolfcam expects LOWERCASE forward-slash paths (no backslash).
  - Paths must NOT start with `/` or contain `..`.
  - The engine rejects zips with ZIP_LZMA; DEFLATE + STORED are the only
    safe compressions. We pick DEFLATE for size.
"""
from __future__ import annotations

import hashlib
import io
import zipfile
from pathlib import Path

import pytest

pytest.importorskip("PIL")

from PIL import Image  # noqa: E402

from creative_suite.pk3_build.zip_pk3 import zip_pk3  # noqa: E402


def _tga_bytes(color: tuple[int, int, int, int]) -> bytes:
    """Build an in-memory TGA blob for testing."""
    img = Image.new("RGBA", (32, 32), color)
    buf = io.BytesIO()
    img.save(buf, format="TGA")
    return buf.getvalue()


def test_zip_pk3_writes_deflate_zip_with_exact_paths(tmp_path: Path) -> None:
    entries = [
        ("textures/base_wall/basewall01b.tga", _tga_bytes((90, 90, 90, 255))),
        ("textures/skin/visor_head.tga",        _tga_bytes((200, 50, 50, 255))),
    ]
    pk3 = tmp_path / "zzz_photorealistic.pk3"

    sha = zip_pk3(entries, pk3)

    assert pk3.exists() and pk3.stat().st_size > 0
    # Returned sha256 matches the file on disk — critical for pack_builds audit trail.
    assert sha == hashlib.sha256(pk3.read_bytes()).hexdigest()
    assert len(sha) == 64

    with zipfile.ZipFile(pk3) as z:
        names = z.namelist()
        assert set(names) == {e[0] for e in entries}
        # Every member must be DEFLATE-compressed (engine rejects LZMA).
        for info in z.infolist():
            assert info.compress_type == zipfile.ZIP_DEFLATED, (
                f"{info.filename} has compress_type={info.compress_type}, "
                "Quake engine only accepts STORED/DEFLATE"
            )
        # Content survives round-trip.
        for internal_path, expected in entries:
            assert z.read(internal_path) == expected


def test_zip_pk3_preserves_path_casing(tmp_path: Path) -> None:
    """Asset internal_path casing is authoritative — the DB stores the
    exact case from the ingest pk3. We must NOT lowercase here, because
    a Linux wolfcam build with case-sensitive FS would then miss textures
    that shaders reference with their original case."""
    entries = [
        ("textures/Base_Wall/BaseWall01b.tga", b"x" * 100),
    ]
    pk3 = tmp_path / "case.pk3"
    zip_pk3(entries, pk3)
    with zipfile.ZipFile(pk3) as z:
        assert "textures/Base_Wall/BaseWall01b.tga" in z.namelist()


def test_zip_pk3_rejects_backslash_paths(tmp_path: Path) -> None:
    """Windows users hand-editing clip lists might slip in backslashes.
    The engine's FS layer does NOT reliably normalize these. Fail loud."""
    with pytest.raises(ValueError, match=r"backslash|invalid.*path"):
        zip_pk3(
            [("textures\\base_wall\\foo.tga", b"x")],
            tmp_path / "bad.pk3",
        )


def test_zip_pk3_rejects_absolute_and_parent_paths(tmp_path: Path) -> None:
    """Zip-slip class of bugs — never let a pk3 write outside baseq3
    if some future tool decides to extract. The engine reads from within
    the archive, but we're being defensive."""
    for bad_path in ("/etc/passwd", "../pak00.pk3", "textures/../../oops.tga"):
        with pytest.raises(ValueError):
            zip_pk3([(bad_path, b"x")], tmp_path / "bad.pk3")


def test_zip_pk3_is_deterministic_given_same_entries(tmp_path: Path) -> None:
    """sha256 stability matters for pack_builds diffing — the same inputs
    should produce the same pk3 bytes so the UI can tell 'nothing changed
    since last build'. We force timestamp=(1980,1,1) in the writer."""
    entries = [
        ("textures/a/x.tga", b"hello"),
        ("textures/a/y.tga", b"world"),
    ]
    a = tmp_path / "a.pk3"
    b = tmp_path / "b.pk3"
    sha_a = zip_pk3(entries, a)
    sha_b = zip_pk3(entries, b)
    assert sha_a == sha_b, "zip_pk3 must be byte-deterministic for same inputs"
