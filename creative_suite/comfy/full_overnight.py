"""Full Q3 photorealistic asset regeneration — multi-pipeline, style-aware, database-backed.

Pipelines (all resumable, all stored in assets.db):
  upscale_only   — 4x-UltraSharp CNN only, zero diffusion (ALL categories)
  tile_d35       — JuggernautXL + TTPLanet Tile denoise=0.35 (SURFACE only)
  tile_d50       — denoise=0.50 (SURFACE only)
  tile_d60       — denoise=0.60 (SURFACE only, experimental)
  tile_d70       — denoise=0.70 (SURFACE only, experimental — gets spicy)
  tile_d80       — denoise=0.80 (SURFACE only, experimental — chaos mode)

Category routing (from E2E verdict 2026-04-21):
  SURFACE (upscale + all tile pipelines):
    players, weapons2, textures, phase5
  FX / shape-critical (upscale_only only):
    weaphits, gfx, icons, ui, wolfcam_hud, powerups, mapobjects, sprites
  Auto-detected: black-pixel ratio >70% → FX, else SURFACE

Output structure:
  photoreal/pipelines/{pipeline_name}/{rel_path}.png
  photoreal/assets.db   ← every asset + render logged here
  photoreal/compare/index.html

Usage:
  python -u creative_suite/comfy/full_overnight.py
  python -u creative_suite/comfy/full_overnight.py --categories players weapons2
  python -u creative_suite/comfy/full_overnight.py --pipelines upscale_only tile_d35 tile_d50
  python -u creative_suite/comfy/full_overnight.py --categories phase5 --pipelines tile_d35 tile_d50 tile_d60

Fully resumable: existing output files and DB records are skipped.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import random
import shutil
import sqlite3
import sys
import time
import zipfile
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from creative_suite.comfy.client import ComfyClient, load_workflow
from creative_suite.comfy.prompts import PHOTOREAL_NEGATIVE_PROMPT, build_final_prompt

# ── Paths ──────────────────────────────────────────────────────────────────────

PAK00           = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Quake Live\baseq3\pak00.pk3")
PHASE5_SRC      = Path(__file__).parent / "assets" / "phase5_png"
WOLFCAM_HUD_SRC = (
    ROOT / "engine" / "engines" / "_canonical"
    / "package-files" / "wolfcam-ql" / "gfx" / "wc"
)

PHOTOREAL  = Path(__file__).parent / "photoreal"
ASSETS     = PHOTOREAL / "assets"
PIPELINES_DIR = PHOTOREAL / "pipelines"
DB_PATH    = PHOTOREAL / "assets.db"

WF_DIR         = Path(__file__).parent / "workflows"
WF_UPSCALE     = WF_DIR / "upscale_only.json"
WF_TILE_SDXL   = WF_DIR / "tile_controlnet_sdxl.json"
WF_REFINE_SDXL = WF_DIR / "tile_refine_sdxl.json"
WF_TILE_SD15   = WF_DIR / "tile_controlnet_sd15.json"

SDXL_CONTROLNET = Path(
    r"E:\PersonalAI\ComfyUI\models\controlnet"
    r"\TTPLANET_Controlnet_Tile_realistic_v2_fp16.safetensors"
)

POLL_INTERVAL = 1.0
TIMEOUT       = 360.0
FX_BLACK_RATIO = 0.70

# ── Pipeline definitions ───────────────────────────────────────────────────────
# Ordered: upscale first, then tile by increasing denoise
# Tuple: (workflow_key, denoise, scope)
#   scope "all"     → runs on every category
#   scope "surface" → runs only on SURFACE categories

PIPELINE_DEFS: OrderedDict[str, tuple[str, float, str]] = OrderedDict([
    ("upscale_only", ("upscale",  1.0,  "all")),
    ("tile_d35",     ("tile",     0.35, "surface")),
    ("tile_d50",     ("tile",     0.50, "surface")),
    ("tile_d60",     ("tile",     0.60, "surface")),
    ("tile_d70",     ("tile",     0.70, "surface")),
    ("tile_d80",     ("tile",     0.80, "surface")),
])

# ── Category routing ───────────────────────────────────────────────────────────

_FX_LABELS = frozenset([
    "weaphits", "gfx", "icons", "ui", "wolfcam_hud",
    "powerups", "mapobjects", "sprites",
])
_SURFACE_LABELS = frozenset([
    "players", "weapons2", "textures", "phase5",
])


def _is_fx_image(path: Path) -> bool:
    try:
        from PIL import Image  # type: ignore[import]
        img = Image.open(path).convert("RGB")
        w, h = img.size
        if w * h == 0:
            return False
        black = sum(1 for r, g, b in img.getdata() if r + g + b < 45)
        return (black / (w * h)) > FX_BLACK_RATIO
    except Exception:
        return False


def _route(label: str, path: Path) -> Literal["surface", "fx"]:
    if label in _SURFACE_LABELS:
        return "surface"
    if label in _FX_LABELS:
        return "fx"
    return "fx" if _is_fx_image(path) else "surface"


# ── Database ───────────────────────────────────────────────────────────────────

def _init_db(db: sqlite3.Connection) -> None:
    db.executescript("""
    CREATE TABLE IF NOT EXISTS assets (
        id        INTEGER PRIMARY KEY,
        rel_path  TEXT    UNIQUE NOT NULL,
        category  TEXT    NOT NULL,
        source    TEXT    NOT NULL,
        route     TEXT    NOT NULL,
        width     INTEGER,
        height    INTEGER,
        file_size INTEGER,
        sha256    TEXT,
        added_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS renders (
        id           INTEGER PRIMARY KEY,
        asset_id     INTEGER NOT NULL REFERENCES assets(id),
        pipeline     TEXT    NOT NULL,
        denoise      REAL    NOT NULL,
        style        TEXT    NOT NULL DEFAULT 'photoreal',
        output_path  TEXT    NOT NULL,
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(asset_id, pipeline, style)
    );

    CREATE INDEX IF NOT EXISTS renders_asset ON renders(asset_id);
    CREATE INDEX IF NOT EXISTS renders_pipeline ON renders(pipeline);
    CREATE INDEX IF NOT EXISTS assets_category ON assets(category);
    CREATE INDEX IF NOT EXISTS assets_route ON assets(route);
    """)
    db.commit()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _upsert_asset(db: sqlite3.Connection, rel: Path, label: str,
                  source: str, route: str) -> int:
    from PIL import Image  # type: ignore[import]
    abs_path = ASSETS / rel
    rel_str = str(rel).replace("\\", "/")

    row = db.execute("SELECT id FROM assets WHERE rel_path=?", (rel_str,)).fetchone()
    if row:
        return row[0]

    w = h = sz = 0
    sha = ""
    try:
        img = Image.open(abs_path)
        w, h = img.size
        sz = abs_path.stat().st_size
        sha = _sha256(abs_path)
    except Exception:
        pass

    cur = db.execute(
        "INSERT OR IGNORE INTO assets (rel_path,category,source,route,width,height,file_size,sha256)"
        " VALUES (?,?,?,?,?,?,?,?)",
        (rel_str, label, source, route, w, h, sz, sha),
    )
    db.commit()
    return cur.lastrowid or db.execute(
        "SELECT id FROM assets WHERE rel_path=?", (rel_str,)
    ).fetchone()[0]


def _log_render(db: sqlite3.Connection, asset_id: int, pipeline: str,
                denoise: float, output_path: Path) -> None:
    rel_out = str(output_path.relative_to(PHOTOREAL)).replace("\\", "/")
    db.execute(
        "INSERT OR REPLACE INTO renders (asset_id,pipeline,denoise,output_path)"
        " VALUES (?,?,?,?)",
        (asset_id, pipeline, denoise, rel_out),
    )
    db.commit()


def _already_rendered(db: sqlite3.Connection, asset_id: int, pipeline: str) -> bool:
    row = db.execute(
        "SELECT 1 FROM renders WHERE asset_id=? AND pipeline=? AND style='photoreal'",
        (asset_id, pipeline),
    ).fetchone()
    return row is not None


# ── Extraction ─────────────────────────────────────────────────────────────────

def _extract_pak00(force: bool = False) -> int:
    from PIL import Image  # type: ignore[import]
    dst_root = ASSETS / "pak00"
    total = 0
    with zipfile.ZipFile(PAK00) as zf:
        entries = [e for e in zf.namelist()
                   if e.lower().endswith((".tga", ".jpg", ".png"))]
        print(f"  pak00.pk3: {len(entries)} image entries")
        for entry in entries:
            out = dst_root / Path(entry.replace("\\", "/")).with_suffix(".png")
            if out.exists() and not force:
                continue
            try:
                raw = zf.read(entry)
                img = Image.open(io.BytesIO(raw))
                img = (img.convert("RGBA") if img.mode in ("P", "LA")
                       else img.convert("RGB"))
                out.parent.mkdir(parents=True, exist_ok=True)
                img.save(out, format="PNG")
                total += 1
            except Exception as exc:
                print(f"    WARN extract {entry}: {exc}")
    return total


def _copy_tree(src_root: Path, dst_root: Path, force: bool = False) -> int:
    total = 0
    if not src_root.exists():
        return 0
    for src in src_root.rglob("*.png"):
        dst = dst_root / src.relative_to(src_root)
        if dst.exists() and not force:
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        total += 1
    return total


# ── Asset list ─────────────────────────────────────────────────────────────────

def _build_asset_list() -> list[tuple[str, str, Path]]:
    """Returns [(label, source, rel_path_under_assets), ...] in priority order."""
    items: list[tuple[str, str, Path]] = []

    def _add(label: str, source: str, root: Path) -> None:
        if root.exists():
            for f in sorted(root.rglob("*.png")):
                items.append((label, source, f.relative_to(ASSETS)))

    _add("players",     "pak00",  ASSETS / "pak00" / "models" / "players")
    _add("phase5",      "phase5", ASSETS / "phase5_png")
    _add("wolfcam_hud", "wolfcam_hud", ASSETS / "wolfcam_hud")
    _add("powerups",    "pak00",  ASSETS / "pak00" / "models" / "powerups")
    _add("mapobjects",  "pak00",  ASSETS / "pak00" / "models" / "mapobjects")
    _add("weaphits",    "pak00",  ASSETS / "pak00" / "models" / "weaphits")
    _add("weapons2",    "pak00",  ASSETS / "pak00" / "models" / "weapons2")
    _add("gfx",         "pak00",  ASSETS / "pak00" / "gfx")
    _add("icons",       "pak00",  ASSETS / "pak00" / "icons")
    _add("sprites",     "pak00",  ASSETS / "pak00" / "sprites")
    _add("textures",    "pak00",  ASSETS / "pak00" / "textures")
    _add("ui",          "pak00",  ASSETS / "pak00" / "ui")

    return items


# ── ComfyUI job ────────────────────────────────────────────────────────────────

def _wait_job(comfy: ComfyClient, job_id: str) -> list[dict[str, str]]:
    deadline = time.monotonic() + TIMEOUT
    while time.monotonic() < deadline:
        outputs = comfy.output_filenames(job_id)
        if outputs:
            return outputs
        time.sleep(POLL_INTERVAL)
    raise TimeoutError(f"job {job_id} timed out after {TIMEOUT}s")


def _run_one(
    src: Path, dst: Path,
    comfy: ComfyClient, workflow: dict,
    prompt: str, denoise: float,
) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        job_id = comfy.submit_img2img(
            workflow, src,
            prompt=prompt,
            seed=random.randint(0, 2**32 - 1),
            denoise=denoise,
            negative_prompt=PHOTOREAL_NEGATIVE_PROMPT,
        )
        outputs = _wait_job(comfy, job_id)
        first = outputs[0]
        png = comfy.fetch_output(
            first["filename"],
            subfolder=first.get("subfolder", ""),
            type_=first.get("type_", "output"),
        )
        dst.write_bytes(png)
        return True
    except Exception as exc:
        print(f"    ERR {src.name}: {exc}")
        return False


# ── Gallery ────────────────────────────────────────────────────────────────────

def _build_gallery(active_pipelines: list[str]) -> None:
    compare_dir = PHOTOREAL / "compare"
    compare_dir.mkdir(parents=True, exist_ok=True)

    # Collect rows
    rows: list[dict] = []
    for orig in sorted(ASSETS.rglob("*.png")):
        rel = orig.relative_to(ASSETS)
        pipe_paths = {
            p: PIPELINES_DIR / p / rel
            for p in active_pipelines
        }
        if any(pp.exists() for pp in pipe_paths.values()):
            rows.append({"orig": orig, "rel": rel, "pipes": pipe_paths})

    pipe_headers = "".join(
        f"<th style='background:#1a1a1a;padding:8px;color:#c8a850;font-size:11px'>"
        f"{_pipe_label(p)}</th>"
        for p in active_pipelines
    )

    body_rows = []
    for r in rows:
        rel  = r["rel"]
        cat  = rel.parts[0]
        name = "/".join(rel.parts[1:])
        orig_rel = "../assets/" + str(rel).replace("\\", "/")

        tds = ""
        for p in active_pipelines:
            pp = r["pipes"][p]
            if pp.exists():
                p_rel = "../pipelines/" + p + "/" + str(rel).replace("\\", "/")
                tds += (
                    f"<td style='padding:2px;text-align:center'>"
                    f"<img src='{p_rel}' style='max-width:160px;max-height:160px;"
                    f"image-rendering:pixelated'></td>"
                )
            else:
                tds += "<td style='padding:2px;color:#333;text-align:center'>—</td>"

        body_rows.append(
            f"<tr>"
            f"<td style='padding:6px;white-space:nowrap;vertical-align:top'>"
            f"<b style='color:#c8a850'>{cat}</b><br>"
            f"<span style='font-size:9px;color:#555'>{name}</span></td>"
            f"<td style='padding:2px;text-align:center'>"
            f"<img src='{orig_rel}' style='max-width:160px;max-height:160px;"
            f"image-rendering:pixelated'></td>"
            f"{tds}</tr>"
        )

    html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'>
<title>QUAKE LEGACY — Photoreal Dataset</title>
<style>
  body{{background:#0d0d0d;color:#eee;font-family:monospace;margin:0;padding:12px}}
  h1{{color:#c8a850;margin:0 0 4px}}
  p{{color:#666;font-size:11px;margin:0 0 12px}}
  table{{border-collapse:collapse;width:100%}}
  th{{padding:6px;text-align:center}}
  td{{border:1px solid #1e1e1e;vertical-align:middle}}
  tr:hover td{{background:#161616}}
</style></head><body>
<h1>QUAKE LEGACY — Photorealistic Asset Dataset</h1>
<p>
  Pipeline: JuggernautXL + TTPLanet Tile ControlNet (SDXL) · {len(rows)} assets · {len(active_pipelines)} pipelines<br>
  Surface route → all tile_d* pipelines &nbsp;|&nbsp; FX route → upscale_only only
</p>
<table>
<tr>
  <th style='text-align:left;background:#1a1a1a;padding:8px;color:#c8a850;font-size:11px'>Asset</th>
  <th style='background:#1a1a1a;padding:8px;color:#4af;font-size:11px'>ORIGINAL</th>
  {pipe_headers}
</tr>
{"".join(body_rows)}
</table></body></html>"""

    (compare_dir / "index.html").write_text(html, encoding="utf-8")
    print(f"  Gallery: {compare_dir / 'index.html'}  ({len(rows)} assets)")


def _pipe_label(name: str) -> str:
    labels = {
        "upscale_only": "4x-UltraSharp<br>CNN only",
        "tile_d35":     "JuggXL + TTPLanet<br>d=0.35 ✓",
        "tile_d50":     "d=0.50<br>experimental",
        "tile_d60":     "d=0.60<br>spicy",
        "tile_d70":     "d=0.70<br>wild",
        "tile_d80":     "d=0.80<br>chaos mode",
    }
    return labels.get(name, name)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(
        description="QUAKE LEGACY photorealistic asset batch — multi-pipeline"
    )
    ap.add_argument(
        "--categories", nargs="*",
        help="Only process these categories (default: all)",
    )
    ap.add_argument(
        "--pipelines", nargs="*",
        choices=list(PIPELINE_DEFS.keys()),
        help="Only run these pipelines (default: all)",
    )
    ap.add_argument(
        "--force-extract", action="store_true",
        help="Re-extract originals even if already present",
    )
    ap.add_argument(
        "--force-render", action="store_true",
        help="Re-render even if output file exists",
    )
    args = ap.parse_args()

    active_pipelines: list[str] = args.pipelines or list(PIPELINE_DEFS.keys())
    filter_cats: set[str] | None = set(args.categories) if args.categories else None

    print("=" * 64)
    print("QUAKE LEGACY — Photorealistic Asset Batch")
    print(f"  pipelines : {' | '.join(active_pipelines)}")
    print(f"  categories: {', '.join(sorted(filter_cats)) if filter_cats else 'all'}")
    print("=" * 64)

    # ── 1: Extract originals ───────────────────────────────────────
    print("\n[1/5] Preparing originals...")
    n_pak = 0
    if PAK00.exists():
        n_pak = _extract_pak00(force=args.force_extract)
    else:
        print(f"  WARN: pak00.pk3 not found at {PAK00}")
    n_p5  = _copy_tree(PHASE5_SRC,      ASSETS / "phase5_png",   force=args.force_extract)
    n_wc  = _copy_tree(WOLFCAM_HUD_SRC, ASSETS / "wolfcam_hud",  force=args.force_extract)
    print(f"  pak00={n_pak}  phase5={n_p5}  wolfcam_hud={n_wc}")

    # ── 2: Database init ───────────────────────────────────────────
    print("\n[2/5] Initialising database...")
    PHOTOREAL.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    _init_db(db)
    print(f"  DB: {DB_PATH}")

    # ── 3: Build asset list ────────────────────────────────────────
    print("\n[3/5] Building asset list...")
    all_assets = _build_asset_list()
    if filter_cats:
        all_assets = [(l, s, r) for l, s, r in all_assets if l in filter_cats]
    if not all_assets:
        print("  No assets found.")
        sys.exit(1)

    cats = Counter(label for label, _, _ in all_assets)
    for cat, cnt in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"    {cat:<20} {cnt}")
    print(f"  Total: {len(all_assets)} assets")

    # ── 4: ComfyUI connectivity ────────────────────────────────────
    print("\n[4/5] Connecting to ComfyUI...")
    try:
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:8188/system_stats", timeout=5).read()
        print("  Connected.")
    except Exception as exc:
        print(f"  ERROR: ComfyUI unreachable — {exc}")
        print("  Start: E:\\PersonalAI\\run_comfyui_api.bat  (WorkingDirectory E:\\PersonalAI)")
        sys.exit(1)

    using_sdxl = SDXL_CONTROLNET.exists()
    wf_upscale = load_workflow(WF_UPSCALE)
    wf_tile    = load_workflow(WF_TILE_SDXL if using_sdxl else WF_TILE_SD15)
    prompt     = build_final_prompt("")

    model_label = ("JuggernautXL + TTPLanet Tile (SDXL)" if using_sdxl
                   else "dreamshaper_8 + Tile (SD1.5 fallback)")
    print(f"  Model: {model_label}")

    wf_map = {"upscale": wf_upscale, "tile": wf_tile}

    # ── 5: Batch ───────────────────────────────────────────────────
    print(f"\n[5/5] Processing {len(all_assets)} assets × {len(active_pipelines)} pipelines...")

    total_done = total_skip = total_err = 0
    start_t = time.monotonic()

    with ComfyClient(base_url="http://127.0.0.1:8188", timeout=90.0) as comfy:
        for idx, (label, source, rel) in enumerate(all_assets, 1):
            orig = ASSETS / rel
            if not orig.exists():
                total_skip += 1
                continue

            route    = _route(label, orig)
            asset_id = _upsert_asset(db, rel, label, source, route)

            for pipe_name in active_pipelines:
                wf_key, denoise, scope = PIPELINE_DEFS[pipe_name]

                # FX assets only get upscale_only
                if scope == "surface" and route == "fx":
                    continue

                dst = PIPELINES_DIR / pipe_name / rel

                if dst.exists() and not args.force_render:
                    if not _already_rendered(db, asset_id, pipe_name):
                        _log_render(db, asset_id, pipe_name, denoise, dst)
                    total_skip += 1
                    continue

                if _already_rendered(db, asset_id, pipe_name) and not args.force_render:
                    total_skip += 1
                    continue

                workflow = wf_map[wf_key]
                ok = _run_one(orig, dst, comfy, workflow, prompt, denoise)

                if ok:
                    _log_render(db, asset_id, pipe_name, denoise, dst)
                    total_done += 1
                else:
                    total_err += 1

            # Progress every 25 assets
            if idx % 25 == 0:
                elapsed = time.monotonic() - start_t
                rate = total_done / max(elapsed, 1)
                remaining = len(all_assets) - idx
                eta_s = int(remaining / max(rate, 0.001))
                print(
                    f"  [{idx}/{len(all_assets)}] "
                    f"done={total_done} skip={total_skip} err={total_err} "
                    f"rate={rate:.1f}/s ETA={eta_s//3600}h{(eta_s%3600)//60}m",
                    flush=True,
                )

    db.close()

    # ── Gallery ────────────────────────────────────────────────────
    print("\nBuilding gallery...")
    _build_gallery(active_pipelines)

    print(f"\n{'='*64}")
    print(f"Batch complete — generated={total_done} skipped={total_skip} errors={total_err}")
    if total_err:
        print(f"Re-run to retry {total_err} failed images.")
        sys.exit(1)


if __name__ == "__main__":
    main()
