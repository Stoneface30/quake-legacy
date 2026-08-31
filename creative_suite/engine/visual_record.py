"""Rule VIS-1 post-render frame capture.

`render_part_v6.py` has called `safe_capture()` since the VIS-1 hook was added,
but the module was never written -- both import paths raised, the render printed
"[visual-record] import failed ... skipping", and no Part ever produced an
automatic visual record.

PRIVACY (hard rule, CLAUDE.md "Public Repo Rules"):
    Quake Live burns opponent nicknames into the gameplay HUD -- frag
    confirmations, the scoreboard, the obituary feed. `docs/visual-record/` is
    tracked in the PUBLIC repo, so body-content frames must never be captured
    here. Only the intro and title-card window is sampled, where the backdrop is
    desaturated, darkened and blurred (P1-Y) and no HUD is composited.

    The author's own handle (Tr4sH) appears in the title-card credit by design
    and is not a third-party identifier.
"""
from __future__ import annotations

import subprocess
from datetime import date
from pathlib import Path
from typing import Any

# Rule P1-N: [PANTHEON 5 s] + [title card 8 s] + [content]. Sampling stops
# short of the 13 s pre-content offset so no gameplay HUD is ever grabbed.
PRE_CONTENT_OFFSET_S = 13.0
SAFE_GRAB_TIMES = (2.0, 3.5, 6.5, 9.0, 11.5)


def _repo_root() -> Path:
    from creative_suite.config import REPO_ROOT

    return Path(REPO_ROOT)


def capture(rendered: Path, part: int, cfg: Any,
            out_dir: Path | None = None) -> list[Path]:
    """Grab the intro/title-card frames from a finished render.

    Returns the list of PNGs written. Raises on ffmpeg failure -- callers that
    must not fail the render should use `safe_capture`.
    """
    rendered = Path(rendered)
    if not rendered.exists():
        raise FileNotFoundError(rendered)

    if out_dir is None:
        out_dir = _repo_root() / "docs" / "visual-record" / date.today().isoformat()
    out_dir.mkdir(parents=True, exist_ok=True)

    ffmpeg = str(getattr(cfg, "ffmpeg_bin", "ffmpeg"))
    written: list[Path] = []
    for t in SAFE_GRAB_TIMES:
        if t >= PRE_CONTENT_OFFSET_S:
            # Defensive: never sample into body content.
            continue
        dst = out_dir / f"part{part:02d}_render_t{t:g}s.png"
        r = subprocess.run(
            [ffmpeg, "-y", "-v", "error", "-ss", f"{t}", "-i", str(rendered),
             "-vframes", "1", "-q:v", "3", str(dst)],
            capture_output=True, text=True, timeout=120,
        )
        if r.returncode == 0 and dst.exists():
            written.append(dst)

    if written:
        _write_readme(out_dir, part, rendered, written)
    return written


def _write_readme(out_dir: Path, part: int, rendered: Path,
                  written: list[Path]) -> None:
    """Append a short provenance note; never clobber an existing hand-written one."""
    readme = out_dir / f"AUTO_part{part:02d}.md"
    lines = [
        f"# Auto visual record — Part {part}",
        "",
        f"Source: `{rendered.name}`",
        "",
        "Frames sampled from the intro / title-card window only "
        f"(< {PRE_CONTENT_OFFSET_S:g} s, Rule P1-N). Body content is deliberately",
        "not captured: the gameplay HUD carries opponent nicknames and this",
        "directory is tracked in the public repo.",
        "",
    ]
    lines += [f"- `{p.name}`" for p in written]
    readme.write_text("\n".join(lines) + "\n", encoding="utf-8")


def safe_capture(rendered: Path, part: int, cfg: Any) -> list[Path]:
    """Best-effort `capture` — logs and returns [] instead of raising."""
    try:
        out = capture(rendered, part, cfg)
        if out:
            print(f"  [visual-record] captured {len(out)} frame(s) -> "
                  f"{out[0].parent}")
        else:
            print("  [visual-record] no frames captured")
        return out
    except Exception as exc:  # noqa: BLE001
        print(f"  [visual-record] capture failed ({exc!r}), skipping")
        return []
