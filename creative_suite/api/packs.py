"""Task 8.3 / 8.4 — pk3 build + install endpoints.

`POST /api/packs/build` gates on Gate CS-1 (≥5 approved variants, ≥1
surface, ≥1 skin) before it writes anything. On success it converts each
approved variant's PNG → TGA, zips them into
`storage/packs/zzz_photorealistic.pk3`, and inserts a `pack_builds` row
stamped with the sha256.

`POST /api/packs/install` copies that pk3 into the configured wolfcam
baseq3 directory and verifies the alpha-sort rule (ENG-2) — the engine
loads pk3s alphabetically, so `zzz_*` MUST sort after `pak00.pk3` for
our overrides to win.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from creative_suite.config import Config
from creative_suite.db.migrate import connect
from creative_suite.pk3_build.png_to_tga import png_to_tga
from creative_suite.pk3_build.zip_pk3 import zip_pk3

router = APIRouter(prefix="/api/packs", tags=["packs"])


PACK_SLUG = "zzz_photorealistic"
PK3_FILENAME = f"{PACK_SLUG}.pk3"

# Gate CS-1 thresholds (spec §7).
MIN_APPROVED = 5
REQUIRED_CATEGORIES = ("surface", "skin")


def _gate_cs1_check(con: Any) -> dict[str, Any]:
    """Return the Gate CS-1 state. Caller raises HTTPException(409) on failure.

    Gate CS-1: ≥5 approved variants total AND at least one approved
    surface AND at least one approved skin. This stops us from shipping
    a pk3 that's just skins (or just walls) and quietly missing either
    half of the style pack.
    """
    total = int(
        con.execute(
            "SELECT COUNT(*) AS c FROM variants WHERE status = 'approved'"
        ).fetchone()["c"]
    )
    per_cat = {
        r["category"]: int(r["c"])
        for r in con.execute(
            "SELECT a.category AS category, COUNT(*) AS c "
            "FROM variants v JOIN assets a ON a.id = v.asset_id "
            "WHERE v.status = 'approved' "
            "GROUP BY a.category"
        )
    }
    missing = [c for c in REQUIRED_CATEGORIES if per_cat.get(c, 0) == 0]
    ok = total >= MIN_APPROVED and not missing
    return {
        "ok": ok,
        "approved": total,
        "min_required": MIN_APPROVED,
        "per_category": per_cat,
        "missing_categories": missing,
    }


def _collect_approved(con: Any) -> list[dict[str, Any]]:
    """Return the rows we'll pack, ordered by asset_id (stable for sha256)."""
    rows = con.execute(
        "SELECT v.id AS variant_id, v.png_path AS png_path, "
        "       a.internal_path AS internal_path, a.category AS category "
        "FROM variants v JOIN assets a ON a.id = v.asset_id "
        "WHERE v.status = 'approved' "
        "ORDER BY v.asset_id, v.id"
    ).fetchall()
    return [dict(r) for r in rows]


def _coerce_internal_path_to_tga(internal_path: str) -> str:
    """Approved variant always renders to 32-bit RGBA TGA in the pk3, even
    if the original asset was .jpg or .png. The engine's shader loader
    resolves `foo` (no ext) against .tga FIRST on vanilla loadoor; we keep
    the basename and swap the extension so existing shader references
    pick up our override."""
    stem, _, _ = internal_path.rpartition(".")
    if not stem:
        # No extension — paranoid path, shouldn't happen for ingested assets.
        return internal_path + ".tga"
    return stem + ".tga"


# ---------------------------------------------------------------------- #
# /api/packs/status — UI polls this to enable the [Build] button.
# ---------------------------------------------------------------------- #


@router.get("/status")
def pack_status(request: Request) -> dict[str, Any]:
    cfg: Config = request.app.state.cfg
    with connect(cfg) as con:
        gate = _gate_cs1_check(con)
        last = con.execute(
            "SELECT id, pack_slug, pk3_path, variant_count, sha256, built_at "
            "FROM pack_builds ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return {
        "gate_cs1": gate,
        "last_build": dict(last) if last is not None else None,
    }


# ---------------------------------------------------------------------- #
# /api/packs/build — Gate CS-1 guarded build.
# ---------------------------------------------------------------------- #


@router.post("/build")
def build_pack(request: Request) -> dict[str, Any]:
    cfg: Config = request.app.state.cfg
    with connect(cfg) as con:
        gate = _gate_cs1_check(con)
        if not gate["ok"]:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": (
                        f"Gate CS-1: need ≥{MIN_APPROVED} approved variants "
                        "incl. ≥1 surface and ≥1 skin"
                    ),
                    **gate,
                },
            )
        approved = _collect_approved(con)

    # Convert each variant's PNG into a TGA under a temp dir, then zip.
    with tempfile.TemporaryDirectory(prefix="cs_pack_") as tmpd:
        tmp = Path(tmpd)
        entries: list[tuple[str, bytes]] = []
        missing: list[int] = []
        for row in approved:
            png_path = Path(row["png_path"])
            if not png_path.exists():
                missing.append(int(row["variant_id"]))
                continue
            internal = _coerce_internal_path_to_tga(row["internal_path"])
            tga_out = tmp / internal
            png_to_tga(png_path, tga_out)
            entries.append((internal, tga_out.read_bytes()))

        if missing:
            raise HTTPException(
                status_code=410,
                detail={
                    "error": "approved variant PNGs missing on disk",
                    "variant_ids": missing,
                },
            )

        cfg.packs_dir.mkdir(parents=True, exist_ok=True)
        pk3_path = cfg.packs_dir / PK3_FILENAME
        sha = zip_pk3(entries, pk3_path, pack_slug=PACK_SLUG)

    with connect(cfg) as con:
        con.execute(
            "INSERT INTO pack_builds (pack_slug, pk3_path, variant_count, sha256) "
            "VALUES (?, ?, ?, ?)",
            (PACK_SLUG, str(pk3_path), len(entries), sha),
        )
        row = con.execute(
            "SELECT id, built_at FROM pack_builds ORDER BY id DESC LIMIT 1"
        ).fetchone()

    return {
        "pack_build_id": int(row["id"]),
        "pack_slug": PACK_SLUG,
        "pk3_path": str(pk3_path),
        "sha256": sha,
        "variant_count": len(entries),
        "built_at": row["built_at"],
    }


# ---------------------------------------------------------------------- #
# /api/packs/install — copy pk3 into wolfcam baseq3 + verify alpha-sort.
# ---------------------------------------------------------------------- #


def _resolve_wolfcam_baseq3(cfg: Config) -> Path:
    """Env override wins; config default is the fallback.

    Test/CI environments set ``WOLFCAM_BASEQ3_DIR`` to a writable tmp dir.
    Production default points at the real wolfcam install."""
    override = os.environ.get("WOLFCAM_BASEQ3_DIR")
    if override:
        return Path(override)
    return cfg.wolfcam_baseq3


@router.post("/install")
def install_pack(request: Request) -> dict[str, Any]:
    cfg: Config = request.app.state.cfg
    src = cfg.packs_dir / PK3_FILENAME
    if not src.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "no built pk3 — POST /api/packs/build first "
                f"(expected {src})"
            ),
        )

    dst_dir = _resolve_wolfcam_baseq3(cfg)
    if not dst_dir.exists():
        raise HTTPException(
            status_code=500,
            detail={
                "error": (
                    "wolfcam baseq3 dir missing — set WOLFCAM_BASEQ3_DIR or "
                    "create the dir"
                ),
                "expected": str(dst_dir),
            },
        )

    dst = dst_dir / PK3_FILENAME
    shutil.copyfile(src, dst)

    # Alpha-sort verification (ENG-2): our pk3 must sort AFTER pak00.pk3.
    pk3s = sorted(p.name for p in dst_dir.glob("*.pk3"))
    our_idx = pk3s.index(PK3_FILENAME)
    pak00_idx = pk3s.index("pak00.pk3") if "pak00.pk3" in pk3s else -1
    alpha_ok = pak00_idx == -1 or our_idx > pak00_idx

    return {
        "copied_to": str(dst),
        "baseq3_pk3s": pk3s,
        "alpha_sort_ok": alpha_ok,
        "reminder_sv_pure": "launch wolfcam with +set sv_pure 0 (ENG-3)",
    }
