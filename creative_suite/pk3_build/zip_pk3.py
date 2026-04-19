"""Write a pk3 (ZIP) from a list of (internal_path, bytes) entries.

Quake pk3 constraints we enforce here:
  - forward-slash paths only (no backslash — Linux wolfcam dies on them)
  - no absolute paths, no `..` segments (defensive — zip-slip class bugs)
  - DEFLATE compression for every member (engine rejects LZMA)
  - deterministic output: fixed timestamp (1980-01-01) + sorted entries,
    so the same approved-variant set always produces the same sha256.
    This lets `pack_builds` rows be idempotent — building twice with no
    changes does NOT insert a new row for the UI.

Returns the sha256 hex digest of the written pk3 so api/packs.py can
stamp it into the `pack_builds.sha256` column.
"""
from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path


_FROZEN_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def _validate_internal_path(p: str) -> None:
    if "\\" in p:
        raise ValueError(f"invalid pk3 path (backslash): {p!r}")
    if p.startswith("/"):
        raise ValueError(f"invalid pk3 path (absolute): {p!r}")
    parts = p.split("/")
    if any(seg in ("", "..", ".") for seg in parts):
        raise ValueError(f"invalid pk3 path (parent/empty segment): {p!r}")


def zip_pk3(
    entries: list[tuple[str, bytes]],
    dst: Path,
    *,
    pack_slug: str | None = None,
) -> str:
    """Write entries into ``dst`` (a .pk3) with DEFLATE compression.

    ``pack_slug`` is accepted for API symmetry but not embedded — the
    slug lives in the DB row, not inside the archive.
    """
    _ = pack_slug  # reserved for future meta file
    for internal_path, _blob in entries:
        _validate_internal_path(internal_path)

    dst.parent.mkdir(parents=True, exist_ok=True)

    # Sort by path for determinism — zipfile writes in the order we feed it.
    ordered = sorted(entries, key=lambda e: e[0])

    with zipfile.ZipFile(dst, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for internal_path, blob in ordered:
            info = zipfile.ZipInfo(filename=internal_path, date_time=_FROZEN_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            # external_attr = regular file 0644 (engine doesn't care, but keeps
            # `unzip` happy on Linux if a user ever cracks the pk3 open).
            info.external_attr = (0o644 & 0xFFFF) << 16
            z.writestr(info, blob)

    return hashlib.sha256(dst.read_bytes()).hexdigest()
