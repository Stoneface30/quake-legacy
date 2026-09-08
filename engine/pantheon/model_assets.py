"""What a player model's animation.cfg declares.

An ASSET question, not a truth question. The answer lives inside a pk3, and
the PANTHEON renderer host is the only thing in the system that can open one,
so this module asks it (`pantheon_frame.exe --dump-model <model>`) and turns
the reply into the `AnimationSet` that `render_frame` consumes.

The split matters. The host reads bytes out of a pak; it decides nothing about
what they mean. `render_frame` decides everything about what they mean and
runs the animation with the engine's own stateful rule, which is proved
against `oracle_anim.exe`. Neither side does the other's job.

This module spawns a process, so it is BACKEND_ALLOWED under HL-1 and nothing
under `engine/pantheon/` that carries game truth may import it. Callers pass
the result INTO `from_frame_truth(..., model_anims=...)`.

`--dump-model` creates no GL context and renders nothing, so it is not a
render and does not consult the RenderPermit: it cannot film over a running
game because it cannot film.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from .render_frame import Animation, AnimationSet

HOST_EXE = Path("G:/QUAKE_LEGACY/engine/pantheon_renderer/build/pantheon_frame.exe")


class ModelAssetError(RuntimeError):
    """The model could not be interrogated, or answered incompletely.

    Raised rather than returning a default. A model whose animation.cfg we
    could not read would otherwise be posed with everything false and every
    animation at frame zero, which looks like a decision and is not one.
    """


def _parse_dump(text: str) -> AnimationSet:
    anims: dict[int, Animation] = {}
    fixed_legs = fixed_torso = False
    declared = None

    for line in text.splitlines():
        parts = line.split()
        if not parts:
            continue
        kw = parts[0]
        if kw == "fixedlegs":
            fixed_legs = parts[1] == "1"
        elif kw == "fixedtorso":
            fixed_torso = parts[1] == "1"
        elif kw == "animations":
            declared = int(parts[1])
        elif kw == "anim":
            if len(parts) != 9:
                raise ModelAssetError("malformed anim line: %r" % line)
            i = int(parts[1])
            anims[i] = Animation(
                first_frame=int(parts[2]), num_frames=int(parts[3]),
                loop_frames=int(parts[4]), frame_lerp=int(parts[5]),
                initial_lerp=int(parts[6]),
                reversed_=parts[7] == "1", flipflop=parts[8] == "1")

    if declared is None:
        raise ModelAssetError("host printed no animation count")
    missing = [i for i in range(declared) if i not in anims]
    if missing:
        raise ModelAssetError(
            "host declared %d animations but did not print %r" % (declared, missing))

    return AnimationSet(animations=tuple(anims[i] for i in range(declared)),
                        fixed_legs=fixed_legs, fixed_torso=fixed_torso)


def load_model_animations(model: str, *, basepath: Path,
                          exe: Path = HOST_EXE,
                          homepath: Path | None = None,
                          game: str | None = None) -> AnimationSet:
    """Ask the host what `model` declares. Raises rather than guessing."""
    if not Path(exe).exists():
        raise ModelAssetError("renderer host not built: %s" % exe)

    argv = [str(exe), "--dump-model", model,
            "--basepath", str(basepath)]
    if homepath is not None:
        argv += ["--home", str(homepath)]
    if game:
        argv += ["--game", game]

    r = subprocess.run(argv, capture_output=True, text=True)
    if r.returncode != 0:
        raise ModelAssetError(
            "host refused model %r (rc=%d)\n%s" % (model, r.returncode,
                                                   (r.stderr or r.stdout)[-2000:]))
    return _parse_dump(r.stdout)


def load_cast_animations(cast, *, basepath: Path, **kw) -> dict[str, AnimationSet]:
    """One AnimationSet per distinct model in a cast mapping.

    The result is what `from_frame_truth(model_anims=...)` wants. Each model is
    interrogated once however many actors wear it.
    """
    out: dict[str, AnimationSet] = {}
    for profile in cast.values():
        model = getattr(profile, "model", str(profile))
        if model not in out:
            out[model] = load_model_animations(model, basepath=basepath, **kw)
    return out
