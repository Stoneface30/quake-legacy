"""ASK THE RUNNING 11.3 BINARY FOR EVERYTHING IT HAS.

One session, two questions: `cvarlist` with no filter and `cmdlist` with no
filter. Both print the complete registered set, so this is the only evidence
that settles what the TARGET runtime has -- as opposed to what the 12.7test49
source tree registers, which is a different program.

Run it once. The output is a file; every later question is answered from that
file rather than from another launch.

    python -m engine.pantheon.engine_census --demo <path.dm_73>
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

# Cvar_List_f prints nine fixed flag columns before the name (cvar.c:1066).
FLAG_COLUMNS = "SsURIALC?"
FLAG_MEANING = {
    "S": "SERVERINFO", "s": "SYSTEMINFO", "U": "USERINFO", "R": "ROM",
    "I": "INIT", "A": "ARCHIVE", "L": "LATCH", "C": "CHEAT",
    "?": "USER_CREATED",       # the engine never registered it
}

MARK_CVARS = "=== PANTHEON CVAR CENSUS"
MARK_CMDS = "=== PANTHEON CMD CENSUS"
MARK_END = "=== PANTHEON CENSUS END"


def census(demo: Path, *, staging: Path | None = None,
           timeout: float = 300.0) -> dict:
    """One offscreen session that asks for the whole inventory."""
    from creative_suite.engine import master_profile as MP
    from creative_suite.engine import wolfcam_capture as wc
    from engine.pantheon import offscreen as O
    from engine.pantheon import store as S

    staging = staging or (S.PROJECT_ROOT / "output" / "demo_v2" / "_wolfcam_staging")
    wc.STAGING = staging
    gamedir = staging / "wolfcam-ql"
    console = gamedir / "qconsole.log"
    if console.exists():
        console.unlink()

    safe = wc.stage_demo(demo, staging=staging)
    lines = [
        f"exec {MP._CFG_FILES[MP.REVIEW_PROFILE_NAME]}",
        f'echo "{MARK_CVARS}"', "cvarlist",
        f'echo "{MARK_CMDS}"', "cmdlist",
        f'echo "{MARK_END}"', "wait 40", "quit",
    ]
    wc.write_engine_file(gamedir / "capture.cfg",
                         "".join(f"{ln}\n" for ln in lines))
    wc.write_engine_file(gamedir / "cgamepostinit.cfg", "exec capture.cfg\n")

    argv = wc.wolfcam_cmd(safe, staging, profile=MP.REVIEW_PROFILE_NAME,
                          extra_sets={**O.OFFSCREEN_SETS, "logfile": 2})
    run = O.run_engine(argv, cwd=staging, timeout=timeout, env=O.ENGINE_ENV(),
                       purpose="runtime capability proof: full inventory",
                       log=console)
    text = console.read_text(encoding="utf-8", errors="replace") if console.exists() else ""
    out = parse(text)
    out.update({"ran": run.ok, "seconds": round(run.seconds, 1),
                "visible_windows": run.visible_windows,
                "stole_focus": run.stole_focus,
                "confined_cursor": run.confined_cursor,
                "captured_at": time.strftime("%Y-%m-%d %H:%M"),
                "console_bytes": len(text)})
    return out


_CVAR = re.compile(r"^([SsURIALC? ]{9})\s+(\S+)\s+\"(.*)\"\s*$")


def parse(text: str) -> dict:
    """Split the console log into the two inventories.

    A `?` in the last flag column means CVAR_USER_CREATED: the engine accepted
    the name and never registered it. Those are the silent no-ops this project
    keeps being bitten by, so they are kept and labelled rather than dropped.
    """
    cvars: dict[str, dict] = {}
    cmds: list[str] = []
    section = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if MARK_CVARS in line:
            section = "cvars"
            continue
        if MARK_CMDS in line:
            section = "cmds"
            continue
        if MARK_END in line:
            section = None
            continue
        if section == "cvars":
            m = _CVAR.match(line)
            if m:
                flags, name, value = m.group(1), m.group(2), m.group(3)
                set_flags = [FLAG_MEANING[c] for c in flags if c in FLAG_MEANING]
                cvars[name] = {"value": value, "flags": set_flags,
                               "registered": "?" not in flags}
        elif section == "cmds":
            for token in line.split():
                if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_+\-.]*", token):
                    cmds.append(token)
    return {"cvars": cvars, "commands": sorted(set(cmds)),
            "cvar_count": len(cvars), "command_count": len(set(cmds))}


def default_path() -> Path:
    from engine.pantheon import store as S
    return S.REPO_ROOT / "docs" / "reference" / "engine_census_11_3.json"


def load() -> dict | None:
    p = default_path()
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:                                           # pragma: no cover
    import argparse

    from engine.pantheon import performance_index as PI

    ap = argparse.ArgumentParser(description="one full runtime inventory")
    ap.add_argument("--demo", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()

    demo = a.demo
    if demo is None:
        con = PI._ro()
        (path,) = con.execute(
            "select path from demos where error is null order by demo_hash "
            "limit 1").fetchone()
        demo = Path(path)

    out = census(demo)
    dest = a.out or default_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("cvars", "commands")}, indent=1))
    print(f"-> {dest}")
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
