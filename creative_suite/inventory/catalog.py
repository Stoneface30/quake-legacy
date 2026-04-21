"""Walk baseq3 pk3 files and classify entries.

ENG-1: Steam paks are the source of truth. This module reads pk3s
non-destructively (read-only zipfile) and returns a list of
asset-catalog entries ready for SQLite ingest.

No FULL_CATALOG.json prerequisite — if the JSON exists we honor it,
otherwise we build in-memory from pk3 direct.
"""
from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, cast

# Extensions we care about in MVP. Sounds explicitly excluded (spec §4.1).
TEXTURE_EXTS = {".tga", ".jpg", ".jpeg", ".png"}
MODEL_EXTS = {".md3"}
SKIN_EXTS = {".skin"}
ALLOWED_EXTS = TEXTURE_EXTS | MODEL_EXTS | SKIN_EXTS


@dataclass(frozen=True)
class CatalogEntry:
    category: str
    subcategory: str | None
    source_pk3: str
    internal_path: str
    checksum: str
    size: int

    def as_dict(self) -> dict[str, object]:
        return {
            "category": self.category,
            "subcategory": self.subcategory,
            "source_pk3": self.source_pk3,
            "internal_path": self.internal_path,
            "checksum": self.checksum,
            "size": self.size,
        }


def _classify(internal_path: str) -> tuple[str, str | None]:
    """Map an internal pk3 path to (category, subcategory).

    Categories in MVP: weapon | skin | surface | effect | gfx | model | misc
    """
    p = internal_path.lower()
    parts = p.split("/")
    ext = "." + p.rsplit(".", 1)[-1] if "." in p else ""

    if p.startswith("models/weapons") or p.startswith("models/ammo") or p.startswith("models/powerups"):
        sub = parts[2] if len(parts) >= 3 else None
        return "weapon", sub
    if p.startswith("models/players"):
        sub = parts[2] if len(parts) >= 3 else None  # player model slug
        return "skin", sub
    if p.startswith("models/"):
        sub = parts[1] if len(parts) >= 2 else None
        return "model", sub
    if p.startswith("textures/"):
        sub = parts[1] if len(parts) >= 2 else None
        return "surface", sub
    if p.startswith("gfx/"):
        sub = parts[1] if len(parts) >= 2 else None
        return "gfx", sub
    if p.startswith(("sprites/", "env/")):
        sub = parts[1] if len(parts) >= 2 else None
        return "effect", sub
    if ext in SKIN_EXTS:
        return "skin", None
    return "misc", parts[0] if parts else None


def walk_pk3(pk3_path: Path) -> Iterable[CatalogEntry]:
    """Yield CatalogEntry for every asset of interest inside pk3_path."""
    src = str(pk3_path)
    with zipfile.ZipFile(pk3_path) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            name = info.filename
            ext = ("." + name.rsplit(".", 1)[-1].lower()) if "." in name else ""
            if ext not in ALLOWED_EXTS:
                continue
            category, sub = _classify(name)
            checksum = hashlib.sha1(
                f"{src}:{name}:{info.file_size}:{info.CRC}".encode()
            ).hexdigest()
            yield CatalogEntry(
                category=category,
                subcategory=sub,
                source_pk3=src,
                internal_path=name,
                checksum=checksum,
                size=info.file_size,
            )


def build_catalog(pk3_paths: Iterable[Path]) -> list[CatalogEntry]:
    """Aggregate entries across multiple pk3s. Later pk3s override earlier on
    internal_path collision (pk3 load-order semantics), but we keep all rows —
    UNIQUE (source_pk3, internal_path) in SQLite dedupes naturally."""
    out: list[CatalogEntry] = []
    for pk3 in pk3_paths:
        if not pk3.exists():
            continue
        out.extend(walk_pk3(pk3))
    return out


def load_or_build_catalog(
    catalog_json: Path | None,
    pk3_paths: Iterable[Path],
) -> list[CatalogEntry]:
    """Load FULL_CATALOG.json if present; otherwise build from pk3s."""
    if catalog_json is not None and catalog_json.exists():
        raw: Any = json.loads(catalog_json.read_text("utf-8"))
        if isinstance(raw, dict):
            raw_dict = cast(dict[str, Any], raw)
            entries_raw: Any = raw_dict["entries"]
        else:
            entries_raw = raw
        out: list[CatalogEntry] = []
        for entry_any in cast(list[Any], entries_raw):
            e: dict[str, Any] = cast(dict[str, Any], entry_any)
            source_pk3: str = str(e["source_pk3"])
            internal_path: str = str(e["internal_path"])
            checksum_raw = e.get("checksum")
            checksum: str = (
                str(checksum_raw)
                if checksum_raw
                else hashlib.sha1(
                    f"{source_pk3}:{internal_path}".encode()
                ).hexdigest()
            )
            subcategory_raw = e.get("subcategory")
            subcategory: str | None = (
                str(subcategory_raw) if subcategory_raw is not None else None
            )
            out.append(
                CatalogEntry(
                    category=str(e["category"]),
                    subcategory=subcategory,
                    source_pk3=source_pk3,
                    internal_path=internal_path,
                    checksum=checksum,
                    size=int(e.get("size", 0) or 0),
                )
            )
        return out
    return build_catalog(pk3_paths)
