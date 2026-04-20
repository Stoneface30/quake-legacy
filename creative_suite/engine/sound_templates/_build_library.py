"""
Build Quake Live sound template library foundation (Rule P1-DD).

Steps:
  1. Inventory all sound/* entries in pak00.pk3 (READ ONLY — ENG-1)
  2. Extract curated subset into raw/
  3. Transcode .ogg -> .wav via ffmpeg (48 kHz mono 16-bit)
  4. Emit manifest.json with auto-classified categories
  5. Smoke report to stdout
"""
from __future__ import annotations

import fnmatch
import json
import os
import shutil
import subprocess
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

PAK = Path(r"C:/Program Files (x86)/Steam/steamapps/common/Quake Live/baseq3/pak00.pk3")
ROOT = Path(r"G:/QUAKE_LEGACY/phase1/sound_templates")
RAW = ROOT / "raw"
FFMPEG = Path(r"G:/QUAKE_LEGACY/tools/ffmpeg/ffmpeg.exe")
FFPROBE = Path(r"G:/QUAKE_LEGACY/tools/ffmpeg/ffprobe.exe")

INVENTORY_TXT = ROOT / "pak00_sound_inventory.txt"
MANIFEST_JSON = ROOT / "manifest.json"

# Path-glob patterns for extraction (relative to pk3 root). Case-insensitive.
# sound/music/** is EXPLICITLY excluded.
EXTRACT_PATTERNS = [
    # Weapons (fire + impact/explode for all weapons)
    "sound/weapons/*",
    "sound/weapons/*/*",
    "sound/weapons/*/*/*",
    # Player events
    "sound/player/*death*",
    "sound/player/*/*death*",
    "sound/player/*gasp*",
    "sound/player/*/*gasp*",
    "sound/player/*fall*",
    "sound/player/*/*fall*",
    "sound/player/*pain*",
    "sound/player/*/*pain*",
    "sound/player/*jump*",
    "sound/player/*/*jump*",
    "sound/player/*land*",
    "sound/player/*/*land*",
    "sound/player/*taunt*",
    "sound/player/*/*taunt*",
    # Misc high-value events
    "sound/misc/*telein*",
    "sound/misc/*teleout*",
    "sound/misc/*quad*",
    "sound/misc/*powerup*",
    "sound/misc/*regen*",
    "sound/misc/*haste*",
    "sound/misc/*invis*",
    "sound/misc/*battlesuit*",
    "sound/misc/*flight*",
    # Items
    "sound/items/*pickup*",
    "sound/items/*health*",
    "sound/items/*armor*",
    "sound/items/*",
    # World / ambient (capped to 50 per task spec)
    "sound/world/*",
    "sound/world/*/*",
    # Feedback (hit markers, accuracy)
    "sound/feedback/*",
    "sound/feedback/*/*",
]

# Hard exclusion (never extract)
EXCLUDE_PATTERNS = [
    "sound/music/*",
    "sound/music/*/*",
]

WORLD_CAP = 50


def match_any(path: str, patterns: list[str]) -> bool:
    p = path.lower()
    for pat in patterns:
        if fnmatch.fnmatch(p, pat.lower()):
            return True
    return False


def inventory(zf: zipfile.ZipFile) -> list[tuple[str, int]]:
    out = []
    for info in zf.infolist():
        if info.is_dir():
            continue
        name = info.filename.replace("\\", "/")
        if name.lower().startswith("sound/"):
            out.append((name, info.file_size))
    return sorted(out)


def should_extract(path: str) -> bool:
    if match_any(path, EXCLUDE_PATTERNS):
        return False
    lower = path.lower()
    # Only wav/ogg audio
    if not (lower.endswith(".wav") or lower.endswith(".ogg")):
        return False
    return match_any(path, EXTRACT_PATTERNS)


def classify(rel_path: str) -> tuple[str, str]:
    """(category, event_type)"""
    p = rel_path.lower().replace("\\", "/")
    # Strip leading "sound/"
    if p.startswith("sound/"):
        p = p[len("sound/"):]

    # Weapons — Quake uses cryptic legacy names:
    #   *lf1a  = launcher fire    (rocklf1a, grenlf1a)
    #   *lx1a  = launcher explode (rocklx1a)
    #   *mx1a  = plasma explode   (plasmx1a)
    #   *gf1a/b= gun fire         (railgf1a, machgf1b, sshotf1b, vulcanf1b, hyprbf1a)
    #   *imp*  = impact           (wnalimpd, wvulimpd, wstbimpd)
    #   *exp*  = explode          (wstbexpl, rockexp)
    #   *hum*  = idle loop        (bfg_hum, lg_hum, rg_hum)
    #   *fly*  = projectile flight (rockfly, lasfly, grhang)
    #   *hit*  = impact (lg_hit)
    #   *fire* = literal fire     (bfg_fire, lg_fire, wnalfire, wstbfire, wvulfire, grfire)
    #   ric*   = ricochet (machinegun)
    if p.startswith("weapons/"):
        parts = p.split("/")
        # If weapon folder exists use it; else top-level file
        if len(parts) >= 3:
            weapon = parts[1]
        else:
            weapon = "generic"
        stem = Path(p).stem.lower()

        # Impact / explode / hit come FIRST (before "fire") because
        # "wstbexpl" contains none of the fire tokens but "impd" matches impact.
        impact_tokens = ("imp", "exp", "rockexp", "hit", "ric", "buletby",
                         "lx1a", "mx1a", "bf1a")  # bf1a = hyperblaster bullet
        fire_tokens = ("fire", "lf1a", "gf1a", "gf1b", "gf2b", "gf3b", "gf4b",
                       "fl1", "flash", "shot")
        idle_tokens = ("hum", "idle", "ready", "raise", "reset", "wind", "actv",
                       "tick", "hang", "pull")
        flight_tokens = ("fly", "rockfly", "lasfly")

        # Special-case: plasmx1a = plasma impact, hyprbf1a = plasma fire
        if weapon == "plasma":
            if "mx1a" in stem or "exp" in stem or "imp" in stem:
                return "weapon_impact", "plasma_impact"
            if "bf1a" in stem or "hypr" in stem or "fire" in stem:
                return "weapon_fire", "plasma_fire"

        if any(t in stem for t in impact_tokens):
            return "weapon_impact", f"{weapon}_impact"
        if any(t in stem for t in fire_tokens):
            return "weapon_fire", f"{weapon}_fire"
        if any(t in stem for t in idle_tokens):
            return "weapon_idle", f"{weapon}_idle"
        if any(t in stem for t in flight_tokens):
            return "weapon_flight", f"{weapon}_flight"
        return "weapon_other", f"{weapon}_{stem}"

    # Player
    if p.startswith("player/"):
        stem = Path(p).stem
        if "death" in stem or "gasp" in stem:
            return "player_death", "death"
        if "fall" in stem:
            return "player_death", "fall"
        if "pain" in stem:
            return "player_pain", "pain"
        if "jump" in stem:
            return "player_move", "jump"
        if "land" in stem:
            return "player_move", "land"
        if "taunt" in stem:
            return "player_taunt", "taunt"
        return "player_other", stem

    # Misc (powerups / teleport)
    if p.startswith("misc/"):
        stem = Path(p).stem
        for key in ("telein", "teleout", "quad", "regen", "haste", "invis",
                    "battlesuit", "flight", "powerup"):
            if key in stem:
                return "powerup_event", key
        return "misc", stem

    # Items
    if p.startswith("items/"):
        stem = Path(p).stem
        if "health" in stem:
            return "pickup", "pickup_health"
        if "armor" in stem:
            return "pickup", "pickup_armor"
        if "pickup" in stem or "respawn" in stem:
            return "pickup", stem
        return "pickup", stem

    # World
    if p.startswith("world/"):
        return "world", Path(p).stem

    # Feedback (hit markers)
    if p.startswith("feedback/"):
        return "feedback", Path(p).stem

    return "uncategorized", Path(p).stem


def run_ffprobe_duration(path: Path) -> float:
    try:
        out = subprocess.check_output(
            [str(FFPROBE), "-v", "error", "-show_entries",
             "format=duration", "-of",
             "default=noprint_wrappers=1:nokey=1", str(path)],
            stderr=subprocess.DEVNULL, text=True, timeout=10,
        ).strip()
        return float(out) if out else 0.0
    except Exception:
        return 0.0


def run_ffmpeg_rms(path: Path) -> float:
    """Mean RMS via ffmpeg volumedetect (dB)."""
    try:
        out = subprocess.check_output(
            [str(FFMPEG), "-hide_banner", "-nostats", "-i", str(path),
             "-af", "volumedetect", "-f", "null", "-"],
            stderr=subprocess.STDOUT, text=True, timeout=15,
        )
        for line in out.splitlines():
            if "mean_volume:" in line:
                # "[Parsed_volumedetect_0 @ 0xXXXX] mean_volume: -23.5 dB"
                val = line.split("mean_volume:")[1].strip().split()[0]
                db = float(val)
                # Convert dBFS to linear RMS
                return 10 ** (db / 20.0)
    except Exception:
        pass
    return 0.0


def transcode_ogg_to_wav(ogg: Path, wav: Path) -> bool:
    if wav.exists():
        return True
    try:
        subprocess.check_output(
            [str(FFMPEG), "-y", "-hide_banner", "-loglevel", "error",
             "-i", str(ogg),
             "-ac", "1", "-ar", "48000", "-sample_fmt", "s16",
             str(wav)],
            stderr=subprocess.STDOUT, timeout=30,
        )
        return True
    except Exception as e:
        print(f"  ogg->wav FAILED: {ogg.name}: {e}", file=sys.stderr)
        return False


def dir_size_bytes(p: Path) -> int:
    total = 0
    for root, _dirs, files in os.walk(p):
        for f in files:
            try:
                total += (Path(root) / f).stat().st_size
            except OSError:
                pass
    return total


def main():
    assert PAK.exists(), f"pak00.pk3 missing: {PAK}"
    assert FFMPEG.exists(), f"ffmpeg missing: {FFMPEG}"
    RAW.mkdir(parents=True, exist_ok=True)

    print(f"[1/5] Inventorying {PAK} ...")
    with zipfile.ZipFile(PAK, "r") as zf:
        inv = inventory(zf)

        with INVENTORY_TXT.open("w", encoding="utf-8") as f:
            f.write(f"# pak00.pk3 sound/ inventory\n")
            f.write(f"# total_entries={len(inv)}\n")
            for name, size in inv:
                f.write(f"{size:>12}  {name}\n")
        print(f"  wrote {INVENTORY_TXT.name} ({len(inv)} entries)")

        # ---- Step 2: extract ----
        print(f"[2/5] Extracting curated subset into {RAW} ...")
        extracted: list[Path] = []
        world_count = 0
        for name, _size in inv:
            if not should_extract(name):
                continue
            if name.lower().startswith("sound/world/"):
                if world_count >= WORLD_CAP:
                    continue
                world_count += 1

            target = RAW / name  # preserves sound/... structure
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                with zf.open(name) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
            extracted.append(target)
        print(f"  extracted {len(extracted)} files (world capped at {WORLD_CAP})")

    # ---- Step 3: transcode ogg -> wav ----
    print("[3/5] Transcoding .ogg -> .wav (48 kHz mono 16-bit) ...")
    transcoded = 0
    for p in list(extracted):
        if p.suffix.lower() == ".ogg":
            wav = p.with_suffix(".wav")
            if transcode_ogg_to_wav(p, wav):
                if wav not in extracted:
                    extracted.append(wav)
                transcoded += 1
    print(f"  transcoded {transcoded} ogg files")

    # ---- Step 4: manifest ----
    print("[4/5] Building manifest (duration + RMS via ffprobe/ffmpeg) ...")
    manifest = {
        "source": "quake_live_pak00.pk3",
        "extracted_at": "2026-04-18",
        "root": str(RAW).replace("\\", "/"),
        "categories": defaultdict(list),
    }
    # Only catalogue .wav files (our template format)
    wav_files = [p for p in extracted if p.suffix.lower() == ".wav"]
    for i, wav in enumerate(sorted(wav_files)):
        rel = wav.relative_to(RAW).as_posix()
        cat, event = classify(rel)
        duration = run_ffprobe_duration(wav)
        rms = run_ffmpeg_rms(wav)
        manifest["categories"][cat].append({
            "path": rel,
            "event_type": event,
            "duration_s": round(duration, 3),
            "rms": round(rms, 4),
            "size_bytes": wav.stat().st_size,
        })
        if (i + 1) % 50 == 0:
            print(f"  catalogued {i + 1}/{len(wav_files)}")

    manifest["categories"] = dict(manifest["categories"])
    with MANIFEST_JSON.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"  wrote {MANIFEST_JSON.name}")

    # ---- Step 5: smoke report ----
    print("\n========= SMOKE REPORT =========")
    print(f"Inventory total (sound/ only):       {len(inv)}")
    print(f"Extracted files (ogg+wav originals): {len(extracted) - transcoded}")
    print(f"Transcoded OGG->WAV:                 {transcoded}")
    print(f"Total WAVs catalogued:               {len(wav_files)}")
    print()
    print("Per-category counts:")
    cat_counts = {k: len(v) for k, v in manifest["categories"].items()}
    for cat in sorted(cat_counts, key=lambda c: -cat_counts[c]):
        print(f"  {cat:22s} {cat_counts[cat]:>5}")
    print()

    event_counter = Counter()
    for items in manifest["categories"].values():
        for it in items:
            event_counter[it["event_type"]] += 1
    print("Top 10 event_types:")
    for ev, n in event_counter.most_common(10):
        print(f"  {ev:28s} {n:>5}")
    print()

    total_bytes = dir_size_bytes(ROOT)
    mb = total_bytes / (1024 * 1024)
    print(f"Total on disk under {ROOT.name}/: {total_bytes} bytes ({mb:.1f} MB)")

    # Missing-expected check
    print()
    print("Missing-expected-sound audit:")
    expected_events = [
        "rocket_fire", "rocket_impact",
        "railgun_fire", "rail_fire",
        "lightning_fire",
        "plasma_fire", "plasma_impact",
        "grenade_fire", "grenade_impact",
        "shotgun_fire", "machinegun_fire",
        "gauntlet_fire", "bfg_fire",
        "death", "pain", "jump", "land",
    ]
    found_events = set(event_counter.keys())
    missing = []
    for ev in expected_events:
        # Match loosely
        hits = [e for e in found_events if ev in e or e.startswith(ev)]
        if not hits:
            missing.append(ev)
        else:
            pass
    if missing:
        print("  MISSING:", ", ".join(missing))
    else:
        print("  all expected events present")


if __name__ == "__main__":
    main()
