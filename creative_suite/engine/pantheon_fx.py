"""PANTHEON FX scripts — the q3mme-dialect ``.fx`` file a scene loads.

Companion to ``pantheon_scene.py``: that module decides WHEN a *cue* fires
(semantic anchor + offset) and WHICH console primitive fires it; this module
writes WHAT fires — the effect scripts themselves, at a chosen intensity.

## Two bindings, and the difference is not cosmetic

``cg_fx_scripts.c:6940-7440`` binds a fixed set of script NAMES to per-frame
engine hooks. Defining one of those names is all it takes to arm it — no
cvar, no console command, no fire time:

* ``weapon/rocket/trail`` (bound at cg_fx_scripts.c:7147) runs **every frame
  for every rocket in flight**, receiving that rocket's own
  ``origin/angles/velocity/dir/axis``. This is the ONLY correct way to give
  a projectile a trail.
* ``player/{head,torso,legs}/trail`` (:6960-6966) are the equivalents proven
  in free_wins_proof.md proof 2.

Everything else is a **cue**: an arbitrarily-named script fired once by
``at <t> runfx <name> [origin]``.

A one-shot ``runfx`` **cannot** produce a trail. It fires a single time at a
single point; ``interval``/``distance`` sub-emitters inside it have no
successive frames to run over. An earlier draft of this module modelled the
projectile trail as a ``runfx`` cue at the launch anchor — it would have
emitted one puff at the muzzle and been reported as a trail. The hook is the
mechanism; ``FxCue`` carries ``parameters["binding"] = "HOOK"`` to say so,
and ``compile_fx_cfg_lines`` then correctly emits no console line for it.

## Authoring constraints learned the hard way (proof 2)

* Shipped q3mme/wolfcam ``.fx`` examples assume **Quake 3** asset names.
  ``sprites/balloon3`` is not in QL's ``pak00.pk3`` and renders as a blue
  placeholder quad. Every shader referenced here is one the shipped QL
  scripts themselves reference (``smokePuff``, ``flareShader``,
  ``rocketExplosion``), which is why the palette is deliberately small.
* The ``axismodel`` model-copy ghost is NOT proven — ``trap_R_GetModelName``
  -> ``RegisterModel`` did not round-trip for QL player models. Only the
  sprite-emitter form is used here.
* ``cg_fxfile`` is ``CVAR_ARCHIVE`` and leaks between runs via
  ``q3config.cfg``. It is in ``pantheon_runtime.RUNTIME_BASELINE`` for
  exactly that reason; a capture that loads one of these scripts must set it
  as an explicit override, never rely on inheritance.

Grammar is modelled directly on the shipped ``q3mme.fx`` /``dirtest.fx``
(``distance N {}``, ``emitter <life> {}``, ``repeat N {}``, ``copy``/
``scale`` for vector maths, ``Sprite``/``Light``/``alphaFade``/``colorFade``)
rather than invented.

## Intensity ladder (§15)

The three levels are the SAME effects at three strengths, not three
different effects:

* ``OFF``    — a real, loadable file that defines nothing.
* ``SUBTLE`` — genuinely restrained: short emitter life, small sizes, no
  added dynamic light on the trail. Reads as "the shot has a look", not
  "an effect happened".
* ``HERO``   — same emitters, longer-lived, larger, brighter, plus a
  coloured dynamic light on the trail and a slow bloom under the impact
  burst. The cap is "unmistakable on a single frame", not "obscures the
  frag".
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from creative_suite.engine.pantheon_scene import (INTENSITY_LEVELS,
                                                  INTENSITY_OFF)

SCRIPT_NAME = "scripts/pantheon_canary.fx"

# HOOK-bound: defining this name arms the engine's per-frame rocket trail.
FX_ROCKET_TRAIL = "weapon/rocket/trail"
# CUE-fired: arbitrary name, fired by `at <t> runfx <name> <x> <y> <z>`.
FX_IMPACT = "pantheon/canary/impact"

# Defining ``weapon/rocket/trail`` REPLACES the stock trail wholesale — it
# does not layer on top of it. The shipped q3mme.fx version opens with
# `color 1 0.75 0 / size 200 / Light`, so a replacement that omits a Light
# silently DELETES the rocket's warm dynamic glow. Measured 2026-09-01: the
# first SUBTLE pass looked DIMMER than FX OFF for exactly this reason, which
# is the opposite of what an effect level is supposed to do. Every level
# therefore carries a light; SUBTLE's simply reproduces the stock one.
_STOCK_TRAIL_LIGHT = ("1 0.75 0", 200)

_LEVEL = {
    "SUBTLE": {
        "trail_distance": 42, "trail_life": 1.1,
        "trail_size": "5 + lerp * 22", "trail_alpha": 0.26,
        "trail_color": "0.80 0.80 0.84",
        "trail_light": _STOCK_TRAIL_LIGHT,   # keep the stock warm glow
        "burst_count": 16, "burst_speed": "70 + rand*60",
        "burst_size": "2 + rand*2", "burst_life": "0.35 + rand*0.15",
        "burst_color": "0.85 0.78 0.62", "burst_alpha": 0.55,
        "bloom": None,
    },
    "HERO": {
        "trail_distance": 24, "trail_life": 2.0,
        "trail_size": "9 + lerp * 52", "trail_alpha": 0.42,
        "trail_color": "0.70 0.80 1.00", "trail_light": ("0.45 0.60 1.0", 210),
        # Retuned down after frame review: the first HERO pass filled the
        # impact area with a bloom that hid the victim entirely. The cap on
        # this level is "unmistakable on a single frame", NOT "obscures the
        # frag" — a fragmovie effect that eats the frag is a failed effect.
        "burst_count": 30, "burst_speed": "180 + rand*220",
        "burst_size": "3 + rand*4", "burst_life": "0.6 + rand*0.35",
        "burst_color": "1.0 0.86 0.55", "burst_alpha": 0.85,
        "bloom": ("1.0 0.72 0.30", 0.5, "80 + 200 * lerp"),
    },
}


def _trail_block(p: dict) -> list[str]:
    """``weapon/rocket/trail`` — per-frame hook, distance-emitted puffs.

    ``distance N {}`` emits one sub-effect per N world units travelled,
    which is what makes the trail density independent of framerate — the
    same reason the shipped script uses it.
    """
    lines = [f"{FX_ROCKET_TRAIL} {{"]
    if p["trail_light"]:
        colour, size = p["trail_light"]
        lines += ["\t// HERO only: coloured dynamic light riding the rocket",
                  f"\tcolor\t{colour}", f"\tsize\t{size}", "\tLight", ""]
    lines += [
        f"\tcolor\t{p['trail_color']}",
        f"\talpha\t{p['trail_alpha']}",
        "\tshader\tsmokePuff",
        "\trotate\t360 * rand",
        f"\tdistance {p['trail_distance']} {{",
        f"\t\temitter {p['trail_life']} {{",
        "\t\t\talphaFade\t0",
        f"\t\t\tsize\t\t{p['trail_size']}",
        "\t\t\tsprite\t\tcullNear",
        "\t\t}",
        "\t}",
        "}",
        "",
    ]
    return lines


def _impact_block(p: dict) -> list[str]:
    """A cue effect. Structure copied from the PROVEN ``dirtest.fx``
    ``weapon/rocket/impact``: ``repeat N`` of outward flare sprites built by
    ``copy``/``scale`` on ``velocity``, then (HERO) one slow bloom."""
    lines = [
        f"{FX_IMPACT} {{",
        "\t// outward flare burst -- dirtest.fx's proven repeat/copy/scale form",
        "\tshader\tflareShader",
        f"\talpha\t{p['burst_alpha']}",
        f"\tcolor\t{p['burst_color']}",
        f"\trepeat {p['burst_count']} {{",
        "\t\twobble\tdir velocity 90 + rand*90",
        f"\t\tscale\tvelocity velocity {p['burst_speed']}",
        f"\t\tsize\t{p['burst_size']}",
        f"\t\temitter \"{p['burst_life']}\" {{",
        "\t\t\tmoveGravity 0",
        "\t\t\tcolorFade 0.7",
        "\t\t\tSprite",
        "\t\t}",
        "\t}",
    ]
    if p["bloom"]:
        colour, life, size = p["bloom"]
        lines += [
            "",
            "\t// HERO only: one slow bloom under the burst",
            "\tshader\trocketExplosion",
            f"\tcolor\t{colour}",
            "\talpha\t1",
            f"\temitter {life} {{",
            f"\t\tsize\t\t{size}",
            "\t\tSprite",
            "\t\tLight",
            "\t}",
        ]
    lines += ["}", ""]
    return lines


def script_source(level: str) -> str:
    """The full ``.fx`` file body for one intensity level."""
    if level not in INTENSITY_LEVELS:
        raise ValueError(f"unknown intensity level: {level!r}")
    if level == INTENSITY_OFF:
        # A real, loadable file that defines nothing. Keeping OFF on the
        # same code path as SUBTLE/HERO means an OFF capture still loads a
        # script and still exercises cg_fxfile, so the only variable across
        # the ladder is effect CONTENT — not whether an fx file was loaded.
        return ("// PANTHEON canary FX -- OFF\n"
                "// Intentionally defines no effects. Loaded anyway so an OFF\n"
                "// capture differs from SUBTLE/HERO ONLY in content.\n")
    p = _LEVEL[level]
    lines = [f"// PANTHEON canary FX -- {level}",
             "// weapon/rocket/trail is a PER-FRAME ENGINE HOOK "
             "(cg_fx_scripts.c:7147):",
             "// defining it is what arms it. It is never fired by runfx.",
             ""]
    lines += _trail_block(p)
    lines += ["// fired as a CUE: at <t> runfx pantheon/canary/impact x y z",
              "// input: origin, dir"]
    lines += _impact_block(p)
    return "\n".join(lines)


def write_script(level: str, gamedir: Path) -> Path:
    """Write the level's script into the gamedir; returns its path."""
    from creative_suite.engine.wolfcam_capture import write_engine_file
    path = Path(gamedir) / SCRIPT_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    # One code path, one guarantee: everything the engine parses goes
    # through write_engine_file (LF-only, ascii). The .fx parser is
    # whitespace tolerant, unlike .cam10's line-positional grammar, so this
    # is hardening rather than a bug fix here — but the CRLF bug that faked
    # an engine defect for a whole session earns every generated engine
    # asset the same discipline.
    write_engine_file(path, script_source(level))
    return path


def script_hash(level: str) -> str:
    return hashlib.sha256(script_source(level).encode("ascii")).hexdigest()
