"""WHICH ASSETS THE PICTURE IS MADE OF, DECLARED RATHER THAN INHERITED.

A Quake install renders whatever pk3 files happen to be in its gamedir, in
alphabetical order, with the last one winning. That is a fine rule for a game
and a terrible one for a film pipeline: it means the look of a shot is decided
by a directory listing nobody wrote down, and two clips cut together can come
from different assets without anything saying so.

This module makes the asset set an explicit, versioned choice.

WHAT THIS FOUND. Four gigabytes of upscaled textures and models -- 4,895 files
across five packs -- were built into `_wolfcam_staging_patched` and every
render this project has ever made used `_wolfcam_staging`, which has none of
them. The assets existed and were never in the picture.

WHAT IT CANNOT PROMISE. A pack that supplies `anarki.png` where the shader
asks for `anarki.tga` may not override anything: id Tech 3 resolves an image
by trying extensions in its own order. So `install()` puts the packs in place
and says so; whether the frame CHANGED is a pixel question, answered by
`docs/visual-record/.../uhd_assets/`, and never assumed from a file listing.
"""
from __future__ import annotations

import json
import os
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from engine.pantheon import store as S


@dataclass(frozen=True)
class AssetPack:
    name: str                       # the pk3 filename, which decides load order
    covers: str                     # what a reader should expect it to change
    approx_mb: int = 0

    def source(self, library: Path) -> Path:
        return library / self.name


@dataclass(frozen=True)
class AssetSet:
    name: str
    description: str
    packs: tuple[AssetPack, ...] = ()
    note: str = ""

    def as_dict(self) -> dict:
        return {"name": self.name, "description": self.description,
                "packs": [p.name for p in self.packs], "note": self.note}


UHD_PACKS = (
    AssetPack("zzz_uhd_01.pk3", "world textures, 1,841 of them", 1502),
    AssetPack("zzz_uhd_02.pk3", "more world textures", 1393),
    AssetPack("zzz_uhd_03.pk3", "player and weapon models", 988),
    AssetPack("zzz_uhd_04.pk3", "further model art", 117),
    AssetPack("zzz_uhd_05.pk3", "remaining model art", 59),
)

STOCK = AssetSet(
    "STOCK",
    "Quake Live as it shipped. The look every demo was recorded against.",
    note="The control. Anything claimed about an upscaled picture is claimed "
         "against this one.")

UHD = AssetSet(
    "UHD", "Upscaled textures and models over the stock game.", UHD_PACKS,
    note="Named zzz_* so they sort last and win, per the project's pack rule. "
         "They carry no shader scripts, so they override by path alone -- "
         "which is why a frame has to be looked at rather than a listing.")

SETS: dict[str, AssetSet] = {s.name: s for s in (STOCK, UHD)}

# Where the built packs live. Not in the repository: they are gigabytes of
# generated art, and the repository forbids committing them.
DEFAULT_LIBRARY = (S.PROJECT_ROOT / "output" / "demo_v2"
                   / "_wolfcam_staging_patched" / "wolfcam-ql")

MANIFEST = "pantheon_assets.json"


def gamedir(staging: Path) -> Path:
    return Path(staging) / "wolfcam-ql"


def library(path: Path | None = None) -> Path:
    return Path(path) if path else DEFAULT_LIBRARY


def available(lib: Path | None = None, set_name: str | None = None) -> dict:
    """What the pack library holds for a set, by name and size.

    `set_name` matters now that the wardrobe registers ten looks: asking about
    ALL sets reports every look that has not been built yet, which is not a
    fault -- a look is a choice that exists whether or not its pack is on
    disk. A caller checking whether it can film asks about the set it intends
    to install.
    """
    lib = library(lib)
    chosen = ([SETS[set_name]] if set_name else list(SETS.values()))
    out = {}
    for s in chosen:
        for p in s.packs:
            src = p.source(lib)
            out[p.name] = {"present": src.exists(),
                           "bytes": src.stat().st_size if src.exists() else 0,
                           "path": str(src)}
    return out


def installed(staging: Path) -> dict:
    """What is in the gamedir right now, and which set it corresponds to."""
    gd = gamedir(staging)
    present = {p.name for p in gd.glob("*.pk3")}
    manifest = gd / MANIFEST
    declared = None
    if manifest.exists():
        try:
            declared = json.loads(manifest.read_text(encoding="utf-8"))
        except Exception:
            declared = None
    return {"gamedir": str(gd), "pk3s": sorted(present),
            "uhd_packs_present": sorted(p.name for p in UHD_PACKS
                                        if p.name in present),
            "declared": declared}


def active_set(staging: Path) -> str:
    """Which set the gamedir is in, read from what is there rather than from
    what someone meant."""
    have = set(installed(staging)["uhd_packs_present"])
    if have == {p.name for p in UHD_PACKS}:
        return UHD.name
    if not have:
        return STOCK.name
    return "MIXED"          # neither one thing nor the other; say so


def install(set_name: str, staging: Path, *, lib: Path | None = None) -> dict:
    """Put a named set in place, by hard link so four gigabytes are not copied.

    Idempotent, and it REMOVES packs the chosen set does not name -- a gamedir
    holding half of a set renders a picture nobody chose.
    """
    if set_name not in SETS:
        # The wardrobe is built from assets.db and registers itself lazily, so
        # a caller asking for NEON does not have to know that looks come from
        # a different module than STOCK and UHD do.
        try:
            from engine.pantheon import asset_library
            asset_library.register()
        except Exception:                                   # noqa: BLE001
            pass                    # no database here; the error below stands
    if set_name not in SETS:
        raise KeyError(f"no such asset set: {set_name}; known: {sorted(SETS)}")
    chosen = SETS[set_name]
    lib = library(lib)
    gd = gamedir(staging)
    gd.mkdir(parents=True, exist_ok=True)

    want = {p.name for p in chosen.packs}
    linked, removed, missing = [], [], []

    for pack in chosen.packs:
        src, dst = pack.source(lib), gd / pack.name
        if not src.exists():
            missing.append(pack.name)
            continue
        if dst.exists():
            if dst.stat().st_size == src.stat().st_size:
                continue
            dst.unlink()
        try:
            os.link(src, dst)          # same volume: no second copy
        except OSError:
            import shutil
            shutil.copy2(src, dst)
        linked.append(pack.name)

    for other in SETS.values():
        for pack in other.packs:
            if pack.name in want:
                continue
            stale = gd / pack.name
            if stale.exists():
                stale.unlink()
                removed.append(pack.name)

    (gd / MANIFEST).write_text(json.dumps({
        "set": chosen.name, "packs": sorted(want),
        "description": chosen.description, "note": chosen.note,
    }, indent=1), encoding="utf-8")

    return {"set": chosen.name, "linked": linked, "already_present":
            sorted(want - set(linked) - set(missing)), "removed": removed,
            "missing": missing, "ok": not missing}


def coverage(set_name: str = "UHD", *, lib: Path | None = None,
             sample: int = 0) -> dict:
    """What the set replaces, by path -- and how many of those paths the
    stock game actually asks for under the SAME extension.

    This is the check that matters: a pack supplying `x.png` where the game
    ships `x.tga` may override nothing at all.
    """
    lib = library(lib)
    stock = S.PROJECT_ROOT / "output" / "demo_v2" / "_wolfcam_staging" / "baseq3" / "pak00.pk3"
    if not stock.exists():
        return {"ok": False, "why": f"no stock pak at {stock}"}

    with zipfile.ZipFile(stock) as z:
        base = {n.lower() for n in z.namelist()}
    base_stems = {n.rsplit(".", 1)[0] for n in base if "." in n}

    exact = same_stem = novel = 0
    examples: list[str] = []
    for pack in SETS[set_name].packs:
        src = pack.source(lib)
        if not src.exists():
            continue
        with zipfile.ZipFile(src) as z:
            for n in z.namelist():
                if n.endswith("/"):
                    continue
                low = n.lower()
                if low in base:
                    exact += 1
                elif "." in low and low.rsplit(".", 1)[0] in base_stems:
                    same_stem += 1
                    if len(examples) < sample:
                        examples.append(n)
                else:
                    novel += 1
    total = exact + same_stem + novel
    return {"set": set_name, "files": total,
            "same_path_same_extension": exact,
            "same_path_other_extension": same_stem,
            "not_in_stock": novel,
            "examples_other_extension": examples,
            "reading": ("only same_path_same_extension is certain to override; "
                        "the rest depends on the engine's extension order and "
                        "must be judged on a frame")}


def report(staging: Path | None = None) -> dict:
    staging = staging or (S.PROJECT_ROOT / "output" / "demo_v2" / "_wolfcam_staging")
    return {"sets": {n: s.as_dict() for n, s in SETS.items()},
            "library": str(library()),
            "available": available(),
            "active_set": active_set(staging),
            "installed": installed(staging)}


def main() -> int:                                           # pragma: no cover
    import argparse
    ap = argparse.ArgumentParser(description="which assets the picture uses")
    ap.add_argument("--install", choices=sorted(SETS))
    ap.add_argument("--coverage", action="store_true")
    a = ap.parse_args()
    staging = S.PROJECT_ROOT / "output" / "demo_v2" / "_wolfcam_staging"
    if a.install:
        print(json.dumps(install(a.install, staging), indent=1))
    if a.coverage:
        print(json.dumps(coverage(sample=5), indent=1))
    if not (a.install or a.coverage):
        print(json.dumps(report(staging), indent=1))
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
