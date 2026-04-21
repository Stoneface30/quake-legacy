"""Prepend the series intro clip to an assembled Part video."""
from pathlib import Path
from typing import Optional
import subprocess
from creative_suite.engine.config import Config


def prepend_intro(part_mp4: Path, cfg: Config, output_path: Optional[Path] = None) -> Path:
    """
    Prepend IntroPart2.mp4 to a Part video using concat demuxer.
    Both clips must be H.264 1920x1080 60fps for stream-copy concat to work.
    If formats differ, re-encode with -c:v libx264.

    Args:
        part_mp4:    Assembled Part video
        cfg:         Config (provides intro_source path)
        output_path: Where to write result (defaults to part_mp4 with _with_intro suffix)

    Returns: output path
    """
    if not cfg.intro_source.exists():
        print(f"[WARN] Intro source not found: {cfg.intro_source} — skipping intro")
        return part_mp4

    if output_path is None:
        output_path = part_mp4.with_stem(part_mp4.stem + "_with_intro")

    # Write concat list
    concat_list = part_mp4.parent / "_intro_concat.txt"
    concat_list.write_text(
        f"file '{cfg.intro_source.as_posix()}'\n"
        f"file '{part_mp4.as_posix()}'\n",
        encoding="utf-8"
    )

    cmd = [
        str(cfg.ffmpeg_bin), "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",           # stream copy if formats match
        "-movflags", "+faststart",
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    concat_list.unlink(missing_ok=True)

    if result.returncode != 0:
        # Fallback: re-encode if stream copy fails (format mismatch)
        print(f"  Stream copy failed, re-encoding intro concat...")
        cmd[cmd.index("-c") + 1] = "libx264"
        cmd.insert(cmd.index("libx264") + 1, "-crf")
        cmd.insert(cmd.index("-crf") + 1, str(cfg.crf))
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Intro concat failed:\n{result.stderr[-500:]}")

    size_mb = output_path.stat().st_size / 1024 / 1024
    print(f"  [DONE] With intro: {output_path} ({size_mb:.0f}MB)")
    return output_path
