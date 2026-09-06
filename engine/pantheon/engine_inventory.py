"""EVERY COMMAND AND CVAR THIS PROJECT COULD TOUCH, GRADED BY REAL EVIDENCE.

Four inventories, kept apart because they are four different programs:

    RUNTIME_11_3   what the binary we film with actually registers, asked of
                   it directly with `cvarlist` and `cmdlist` in one session
    SOURCE_12_7    what the wolfcamql source tree registers -- a LATER program
                   than the one on disk, so its presence proves nothing here
    BINARY_11_3    strings found inside the 11.3 executable
    Q3MME          a different engine entirely, with its own vocabulary

The target rule is absolute: 11.3 runtime outranks 12.7 source. Something the
source registers and the runtime does not is SOURCE_ONLY, and production may
not use it.

    RUNTIME_REGISTERED        the running binary registered it
    RUNTIME_ACCEPTED_UNSET    the runtime holds it but never registered it --
                              a silent no-op, the failure mode of this project
    TARGET_BINARY_RECOGNIZED  the name is in the 11.3 executable's strings
    SOURCE_REGISTERED         the 12.7 source registers it
    DOCUMENTED_ONLY           a document says so and nothing else does
    UNSUPPORTED_TARGET        another engine has it and 11.3 does not
    UNKNOWN                   asked and not answered

UNKNOWN is a classification. UNCLASSIFIED is not, and the doctor fails on one.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from engine.pantheon import store as S


class Grade(str, Enum):
    RUNTIME_REGISTERED = "RUNTIME_REGISTERED"
    RUNTIME_ACCEPTED_UNSET = "RUNTIME_ACCEPTED_UNSET"
    TARGET_BINARY_RECOGNIZED = "TARGET_BINARY_RECOGNIZED"
    SOURCE_REGISTERED = "SOURCE_REGISTERED"
    DOCUMENTED_ONLY = "DOCUMENTED_ONLY"
    UNSUPPORTED_TARGET = "UNSUPPORTED_TARGET"
    UNKNOWN = "UNKNOWN"


USABLE_IN_PRODUCTION = (Grade.RUNTIME_REGISTERED,)


class Origin(str, Enum):
    RUNTIME_11_3 = "RUNTIME_11_3"
    SOURCE_12_7 = "SOURCE_12_7"
    BINARY_11_3 = "BINARY_11_3"
    Q3MME = "Q3MME"


@dataclass
class Item:
    name: str
    kind: str                       # "cvar" | "command"
    grade: Grade
    origins: tuple[str, ...]
    value: str | None = None        # what the runtime holds, when it holds it
    flags: tuple[str, ...] = ()
    capability: str | None = None   # the semantic name, when one exists
    note: str = ""

    def as_dict(self) -> dict:
        return {"name": self.name, "kind": self.kind, "grade": self.grade.value,
                "origins": list(self.origins), "value": self.value,
                "flags": list(self.flags), "capability": self.capability,
                "note": self.note}


# -- reading each source ----------------------------------------------------

def _repo(*parts: str) -> Path:
    return S.REPO_ROOT.joinpath(*parts)


def _project(*parts: str) -> Path:
    return S.PROJECT_ROOT.joinpath(*parts)


def runtime() -> dict:
    """The census this project took of the running 11.3 client."""
    from engine.pantheon import engine_census as EC
    return EC.load() or {"cvars": {}, "commands": []}


_KB_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|")


def source_12_7() -> dict[str, set[str]]:
    """The wolfcamql source scan: 449 commands, 1983 cvar registrations.

    Section A is commands; B, C and D are cvars. The file is a static scan of
    a 12.7test49 tree, which is NOT the program on disk.
    """
    p = _project("engine", "engines", "wolfcam-knowledge", "01-commands-cvars.md")
    out = {"commands": set(), "cvars": set()}
    if not p.exists():
        return out
    section = None
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("## A."):
            section = "commands"
        elif line.startswith(("## B.", "## C.", "## D.")):
            section = "cvars"
        elif line.startswith("## E."):
            section = None
        elif section:
            m = _KB_ROW.match(line)
            if m:
                out[section].add(m.group(1).strip())
    return out


def binary_11_3() -> set[str]:
    """Strings inside the executable we actually run.

    Weaker than the runtime answer and stronger than the source: a name in
    here is at least present in this build. Absence proves nothing -- the dump
    is not exhaustive, and cg_enemyModel is missing from it while the runtime
    registers it.
    """
    p = _project("engine", "engines", "ghidra", "reports",
                 "wolfcamql-11.3.strings.txt")
    if not p.exists():
        return set()
    names: set[str] = set()
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        for tok in re.findall(r"\b(?:cg_|cl_|r_|s_|com_|sv_|mme_|in_|m_)[A-Za-z0-9_]{2,}", line):
            names.add(tok)
    return names


_Q3MME_CVAR = re.compile(r"^([a-z][A-Za-z0-9_]{2,})\s+\[")
_Q3MME_CMD = re.compile(r"^([a-z][A-Za-z0-9_]{2,})\s*$")


def q3mme() -> dict[str, set[str]]:
    """A different engine's vocabulary, kept separate on purpose."""
    root = _project("engine", "engines", "_forks", "q3mme")
    out = {"commands": set(), "cvars": set()}
    cmds = root / "cmds.txt"
    cvars = root / "cvars.txt"
    if cmds.exists():
        for line in cmds.read_text(encoding="utf-8", errors="replace").splitlines():
            m = _Q3MME_CMD.match(line)
            if m and not line.startswith(" "):
                out["commands"].add(m.group(1))
    if cvars.exists():
        for line in cvars.read_text(encoding="utf-8", errors="replace").splitlines():
            m = _Q3MME_CVAR.match(line)
            if m:
                out["cvars"].add(m.group(1))
    return out


# -- semantic mapping -------------------------------------------------------
#
# The one place a raw engine name becomes a capability. Everything above the
# backend asks for the right-hand side and never the left.

CVAR_CAPABILITY: dict[str, str] = {
    "cg_enemymodel": "FORCE_ENEMY_MODEL",
    "cg_enemyheadmodel": "FORCE_ENEMY_MODEL",
    "cg_enemylegsskin": "FORCE_ENEMY_SKIN",
    "cg_enemytorsoskin": "FORCE_ENEMY_SKIN",
    "cg_enemyheadskin": "FORCE_ENEMY_SKIN",
    "cg_enemylegscolor": "FORCE_ENEMY_COLOUR",
    "cg_enemytorsocolor": "FORCE_ENEMY_COLOUR",
    "cg_enemyheadcolor": "FORCE_ENEMY_COLOUR",
    "cg_teammodel": "FORCE_TEAM_MODEL",
    "cg_teamheadmodel": "FORCE_TEAM_MODEL",
    "cg_teamlegsskin": "FORCE_TEAM_SKIN",
    "cg_teamtorsoskin": "FORCE_TEAM_SKIN",
    "cg_teamheadskin": "FORCE_TEAM_SKIN",
    "cg_teamlegscolor": "FORCE_TEAM_COLOUR",
    "cg_teamtorsocolor": "FORCE_TEAM_COLOUR",
    "cg_teamheadcolor": "FORCE_TEAM_COLOUR",
    "cg_forcemodel": "FORCE_ALL_MODELS",
    "cg_forceteammodel": "FORCE_TEAM_MODEL_SWITCH",
    "cg_wh": "XRAY_PLAYER",
    "cg_whcolor": "XRAY_PLAYER",
    "cg_whalpha": "XRAY_PLAYER",
    "cg_whenemycolor": "XRAY_PLAYER",
    "cg_whenemyalpha": "XRAY_PLAYER",
    "cg_whshader": "XRAY_SHADER",
    "cg_whenemyshader": "XRAY_SHADER",
    "cg_whincludedeadbody": "XRAY_INCLUDE_DEAD",
    "cg_whincludeprojectile": "XRAY_INCLUDE_PROJECTILE",
    "cl_aviframerate": "AUDIO_CAPTURE",
    "cl_avicodec": "BEAUTY_PASS",
    "cl_avidemo": "BEAUTY_PASS",
    "cl_avimotionjpeg": "BEAUTY_PASS",
    "mme_savedepth": "DEPTH_CAPTURE",
    "mme_savestencil": "ACTOR_ID_PASS",
    "in_nograb": "POINTER_NOT_GRABBED",
    "in_mouse": "POINTER_NOT_GRABBED",
    "timescale": "TIME_SCALE",
    "cl_freezedemo": "DEMO_FREEZE",
    "cl_freezedemopausevideorecording": "DEMO_FREEZE",
    "mme_blurframes": "MOTION_BLUR",
    "mme_bluroverlap": "MOTION_BLUR",
    "mme_blurtype": "MOTION_BLUR",
    "mme_depthfocus": "DEPTH_CAPTURE",
    "mme_depthrange": "DEPTH_CAPTURE",
    "cl_avipipecommand": "FFMPEG_PIPE_CAPTURE",
    "cl_avipipeextension": "FFMPEG_PIPE_CAPTURE",
    "cg_fov": "CAMERA_FOV",
    "cg_zoomfov": "CAMERA_FOV",
    "cg_railtrailtime": "PLAYER_RAIL_COLOUR",
}

COMMAND_CAPABILITY: dict[str, str] = {
    "freecam": "CAMERA_FREE",
    "setviewpos": "CAMERA_FREE",
    "setviewangles": "CAMERA_FREE",
    "follow": "CAMERA_FOLLOW",
    "chase": "CHASE_ENTITY",
    "view": "CHASE_ENTITY",
    "playcamera": "CAMERA_PATH",
    "stopcamera": "CAMERA_PATH",
    "addcamerapoint": "CAMERA_PATH",
    "savecamera": "CAMERA_PATH",
    "loadcamera": "CAMERA_PATH",
    "q3mmecamera": "CAMERA_PATH",
    "ecam": "CAMERA_PATH",
    "video": "BEAUTY_PASS",
    "stopvideo": "BEAUTY_PASS",
    "at": "TIMED_CONSOLE",
    "clearat": "TIMED_CONSOLE",
    "listat": "TIMED_CONSOLE",
    "seekservertime": "DEMO_SEEK",
    "seekclock": "DEMO_SEEK",
    "entityfreeze": "FREEZE_ENTITY",
    "remapshader": "SHADER_REMAP",
    "clearremappedshader": "SHADER_REMAP",
    "runfx": "SCENE_FX",
    "runfxat": "SCENE_FX",
    "fxload": "SCENE_FX",
    "cvarinterp": "CVAR_RAMP",
    "clearcvarinterp": "CVAR_RAMP",
    "seek": "DEMO_SEEK",
    "seekend": "DEMO_SEEK",
    "seeknext": "DEMO_SEEK",
    "seekprev": "DEMO_SEEK",
    "seeknextround": "DEMO_SEEK",
    "seekprevround": "DEMO_SEEK",
    "servertime": "DEMO_SEEK",
    "exec_at_time": "TIMED_CONSOLE",
    "listtimeditems": "TIMED_CONSOLE",
    "listentityfreeze": "FREEZE_ENTITY",
    "freecamsetpos": "CAMERA_FREE",
    "freecamlookatplayer": "CAMERA_FREE",
    "follownext": "CAMERA_FOLLOW",
    "followprev": "CAMERA_FOLLOW",
    "selectcamerapoint": "CAMERA_PATH",
    "editcamerapoint": "CAMERA_PATH",
    "deletecamerapoint": "CAMERA_PATH",
    "clearcamerapoints": "CAMERA_PATH",
    "playq3mmecamera": "CAMERA_PATH",
    "saveq3mmecamera": "CAMERA_PATH",
    "loadq3mmecamera": "CAMERA_PATH",
    "stopq3mmecamera": "CAMERA_PATH",
    "idcamera": "CAMERA_CUT",
    "stopidcamera": "CAMERA_CUT",
    "camtracesave": "CAMERA_PATH",
    "pause": "DEMO_FREEZE",
}

# Whole families that are real engine surface but nothing in this project will
# ever ask for. Ignoring is a CLASSIFICATION: it says someone looked.
IGNORED_PREFIXES = (
    "sv_", "g_", "bot_", "ui_", "net_", "rate", "snaps", "cl_allowdownload",
    "password", "banclient", "banuser", "ban", "kick", "callvote", "vote",
    "team", "say", "tell", "addbot", "record", "stoprecord", "demo", "map",
    "devmap", "spdevmap", "reconnect", "connect", "disconnect", "quit",
    "bind", "unbind", "alias", "exec", "vstr", "wait", "echo", "set", "seta",
    "sets", "setu", "toggle", "cmd", "clientinfo", "configstrings", "serverinfo",
    "systeminfo", "userinfo", "modelist", "screenshot", "levelshot", "condump",
    "clear", "messagemode", "scoresup", "scoresdown", "sizeup", "sizedown",
    "weapnext", "weapprev", "weapon", "+", "-", "centerview", "gc", "download",
    # Sound hardware, joystick and renderer debugging: surface that exists and
    # that a film pipeline never touches. Naming them here is the difference
    # between "ignored" and "nobody looked".
    "s_al", "s_dev", "s_khz", "s_mixa", "s_mixp", "in_joystick", "in_joy",
    "r_debug", "r_showtris", "r_shownormals", "r_speeds", "r_logfile",
)

IGNORED_REASON = ("server administration, chat, binding, matchmaking or "
                  "player input: real engine surface this project never drives")


def _capability_for(name: str, kind: str) -> str | None:
    table = CVAR_CAPABILITY if kind == "cvar" else COMMAND_CAPABILITY
    return table.get(name.lower())


def _ignored(name: str) -> bool:
    low = name.lower()
    return any(low.startswith(p) for p in IGNORED_PREFIXES)


# -- the whole picture ------------------------------------------------------

def build() -> dict:
    rt = runtime()
    src = source_12_7()
    binary = binary_11_3()
    mme = q3mme()

    rt_cvars = rt.get("cvars", {})
    rt_cmds = set(rt.get("commands", []))
    rt_lower = {k.lower(): k for k in rt_cvars}

    items: list[Item] = []

    def grade_cvar(name: str) -> tuple[Grade, tuple[str, ...], str | None, tuple[str, ...]]:
        low = name.lower()
        key = rt_lower.get(low)
        origins: list[str] = []
        if key:
            origins.append(Origin.RUNTIME_11_3.value)
        if name in src["cvars"] or low in {c.lower() for c in src["cvars"]}:
            origins.append(Origin.SOURCE_12_7.value)
        if name in binary:
            origins.append(Origin.BINARY_11_3.value)
        if name in mme["cvars"]:
            origins.append(Origin.Q3MME.value)
        if key:
            e = rt_cvars[key]
            g = (Grade.RUNTIME_REGISTERED if e.get("registered")
                 else Grade.RUNTIME_ACCEPTED_UNSET)
            return g, tuple(origins), e.get("value"), tuple(e.get("flags", []))
        if Origin.BINARY_11_3.value in origins:
            return Grade.TARGET_BINARY_RECOGNIZED, tuple(origins), None, ()
        if Origin.SOURCE_12_7.value in origins:
            return Grade.SOURCE_REGISTERED, tuple(origins), None, ()
        if Origin.Q3MME.value in origins:
            return Grade.UNSUPPORTED_TARGET, tuple(origins), None, ()
        # No inventory has it, and this project's own table names it. That is a
        # name someone read in a document or a forum post -- the weakest
        # evidence there is, and it must never reach production.
        return Grade.DOCUMENTED_ONLY, tuple(origins), None, ()

    seen_cvars = set()
    for name in sorted({*rt_cvars, *src["cvars"], *mme["cvars"],
                        *CVAR_CAPABILITY}):
        if name.lower() in seen_cvars:
            continue
        seen_cvars.add(name.lower())
        g, origins, value, flags = grade_cvar(name)
        cap = _capability_for(name, "cvar")
        note = ""
        if g is Grade.RUNTIME_ACCEPTED_UNSET:
            note = ("the runtime holds this name but never registered it: "
                    "setting it is a silent no-op")
        elif g is Grade.SOURCE_REGISTERED:
            note = "in the 12.7 source and NOT in the 11.3 runtime: SOURCE_ONLY"
        elif g is Grade.UNSUPPORTED_TARGET:
            note = "q3mme vocabulary; the target runtime does not have it"
        elif g is Grade.DOCUMENTED_ONLY:
            note = ("named in this project's own tables and in NO inventory: "
                    "not the runtime, not the 12.7 source, not the binary "
                    "strings, not q3mme. Treat as hearsay.")
        elif not cap and _ignored(name):
            note = IGNORED_REASON
        items.append(Item(name, "cvar", g, origins, value, flags, cap, note))

    def grade_cmd(name: str) -> tuple[Grade, tuple[str, ...]]:
        origins: list[str] = []
        if name in rt_cmds:
            origins.append(Origin.RUNTIME_11_3.value)
        if name in src["commands"]:
            origins.append(Origin.SOURCE_12_7.value)
        if name in mme["commands"]:
            origins.append(Origin.Q3MME.value)
        if Origin.RUNTIME_11_3.value in origins:
            return Grade.RUNTIME_REGISTERED, tuple(origins)
        if Origin.SOURCE_12_7.value in origins:
            return Grade.SOURCE_REGISTERED, tuple(origins)
        if Origin.Q3MME.value in origins:
            return Grade.UNSUPPORTED_TARGET, tuple(origins)
        return Grade.DOCUMENTED_ONLY, tuple(origins)

    for name in sorted({*rt_cmds, *src["commands"], *mme["commands"],
                        *COMMAND_CAPABILITY}):
        g, origins = grade_cmd(name)
        cap = _capability_for(name, "command")
        note = ""
        if g is Grade.SOURCE_REGISTERED:
            note = "in the 12.7 source and NOT in the 11.3 runtime: SOURCE_ONLY"
        elif g is Grade.UNSUPPORTED_TARGET:
            note = "q3mme vocabulary; the target runtime does not have it"
        elif g is Grade.DOCUMENTED_ONLY:
            note = ("named in this project's own tables and in NO inventory: "
                    "treat as hearsay")
        elif not cap and _ignored(name):
            note = IGNORED_REASON
        items.append(Item(name, "command", g, origins, capability=cap, note=note))

    return {"items": items, "runtime_captured_at": rt.get("captured_at"),
            "sources": {
                "runtime_cvars": len(rt_cvars),
                "runtime_commands": len(rt_cmds),
                "source_12_7_cvars": len(src["cvars"]),
                "source_12_7_commands": len(src["commands"]),
                "binary_names": len(binary),
                "q3mme_cvars": len(mme["cvars"]),
                "q3mme_commands": len(mme["commands"])}}


def unclassified(items: list[Item]) -> list[Item]:
    """An item with no grade, no capability, no ignore reason and no note.

    UNKNOWN is a classification -- somebody asked and the answer was nothing.
    An item with nothing said about it at all is the failure this pass exists
    to prevent.
    """
    return [i for i in items
            if i.capability is None and not i.note
            and i.grade not in (Grade.RUNTIME_REGISTERED,
                                Grade.RUNTIME_ACCEPTED_UNSET)]


def report() -> dict:
    built = build()
    items: list[Item] = built["items"]
    by_grade: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    for i in items:
        by_grade[i.grade.value] = by_grade.get(i.grade.value, 0) + 1
        by_kind[i.kind] = by_kind.get(i.kind, 0) + 1
    caps = {i.capability for i in items if i.capability}
    return {"sources": built["sources"],
            "runtime_captured_at": built["runtime_captured_at"],
            "items": len(items), "by_kind": by_kind, "by_grade": by_grade,
            "semantic_capabilities": len(caps),
            "mapped_items": sum(1 for i in items if i.capability),
            "ignored_items": sum(1 for i in items if i.note == IGNORED_REASON),
            "unclassified": len(unclassified(items))}


def find(name: str) -> Item | None:
    low = name.lower()
    return next((i for i in build()["items"] if i.name.lower() == low), None)


def usable(name: str) -> bool:
    i = find(name)
    return bool(i and i.grade in USABLE_IN_PRODUCTION)


def write(dest: Path | None = None) -> Path:
    built = build()
    dest = dest or (S.REPO_ROOT / "docs" / "reference" / "engine_inventory.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(
        {"sources": built["sources"],
         "runtime_captured_at": built["runtime_captured_at"],
         "items": [i.as_dict() for i in built["items"]]},
        indent=1), encoding="utf-8")
    return dest


def main() -> int:                                           # pragma: no cover
    import argparse
    ap = argparse.ArgumentParser(description="the whole engine inventory")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--unclassified", action="store_true")
    ap.add_argument("--name")
    a = ap.parse_args()
    if a.name:
        i = find(a.name)
        print(json.dumps(i.as_dict() if i else {"name": a.name,
                                                "found": False}, indent=1))
    elif a.unclassified:
        for i in unclassified(build()["items"]):
            print(f"  {i.kind:8s} {i.name}")
    else:
        print(json.dumps(report(), indent=1))
    if a.write:
        print("->", write())
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
