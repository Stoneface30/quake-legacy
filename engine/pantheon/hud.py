"""THE HUD IS A FILM SURFACE, NOT A GAME OVERLAY.

Every 2D element Quake draws over the world -- crosshairs, ammo digits, item
icons, medals, the lagometer, powerup overlays -- is a named shader in
`scripts/gfx.shader`. A shader is a small program: it can scroll its texture,
rotate it, pulse its colour, fade its alpha, flip through frames, or draw
nothing at all. That is an animation system, and it was already in the game.

WHAT THE PROJECT ALREADY DID, AND WHAT IT PROVES. `zzz_zz_moviehud.pk3` holds
exactly one file, a copy of the stock `scripts/gfx.shader` with ONE block
changed: `net` draws `$whiteimage` under `blendfunc GL_ZERO GL_ONE`, which
multiplies the frame by zero and shows nothing. The connection-interrupted
icon is gone from every clip we have ever filmed. So the override works, the
override point is this file, and the unit of override is THE WHOLE FILE -- a
later pk3 supplying `scripts/gfx.shader` replaces the earlier one rather than
adding to it. This module therefore always emits a complete file.

THE HONEST LIMIT, STATED UP FRONT. A Quake shader wave is a function of the
engine clock. `rgbGen wave sin 0.5 0.5 0 2` pulses twice a second from the
moment the map loads and cannot be told to peak on a rocket impact. So:

    FREE_RUNNING   the effect animates by itself, forever, uncued.
    CUEABLE        the effect is a STATE, and the cue is the cut between two
                   renders of the same moment that differ only in this pack.

The second is the useful one for film, and it is why this module and
`asset_library` produce the same kind of object: a named pack that is the only
variable between two otherwise identical captures. Cueing a HUD effect to a
beat is stitching, not shader authoring. See `morph.py`.

WHAT THIS MODULE DOES NOT CLAIM. It writes shader text and a pk3. Whether the
picture changed is a pixel question, answered by a capture and a human, and
recorded in `visual_proof`. Nothing here reports a proof it did not receive.
"""
from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from engine.pantheon import store as S

# The stock file every override starts from. Read-only, per the project rule
# that shipped paks are source of truth.
STOCK_PAK = (S.PROJECT_ROOT / "output" / "demo_v2" / "_wolfcam_staging"
             / "baseq3" / "pak00.pk3")
SHADER_PATH = "scripts/gfx.shader"

# Sorts after `zzz_zz_moviehud.pk3`, so a pack built here wins over it.
PACK_NAME = "zzz_zzz_pantheon_hud.pk3"


# ── what is on the surface ─────────────────────────────────────────────────

#: Which family a shader name belongs to. Ordered: the first match wins, so
#: the specific prefixes are listed before the general ones.
FAMILY_RULES: tuple[tuple[str, str], ...] = (
    ("medal_", "MEDALS"),            # accuracy, assist, capture, combokill...
    ("icons/", "ITEM_ICONS"),        # weapon and powerup inventory icons
    ("powerups/", "POWERUP_SKINS"),  # the full-model overlays, not icons
    ("sprites/", "SPRITES"),         # friend markers, flag carriers, balloons
    ("gfx/2d/", "SCREEN_2D"),        # crosshairs, numbers, cursor, menus
    ("gfx/damage/", "DAMAGE_MARKS"), # decals on the world
    ("gfx/misc/", "WORLD_FX"),       # rain, snow, tracers
    ("gfx/", "GFX_OTHER"),
    ("models/", "MODEL_FX"),
    ("textures/", "TEXTURE_FX"),
)

#: Named individually because they are single shaders that matter to a film.
NAMED_FAMILY: dict[str, str] = {
    # `disconnected` is the block that draws `gfx/2d/net.tga` -- the icon the
    # shipped movie pack already hides. There is no shader called `net`.
    "lagometer": "TELEMETRY",
    "disconnected": "TELEMETRY",
    "console": "CHROME",
    "menuback": "CHROME",
    "menubacknologo": "CHROME",
    "browserShader": "CHROME",
    "white": "CHROME",
}

#: The families a film actually composites. Everything else is scenery.
HUD_FAMILIES = ("SCREEN_2D", "ITEM_ICONS", "MEDALS", "TELEMETRY", "SPRITES")


@dataclass(frozen=True)
class HudShader:
    """One shader block, as it stands in the stock file."""
    name: str
    family: str
    body: str                       # everything between the braces, verbatim
    maps: tuple[str, ...] = ()      # the textures its stages draw
    directives: tuple[str, ...] = ()  # lowercased keywords present in the body

    @property
    def animated_already(self) -> bool:
        """True when the stock game already moves this element."""
        return any(d in self.directives
                   for d in ("tcmod", "animmap", "deformvertexes"))


def family_of(name: str) -> str:
    if name in NAMED_FAMILY:
        return NAMED_FAMILY[name]
    for prefix, fam in FAMILY_RULES:
        if name.startswith(prefix):
            return fam
    return "OTHER"


_BLOCK = re.compile(r"(?m)^(?P<name>\S+)[ \t]*\r?\n\{(?P<body>.*?)\r?\n\}",
                    re.S)


def stock_text(pak: Path | None = None) -> str:
    """The shipped `gfx.shader`, read out of the pak without unpacking it."""
    pak = Path(pak) if pak else STOCK_PAK
    if not pak.exists():
        raise FileNotFoundError(f"no stock pak at {pak}")
    with zipfile.ZipFile(pak) as z:
        return z.read(SHADER_PATH).decode("latin-1")


def inventory(text: str | None = None) -> tuple[HudShader, ...]:
    """Every shader block in the file, classified. Parses, never guesses."""
    text = stock_text() if text is None else text
    out = []
    for m in _BLOCK.finditer(text):
        name, body = m.group("name"), m.group("body")
        maps = tuple(mm.group(1) for mm in
                     re.finditer(r"(?im)^\s*(?:clamp)?map\s+(\S+)", body)
                     if not mm.group(1).startswith("//"))
        directives = tuple(sorted({d.lower() for d in re.findall(
            r"(?im)^\s*([A-Za-z_]+)", body)}))
        out.append(HudShader(name, family_of(name), body, maps, directives))
    return tuple(out)


def families(text: str | None = None) -> dict[str, int]:
    """How many shaders each family holds. The inventory, counted."""
    counts: dict[str, int] = {}
    for sh in inventory(text):
        counts[sh.family] = counts.get(sh.family, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: -kv[1]))


# ── what a film can ask the surface to do ──────────────────────────────────

FREE_RUNNING = "FREE_RUNNING"    # animates on the engine clock, uncued
CUEABLE = "CUEABLE"              # a state; the cut between packs is the cue


@dataclass(frozen=True)
class HudEffect:
    """A film word for a HUD treatment, and how it rewrites the surface.

    `rewrite` receives the stock shader and returns the replacement body, or
    None to leave the shader exactly as it shipped. Effects are described in
    film terms; the shader syntax is an implementation detail of this module
    and appears nowhere above it.
    """
    name: str
    intent: str
    timing: str                      # FREE_RUNNING or CUEABLE
    applies_to: tuple[str, ...]      # family names
    rewrite: object = None           # Callable[[HudShader], str | None]
    note: str = ""

    def targets(self, shaders) -> tuple[HudShader, ...]:
        return tuple(s for s in shaders if s.family in self.applies_to)


def _hidden(_sh: HudShader) -> str:
    """Draw nothing. The proven idiom, copied from the shipped movie pack:
    multiply the frame by zero rather than trying to make the art invisible."""
    return "\n\t{\n\t\tmap $whiteimage\n\t\tblendfunc GL_ZERO GL_ONE\n\t}"


def _first_map(sh: HudShader) -> str:
    return sh.maps[0] if sh.maps else "$whiteimage"


def _ghost(alpha: float):
    def rw(sh: HudShader) -> str:
        return (f"\n\tnopicmip\n\t{{\n\t\tmap {_first_map(sh)}\n"
                f"\t\tblendfunc GL_SRC_ALPHA GL_ONE_MINUS_SRC_ALPHA\n"
                f"\t\talphaGen constant {alpha:.2f}\n\t}}")
    return rw


def _pulse(base: float, amp: float, freq: float):
    def rw(sh: HudShader) -> str:
        return (f"\n\tnopicmip\n\t{{\n\t\tmap {_first_map(sh)}\n"
                f"\t\tblendfunc GL_SRC_ALPHA GL_ONE_MINUS_SRC_ALPHA\n"
                f"\t\trgbGen wave sin {base:.2f} {amp:.2f} 0 {freq:.2f}\n\t}}")
    return rw


def _flare(sh: HudShader) -> str:
    """The element glows: its own art, plus an additive copy of itself."""
    m = _first_map(sh)
    return (f"\n\tnopicmip\n\t{{\n\t\tmap {m}\n"
            f"\t\tblendfunc GL_SRC_ALPHA GL_ONE_MINUS_SRC_ALPHA\n\t}}\n"
            f"\t{{\n\t\tmap {m}\n\t\tblendfunc add\n"
            f"\t\trgbGen wave sin 0.20 0.20 0 1.50\n\t}}")


def _drift(sh: HudShader) -> str:
    """A slow scroll across the element. Reads as a CRT or a scan."""
    return (f"\n\tnopicmip\n\t{{\n\t\tmap {_first_map(sh)}\n"
            f"\t\tblendfunc GL_SRC_ALPHA GL_ONE_MINUS_SRC_ALPHA\n"
            f"\t\ttcMod scroll 0 0.15\n\t}}")


def _shimmer(sh: HudShader) -> str:
    """Heat-haze on the element, using the same turb the game uses on
    powerup skins."""
    return (f"\n\tnopicmip\n\t{{\n\t\tmap {_first_map(sh)}\n"
            f"\t\tblendfunc GL_SRC_ALPHA GL_ONE_MINUS_SRC_ALPHA\n"
            f"\t\ttcMod turb 0 0.06 0 0.4\n\t}}")


EFFECTS: dict[str, HudEffect] = {}


def _add(e: HudEffect) -> HudEffect:
    EFFECTS[e.name] = e
    return e


_add(HudEffect(
    "HUD_CLEAN", "No HUD at all: a clean plate of pure gameplay.",
    CUEABLE, HUD_FAMILIES, _hidden,
    note="The base plate for compositing. Cut against a HUD_STOCK render of "
         "the same moment and the HUD appears or vanishes on the cut."))

_add(HudEffect(
    "HUD_GHOST", "The HUD is present but half there, so the world reads "
                 "through it.",
    CUEABLE, HUD_FAMILIES, _ghost(0.35)))

_add(HudEffect(
    "HUD_BREATHE", "The HUD pulses gently, as if it were alive.",
    FREE_RUNNING, HUD_FAMILIES, _pulse(0.75, 0.25, 0.5),
    note="Uncued by construction: the wave runs on the engine clock from map "
         "load. Use it for mood, never to hit a beat."))

_add(HudEffect(
    "HUD_FLARE", "Every HUD element glows, hot and additive.",
    FREE_RUNNING, ("SCREEN_2D", "ITEM_ICONS", "MEDALS"), _flare))

_add(HudEffect(
    "HUD_DRIFT", "A slow scan drifts across the HUD art.",
    FREE_RUNNING, ("SCREEN_2D", "MEDALS"), _drift))

_add(HudEffect(
    "HUD_SHIMMER", "The HUD ripples, the way the game already ripples a "
                   "powerup skin.",
    FREE_RUNNING, ("SCREEN_2D", "ITEM_ICONS"), _shimmer))

_add(HudEffect(
    "HUD_MEDALS_ONLY", "Everything hidden except the medals, so an award can "
                       "be composited alone over other footage.",
    CUEABLE, tuple(f for f in HUD_FAMILIES if f != "MEDALS"), _hidden,
    note="An isolation, not a hide: the families NOT named here keep their "
         "stock appearance."))

_add(HudEffect(
    "HUD_TELEMETRY_OFF", "Hide the lagometer, the netgraph and the "
                         "disconnected icon, and nothing else.",
    CUEABLE, ("TELEMETRY",), _hidden,
    note="A superset of the shipped movie pack, which hides `disconnected` "
         "and leaves the lagometer drawing."))

#: The identity. Emitting it proves the writer is faithful: the output must be
#: byte-identical to the stock file.
_add(HudEffect(
    "HUD_STOCK", "The HUD exactly as the game ships it.",
    CUEABLE, (), None,
    note="The control leg. Every claim about a HUD treatment is a claim "
         "against this one."))


# ── writing the surface back out ───────────────────────────────────────────

def apply(effect_name: str, text: str | None = None) -> tuple[str, list[str]]:
    """Rewrite the shader file for one effect.

    Returns the complete new file and the names of the shaders it changed.
    Every block the effect does not name is reproduced verbatim, including
    comments and whitespace, so a diff against stock shows only the intent.
    """
    if effect_name not in EFFECTS:
        raise KeyError(f"no such HUD effect: {effect_name}; "
                       f"known: {sorted(EFFECTS)}")
    effect = EFFECTS[effect_name]
    text = stock_text() if text is None else text
    if effect.rewrite is None or not effect.applies_to:
        return text, []

    changed: list[str] = []

    def sub(m: re.Match) -> str:
        name, body = m.group("name"), m.group("body")
        fam = family_of(name)
        if fam not in effect.applies_to:
            return m.group(0)
        new = effect.rewrite(HudShader(
            name, fam, body,
            tuple(mm.group(1) for mm in
                  re.finditer(r"(?im)^\s*(?:clamp)?map\s+(\S+)", body)),
            ()))
        if new is None:
            return m.group(0)
        changed.append(name)
        return f"{name}\n{{{new}\n}}"

    return _BLOCK.sub(sub, text), changed


def build_pack(effect_name: str, out_dir: Path,
               text: str | None = None) -> dict:
    """Write a pk3 that applies one effect, and say exactly what it changed.

    The pack carries the whole shader file because that is the unit the engine
    replaces. It is named to sort last so it wins over every other pack,
    including the existing movie HUD pack.
    """
    new_text, changed = apply(effect_name, text)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pk3 = out_dir / PACK_NAME

    with zipfile.ZipFile(pk3, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(SHADER_PATH, new_text.encode("latin-1"))

    effect = EFFECTS[effect_name]
    return {
        "effect": effect_name,
        "intent": effect.intent,
        "timing": effect.timing,
        "pack": str(pk3),
        "bytes": pk3.stat().st_size,
        "shaders_changed": len(changed),
        "changed": sorted(changed),
        # Said plainly, because the alternative is implying a proof.
        "proven": False,
        "how_to_prove": "capture one moment with this pack and once without, "
                        "then look at the two frames",
    }


def report(text: str | None = None) -> dict:
    """The HUD surface, as it stands. Facts only."""
    shaders = inventory(text)
    fam = families(text)
    return {
        "source": f"{STOCK_PAK.name}:{SHADER_PATH}",
        "shaders": len(shaders),
        "families": fam,
        "film_families": {k: v for k, v in fam.items() if k in HUD_FAMILIES},
        "already_animated": sorted(s.name for s in shaders
                                   if s.animated_already),
        "effects": {
            name: {"intent": e.intent, "timing": e.timing,
                   "applies_to": list(e.applies_to), "note": e.note}
            for name, e in EFFECTS.items()},
        "cueable": sorted(n for n, e in EFFECTS.items()
                          if e.timing == CUEABLE),
        "free_running": sorted(n for n, e in EFFECTS.items()
                               if e.timing == FREE_RUNNING),
    }
