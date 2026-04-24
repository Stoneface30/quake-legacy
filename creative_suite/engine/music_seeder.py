"""music_seeder.py — seed music_assignments DB from beats.json files.

Scans creative_suite/engine/music/ for:
  - partNN_music.mp3.beats.json  (legacy single-track)
  - partNN_music_NN.mp3          (multi-track — infers role from suffix _01/_02/...)

For each discovered track+beats.json pair, upserts a row in music_assignments
with real BPM from the tempo field.  Safe to re-run — uses upsert semantics.

Usage:
    python -m creative_suite.engine.music_seeder [--dry-run] [--parts 4,5,6]
    python -m creative_suite.engine.music_seeder --db path/to/studio_nle.db
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Repo root: two parents up from creative_suite/engine/
_ENGINE_DIR = Path(__file__).parent          # creative_suite/engine/
_CS_DIR     = _ENGINE_DIR.parent             # creative_suite/
_REPO_ROOT  = _CS_DIR.parent                 # G:/QUAKE_LEGACY

# Default DB path
_DEFAULT_DB = _CS_DIR / "database" / "studio_nle.db"

# Default music dir
_DEFAULT_MUSIC_DIR = _ENGINE_DIR / "music"

# Multi-track filename: partNN_music_NN.ext  (suffix _01 = intro, _02 = main_1, etc.)
_MULTI_TRACK_RE = re.compile(
    r"^part(\d{2})_music_(\d{2})\.([^.]+)$", re.IGNORECASE
)
# Single-track filename: partNN_music.ext  (legacy)
_SINGLE_TRACK_RE = re.compile(
    r"^part(\d{2})_music\.([^.]+)$", re.IGNORECASE
)
# Intro / outro filenames: partNN_intro_music.ext, partNN_outro_music.ext
_INTRO_RE = re.compile(r"^part(\d{2})_intro_music\.([^.]+)$", re.IGNORECASE)
_OUTRO_RE = re.compile(r"^part(\d{2})_outro_music\.([^.]+)$", re.IGNORECASE)
# Series-level defaults: pantheon_intro_music.*, pantheon_outro_music.*
_SERIES_INTRO_RE = re.compile(r"^pantheon_intro_music\.([^.]+)$", re.IGNORECASE)
_SERIES_OUTRO_RE = re.compile(r"^pantheon_outro_music\.([^.]+)$", re.IGNORECASE)

_MUSIC_EXTS = {".mp3", ".ogg", ".wav", ".flac", ".aac", ".m4a"}


def _parse_beats_json(path: Path) -> tuple[float, float] | None:
    """Return (tempo_bpm, duration_s) from a beats.json file, or None."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        tempo = float(data.get("tempo", 0))
        duration = float(data.get("duration", 0))
        if tempo > 0:
            return tempo, duration
    except Exception:
        pass
    return None


def _find_beats_json(track_path: Path) -> Path | None:
    """Look for a sidecar beats.json next to a track file.

    Checks:
      - track.mp3.beats.json
      - track.beats.json
    """
    for candidate in [
        track_path.parent / (track_path.name + ".beats.json"),
        track_path.with_suffix(".beats.json"),
    ]:
        if candidate.exists():
            return candidate
    return None


def _role_from_suffix(suffix_num: int) -> str:
    """Map numeric multi-track suffix to role name.

    _01 → intro
    _02 → main_1
    _03 → main_2
    _04 → outro
    _05+ → main_N (where N = suffix_num - 2)
    """
    mapping = {1: "intro", 2: "main_1", 3: "main_2", 4: "outro"}
    if suffix_num in mapping:
        return mapping[suffix_num]
    return f"main_{suffix_num - 1}"


def _part_level_beats_json(music_dir: Path, part: int) -> Path | None:
    """Return the part-level legacy beats.json (partNN_music.*.beats.json), or None.

    The real track file partNN_music.mp3 may not exist if only the multi-track
    _01/_02/... files are present.  We scan for any partNN_music.* file — that
    includes the .beats.json sidecar itself which we return directly when found.
    """
    nn = f"{part:02d}"
    for f in sorted(music_dir.glob(f"part{nn}_music.*")):
        # If the glob returned the beats.json itself, use it directly
        if f.name.endswith(".beats.json"):
            return f
        # Otherwise look for the sidecar alongside the track file
        bjson = music_dir / (f.name + ".beats.json")
        if bjson.exists():
            return bjson
    return None


def discover_tracks(music_dir: Path, parts_filter: set[int] | None = None) -> list[dict]:
    """Scan music_dir and return a list of track dicts ready for DB upsert.

    Each dict has: part, role, filename, bpm, duration_s
    BPM resolution order:
      1. Sidecar: <filename>.beats.json
      2. Part-level legacy: partNN_music.mp3.beats.json (tempo shared for all slots)
    """
    if not music_dir.exists():
        print(f"[seeder] music dir not found: {music_dir}", file=sys.stderr)
        return []

    # Cache part-level BPM so we read each beats.json once
    _part_bpm_cache: dict[int, tuple[float, float] | None] = {}

    def _part_bpm(part: int) -> tuple[float, float] | None:
        if part not in _part_bpm_cache:
            bjson = _part_level_beats_json(music_dir, part)
            _part_bpm_cache[part] = _parse_beats_json(bjson) if bjson else None
        return _part_bpm_cache[part]

    records: list[dict] = []

    for f in sorted(music_dir.iterdir()):
        if f.suffix.lower() not in _MUSIC_EXTS:
            continue

        part: int | None = None
        role: str | None = None

        m = _MULTI_TRACK_RE.match(f.name)
        if m:
            part = int(m.group(1))
            role = _role_from_suffix(int(m.group(2)))
        else:
            m = _SINGLE_TRACK_RE.match(f.name)
            if m:
                # Skip single-track file if multi-track _01 exists (avoid duplicate main_1)
                nn = f"{int(m.group(1)):02d}"
                if any(music_dir.glob(f"part{nn}_music_01.*")):
                    continue
                part = int(m.group(1))
                role = "main_1"
            else:
                m = _INTRO_RE.match(f.name)
                if m:
                    part = int(m.group(1))
                    role = "intro"
                else:
                    m = _OUTRO_RE.match(f.name)
                    if m:
                        part = int(m.group(1))
                        role = "outro"

        if part is None or role is None:
            continue
        if parts_filter and part not in parts_filter:
            continue

        bpm: float | None = None
        duration_s: float | None = None

        # Try sidecar first
        beats_file = _find_beats_json(f)
        if beats_file:
            result = _parse_beats_json(beats_file)
            if result:
                bpm, duration_s = result

        # Fall back to part-level legacy beats.json for BPM (duration stays None)
        if bpm is None:
            part_result = _part_bpm(part)
            if part_result:
                bpm = part_result[0]   # share tempo; duration unknown for this slot

        records.append({
            "part":       part,
            "role":       role,
            "filename":   f.name,
            "bpm":        round(bpm, 2) if bpm else None,
            "duration_s": duration_s,
        })

    return records


def seed(db_path: Path, music_dir: Path,
         parts_filter: set[int] | None = None,
         dry_run: bool = False) -> int:
    """Discover tracks and upsert into music_assignments. Returns count seeded."""
    from creative_suite.database.nle_db import upsert_music_assignment

    records = discover_tracks(music_dir, parts_filter)
    if not records:
        print("[seeder] no tracks found — nothing to seed")
        return 0

    count = 0
    for rec in records:
        print(
            f"  part{rec['part']:02d} {rec['role']:<10}  {rec['filename']}"
            f"  BPM={rec['bpm'] or '?':>6}  dur={rec['duration_s'] or '?':.0f}s"
            if rec["duration_s"] else
            f"  part{rec['part']:02d} {rec['role']:<10}  {rec['filename']}"
            f"  BPM={rec['bpm'] or '?'}"
        )
        if not dry_run:
            upsert_music_assignment(
                db_path=db_path,
                part=rec["part"],
                role=rec["role"],
                track_filename=rec["filename"],
                artist=None,
                title=None,
                bpm=rec["bpm"],
                duration_s=rec["duration_s"],
                position={"intro": 0, "main_1": 1, "main_2": 2, "outro": 3}.get(rec["role"], 1),
            )
        count += 1

    if dry_run:
        print(f"[seeder] DRY RUN — would seed {count} track(s)")
    else:
        print(f"[seeder] seeded {count} track(s) -> {db_path}")
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed music_assignments from beats.json files")
    parser.add_argument("--db",       default=str(_DEFAULT_DB),       help="Path to studio_nle.db")
    parser.add_argument("--music",    default=str(_DEFAULT_MUSIC_DIR), help="Path to music dir")
    parser.add_argument("--parts",    default=None, help="Comma-separated part numbers e.g. 4,5,6")
    parser.add_argument("--dry-run",  action="store_true",             help="Print without writing")
    args = parser.parse_args()

    parts_filter: set[int] | None = None
    if args.parts:
        parts_filter = {int(x.strip()) for x in args.parts.split(",") if x.strip()}

    seed(
        db_path=Path(args.db),
        music_dir=Path(args.music),
        parts_filter=parts_filter,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
