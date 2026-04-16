"""Central configuration for Phase 1 — all paths and constants."""
from pathlib import Path
from typing import Optional, List

# Project root is one level up from phase1/
ROOT = Path(__file__).parent.parent


class Config:
    """All paths and pipeline constants. Uses explicit __init__ — no shared class-level mutables."""

    def __init__(self):
        # ── Binaries ──────────────────────────────────────────
        self.ffmpeg_bin:    Path = ROOT / "tools" / "ffmpeg" / "ffmpeg.exe"
        self.ffprobe_bin:   Path = ROOT / "tools" / "ffmpeg" / "ffprobe.exe"

        # ── Source clips — three-tier structure ───────────────────
        # HARD RULE: ALL clips for a Part come from T1+T2+T3 combined.
        # T1 = top tier (main frags), T2 = second tier, T3 = lower tier.
        # T3 multi-angle subdirs = priority intro/outro candidates.
        # T2 multi-angle subdirs = secondary intro/outro candidates.
        # T1 clips = backbone of every Part.
        self.clips_root:    Path = ROOT / "QUAKE VIDEO"   # parent of T1/T2/T3
        self.tier_roots: dict = {
            1: ROOT / "QUAKE VIDEO" / "T1",
            2: ROOT / "QUAKE VIDEO" / "T2",
            3: ROOT / "QUAKE VIDEO" / "T3",
        }
        self.intro_source:  Path = ROOT / "FRAGMOVIE VIDEOS" / "IntroPart2.mp4"
        # PANTHEON intro: 25.77s, grey/silver logo → in-game CA Tribute billboard.
        # Prepended to EVERY Part automatically. Never skip.

        # ── Clip lists ────────────────────────────────────────
        self.clip_lists_dir: Path = ROOT / "phase1" / "clip_lists"

        # ── Output ────────────────────────────────────────────
        self.output_dir:    Path = ROOT / "output"
        self.preview_dir:   Path = ROOT / "output" / "previews"

        # ── Encoding ──────────────────────────────────────────
        self.target_fps:    int  = 60
        self.target_width:  int  = 1920
        self.target_height: int  = 1080
        self.crf:           int  = 17
        self.preset:        str  = "slow"
        self.audio_bitrate: str  = "320k"

        # ── Color grade (Tribute series style) ────────────────
        self.grade_contrast:    float = 1.4
        self.grade_saturation:  float = 1.7
        self.grade_brightness:  float = 0.0
        self.bloom_sigma:       int   = 18
        self.bloom_opacity:     float = 0.3   # matches spec

        # ── Transitions ───────────────────────────────────────
        self.xfade_duration:    float = 0.25  # cross-fade between clips (seconds)
        self.intro_fade_in:     float = 1.5   # fade in from black
        self.outro_fade_out:    float = 2.5   # fade to black

        # ── Parts ─────────────────────────────────────────────
        self.parts: List[int] = list(range(4, 13))  # instance attribute, not class-level

        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.preview_dir.mkdir(parents=True, exist_ok=True)
        self.clip_lists_dir.mkdir(parents=True, exist_ok=True)

    def part_dir(self, part: int, tier: int = 1) -> Path:
        """Return the Part directory for a given tier (1=T1, 2=T2, 3=T3)."""
        return self.tier_roots[tier] / f"Part{part}"

    def all_tier_part_dirs(self, part: int) -> list:
        """Return all three tier Part directories that exist."""
        return [d for d in [self.tier_roots[t] / f"Part{part}" for t in (1, 2, 3)] if d.exists()]

    def clip_list_path(self, part: int) -> Path:
        return self.clip_lists_dir / f"part{part:02d}.txt"

    def output_path(self, part: int) -> Path:
        return self.output_dir / f"Part{part}.mp4"

    def preview_path(self, part: int) -> Path:
        return self.preview_dir / f"Part{part}_preview.mp4"

    def normalize_path(self, avi_path: Path) -> Path:
        """CFR-normalized version of an AVI clip."""
        norm_dir = self.output_dir / "normalized"
        norm_dir.mkdir(exist_ok=True)
        return norm_dir / (avi_path.stem + "_cfr60.mp4")

    def music_path(self, part: int) -> Optional[Path]:
        """Auto-detect music file for this Part. Returns None if not found."""
        music_dir = ROOT / "phase1" / "music"
        for ext in [".mp3", ".ogg", ".wav", ".flac"]:
            candidate = music_dir / f"part{part:02d}_music{ext}"
            if candidate.exists():
                return candidate
        return None
