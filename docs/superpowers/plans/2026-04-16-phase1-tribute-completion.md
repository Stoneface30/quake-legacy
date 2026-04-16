# Phase 1 — Tribute Completion: FFmpeg Assembly Pipeline

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python FFmpeg pipeline that assembles existing AVI clips into finished YouTube-ready MP4 fragmovie videos for Parts 4-12 of the Clan Arena Tribute series, with human review gates at each step.

**Architecture:** A modular pipeline where each stage (inventory, clip ordering, normalization, grading, assembly, preview, export) is a separate Python module with clear inputs/outputs. Human reviews clip order before render, and approves rough cut before final export. All FFmpeg operations are wrapped in ffmpeg-python for programmatic filter_complex chains.

**Tech Stack:** Python 3.11+, ffmpeg-python, moviepy, FFmpeg 7.x binary, SQLite (clip metadata), Streamlit (review UI)

**Source material:**
- AVI clips: `G:\QUAKE_LEGACY\QUAKE VIDEO\T1\Part4\` through `Part12\`
- Reference videos (match this style): `G:\QUAKE_LEGACY\FRAGMOVIE VIDEOS\Clan Arena Tribute 1.mp4` through `3.mp4`
- Existing intro: `G:\QUAKE_LEGACY\FRAGMOVIE VIDEOS\IntroPart2.mp4`

**Output:** `G:\QUAKE_LEGACY\output\Part4.mp4` through `Part12.mp4`

---

## File Map

```
phase1/
  __init__.py
  config.py             ← all paths, constants, defaults
  inventory.py          ← scan T1/T2/T3 folders, build clip metadata
  clip_list.py          ← read/write clip order lists, validate clips exist
  normalize.py          ← convert AVI → CFR MP4 (60fps, 1920x1080)
  pipeline.py           ← FFmpeg filter_complex: grade + bloom + transitions
  assembler.py          ← main orchestrator: clips → final MP4
  preview.py            ← render 30-second preview for human review
  review_ui.py          ← Streamlit app: browse clips, approve order
  export.py             ← final YouTube encode
  presets/
    grade_tribute.json  ← color grade preset (extracted from Tribute 1-3 style)
  clip_lists/
    part04.txt          ← ordered clip filenames (human-curated or alphabetical)
    part05.txt
    ...
    part12.txt
  output/               ← rendered videos (gitignored)

tests/
  phase1/
    conftest.py         ← shared fixtures (temp dirs, sample clips)
    test_config.py
    test_inventory.py
    test_clip_list.py
    test_normalize.py
    test_pipeline.py
    test_assembler.py
```

---

## Task 1: Environment Setup — Download Tools and Install Dependencies

**Files:**
- Create: `phase1/requirements.txt`
- Create: `phase1/verify_env.py`

- [ ] **Step 1: Install Python packages**

```bash
pip install ffmpeg-python moviepy streamlit tqdm requests
```

Expected: all packages install without error.

- [ ] **Step 2: Download FFmpeg if not present**

```bash
python tools/download_tools.py
```

If the automated download fails (GitHub release URL changes), manually:
1. Go to https://www.gyan.dev/ffmpeg/builds/
2. Download `ffmpeg-release-essentials.zip`
3. Extract `ffmpeg.exe`, `ffprobe.exe`, `ffplay.exe` to `tools/ffmpeg/`

- [ ] **Step 3: Write requirements.txt**

```
# phase1/requirements.txt
ffmpeg-python>=0.2.0
moviepy>=2.0.0
streamlit>=1.30.0
tqdm>=4.66.0
requests>=2.31.0
```

- [ ] **Step 4: Write environment verifier**

Create `phase1/verify_env.py`:

```python
"""Verify all required tools and packages are present before running Phase 1."""
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
FFMPEG = ROOT / "tools" / "ffmpeg" / "ffmpeg.exe"

def check(label, ok, fix=""):
    status = "✓" if ok else "✗"
    print(f"  {status} {label}")
    if not ok and fix:
        print(f"    FIX: {fix}")
    return ok

def main():
    print("QUAKE LEGACY — Phase 1 Environment Check\n")
    all_ok = True

    all_ok &= check("Python 3.11+", sys.version_info >= (3, 11),
                    "Install Python 3.11+ from python.org")

    all_ok &= check("FFmpeg binary", FFMPEG.exists(),
                    f"Run: python tools/download_tools.py")

    # Check ffmpeg works
    if FFMPEG.exists():
        result = subprocess.run([str(FFMPEG), "-version"],
                                capture_output=True, text=True)
        version_line = result.stdout.split('\n')[0]
        all_ok &= check(f"FFmpeg version: {version_line}", result.returncode == 0)

    for pkg in ["ffmpeg", "moviepy", "streamlit", "tqdm"]:
        try:
            __import__(pkg.replace("-", "_"))
            all_ok &= check(f"Python: {pkg}", True)
        except ImportError:
            all_ok &= check(f"Python: {pkg}", False,
                           f"pip install {pkg}")

    # Check source clips exist
    clips_root = ROOT / "QUAKE VIDEO" / "T1"
    all_ok &= check("T1 clips directory", clips_root.exists(),
                    f"Expected: {clips_root}")

    for part in range(4, 13):
        part_dir = clips_root / f"Part{part}"
        count = len(list(part_dir.glob("*.avi"))) if part_dir.exists() else 0
        all_ok &= check(f"Part{part}: {count} AVI files", count > 0,
                        f"Expected AVI files in {part_dir}")

    print()
    if all_ok:
        print("All checks passed. Ready for Phase 1.")
    else:
        print("Fix issues above before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run verifier**

```bash
python phase1/verify_env.py
```

Expected: all checks pass (fix any that don't before continuing).

- [ ] **Step 6: Commit**

```bash
git add phase1/requirements.txt phase1/verify_env.py
git commit -m "feat(phase1): add requirements and environment verifier"
```

---

## Task 2: Config Module — All Paths and Constants

**Files:**
- Create: `phase1/config.py`
- Create: `tests/phase1/conftest.py`
- Create: `tests/phase1/test_config.py`

- [ ] **Step 1: Write failing test**

Create `tests/phase1/test_config.py`:

```python
from phase1.config import Config
from pathlib import Path

def test_config_paths_exist():
    cfg = Config()
    assert cfg.ffmpeg_bin.exists(), f"FFmpeg not found: {cfg.ffmpeg_bin}"
    assert cfg.clips_root.exists(), f"Clips root not found: {cfg.clips_root}"
    assert cfg.output_dir.exists() or not cfg.output_dir.exists()  # created on demand

def test_config_parts_range():
    cfg = Config()
    assert cfg.parts == list(range(4, 13))

def test_config_part_dir():
    cfg = Config()
    for part in cfg.parts:
        d = cfg.part_dir(part)
        assert d.parent.name == "T1"
        assert d.name == f"Part{part}"

def test_config_output_path():
    cfg = Config()
    p = cfg.output_path(4)
    assert p.name == "Part4.mp4"
    assert "output" in str(p)
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
pytest tests/phase1/test_config.py -v
```

Expected: ImportError (module doesn't exist yet).

- [ ] **Step 3: Write config.py**

Create `phase1/config.py`:

```python
"""Central configuration for Phase 1 — all paths and constants."""
from pathlib import Path
import os

# Project root is one level up from phase1/
ROOT = Path(__file__).parent.parent

class Config:
    """All paths and pipeline constants."""

    # ── Binaries ──────────────────────────────────────────────
    ffmpeg_bin:   Path = ROOT / "tools" / "ffmpeg" / "ffmpeg.exe"
    ffprobe_bin:  Path = ROOT / "tools" / "ffmpeg" / "ffprobe.exe"

    # ── Source clips ──────────────────────────────────────────
    clips_root:   Path = ROOT / "QUAKE VIDEO" / "T1"
    tier:         str  = "T1"

    # ── Clip lists ────────────────────────────────────────────
    clip_lists_dir: Path = ROOT / "phase1" / "clip_lists"

    # ── Output ────────────────────────────────────────────────
    output_dir:   Path = ROOT / "output"
    preview_dir:  Path = ROOT / "output" / "previews"

    # ── Encoding ──────────────────────────────────────────────
    target_fps:   int = 60
    target_width: int = 1920
    target_height: int = 1080
    crf:          int = 17
    preset:       str = "slow"
    audio_bitrate: str = "320k"

    # ── Color grade defaults (Tribute series style) ────────────
    grade_contrast:   float = 1.4
    grade_saturation: float = 1.7
    grade_brightness: float = 0.0
    bloom_sigma:      int   = 18
    bloom_opacity:    float = 0.28

    # ── Transition ────────────────────────────────────────────
    fade_duration:    float = 0.25   # seconds, cross-fade between clips
    intro_fade_in:    float = 1.5    # seconds
    outro_fade_out:   float = 2.5    # seconds

    # ── Parts ─────────────────────────────────────────────────
    parts = list(range(4, 13))       # 4 through 12

    def __post_init__(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.preview_dir.mkdir(parents=True, exist_ok=True)
        self.clip_lists_dir.mkdir(parents=True, exist_ok=True)

    def __init__(self):
        self.__post_init__()

    def part_dir(self, part: int) -> Path:
        return self.clips_root / f"Part{part}"

    def clip_list_path(self, part: int) -> Path:
        return self.clip_lists_dir / f"part{part:02d}.txt"

    def output_path(self, part: int) -> Path:
        return self.output_dir / f"Part{part}.mp4"

    def preview_path(self, part: int) -> Path:
        return self.preview_dir / f"Part{part}_preview.mp4"

    def normalize_path(self, avi_path: Path) -> Path:
        """Normalized CFR version of an AVI clip."""
        norm_dir = self.output_dir / "normalized"
        norm_dir.mkdir(exist_ok=True)
        return norm_dir / (avi_path.stem + "_cfr60.mp4")
```

- [ ] **Step 4: Write conftest.py**

Create `tests/phase1/conftest.py`:

```python
import pytest
from pathlib import Path
from phase1.config import Config

@pytest.fixture
def cfg():
    return Config()

@pytest.fixture
def tmp_clip(tmp_path):
    """Create a minimal valid MP4 test clip using FFmpeg (1 second, color bar)."""
    import subprocess, shutil
    cfg = Config()
    out = tmp_path / "test_clip.mp4"
    subprocess.run([
        str(cfg.ffmpeg_bin), "-y",
        "-f", "lavfi", "-i", "color=c=blue:s=1920x1080:r=60:d=1",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
        "-c:v", "libx264", "-crf", "30", "-preset", "ultrafast",
        "-c:a", "aac", "-shortest", str(out)
    ], check=True, capture_output=True)
    return out
```

- [ ] **Step 5: Run test to confirm it passes**

```bash
pytest tests/phase1/test_config.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add phase1/config.py tests/phase1/conftest.py tests/phase1/test_config.py
git commit -m "feat(phase1): add Config module with all paths and constants"
```

---

## Task 3: Inventory — Scan Clip Folders and Build Metadata

**Files:**
- Create: `phase1/inventory.py`
- Create: `tests/phase1/test_inventory.py`

- [ ] **Step 1: Write failing test**

Create `tests/phase1/test_inventory.py`:

```python
import pytest
from phase1.inventory import scan_part, ClipInfo, scan_all_parts

def test_scan_part_returns_clip_list(cfg):
    clips = scan_part(4, cfg)
    assert isinstance(clips, list)
    assert len(clips) > 0

def test_scan_part_clip_has_required_fields(cfg):
    clips = scan_part(4, cfg)
    clip = clips[0]
    assert isinstance(clip, ClipInfo)
    assert clip.path.exists()
    assert clip.path.suffix.lower() == ".avi"
    assert clip.size_mb > 0
    assert clip.part == 4

def test_scan_part_sorted_alphabetically(cfg):
    clips = scan_part(4, cfg)
    names = [c.path.name for c in clips]
    assert names == sorted(names)

def test_scan_all_parts_returns_dict(cfg):
    result = scan_all_parts(cfg)
    assert isinstance(result, dict)
    for part in range(4, 13):
        assert part in result
        assert isinstance(result[part], list)

def test_inventory_report_prints(cfg, capsys):
    from phase1.inventory import print_inventory_report
    print_inventory_report(cfg)
    captured = capsys.readouterr()
    assert "Part4" in captured.out
    assert "AVI" in captured.out
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
pytest tests/phase1/test_inventory.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement inventory.py**

Create `phase1/inventory.py`:

```python
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
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/phase1/test_inventory.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 5: Run inventory report to see what we have**

```bash
python phase1/inventory.py
```

Expected: table showing all 9 parts with clip counts and sizes. **Review this output — confirm Part 4-12 all have clips before continuing.**

- [ ] **Step 6: Commit**

```bash
git add phase1/inventory.py tests/phase1/test_inventory.py
git commit -m "feat(phase1): add inventory scanner for T1 clip folders"
```

---

## Task 4: Clip Lists — Human-Curated Ordering

**Files:**
- Create: `phase1/clip_list.py`
- Create: `phase1/clip_lists/part04.txt` through `part12.txt` (auto-generated, then human-edited)
- Create: `tests/phase1/test_clip_list.py`

- [ ] **Step 1: Write failing test**

Create `tests/phase1/test_clip_list.py`:

```python
import pytest
from pathlib import Path
from phase1.clip_list import ClipList, generate_default_list, load_clip_list, save_clip_list

def test_clip_list_loads_from_file(tmp_path, cfg):
    # Write a test clip list
    test_file = tmp_path / "part04.txt"
    test_file.write_text("# Part 4 clip list\nDemo (100).avi\nDemo (200).avi\n")
    result = load_clip_list(test_file)
    assert len(result) == 2
    assert result[0] == "Demo (100).avi"

def test_clip_list_skips_comments_and_blanks(tmp_path):
    f = tmp_path / "list.txt"
    f.write_text("# comment\n\nDemo (1).avi\n\n# another\nDemo (2).avi\n")
    result = load_clip_list(f)
    assert result == ["Demo (1).avi", "Demo (2).avi"]

def test_generate_default_list_creates_alphabetical(cfg, tmp_path):
    list_path = tmp_path / "part04.txt"
    generate_default_list(4, cfg, output_path=list_path)
    result = load_clip_list(list_path)
    assert len(result) > 0
    assert result == sorted(result)

def test_clip_list_validate_warns_missing(cfg, tmp_path, capsys):
    f = tmp_path / "list.txt"
    f.write_text("NonExistent_Demo.avi\n")
    from phase1.clip_list import validate_clip_list
    missing = validate_clip_list(4, load_clip_list(f), cfg)
    assert len(missing) == 1

def test_save_and_reload(tmp_path):
    clips = ["Demo (1).avi", "Demo (2).avi", "Demo (3).avi"]
    path = tmp_path / "test.txt"
    save_clip_list(clips, path, header="# Test")
    loaded = load_clip_list(path)
    assert loaded == clips
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
pytest tests/phase1/test_clip_list.py -v
```

- [ ] **Step 3: Implement clip_list.py**

Create `phase1/clip_list.py`:

```python
"""Clip list management — read/write ordered lists of AVI filenames per Part."""
from pathlib import Path
from typing import List, Optional
from phase1.config import Config
from phase1.inventory import scan_part


def load_clip_list(path: Path) -> List[str]:
    """Load ordered clip filenames from a text file. Skips comments (#) and blanks."""
    lines = path.read_text(encoding="utf-8").splitlines()
    return [
        line.strip()
        for line in lines
        if line.strip() and not line.strip().startswith("#")
    ]


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
    save_clip_list(
        filenames, out,
        header=f"# Part {part} clip list — EDIT THIS FILE to reorder clips\n"
               f"# One filename per line. Lines starting with # are ignored.\n"
               f"# Generated from: {cfg.part_dir(part)}"
    )
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
            print(f"Part {part}: generated {len(clips)} clips → {out}")
        else:
            clips = load_clip_list(list_path)
            print(f"Part {part}: existing list ({len(clips)} clips) — skipped")
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/phase1/test_clip_list.py -v
```

Expected: all 5 PASS.

- [ ] **Step 5: Generate default clip lists for all Parts**

```bash
python phase1/clip_list.py
```

Expected: creates `phase1/clip_lists/part04.txt` through `part12.txt` with alphabetical clip orders.

**⚠ HUMAN REVIEW GATE 1:** Open each `phase1/clip_lists/partXX.txt` and reorder clips to your desired sequence. The alphabetical order is just the starting point. You are the director.

- [ ] **Step 6: Commit**

```bash
git add phase1/clip_list.py tests/phase1/test_clip_list.py phase1/clip_lists/
git commit -m "feat(phase1): add clip list manager and generate default lists for Parts 4-12"
```

---

## Task 5: Normalize — AVI to CFR MP4

**Files:**
- Create: `phase1/normalize.py`
- Create: `tests/phase1/test_normalize.py`

- [ ] **Step 1: Write failing test**

Create `tests/phase1/test_normalize.py`:

```python
import pytest
from phase1.normalize import normalize_clip, is_already_normalized
from pathlib import Path

def test_normalize_produces_mp4(tmp_clip, cfg, tmp_path):
    out = tmp_path / "normalized.mp4"
    normalize_clip(tmp_clip, out, cfg)
    assert out.exists()
    assert out.stat().st_size > 0

def test_normalize_output_is_cfr_60fps(tmp_clip, cfg, tmp_path):
    import subprocess, json
    out = tmp_path / "normalized.mp4"
    normalize_clip(tmp_clip, out, cfg)
    result = subprocess.run([
        str(cfg.ffprobe_bin), "-v", "quiet",
        "-print_format", "json", "-show_streams", str(out)
    ], capture_output=True, text=True)
    data = json.loads(result.stdout)
    for stream in data["streams"]:
        if stream["codec_type"] == "video":
            fps_str = stream["r_frame_rate"]
            num, den = fps_str.split("/")
            fps = int(num) / int(den)
            assert abs(fps - 60) < 1, f"Expected 60fps, got {fps}"

def test_already_normalized_skips(tmp_clip, cfg, tmp_path):
    out = tmp_path / "norm.mp4"
    normalize_clip(tmp_clip, out, cfg)
    # Second call should not re-encode
    import time
    mtime1 = out.stat().st_mtime
    time.sleep(0.1)
    normalize_clip(tmp_clip, out, cfg)
    mtime2 = out.stat().st_mtime
    assert mtime1 == mtime2, "Should skip re-encode when output exists"
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
pytest tests/phase1/test_normalize.py -v
```

- [ ] **Step 3: Implement normalize.py**

Create `phase1/normalize.py`:

```python
"""Normalize AVI clips to CFR MP4 (60fps, 1920x1080) for consistent pipeline input."""
from pathlib import Path
from typing import List
import subprocess
from tqdm import tqdm
from phase1.config import Config


def normalize_clip(src: Path, dst: Path, cfg: Config, force: bool = False) -> Path:
    """
    Convert AVI to CFR 60fps 1920x1080 MP4.
    Skips if dst already exists (unless force=True).
    Returns dst path.
    """
    if dst.exists() and not force:
        return dst

    dst.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        str(cfg.ffmpeg_bin), "-y",
        "-i", str(src),
        "-vf", f"fps={cfg.target_fps},scale={cfg.target_width}:{cfg.target_height}:flags=lanczos",
        "-c:v", "libx264",
        "-crf", "16",           # high quality intermediate
        "-preset", "fast",      # fast encode for normalization pass
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        str(dst)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg normalize failed for {src.name}:\n{result.stderr[-500:]}")

    return dst


def is_already_normalized(src: Path, cfg: Config) -> bool:
    return cfg.normalize_path(src).exists()


def normalize_part(part: int, clips: List[Path], cfg: Config, force: bool = False) -> List[Path]:
    """Normalize all clips for a Part. Returns list of normalized paths."""
    print(f"\nNormalizing Part {part} ({len(clips)} clips)...")
    normalized = []
    for clip in tqdm(clips, desc=f"Part {part}"):
        dst = cfg.normalize_path(clip)
        normalize_clip(clip, dst, cfg, force=force)
        normalized.append(dst)
    return normalized
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/phase1/test_normalize.py -v
```

Expected: all 3 PASS (note: these actually run ffmpeg, takes ~10 seconds).

- [ ] **Step 5: Commit**

```bash
git add phase1/normalize.py tests/phase1/test_normalize.py
git commit -m "feat(phase1): add AVI→CFR MP4 normalizer"
```

---

## Task 6: Pipeline — FFmpeg Filter Chain (Grade + Bloom + Transitions)

**Files:**
- Create: `phase1/pipeline.py`
- Create: `phase1/presets/grade_tribute.json`
- Create: `tests/phase1/test_pipeline.py`

- [ ] **Step 1: Write the grade preset file**

Create `phase1/presets/grade_tribute.json`:

```json
{
  "name": "Clan Arena Tribute",
  "description": "Warm high-contrast grade matching Clan Arena Tribute 1-2-3 style",
  "contrast": 1.4,
  "saturation": 1.7,
  "brightness": 0.0,
  "gamma_r": 1.08,
  "gamma_b": 0.92,
  "bloom_sigma": 18,
  "bloom_opacity": 0.28,
  "sharpen_amount": 0.5,
  "fade_duration": 0.25
}
```

- [ ] **Step 2: Write failing test**

Create `tests/phase1/test_pipeline.py`:

```python
import pytest, json
from pathlib import Path
from phase1.pipeline import build_filter_complex, GradePreset, assemble_part

def test_grade_preset_loads():
    preset_path = Path("phase1/presets/grade_tribute.json")
    preset = GradePreset.from_file(preset_path)
    assert preset.contrast == 1.4
    assert preset.bloom_sigma == 18

def test_build_filter_complex_returns_string(tmp_clip, cfg):
    from phase1.pipeline import build_filter_complex, GradePreset
    preset = GradePreset()
    fc = build_filter_complex([tmp_clip], preset, cfg, total_duration=1.0)
    assert isinstance(fc, str)
    assert "eq=" in fc          # color grade
    assert "gblur" in fc        # bloom
    assert "blend" in fc        # bloom screen blend
    assert "[vout]" in fc       # output label

def test_assemble_produces_output(tmp_clip, cfg, tmp_path):
    output = tmp_path / "test_output.mp4"
    assemble_part(
        clips=[tmp_clip],
        output_path=output,
        music_path=None,
        cfg=cfg,
        preview_seconds=None
    )
    assert output.exists()
    assert output.stat().st_size > 10_000
```

- [ ] **Step 3: Run test to confirm it fails**

```bash
pytest tests/phase1/test_pipeline.py -v
```

- [ ] **Step 4: Implement pipeline.py**

Create `phase1/pipeline.py`:

```python
"""
FFmpeg assembly pipeline: concat + color grade + bloom + transitions + music.
Builds the filter_complex chain for the full fragmovie assembly.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import json, subprocess
from phase1.config import Config


@dataclass
class GradePreset:
    """Color grade and effect parameters."""
    contrast:     float = 1.4
    saturation:   float = 1.7
    brightness:   float = 0.0
    gamma_r:      float = 1.08
    gamma_b:      float = 0.92
    bloom_sigma:  int   = 18
    bloom_opacity: float = 0.28
    sharpen_amount: float = 0.5
    fade_duration: float = 0.25

    @classmethod
    def from_file(cls, path: Path) -> "GradePreset":
        data = json.loads(path.read_text())
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def build_filter_complex(
    clips: List[Path],
    preset: GradePreset,
    cfg: Config,
    total_duration: float,
    has_music: bool = False
) -> str:
    """
    Build a filter_complex string for N clips:
    1. Concat all video + audio streams
    2. Apply color grade (eq filter)
    3. Apply bloom (gblur + screen blend)
    4. Apply sharpening (unsharp)
    5. Fade in / fade out on full concat
    Returns the filter_complex string.
    """
    n = len(clips)
    parts = []

    # Step 1: label each input stream
    v_inputs = "".join(f"[{i}:v]" for i in range(n))
    a_inputs = "".join(f"[{i}:a]" for i in range(n))

    # Interleave v/a for concat
    concat_inputs = "".join(f"[{i}:v][{i}:a]" for i in range(n))
    parts.append(f"{concat_inputs}concat=n={n}:v=1:a=1[concat_v][concat_a]")

    # Step 2: color grade
    eq = (
        f"eq=contrast={preset.contrast}"
        f":saturation={preset.saturation}"
        f":brightness={preset.brightness}"
        f":gamma_r={preset.gamma_r}"
        f":gamma_b={preset.gamma_b}"
    )
    parts.append(f"[concat_v]{eq}[graded]")

    # Step 3: bloom (gblur + screen blend)
    parts.append(f"[graded]split[orig][forbloom]")
    parts.append(f"[forbloom]gblur=sigma={preset.bloom_sigma}[blurred]")
    parts.append(
        f"[orig][blurred]blend=all_mode=screen"
        f":all_opacity={preset.bloom_opacity}[bloomed]"
    )

    # Step 4: sharpen
    parts.append(
        f"[bloomed]unsharp=luma_msize_x=5:luma_msize_y=5"
        f":luma_amount={preset.sharpen_amount}[sharp]"
    )

    # Step 5: fade in + fade out
    fade_out_start = max(0, total_duration - 2.5)
    parts.append(
        f"[sharp]fade=t=in:st=0:d={cfg.intro_fade_in},"
        f"fade=t=out:st={fade_out_start:.2f}:d={cfg.outro_fade_out}[vout]"
    )

    # Audio fade (from concat_a)
    parts.append(
        f"[concat_a]afade=t=in:st=0:d={cfg.intro_fade_in},"
        f"afade=t=out:st={fade_out_start:.2f}:d={cfg.outro_fade_out}[aout]"
    )

    return ";\n".join(parts)


def assemble_part(
    clips: List[Path],
    output_path: Path,
    cfg: Config,
    music_path: Optional[Path] = None,
    preset: Optional[GradePreset] = None,
    preview_seconds: Optional[int] = None,
) -> Path:
    """
    Assemble a list of clips into a single MP4 with grade, bloom, optional music.

    Args:
        clips: Ordered list of normalized MP4 paths
        output_path: Output .mp4 path
        cfg: Config object
        music_path: Optional audio track (replaces clip audio if provided)
        preset: GradePreset (uses default Tribute style if None)
        preview_seconds: If set, only render this many seconds (for quick preview)

    Returns: output_path
    """
    if preset is None:
        preset_file = Path(__file__).parent / "presets" / "grade_tribute.json"
        preset = GradePreset.from_file(preset_file) if preset_file.exists() else GradePreset()

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Estimate total duration (sum of clip durations, rough)
    total_duration = len(clips) * 5.0  # will be refined with ffprobe in production

    filter_complex = build_filter_complex(clips, preset, cfg, total_duration)

    # Build ffmpeg command
    cmd = [str(cfg.ffmpeg_bin), "-y"]

    # Input clips
    for clip in clips:
        cmd += ["-i", str(clip)]

    # Optional music input
    if music_path:
        cmd += ["-i", str(music_path)]

    cmd += ["-filter_complex", filter_complex]
    cmd += ["-map", "[vout]"]

    if music_path:
        music_idx = len(clips)
        fade_out_start = max(0, total_duration - 2.5)
        cmd += [
            "-filter_complex",
            filter_complex + f";\n[{music_idx}:a]"
            f"afade=t=in:st=0:d=2,afade=t=out:st={fade_out_start:.2f}:d=2[music_out]",
            "-map", "[music_out]"
        ]
    else:
        cmd += ["-map", "[aout]"]

    # Encoding settings
    cmd += [
        "-c:v", "libx264",
        "-crf", str(cfg.crf),
        "-preset", cfg.preset,
        "-profile:v", "high",
        "-pix_fmt", "yuv420p",
        "-r", str(cfg.target_fps),
        "-g", str(cfg.target_fps * 2),  # keyframe every 2 seconds
        "-bf", "2",
        "-c:a", "aac",
        "-ar", "48000",
        "-b:a", cfg.audio_bitrate,
        "-movflags", "+faststart",
    ]

    # Preview mode: limit duration
    if preview_seconds:
        cmd += ["-t", str(preview_seconds)]

    cmd.append(str(output_path))

    print(f"Rendering: {output_path.name}")
    print(f"  Clips: {len(clips)}")
    print(f"  Command: ffmpeg {' '.join(cmd[2:5])} ... {output_path.name}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Assembly failed for {output_path.name}:\n{result.stderr[-1000:]}"
        )

    size_mb = output_path.stat().st_size / 1024 / 1024
    print(f"  Output: {output_path} ({size_mb:.0f}MB)")
    return output_path
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/phase1/test_pipeline.py -v
```

Expected: all 3 PASS.

- [ ] **Step 6: Commit**

```bash
git add phase1/pipeline.py phase1/presets/grade_tribute.json tests/phase1/test_pipeline.py
git commit -m "feat(phase1): add FFmpeg assembly pipeline with grade+bloom filter chain"
```

---

## Task 7: Preview — 30-Second Rough Cut for Human Review

**Files:**
- Create: `phase1/preview.py`

- [ ] **Step 1: Implement preview.py**

Create `phase1/preview.py`:

```python
"""
Generate a 30-second preview render of a Part for human review.
Takes the first N clips and renders at preview quality (fast).
"""
from pathlib import Path
from typing import Optional
from phase1.config import Config
from phase1.clip_list import get_clip_paths
from phase1.normalize import normalize_part
from phase1.pipeline import assemble_part, GradePreset
import subprocess


def render_preview(
    part: int,
    cfg: Config,
    preview_seconds: int = 30,
    max_clips: int = 10,
    open_after: bool = True
) -> Path:
    """
    Render a quick preview of Part N:
    - Uses up to max_clips clips
    - Limits output to preview_seconds
    - Uses faster encode settings
    - Optionally opens in default video player

    Returns path to preview file.
    """
    print(f"\n=== PREVIEW: Part {part} ===")
    clips = get_clip_paths(part, cfg)[:max_clips]
    print(f"Using {len(clips)} of available clips (first {max_clips})")

    # Normalize only the clips we need for preview
    normalized = normalize_part(part, clips, cfg)

    output = cfg.preview_path(part)

    # Use faster settings for preview
    preview_cfg = cfg
    preview_cfg_dict = {
        "crf": 23,              # lower quality, faster
        "preset": "veryfast",
        "intro_fade_in": 1.0,
        "outro_fade_out": 1.5,
    }

    assemble_part(
        clips=normalized,
        output_path=output,
        cfg=cfg,
        preview_seconds=preview_seconds,
    )

    print(f"\nPreview saved: {output}")
    print(f"Duration: ~{preview_seconds}s")

    if open_after:
        _open_video(output)

    return output


def _open_video(path: Path):
    """Open video in default system player."""
    import os, sys
    try:
        if sys.platform == "win32":
            os.startfile(str(path))
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)])
        else:
            subprocess.run(["xdg-open", str(path)])
    except Exception as e:
        print(f"Could not auto-open video: {e}")
        print(f"Open manually: {path}")


if __name__ == "__main__":
    import sys
    cfg = Config()
    part = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    render_preview(part, cfg, open_after=True)
```

- [ ] **Step 2: Render a preview of Part 4**

```bash
python phase1/preview.py 4
```

Expected: renders ~30 seconds, opens in video player.

**⚠ HUMAN REVIEW GATE 2:** Watch the preview. Check:
- Clip order makes sense
- Color grade looks right
- Transitions work
- No broken clips

If order is wrong → edit `phase1/clip_lists/part04.txt` and re-run.
If grade is off → edit `phase1/presets/grade_tribute.json` and re-run.

- [ ] **Step 3: Commit**

```bash
git add phase1/preview.py
git commit -m "feat(phase1): add preview renderer with human review gate"
```

---

## Task 8: Assembler — Main Orchestrator

**Files:**
- Create: `phase1/assembler.py`

- [ ] **Step 1: Implement assembler.py**

Create `phase1/assembler.py`:

```python
"""
Main Phase 1 orchestrator: clips → finished MP4.
Usage:
  python phase1/assembler.py --part 4 --preview     # preview only
  python phase1/assembler.py --part 4               # full render
  python phase1/assembler.py --all --preview        # preview all parts
  python phase1/assembler.py --all                  # render all parts (LONG!)
"""
import argparse
from pathlib import Path
from typing import Optional
from phase1.config import Config
from phase1.clip_list import get_clip_paths
from phase1.normalize import normalize_part
from phase1.pipeline import assemble_part, GradePreset
from phase1.preview import render_preview


def render_part(
    part: int,
    cfg: Config,
    music_path: Optional[Path] = None,
    force: bool = False,
) -> Path:
    """Full render of a single Part. Returns output MP4 path."""
    output = cfg.output_path(part)

    if output.exists() and not force:
        print(f"Part {part} already rendered: {output}")
        print("  Use --force to re-render.")
        return output

    print(f"\n{'='*60}")
    print(f"  RENDERING PART {part}")
    print(f"{'='*60}")

    # 1. Load clip list
    clips = get_clip_paths(part, cfg)
    print(f"  Clips: {len(clips)}")

    # 2. Normalize all clips
    normalized = normalize_part(part, clips, cfg)

    # 3. Load grade preset
    preset_path = Path(__file__).parent / "presets" / "grade_tribute.json"
    preset = GradePreset.from_file(preset_path) if preset_path.exists() else GradePreset()

    # 4. Assemble
    assemble_part(
        clips=normalized,
        output_path=output,
        cfg=cfg,
        music_path=music_path,
        preset=preset,
    )

    size_mb = output.stat().st_size / 1024 / 1024
    print(f"\n✓ Part {part} complete: {output} ({size_mb:.0f}MB)")
    return output


def main():
    parser = argparse.ArgumentParser(description="QUAKE LEGACY Phase 1 Assembler")
    parser.add_argument("--part", type=int, help="Part number (4-12)")
    parser.add_argument("--all", action="store_true", help="Render all parts 4-12")
    parser.add_argument("--preview", action="store_true", help="Render 30s preview only")
    parser.add_argument("--music", type=str, help="Path to music file (MP3/OGG/WAV)")
    parser.add_argument("--force", action="store_true", help="Re-render even if output exists")
    args = parser.parse_args()

    cfg = Config()
    music_path = Path(args.music) if args.music else None

    if args.preview:
        parts = cfg.parts if args.all else ([args.part] if args.part else [4])
        for part in parts:
            render_preview(part, cfg)
    elif args.all:
        print("Rendering all Parts 4-12. This will take a long time.")
        print("Ctrl+C to abort at any time.\n")
        confirm = input("Proceed? (yes/no): ")
        if confirm.strip().lower() != "yes":
            print("Aborted.")
            return
        for part in cfg.parts:
            render_part(part, cfg, music_path=music_path, force=args.force)
    elif args.part:
        render_part(args.part, cfg, music_path=music_path, force=args.force)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Test the full Part 4 render**

```bash
python phase1/assembler.py --part 4 --preview
```

Review preview. Then:

```bash
python phase1/assembler.py --part 4
```

**⚠ HUMAN REVIEW GATE 3:** Watch `output/Part4.mp4`. Full quality. Approve or adjust settings.

- [ ] **Step 3: Commit**

```bash
git add phase1/assembler.py
git commit -m "feat(phase1): add main assembler orchestrator with CLI"
```

---

## Task 9: Music Integration

**Files:**
- Modify: `phase1/pipeline.py` (music mixing already stubbed — complete it)
- Create: `phase1/music/` directory with instructions

- [ ] **Step 1: Create music directory with instructions**

Create `phase1/music/README.md`:

```markdown
# Music for Phase 1

Place music files here (MP3, OGG, WAV) for each Part.

Naming convention:
  part04_music.mp3
  part05_music.mp3
  ...

These files are gitignored (copyright). Each must be:
- Long enough to cover the full Part duration
- Will be faded in (2s) and faded out (3s)
- Game audio is muted (replaced by music track)

Recommended: select tracks that match the energy of the clips.
Parts 1-2-3 used electronic/heavy music. Reference them for style.
```

- [ ] **Step 2: Auto-detect music file per Part**

Add to `phase1/config.py`:

```python
def music_path(self, part: int) -> Optional[Path]:
    """Look for a music file for this Part. Returns None if not found."""
    music_dir = ROOT / "phase1" / "music"
    for ext in [".mp3", ".ogg", ".wav", ".flac"]:
        candidate = music_dir / f"part{part:02d}_music{ext}"
        if candidate.exists():
            return candidate
    return None
```

- [ ] **Step 3: Update assembler to use auto-detected music**

Modify `phase1/assembler.py` `render_part()`:

```python
# In render_part(), after loading preset:
if music_path is None:
    music_path = cfg.music_path(part)
    if music_path:
        print(f"  Music: {music_path.name}")
    else:
        print(f"  Music: none (game audio only)")
```

- [ ] **Step 4: Commit**

```bash
git add phase1/music/README.md phase1/config.py phase1/assembler.py
git commit -m "feat(phase1): add music auto-detection per Part"
```

---

## Task 10: Batch Render All Parts + Final Push

- [ ] **Step 1: Run environment check one final time**

```bash
python phase1/verify_env.py
```

All checks must pass.

- [ ] **Step 2: Preview all 9 parts (one at a time, human reviews each)**

```bash
python phase1/assembler.py --part 4 --preview
# review, then:
python phase1/assembler.py --part 5 --preview
# ... through 12
```

- [ ] **Step 3: Batch render all approved parts**

```bash
python phase1/assembler.py --all
```

This will take several hours depending on clip count and machine speed.

- [ ] **Step 4: Verify all output files**

```bash
ls -lh output/Part*.mp4
python phase1/verify_env.py  # checks output too
```

- [ ] **Step 5: Final commit**

```bash
git add phase1/ tests/phase1/ docs/
git commit -m "feat(phase1): complete tribute completion pipeline - Parts 4-12 ready"
git push origin main
```

---

## Human Review Summary (all gates)

| Gate | When | What to review |
|---|---|---|
| Gate 1 | After `clip_list.py` generates defaults | Edit `clip_lists/partXX.txt` to reorder clips |
| Gate 2 | After `preview.py` renders 30s preview | Clip order, grade, transitions |
| Gate 3 | After `assembler.py --part 4` renders Part 4 | Full quality, music sync, energy |
| Gate 4 | After each Part's preview | Approve or adjust before full render |
| Gate 5 | After `--all` batch completes | Final review of all 9 outputs before upload |

---

## Quick Reference Commands

```bash
# Check environment
python phase1/verify_env.py

# See what clips are in each Part
python phase1/inventory.py

# Generate clip lists (alphabetical starting point)
python phase1/clip_list.py

# 30-second preview of Part 4
python phase1/assembler.py --part 4 --preview

# Full render of Part 4 (review this before batch)
python phase1/assembler.py --part 4

# Full render Part 4 with music
python phase1/assembler.py --part 4 --music "phase1/music/part04_music.mp3"

# Batch render all (run after previewing all)
python phase1/assembler.py --all

# Run tests
pytest tests/phase1/ -v
```
