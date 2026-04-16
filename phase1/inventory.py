"""Scan T1/T2/T3 clip folders and build clip metadata."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict
import subprocess, json
from phase1.config import Config


@dataclass
class ClipInfo:
    path: Path
    part: int
    size_mb: float
    duration_s: float = 0.0
    width: int = 0
    height: int = 0
    fps: float = 0.0

    def __str__(self):
        return f"{self.path.name} ({self.size_mb:.0f}MB, {self.duration_s:.1f}s)"


def get_clip_info(path: Path, cfg: Config) -> ClipInfo:
    """Run ffprobe on a clip to get duration, resolution, fps."""
    result = subprocess.run([
        str(cfg.ffprobe_bin), "-v", "quiet",
        "-print_format", "json",
        "-show_streams", "-show_format",
        str(path)
    ], capture_output=True, text=True)

    size_mb = path.stat().st_size / 1024 / 1024
    info = ClipInfo(path=path, part=0, size_mb=round(size_mb, 1))

    if result.returncode == 0:
        data = json.loads(result.stdout)
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                info.width = stream.get("width", 0)
                info.height = stream.get("height", 0)
                # Parse fps: "60000/1001" or "60/1"
                fps_str = stream.get("r_frame_rate", "0/1")
                num, den = fps_str.split("/")
                info.fps = round(int(num) / max(int(den), 1), 2)
        fmt = data.get("format", {})
        info.duration_s = round(float(fmt.get("duration", 0)), 2)

    return info


def scan_part(part: int, cfg: Config, probe: bool = False) -> List[ClipInfo]:
    """Return sorted list of ClipInfo for all AVI files in a Part folder."""
    part_dir = cfg.part_dir(part)
    if not part_dir.exists():
        return []

    clips = []
    for avi in sorted(part_dir.glob("*.avi")):
        info = get_clip_info(avi, cfg) if probe else ClipInfo(
            path=avi,
            part=part,
            size_mb=round(avi.stat().st_size / 1024 / 1024, 1)
        )
        info.part = part
        clips.append(info)
    return clips


def scan_all_parts(cfg: Config, probe: bool = False) -> Dict[int, List[ClipInfo]]:
    """Scan all parts 4-12, return dict of {part: [ClipInfo]}."""
    return {part: scan_part(part, cfg, probe=probe) for part in cfg.parts}


def print_inventory_report(cfg: Config):
    """Print a human-readable inventory table."""
    all_parts = scan_all_parts(cfg)
    total_clips = 0
    total_mb = 0

    print(f"\n{'Part':<8} {'AVI Count':<12} {'Total MB':<12} {'Sample clips'}")
    print("-" * 70)
    for part, clips in sorted(all_parts.items()):
        count = len(clips)
        mb = sum(c.size_mb for c in clips)
        samples = ", ".join(c.path.stem[:20] for c in clips[:3])
        print(f"Part{part:<4} {count:<12} {mb:<12.0f} {samples}...")
        total_clips += count
        total_mb += mb

    print("-" * 70)
    print(f"{'TOTAL':<8} {total_clips:<12} {total_mb:<12.0f}")


if __name__ == "__main__":
    cfg = Config()
    print_inventory_report(cfg)
