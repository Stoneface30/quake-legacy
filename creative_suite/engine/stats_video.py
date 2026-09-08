"""Phase 1+2 project presentation video (draft generator).

PANTHEON-styled stat cards (PIL) + showcase footage, assembled with ffmpeg.
Data source: output/demo_v2/project_stats.json (DB-derived). Draft quality —
the user reviews structure before any final polish.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# DATA, not code: under a worktree these differ, and opening a
# database beneath the wrong one silently CREATES an empty file
# rather than failing. See engine.pantheon.store.
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()
STATS = REPO_ROOT / "output" / "demo_v2" / "project_stats.json"
OUT_DIR = REPO_ROOT / "output" / "demo_v2" / "presentation"
FF = REPO_ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffmpeg.exe"

W, H = 1920, 1080
BG = (14, 14, 16)
GREY = (176, 180, 188)
SILVER = (225, 228, 233)
GOLD = (212, 175, 55)
BLUE = (36, 62, 122)


def _font(size: int, bold=False):
    for name in (("arialbd.ttf" if bold else "arial.ttf"),
                 "segoeui.ttf"):
        try:
            return ImageFont.truetype(f"C:/Windows/Fonts/{name}", size)
        except OSError:
            continue
    return ImageFont.load_default()


def card(title: str, rows: list[tuple[str, str]], sub: str = "") -> Image.Image:
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    # frame + header rule (PANTHEON grey/silver, gold accents)
    d.rectangle([60, 60, W - 60, H - 60], outline=(60, 62, 68), width=2)
    d.text((110, 110), "PANTHEON", font=_font(34, True), fill=GOLD)
    d.text((110, 158), "pTn.Tr4sH  ·  QUAKE LIVE  ·  CLAN ARENA",
           font=_font(24), fill=GREY)
    d.line([110, 210, W - 110, 210], fill=(70, 72, 78), width=2)
    d.text((110, 250), title, font=_font(58, True), fill=SILVER)
    y = 380
    for label, value in rows:
        d.text((150, y), value, font=_font(64, True), fill=GOLD)
        d.text((640, y + 14), label, font=_font(36), fill=SILVER)
        y += 108
    if sub:
        d.text((110, H - 140), sub, font=_font(24), fill=GREY)
    return im


def build() -> Path:
    s = json.loads(STATS.read_text())
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cards = [
        ("title", card("THE DEMO ARCHIVE PROJECT",
                       [("years of Quake Live demos, 2010-2013", "13.2 GB"),
                        ("recovered from one broken parser bit", "x966")],
                       "Phase 1: preserve the historical AVI series"
                       " - Phase 2: mine the raw demos")),
        ("corpus", card("THE CORPUS",
                        [("physical demo files", f"{s['physical_demo_files']:,}"),
                         ("unique demos", f"{s['unique_demos']:,}"),
                         ("hours of gameplay", f"{s['gameplay_hours_estimate']:,.0f}"),
                         ("maps", str(s['maps_played']))],
                        "98% Clan Arena - campgrounds, asylum, overkill,"
                        " hiddenfortress, trinity, quarantine")),
        ("kills", card("THE KILLS",
                       [("kills witnessed in demos", f"{s['match_kills_all_players']:,}"),
                        ("by pTn.Tr4sH", f"{s['recorder_kills']:,}"),
                        ("distinct opponents fragged", f"{s['distinct_victim_names']:,}"),
                        ("clutch rounds won", f"{s['clutch_rounds_won']:,}")],
                       "every kill parsed from raw .dm_73 network messages"
                       " - custom protocol-73 parser, 0 packet errors")),
        ("skill", card("THE SKILL, MEASURED",
                       [("geometry-confirmed direct rockets",
                         f"{s['skill_labels'].get('DIRECT_CONFIRMED_GEO', 0):,}"),
                        ("clean flicks (aim-curve verified)",
                         f"{s['skill_labels'].get('CLEAN_FLICK', 0):,}"),
                        ("airborne rocket kills",
                         f"{s['skill_labels'].get('AIR_ROCKET_GEO', 0):,}"),
                        ("pixel shots (BSP-verified)",
                         f"{s['skill_labels'].get('PIXEL_SHOT_GEO', 0):,}")],
                       "view-angle timeseries - LG damage flows - projectile"
                       " reconstruction - BSP visibility")),
        ("rank", card("THE RECORD (archive-verified)",
                      [("peak world rank, Clan Arena", "#39"),
                       ("peak Elo, Master ladder", "2326"),
                       ("France ranking", "#3"),
                       ("ranked CA games on QLRanks", "2,858")],
                      "18 Wayback Machine snapshots of qlranks.com,"
                      " 2012-2015 - numbers verbatim from the archive")),
        ("pipeline", card("THE PIPELINE",
                          [("frags classified", f"{s['recognized_frag_rows']:,}"),
                           ("full re-parses needed per new idea", "0"),
                           ("re-ranking runtime", "2.5 s"),
                           ("tests passing", str(s['pipeline']['tests_passing']))],
                          "demos parsed once - features cached forever -"
                          " taxonomy is a query, not a rescan")),
    ]
    seq = []
    for name, im in cards:
        p = OUT_DIR / f"card_{name}.png"
        im.save(p)
        seq.append(p)

    # card segments (4s each) + showcase excerpt if present
    parts = []
    for i, p in enumerate(seq):
        seg = OUT_DIR / f"seg_{i}.mp4"
        subprocess.run([str(FF), "-y", "-loglevel", "error", "-loop", "1",
                        "-i", str(p), "-t", "4", "-r", "30",
                        "-vf", "fade=in:0:12,fade=out:108:12",
                        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
                        "-an", str(seg)], check=True, timeout=300)
        parts.append(seg)
    show = REPO_ROOT / "output" / "demo_v2" / "showcase_C.mp4"
    if show.exists():
        seg = OUT_DIR / "seg_showcase.mp4"
        subprocess.run([str(FF), "-y", "-loglevel", "error", "-ss", "3",
                        "-t", "7", "-i", str(show), "-vf",
                        "scale=1920:1080,fade=in:0:10", "-r", "30", "-an",
                        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
                        str(seg)], check=True, timeout=300)
        parts.insert(4, seg)

    lst = OUT_DIR / "concat.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    out = OUT_DIR / "project_presentation_draft.mp4"
    subprocess.run([str(FF), "-y", "-loglevel", "error", "-f", "concat",
                    "-safe", "0", "-i", str(lst), "-c", "copy", str(out)],
                   check=True, timeout=300)
    return out


if __name__ == "__main__":
    p = build()
    print("presentation draft:", p, f"{p.stat().st_size/1e6:.0f} MB")
