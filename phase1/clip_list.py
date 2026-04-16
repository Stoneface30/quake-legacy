"""
Clip list management — read/write ordered lists of AVI filenames per Part.

Extended format supports multi-angle cuts and slow-motion:

    # Regular single clip (first-person only):
    Demo (112)  - 21.avi

    # Cut from FP to freelook angle:
    Demo (104) - 8.avi > Demo (104FL1).avi

    # Slow-motion on a clip (0.25x speed at kill moment):
    Demo (209)  -  183.avi [slow]

    # Multi-angle with slow-mo on the freelook:
    Demo (209)  -  183.avi > Demo (209FL1).avi [slow]

    # Intro clip then FP frag (hard cut, no xfade from intro):
    Demo (490)  - 596.avi [intro]

    # Intro then FP then freelook:
    Demo (490)  - 596.avi [intro] > Demo (490FL1).avi

Each line produces one ClipEntry. The assembler expands entries with >
into multiple clip segments joined by a hard cut (no xfade between angles).
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
from phase1.config import Config
from phase1.inventory import scan_part


@dataclass
class ClipEntry:
    """A single line from the clip list, parsed into segments + flags."""
    segments: List[str]          # ordered filenames (1 = single, 2+ = multi-angle)
    slow: bool = False           # apply slow-motion filter to last segment
    intro: bool = False          # hard cut before this entry (no xfade from prior)
    raw_line: str = ""           # original text for debugging


def parse_clip_entry(line: str) -> ClipEntry:
    """Parse one clip list line into a ClipEntry."""
    raw = line.strip()

    # Extract flags
    slow = "[slow]" in raw
    intro = "[intro]" in raw
    cleaned = raw.replace("[slow]", "").replace("[intro]", "").strip()

    # Split on > for multi-angle
    segments = [s.strip() for s in cleaned.split(">") if s.strip()]

    return ClipEntry(segments=segments, slow=slow, intro=intro, raw_line=raw)


def load_clip_list(path: Path) -> List[str]:
    """Load ordered clip filenames from a text file. Skips comments (#) and blanks.

    Returns flat list of filenames (legacy format — single clips only).
    Use load_clip_entries() for extended format with slow/intro/multi-angle.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    return [
        line.strip()
        for line in lines
        if line.strip() and not line.strip().startswith("#")
    ]


def load_clip_entries(path: Path) -> List[ClipEntry]:
    """Load clip list with full extended format support."""
    lines = path.read_text(encoding="utf-8").splitlines()
    entries = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        entries.append(parse_clip_entry(stripped))
    return entries


def save_clip_list(clips: List[str], path: Path, header: str = ""):
    """Save clip list to file with optional header comment."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    if header:
        lines.append(header)
    lines.append(f"# {len(clips)} clips total")
    lines.append("")
    lines.extend(clips)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_default_list(part: int, cfg: Config, output_path: Optional[Path] = None) -> Path:
    """Generate alphabetical clip list from Part folder. Returns path to written file."""
    clips = scan_part(part, cfg)
    filenames = [c.path.name for c in clips]
    out = output_path or cfg.clip_list_path(part)
    # I6 fix: join header lines before passing — save_clip_list appends as one element
    header = "\n".join([
        f"# Part {part} clip list -- EDIT THIS FILE to reorder clips",
        "# One filename per line. Lines starting with # are ignored.",
        f"# Generated from: {cfg.part_dir(part)}",
    ])
    save_clip_list(filenames, out, header=header)
    return out


def validate_clip_list(part: int, filenames: List[str], cfg: Config) -> List[str]:
    """Return list of filenames that don't exist in the Part folder."""
    part_dir = cfg.part_dir(part)
    missing = [f for f in filenames if not (part_dir / f).exists()]
    if missing:
        print(f"WARNING: Part {part} — {len(missing)} clips not found:")
        for m in missing:
            print(f"  MISSING: {m}")
    return missing


def get_clip_paths(part: int, cfg: Config) -> List[Path]:
    """Load clip list for a Part and return full paths. Validates all exist."""
    list_path = cfg.clip_list_path(part)
    if not list_path.exists():
        print(f"No clip list found for Part {part}. Generating default (alphabetical)...")
        generate_default_list(part, cfg)

    filenames = load_clip_list(list_path)

    # S2 fix: catch empty part before it reaches ffmpeg
    if not filenames:
        raise ValueError(
            f"Part {part} clip list is empty. "
            f"Check {list_path} and {cfg.part_dir(part)}"
        )

    missing = validate_clip_list(part, filenames, cfg)
    if missing:
        raise FileNotFoundError(
            f"Part {part}: {len(missing)} clips missing from {cfg.part_dir(part)}"
        )

    return [cfg.part_dir(part) / f for f in filenames]


if __name__ == "__main__":
    """Generate default clip lists for all parts that don't have one."""
    cfg = Config()
    for part in cfg.parts:
        list_path = cfg.clip_list_path(part)
        if not list_path.exists():
            out = generate_default_list(part, cfg)
            clips = load_clip_list(out)
            print(f"Part {part}: generated {len(clips)} clips -> {out}")
        else:
            clips = load_clip_list(list_path)
            print(f"Part {part}: existing list ({len(clips)} clips) — skipped")
