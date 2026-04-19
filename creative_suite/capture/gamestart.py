"""Max-quality wolfcam capture cfg writer (spec §4.4).

Emits a `gamestart.cfg` that wolfcamql loads via `+exec cap.cfg`. The
cvar block maxes every quality dial the engine supports: 4K resolution,
16× anisotropic filter, negative LOD bias, fine curve subdivisions, HUD
off, deterministic fps.

The `seekclock ... ; video avi ... ; at ... quit` oneliner is the WQL
automation idiom: seek into the demo, start AVI capture at a named file,
quit at a timestamp. Phase 2's per-frag launcher calls us once per clip.
"""
from __future__ import annotations

from pathlib import Path


# Spec §4.4 verbatim order — any reorder breaks the cfg-diff smoke test.
# cg_drawGun is appended separately because its value flips per view
# (1 for FP spine, 0 for FL angles — both are captured per demo).
MAX_QUALITY_CVARS: list[str] = [
    "r_mode -1",
    "r_customwidth 3840",
    "r_customheight 2160",
    "r_fullscreen 0",
    "cg_fov 100",
    "r_picmip 0",
    "r_textureMode GL_LINEAR_MIPMAP_LINEAR",
    "r_ext_texture_filter_anisotropic 1",
    "r_ext_max_anisotropy 16",
    "r_lodbias -2",
    "r_subdivisions 1",
    "cg_drawFPS 0",
    "cg_draw2D 0",
    "cg_drawCrosshair 0",
    "com_maxfps 125",
    "com_hunkmegs 512",
    "set sv_pure 0",
]


def write_gamestart_cfg(
    out_path: Path,
    *,
    demo_name: str,
    seek_clock: str,
    quit_at: str,
    fp_view: bool = True,
) -> None:
    """Write a gamestart.cfg to ``out_path``.

    Parameters:
      demo_name:  AVI basename (no extension) — wolfcam will prefix
                  with its output dir.
      seek_clock: wolfcam `seekclock` arg, e.g. ``"8:52"``.
      quit_at:    wolfcam `at <time> quit` arg, e.g. ``"9:05"``.
      fp_view:    True → cg_drawGun 1 (first-person spine clip);
                  False → cg_drawGun 0 (free-look camera angle clip).

    File layout:
        r_mode -1
        r_customwidth 3840
        ...                   (all §4.4 cvars in spec order)
        com_hunkmegs 512
        set sv_pure 0
        cg_drawGun {1|0}
        seekclock 8:52; video avi name :frag_001; at 9:05 quit
    """
    if not demo_name or "\n" in demo_name:
        raise ValueError(f"invalid demo_name: {demo_name!r}")
    for label, value in (("seek_clock", seek_clock), ("quit_at", quit_at)):
        if not value or "\n" in value or ";" in value:
            raise ValueError(f"invalid {label}: {value!r}")

    lines = list(MAX_QUALITY_CVARS)
    lines.append("cg_drawGun 1" if fp_view else "cg_drawGun 0")
    lines.append(
        f"seekclock {seek_clock}; video avi name :{demo_name}; "
        f"at {quit_at} quit"
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
