"""EVERY LOOK WE GENERATED, NOT JUST THE ONE WE SHIPPED.

`assets.db` holds 5,776 source images from the game and 14,413 renders of them
across ELEVEN families -- photoreal, depth_realism, neon, painterly, isometric,
chromatic, dreamlike, edge_chrome, zavy_depth, pixel_art, and the plain
upscale. The pack builder only ever packed `upscale_only`, so 8,637 finished
renders of the game's own art have never been in a picture.

That is the difference between this project and a downloaded HD texture pack.
An HD pack is one look, and everybody has it. A database of eleven looks over
the same 5,776 paths is a WARDROBE: the same moment can be filmed repeatedly
with the art as the only variable, and the cuts or dissolves between those
takes are an effect nobody can buy.

WHAT THIS MODULE IS. The bridge from the database to `assets.AssetSet`, so a
look is installable by name and `offscreen.capture(asset_set="NEON")` means
something. It plans without touching the renders on disk, so asking what a
look would contain is cheap and answering is honest about what is missing.

WHAT IT REFUSES TO DO. It does not claim a look is good, or that it changed
the frame. `plan()` reports coverage; a picture is a pixel question. And it
carries the project's routing rule rather than ignoring it: diffusion destroys
alpha edges on FX sheets, so a look that restyles them says so out loud.
"""
from __future__ import annotations

import sqlite3
import zipfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from engine.pantheon import assets as A
from engine.pantheon import store as S

PHOTOREAL = S.PROJECT_ROOT / "creative_suite" / "comfy" / "photoreal"
ASSETS_DB = PHOTOREAL / "assets.db"
STOCK_PAK = (S.PROJECT_ROOT / "output" / "demo_v2" / "_wolfcam_staging"
             / "baseq3" / "pak00.pk3")

#: Categories whose art is shape- and alpha-critical. The project's PH5-7
#: routing rule says diffusion destroys these; only the plain upscale is safe.
#: A stylised look may still choose to restyle them -- but it must say so.
FX_CATEGORIES = frozenset({
    "weaphits", "gfx", "icons", "ui", "wolfcam_hud", "powerups",
    "mapobjects", "sprites"})

#: The one family that is not a style: it is the same art, larger.
FIDELITY_FAMILY = "upscale_only"


def _connect() -> sqlite3.Connection:
    if not ASSETS_DB.exists():
        raise FileNotFoundError(f"no assets database at {ASSETS_DB}")
    return sqlite3.connect(f"file:{ASSETS_DB}?mode=ro", uri=True)


@dataclass(frozen=True)
class Family:
    """One render family, as the database describes it."""
    name: str
    renders: int
    categories: tuple[str, ...]
    fx_categories: tuple[str, ...]

    @property
    def is_fidelity(self) -> bool:
        return self.name == FIDELITY_FAMILY

    @property
    def restyles_fx(self) -> bool:
        """True when this family has renders for shape-critical art, which the
        routing rule warns about."""
        return bool(self.fx_categories) and not self.is_fidelity


@lru_cache(maxsize=1)
def families() -> dict[str, Family]:
    """Every render family in the database, with what it actually covers."""
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT r.pipeline, a.category, COUNT(*) FROM renders r "
            "JOIN assets a ON a.id = r.asset_id "
            "WHERE r.status = 'ok' GROUP BY 1, 2").fetchall()
    finally:
        conn.close()

    acc: dict[str, dict] = {}
    for pipeline, category, n in rows:
        e = acc.setdefault(pipeline, {"n": 0, "cats": set()})
        e["n"] += n
        e["cats"].add(category)

    out = {}
    for name, e in acc.items():
        cats = tuple(sorted(e["cats"]))
        out[name] = Family(name, e["n"], cats,
                           tuple(c for c in cats if c in FX_CATEGORIES))
    return dict(sorted(out.items(), key=lambda kv: -kv[1].renders))


@lru_cache(maxsize=1)
def pak_index() -> dict[str, str]:
    """Stem (lowercased, no extension) -> the path the game actually ships.

    A look can only override a path the game asks for, under the extension the
    game asks for. This index is what makes that checkable instead of assumed.
    """
    if not STOCK_PAK.exists():
        return {}
    with zipfile.ZipFile(STOCK_PAK) as z:
        return {n.rsplit(".", 1)[0].lower(): n
                for n in z.namelist() if not n.endswith("/")}


def _in_pak_stem(rel_path: str) -> str:
    return (rel_path.split("pak00/", 1)[-1].rsplit(".", 1)[0]
            .replace("\\", "/").lower())


@dataclass(frozen=True)
class LookPlan:
    """What installing a look would actually put in front of the engine."""
    look: str
    family: str
    renders: int             # rows the database has for this family
    overridable: int         # of those, ones that replace a real pak path
    missing_on_disk: int     # rows whose file is not there
    not_in_pak: int          # rows that override nothing
    fx_touched: int          # shape-critical images this look restyles
    approx_mb: float

    @property
    def ok(self) -> bool:
        return self.overridable > 0

    def as_dict(self) -> dict:
        d = self.__dict__.copy()
        d["ok"] = self.ok
        return d


def plan(family: str, *, verify_disk: bool = True) -> LookPlan:
    """What a look would contain, measured against the pak and the disk.

    `verify_disk=False` skips the per-file existence check, which is the slow
    part; the count then means "rows the database believes in".
    """
    fams = families()
    if family not in fams:
        raise KeyError(f"no such render family: {family}; "
                       f"known: {sorted(fams)}")
    idx = pak_index()
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT a.rel_path, a.category, r.output_path FROM assets a "
            "JOIN renders r ON r.asset_id = a.id "
            "WHERE r.pipeline = ? AND r.status = 'ok'", (family,)).fetchall()
    finally:
        conn.close()

    overridable = missing = not_in_pak = fx = 0
    total_bytes = 0
    for rel_path, category, output_path in rows:
        if _in_pak_stem(rel_path) not in idx:
            not_in_pak += 1
            continue
        src = PHOTOREAL / output_path
        if verify_disk:
            if not src.exists():
                missing += 1
                continue
            total_bytes += src.stat().st_size
        overridable += 1
        if category in FX_CATEGORIES:
            fx += 1

    return LookPlan(look=family.upper(), family=family, renders=len(rows),
                    overridable=overridable, missing_on_disk=missing,
                    not_in_pak=not_in_pak, fx_touched=fx,
                    approx_mb=round(total_bytes / 1e6, 1))


def report(*, verify_disk: bool = False) -> dict:
    """The wardrobe, as it stands. Facts from the database, nothing claimed."""
    fams = families()
    shipped = {p.name for p in A.UHD_PACKS}
    return {
        "database": str(ASSETS_DB),
        "families": len(fams),
        "renders_total": sum(f.renders for f in fams.values()),
        "shipped_packs": sorted(shipped),
        "shipped_family": FIDELITY_FAMILY,
        "never_packed": sorted(n for n in fams if n != FIDELITY_FAMILY),
        "renders_never_packed": sum(f.renders for n, f in fams.items()
                                    if n != FIDELITY_FAMILY),
        "detail": {n: {"renders": f.renders,
                       "categories": list(f.categories),
                       "restyles_shape_critical_art": f.restyles_fx}
                   for n, f in fams.items()},
        "plans": ({n: plan(n, verify_disk=True).as_dict() for n in fams}
                  if verify_disk else {}),
    }


# ── making a look installable ──────────────────────────────────────────────

#: Families with too few renders to dress a scene. They are E2E samples, kept
#: for comparison, and a look built from one would be mostly stock.
MIN_RENDERS_FOR_A_LOOK = 500


def look_name(family: str) -> str:
    return family.upper()


def register(*, min_renders: int = MIN_RENDERS_FOR_A_LOOK) -> list[str]:
    """Publish every substantial family as a named `assets.AssetSet`.

    After this, `assets.install("NEON", staging)` and
    `offscreen.capture(asset_set="NEON")` are meaningful. The pack files
    themselves are built by `build()`; registering says the look EXISTS as a
    choice, not that its packs are on disk -- `assets.install` already reports
    a missing pack rather than pretending.
    """
    added = []
    for name, fam in families().items():
        if fam.renders < min_renders or name == FIDELITY_FAMILY:
            continue
        look = look_name(name)
        if look in A.SETS:
            continue
        packs = (A.AssetPack(f"zzz_look_{name}.pk3",
                             f"{name} restyle of {fam.renders} game images"),)
        note = (f"Built from assets.db family '{name}'. "
                + ("Restyles shape-critical art (alpha edges on FX sheets); "
                   "compare against STOCK before trusting it. "
                   if fam.restyles_fx else "")
                + "Whether the frame changed is a pixel question.")
        A.SETS[look] = A.AssetSet(
            look, f"The {name} look over the stock game.", packs, note=note)
        added.append(look)
    return added


def build(family: str, out_dir: Path | None = None, *,
          split_bytes: int = 1_500_000_000) -> dict:
    """Write the pk3 for one look.

    Reuses the proven conversion: an image only overrides a stock path when it
    is written AT that path with THAT extension, so every render is converted
    to whatever the game ships and skipped when it cannot be.
    """
    from PIL import Image
    import io

    fams = families()
    if family not in fams:
        raise KeyError(f"no such render family: {family}")
    out_dir = Path(out_dir) if out_dir else A.DEFAULT_LIBRARY
    out_dir.mkdir(parents=True, exist_ok=True)
    idx = pak_index()

    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT a.rel_path, r.output_path FROM assets a "
            "JOIN renders r ON r.asset_id = a.id "
            "WHERE r.pipeline = ? AND r.status = 'ok' ORDER BY a.rel_path",
            (family,)).fetchall()
    finally:
        conn.close()

    included, skipped, packs = [], [], []
    n, written = 1, 0
    path = out_dir / f"zzz_look_{family}.pk3"
    zf = zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED)
    packs.append(str(path))

    try:
        for rel_path, output_path in rows:
            orig = idx.get(_in_pak_stem(rel_path))
            if orig is None:
                skipped.append((rel_path, "overrides nothing in pak00"))
                continue
            src = PHOTOREAL / output_path
            if not src.exists():
                skipped.append((rel_path, "render missing on disk"))
                continue
            try:
                buf = io.BytesIO()
                with Image.open(src) as im:
                    suffix = Path(orig).suffix.lower()
                    fmt = {".tga": "TGA", ".jpg": "JPEG", ".jpeg": "JPEG",
                           ".png": "PNG"}.get(suffix)
                    if fmt is None:
                        skipped.append((rel_path, f"no writer for {suffix}"))
                        continue
                    if fmt == "JPEG" and im.mode not in ("RGB", "L"):
                        im = im.convert("RGB")
                    im.save(buf, fmt)
                data = buf.getvalue()
            except Exception as exc:                      # noqa: BLE001
                skipped.append((rel_path, f"convert failed: {exc}"))
                continue

            if written + len(data) > split_bytes:
                zf.close()
                n += 1
                written = 0
                path = out_dir / f"zzz_look_{family}_{n:02d}.pk3"
                zf = zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED)
                packs.append(str(path))
            zf.writestr(orig, data)
            written += len(data)
            included.append(orig)
    finally:
        zf.close()

    return {"look": look_name(family), "family": family, "packs": packs,
            "included": len(included), "skipped": len(skipped),
            "skipped_reasons": sorted({r for _, r in skipped}),
            "proven": False,
            "how_to_prove": "film one moment with this look and once with "
                            "STOCK, then look at the two frames"}
