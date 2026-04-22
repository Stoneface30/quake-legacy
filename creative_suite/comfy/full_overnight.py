"""Full Q3 photorealistic asset regeneration — multi-pipeline, style-aware, database-backed.

Pipelines (all resumable, all stored in assets.db):
  upscale_only   — 4x-UltraSharp CNN only, zero diffusion (ALL categories)

  8 STYLE PIPELINES (SURFACE categories only):
  photoreal      — JuggernautXL + TTPLanet Tile, d=0.35  → clean photorealistic surface
  chromatic      — ZavyChromaXL + TTPLanet Tile, d=0.35  → vibrant chromatic saturation
  edge_chrome    — ZavyChromaXL + Canny SDXL,   d=0.45  → sharp edges + chromatic fills
  depth_realism  — JuggernautXL + DepthAnyV2 + Depth SDXL, d=0.40 → volumetric photoreal
  isometric      — stylized-isometric-sdxl + TTPLanet Tile, d=0.45 → isometric game-art
  painterly      — dreamshaper_8 SD1.5 + Tile SD1.5, d=0.35 → soft painterly
  dreamlike      — dreamshaper_8 SD1.5 + Tile SD1.5, d=0.55 → deeper dreamlike transform
  zavy_depth     — ZavyChromaXL + DepthAnyV2 + Depth SDXL, d=0.40 → vibrant + volumetric

  All style workflows: NO internal upscale — use --twopass to feed CNN-upscaled images.
  All style workflows: NO LoRA — style from checkpoint + ControlNet type only.

Category routing (from E2E verdict 2026-04-21):
  SURFACE (upscale + all style pipelines):
    players, weapons2, textures, phase5
  FX / shape-critical (upscale_only only):
    weaphits, gfx, icons, ui, wolfcam_hud, powerups, mapobjects, sprites
  Auto-detected: black-pixel ratio >70% → FX, else SURFACE

Output structure:
  photoreal/pipelines/{pipeline_name}/{rel_path}.png
  photoreal/assets.db   ← every asset + render logged here
  photoreal/compare/index.html

Usage:
  python -u creative_suite/comfy/full_overnight.py --twopass
  python -u creative_suite/comfy/full_overnight.py --twopass --categories players weapons2
  python -u creative_suite/comfy/full_overnight.py --twopass --pipelines photoreal chromatic edge_chrome
  python -u creative_suite/comfy/full_overnight.py --pipelines upscale_only

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

WF_DIR            = Path(__file__).parent / "workflows"
WF_UPSCALE        = WF_DIR / "upscale_only.json"
# ── 10 style workflows (no internal upscale) ──────────────────────────────────
WF_PHOTOREAL      = WF_DIR / "style_photoreal.json"      # JuggXL + TTPLanet Tile
WF_CHROMATIC      = WF_DIR / "style_chromatic.json"      # ZavyChromaXL + TTPLanet Tile
WF_EDGE_CHROME    = WF_DIR / "style_edge_chrome.json"    # ZavyChromaXL + Canny SDXL
WF_DEPTH_REALISM  = WF_DIR / "style_depth_realism.json"  # JuggXL + DepthAnyV2 + Depth SDXL
WF_ISOMETRIC      = WF_DIR / "style_isometric.json"      # stylized-isometric-sdxl + TTPLanet
WF_PAINTERLY      = WF_DIR / "style_painterly.json"      # dreamshaper_8 + Tile SD1.5 (painterly+dreamlike)
WF_ZAVY_DEPTH     = WF_DIR / "style_zavy_depth.json"     # ZavyChromaXL + DepthAnyV2 + Depth SDXL
WF_PIXEL_ART      = WF_DIR / "style_pixel_art.json"      # JuggXL + pixel-art-xl LoRA + TTPLanet
WF_NEON           = WF_DIR / "style_neon.json"           # ZavyXL + NeonifyV2 LoRA + Canny SDXL

POLL_INTERVAL = 2.0
TIMEOUT       = 900.0   # 15 min — SDXL cold-start (first job loads 6GB checkpoint)
FX_BLACK_RATIO = 0.70

# ── Pipeline definitions ───────────────────────────────────────────────────────
# Ordered: upscale first, then tile by increasing denoise
# Tuple: (workflow_key, denoise, scope)
#   scope "all"     → runs on every category
#   scope "surface" → runs only on SURFACE categories

PIPELINE_DEFS: OrderedDict[str, tuple[str, float, str]] = OrderedDict([
    # ── Base CNN pass (all categories) ─────────────────────────────────
    ("upscale_only",  ("upscale",        1.0,  "all")),
    # ── 10 distinct style passes (SURFACE only, use --twopass) ─────────
    # Each pair shares a checkpoint → minimal VRAM swaps in pipeline-first mode
    # ── JuggernautXL family ─────────────────────────────────────────────
    ("photoreal",     ("photoreal",      0.35, "surface")),  # JuggXL + TTPLanet Tile
    ("depth_realism", ("depth_realism",  0.40, "surface")),  # JuggXL + DepthAnyV2 + Depth SDXL
    ("pixel_art",     ("pixel_art",      0.55, "surface")),  # JuggXL + pixel-art-xl LoRA + TTPLanet
    # ── ZavyChromaXL family ─────────────────────────────────────────────
    ("chromatic",     ("chromatic",      0.35, "surface")),  # ZavyXL + TTPLanet Tile
    ("edge_chrome",   ("edge_chrome",    0.45, "surface")),  # ZavyXL + Canny SDXL
    ("zavy_depth",    ("zavy_depth",     0.40, "surface")),  # ZavyXL + DepthAnyV2 + Depth SDXL
    ("neon",          ("neon",           0.50, "surface")),  # ZavyXL + NeonifyV2 LoRA + Canny SDXL
    # ── stylized-isometric-sdxl ─────────────────────────────────────────
    ("isometric",     ("isometric",      0.45, "surface")),  # iso-sdxl + TTPLanet Tile
    # ── dreamshaper_8 SD1.5 family ──────────────────────────────────────
    ("painterly",     ("painterly",      0.35, "surface")),  # dream8 + Tile SD1.5
    ("dreamlike",     ("painterly",      0.55, "surface")),  # dream8 + Tile SD1.5 (deeper)
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
    # Migrate existing DBs that predate the source/file_size columns
    for col, defn in [("source", "TEXT NOT NULL DEFAULT ''"), ("file_size", "INTEGER")]:
        try:
            db.execute(f"ALTER TABLE assets ADD COLUMN {col} {defn}")
            db.commit()
        except sqlite3.OperationalError:
            pass  # column already exists


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


# ── Resolution cap ─────────────────────────────────────────────────────────────

_RESIZE_CACHE: dict[Path, Path] = {}   # src_path -> tmp_path

def _cap_resolution(src: Path, max_side: int = 1024) -> Path:
    """If src exceeds max_side on either dimension, resize proportionally and
    return a temp path. Otherwise return src unchanged. Results are cached so
    the same source is only resized once per batch run."""
    from PIL import Image
    import tempfile

    if src in _RESIZE_CACHE:
        return _RESIZE_CACHE[src]
    try:
        img = Image.open(src)
        w, h = img.size
        if max(w, h) <= max_side:
            return src
        scale = max_side / max(w, h)
        nw, nh = int(w * scale), int(h * scale)
        img = img.resize((nw, nh), Image.LANCZOS)
        tmp = Path(tempfile.mktemp(suffix=".png", prefix="ql_resize_"))
        img.save(tmp, format="PNG")
        _RESIZE_CACHE[src] = tmp
        return tmp
    except Exception:
        return src   # fall back to original on error


# ── ComfyUI job ────────────────────────────────────────────────────────────────

COMFY_URL = "http://127.0.0.1:8188"
COMFY_WAIT_SECS = 300   # how long to wait for ComfyUI to come back up
COMFY_RETRY_INTERVAL = 10


def _comfy_alive() -> bool:
    """Quick health-check — returns True if ComfyUI is responding."""
    import urllib.request
    try:
        urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=5).read()
        return True
    except Exception:
        return False


def _wait_comfy_up() -> bool:
    """Block until ComfyUI is reachable or COMFY_WAIT_SECS elapses."""
    deadline = time.monotonic() + COMFY_WAIT_SECS
    while time.monotonic() < deadline:
        if _comfy_alive():
            return True
        print(f"    [health] ComfyUI down — retrying in {COMFY_RETRY_INTERVAL}s …", flush=True)
        time.sleep(COMFY_RETRY_INTERVAL)
    return False


def _wait_job(comfy: ComfyClient, job_id: str) -> list[dict[str, str]]:
    deadline = time.monotonic() + TIMEOUT
    while time.monotonic() < deadline:
        try:
            outputs = comfy.output_filenames(job_id)
        except Exception:
            # ComfyUI may have restarted — give it time then keep polling
            time.sleep(COMFY_RETRY_INTERVAL)
            continue
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
    # Health-check before submitting — wait up to COMFY_WAIT_SECS if down
    if not _comfy_alive():
        print("    [health] ComfyUI unreachable before submit — waiting …", flush=True)
        if not _wait_comfy_up():
            print("    [health] ComfyUI did not recover — skipping asset.", flush=True)
            return False
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
        print(f"    ERR {src.name}: {exc}", flush=True)
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
  10 styles: photoreal | chromatic | edge_chrome | depth_realism | isometric | painterly | dreamlike | zavy_depth | pixel_art | neon · {len(rows)} assets · {len(active_pipelines)} pipelines<br>
  Surface route → all style pipelines &nbsp;|&nbsp; FX route → upscale_only only
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
        "upscale_only":  "4x-UltraSharp<br>CNN only",
        # JuggXL family
        "photoreal":     "PHOTOREAL<br>JuggXL+Tile d=0.35",
        "depth_realism": "DEPTH REAL<br>JuggXL+Depth d=0.40",
        "pixel_art":     "PIXEL ART<br>JuggXL+LoRA+Tile d=0.55",
        # ZavyXL family
        "chromatic":     "CHROMATIC<br>ZavyXL+Tile d=0.35",
        "edge_chrome":   "EDGE CHROME<br>ZavyXL+Canny d=0.45",
        "zavy_depth":    "ZAVY DEPTH<br>ZavyXL+Depth d=0.40",
        "neon":          "NEON<br>ZavyXL+NeonLoRA+Canny d=0.50",
        # Isometric
        "isometric":     "ISOMETRIC<br>IsoXL+Tile d=0.45",
        # dreamshaper family
        "painterly":     "PAINTERLY<br>Dream8+Tile d=0.35",
        "dreamlike":     "DREAMLIKE<br>Dream8+Tile d=0.55",
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
    ap.add_argument(
        "--twopass", action="store_true",
        help="Use upscale_only CNN output as source instead of raw pak00 PNG",
    )
    ap.add_argument(
        "--chunk-size", type=int, default=200,
        metavar="N",
        help=(
            "Pipeline-rotation chunk size (default 200). "
            "Process N assets per pipeline before rotating to the next. "
            "Use 0 to process ALL assets per pipeline before rotating (most VRAM-efficient). "
            "Smaller values give earlier cross-style results and catch hallucinations sooner."
        ),
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

    wf_upscale       = load_workflow(WF_UPSCALE)
    wf_photoreal     = load_workflow(WF_PHOTOREAL)
    wf_chromatic     = load_workflow(WF_CHROMATIC)
    wf_edge_chrome   = load_workflow(WF_EDGE_CHROME)
    wf_depth_realism = load_workflow(WF_DEPTH_REALISM)
    wf_isometric     = load_workflow(WF_ISOMETRIC)
    wf_painterly     = load_workflow(WF_PAINTERLY)
    wf_zavy_depth    = load_workflow(WF_ZAVY_DEPTH)
    wf_pixel_art     = load_workflow(WF_PIXEL_ART)
    wf_neon          = load_workflow(WF_NEON)
    prompt           = build_final_prompt("")

    print("  Workflows loaded: 10 style pipelines (8 no-LoRA + 2 signature LoRA)")
    print("  Checkpoints: JuggXL | ZavyChromaXL | stylized-isometric-sdxl | dreamshaper_8")
    print("  ControlNets: TTPLanet Tile | Canny SDXL | Depth SDXL | Tile SD1.5")
    print("  LoRAs: pixel-art-xl (163MB) | NeonifyV2-4Extreme (1.7GB)")

    wf_map = {
        "upscale":        wf_upscale,
        "photoreal":      wf_photoreal,
        "chromatic":      wf_chromatic,
        "edge_chrome":    wf_edge_chrome,
        "depth_realism":  wf_depth_realism,
        "isometric":      wf_isometric,
        "painterly":      wf_painterly,      # shared by painterly + dreamlike (denoise differs)
        "zavy_depth":     wf_zavy_depth,
        "pixel_art":      wf_pixel_art,
        "neon":           wf_neon,
    }

    # ── 5: Batch (pipeline-first, chunk rotation) ─────────────────
    # Pipeline-first: one checkpoint stays in VRAM for the whole chunk.
    # chunk_size=200 means process 200 assets per pipeline before rotating to next.
    # This gives early cross-style results + catches hallucinations before wasting VRAM.
    chunk_size = args.chunk_size if args.chunk_size > 0 else len(all_assets)
    total_jobs = len(all_assets) * len(active_pipelines)
    print(f"\n[5/5] Pipeline-first batch:")
    print(f"  assets={len(all_assets)} × pipelines={len(active_pipelines)} = {total_jobs} jobs")
    print(f"  chunk_size={chunk_size} — rotating through {len(active_pipelines)} styles per chunk")

    total_done = total_skip = total_err = 0
    start_t = time.monotonic()

    # Pre-compute per-asset route + db-id to avoid redundant I/O in inner loop
    asset_meta: list[tuple[int, str, str, str, Path, str]] = []  # (asset_id, label, source, route, orig, rel_str)
    print("  Pre-computing asset metadata...")
    for label, source, rel in all_assets:
        orig = ASSETS / rel
        if not orig.exists():
            total_skip += 1
            continue
        route = _route(label, orig)
        asset_id = _upsert_asset(db, rel, label, source, route)
        asset_meta.append((asset_id, label, source, route, orig, str(rel).replace("\\", "/")))
    print(f"  {len(asset_meta)} valid assets ({total_skip} missing)")

    with ComfyClient(base_url="http://127.0.0.1:8188", timeout=90.0) as comfy:
        # Outer: pipeline rotation chunks
        for chunk_start in range(0, len(asset_meta), chunk_size):
            chunk = asset_meta[chunk_start : chunk_start + chunk_size]
            chunk_end = chunk_start + len(chunk)

            for pipe_name in active_pipelines:
                wf_key, denoise, scope = PIPELINE_DEFS[pipe_name]
                workflow = wf_map[wf_key]
                pipe_done = pipe_skip = pipe_err = 0

                print(
                    f"\n  [{pipe_name}] assets {chunk_start+1}..{chunk_end} "
                    f"(d={denoise})",
                    flush=True,
                )

                for asset_id, label, source, route, orig, rel_str in chunk:
                    # FX assets only get upscale_only
                    if scope == "surface" and route == "fx":
                        pipe_skip += 1
                        total_skip += 1
                        continue

                    rel_path = Path(rel_str)
                    dst = PIPELINES_DIR / pipe_name / rel_path

                    if dst.exists() and not args.force_render:
                        if not _already_rendered(db, asset_id, pipe_name):
                            _log_render(db, asset_id, pipe_name, denoise, dst)
                        pipe_skip += 1
                        total_skip += 1
                        continue

                    if _already_rendered(db, asset_id, pipe_name) and not args.force_render:
                        pipe_skip += 1
                        total_skip += 1
                        continue

                    # Source: twopass uses CNN-upscaled image as input
                    src = orig
                    if args.twopass and pipe_name != "upscale_only":
                        up = PIPELINES_DIR / "upscale_only" / rel_path
                        if up.exists():
                            src = up
                    # Cap at 1024px — prevents SDXL latent blowup (21s/step issue)
                    src = _cap_resolution(src, max_side=1024)

                    ok = _run_one(src, dst, comfy, workflow, prompt, denoise)

                    if ok:
                        _log_render(db, asset_id, pipe_name, denoise, dst)
                        pipe_done += 1
                        total_done += 1
                    else:
                        pipe_err += 1
                        total_err += 1

                # ── Per-pipeline chunk summary (hallucination checkpoint) ──
                elapsed = time.monotonic() - start_t
                rate = total_done / max(elapsed, 1)
                print(
                    f"  [{pipe_name}] chunk done: rendered={pipe_done} "
                    f"skip={pipe_skip} err={pipe_err} "
                    f"| total: done={total_done} skip={total_skip} err={total_err} "
                    f"rate={rate:.2f}/s  elapsed={int(elapsed//60)}m",
                    flush=True,
                )
                if pipe_err > pipe_done * 0.3 and pipe_done > 0:
                    print(
                        f"  WARN [{pipe_name}] error rate >30% — check ComfyUI logs for hallucination",
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
