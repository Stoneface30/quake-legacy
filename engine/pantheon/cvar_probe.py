"""Ask the RUNNING engine which cvars exist, and what they are set to.

WHY THIS EXISTS. Every appearance question answered from the C source so far
has been wrong, and the repository's own command audit ends with "runtime
cvarlist, cmdlist and captured on/off proofs remain pending". A documentary
that names a command on screen has to have watched that command exist in the
binary it films with -- 11.3, not the 12.7test49 tree the source lives in.

HOW. `cvarlist <wildcard>` is a real console command whose match runs through
Com_Filter, and its flag column marks a cvar the engine never registered with
`?` (CVAR_USER_CREATED). So a name that comes back carrying `?` is a name the
engine ACCEPTED and IGNORED -- exactly the silent no-op that has bitten this
project before. Running it from `cgamepostinit` means the cgame VM is loaded
and `cg_*` exists at all.

    python -m engine.pantheon.cvar_probe --demo <path.dm_73>
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path

MAIN = Path("G:/QUAKE_LEGACY")
sys.path.insert(0, str(MAIN))

# The families this documentary needs to name on screen. Wildcards, not exact
# names: the point is to discover what the binary has, not to confirm a guess.
FAMILIES = [
    "r_picmip", "r_fastsky", "r_subdivisions", "r_vertexlight", "r_lightmap",
    "r_mapoverbright*", "r_overbright*", "r_gamma", "r_intensity",
    "r_ext_compress*", "r_texturemode", "r_detailtextures", "r_dynamiclight",
    "cg_drawgun", "cg_gun*", "cg_fov*", "cg_zoomfov",
    "cg_forcemodel", "cg_enemy*", "cg_team*", "cg_own*", "cg_self*",
    "cg_rail*", "cg_old*", "cg_grenade*", "cg_rocket*", "cg_plasma*",
    "cg_lightning*", "cg_truelightning", "cg_impact*", "cg_muzzleflash",
    "cg_marks*", "cg_brass*", "cg_smoke*", "cg_shadows", "cg_gibs",
    "cg_crosshair*", "cg_draw2d", "cg_simpleitems", "cg_wh*",
    "cl_avi*", "com_maxfps", "r_swapinterval", "r_finish",
    # Found only by reading the rail selection code, not by guessing a prefix:
    # absolute red/blue rail colours live outside the cg_team*/cg_enemy*
    # namespaces, and the freecam has its own team-settings switch that decides
    # whether a spectating camera resolves "us" at all.
    "*RedBlueRail*", "cg_red*", "cg_blue*", "cg_freecam*", "cg_useCustom*",
    "*railcolor*", "*railitem*",
]

# Cvar_List_f prints NINE fixed flag columns before the name, in this order
# (cvar.c:1066-1110). The last two are the ones that decide how a documentary
# may use a command at all.
FLAG_COLUMNS = "SsURIALC?"
FLAG_MEANING = {
    "S": "SERVERINFO", "s": "SYSTEMINFO", "U": "USERINFO", "R": "ROM",
    "I": "INIT", "A": "ARCHIVE",
    "L": "LATCH",          # takes effect on vid_restart, NOT live
    "C": "CHEAT",          # refused unless cheats are on
    "?": "USER_CREATED",   # the engine accepted the name and registered
                           # nothing behind it -- a silent no-op
}
CVAR_LINE = re.compile(
    r"^(?P<flags>.{9})\s+(?P<name>[A-Za-z_]\w*)\s+\"(?P<value>.*)\"\s*$")


def probe(demo: Path, *, staging: Path | None = None, timeout: int = 240
          ) -> dict:
    from creative_suite.engine import wolfcam_capture as wc
    staging = staging or wc.STAGING
    gamedir = staging / "wolfcam-ql"
    dump = gamedir / "cvarprobe.txt"
    if dump.exists():
        dump.unlink()

    safe = wc.stage_demo(demo)
    lines = ["clear"]
    for fam in FAMILIES:
        lines += [f'echo "=== {fam}"', f"cvarlist {fam}"]
    lines += [f"condump {dump.name}", "quit"]
    wc.write_engine_file(gamedir / "capture.cfg",
                         "".join(f"{ln}\n" for ln in lines))
    wc.write_engine_file(gamedir / "cgamepostinit.cfg", "exec capture.cfg\n")

    cmd = wc.wolfcam_cmd(safe, staging)
    from creative_suite.engine import render_permit
    render_permit.require("runtime_capability_proof:cvar_probe")
    env = dict(os.environ, SDL_VIDEODRIVER="windib")
    t0 = time.time()
    proc = subprocess.Popen(cmd, cwd=staging, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    try:
        rc = proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.terminate()                          # CS-4
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill(); proc.wait()
        rc = "TIMEOUT"

    if not dump.exists():
        raise RuntimeError(f"cvar probe wrote no dump (rc={rc}, "
                           f"{time.time()-t0:.0f}s)")
    return parse(dump.read_text(encoding="latin-1", errors="replace"))


def parse(text: str) -> dict:
    """{family: [{name, value, user_created}]} from a condump."""
    out, fam = {}, None
    for raw in text.splitlines():
        ln = re.sub(r"\^\d", "", raw).rstrip()
        if ln.startswith("=== "):
            fam = ln[4:].strip()
            out.setdefault(fam, [])
            continue
        m = CVAR_LINE.match(ln)
        if m and fam is not None:
            flags = m.group("flags")
            named = [FLAG_MEANING[c] for i, c in enumerate(FLAG_COLUMNS)
                     if i < len(flags) and flags[i] == c]
            out[fam].append({
                "name": m.group("name"),
                "value": m.group("value"),
                "flags": named,
                # A latched cvar does nothing until vid_restart, so an A/B that
                # sets it between two shots of one capture proves nothing.
                "latched": "LATCH" in named,
                "cheat": "CHEAT" in named,
                # The engine took the name and registered nothing behind it.
                "user_created": "USER_CREATED" in named,
            })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--demo", type=Path,
                    default=Path(".tmp/synthetic/"
                                 "DIEGETIC_PRESENTER_PROOF_01.dm_73"))
    ap.add_argument("--out", type=Path,
                    default=Path(".tmp/engine/cvarlist_11_3.json"))
    args = ap.parse_args()
    found = probe(args.demo.resolve())
    import json
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(found, indent=1), encoding="utf-8")
    total = sum(len(v) for v in found.values())
    ghosts = [c["name"] for v in found.values() for c in v if c["user_created"]]
    print(f"{total} cvars over {len(found)} families -> {args.out}")
    print(f"USER_CREATED (accepted, unregistered): {sorted(set(ghosts)) or 'none'}")
    return 0


if __name__ == "__main__":                     # pragma: no cover - CLI
    raise SystemExit(main())
