"""Install the q3mme FX scripts so PANTHEON's cgame can run them.

WHAT THIS TURNS ON. cgame carries a complete effects scripting engine --
`cgame/cg_q3mme_scripts.c`, 7,584 lines -- and it is already linked into
pantheon_cgame.exe. It is inert for one reason: `cg_fxfile` is empty, so
CG_ReloadQ3mmeScripts parses nothing at CG_Init and every effect falls back to
the hardcoded C path.

WHY IT MATTERS MORE THAN IT SOUNDS. Q3 shaders animate on the engine clock --
`rgbGen wave`, `tcMod`, `animMap` are free-running, which is why
`engine/pantheon/hud.py` had to classify them FREE_RUNNING and could not offer
them as cueable effects. An FX script is different: it is evaluated when an
event fires, with the event's own inputs (origin, direction, velocity, team,
clientnum, surfacetype, powerups), so an explosion can be authored to do
something specific at a moment we choose. That is the difference between a
texture that happens to be shimmering and an effect that is CUED.

Scripts are looked up through the game filesystem, so `cg_fxfile` is a VFS
path such as `scripts/q3mme.fx`, not an OS path.

    python install_fx_scripts.py <staging-dir> [--game baseq3]
    pantheon_cgame.exe ... --set cg_fxfile scripts/q3mme.fx

Sources, both already in the repo:
  engine/engines/_canonical/package-files/wolfcam-ql/scripts/*.fx
      wolfcam's port of the q3mme scripts -- deliberately close to stock, so
      it is the safe baseline to diff our own authoring against.
  engine/engines/_forks/q3mme/trunk/files/scripts/*.fx
      q3mme's originals (base_weapons, base_player, base_extra, extra).
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parents[2]
SOURCES = (
    CODE_ROOT / "engine/engines/_canonical/package-files/wolfcam-ql/scripts",
    CODE_ROOT / "engine/engines/_forks/q3mme/trunk/files/scripts",
)


def install(staging: Path, game: str = "baseq3") -> list[str]:
    dest = staging / game / "scripts"
    dest.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for src in SOURCES:
        if not src.is_dir():
            continue
        for fx in sorted(src.glob("*.fx")):
            target = dest / fx.name
            # First source wins. wolfcam's port is listed first because it is
            # the one written against this cgame's inputs; q3mme's originals
            # fill in names wolfcam did not port.
            if target.exists():
                continue
            shutil.copy2(fx, target)
            written.append(f"{game}/scripts/{fx.name}")
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("staging", type=Path)
    ap.add_argument("--game", default="baseq3")
    a = ap.parse_args()
    if not a.staging.is_dir():
        print(f"no such staging dir: {a.staging}", file=sys.stderr)
        return 2
    written = install(a.staging, a.game)
    if not written:
        print("nothing to install -- the scripts are already there")
    for w in written:
        print("installed", w)
    print("\nnow render with:  --set cg_fxfile scripts/q3mme.fx")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
