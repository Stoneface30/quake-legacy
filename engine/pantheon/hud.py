"""THE HUD IS A FILM SURFACE, NOT A GAME OVERLAY.

TWO SURFACES, AND THE CVARS COME FIRST.

    cvars    WHETHER an element draws, WHERE, how big, how faded, what
             colour, how long it dwells. 383 `cg_draw*` cvars over 81
             elements; 30 of them carry a full control set. Per element,
             set per capture, therefore CUEABLE.
    shaders  WHAT THE ART LOOKS LIKE. 281 blocks in `scripts/gfx.shader`,
             which can scroll, rotate, pulse, fade or draw nothing.

This module was written shader-first and that was the wrong order. The engine
already had a dedicated switch for every element, the census had ingested all
383 of them, and project profiles used 42 -- so 341 controls sat unoffered
while a HUD treatment was attempted by rewriting art. The control surface is
now the primary one (`elements`, `hide`, `restyle`); the shader surface below
is for restyling the art those elements draw, which no cvar can do.

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


# ── THE CONTROL SURFACE THIS MODULE SHOULD HAVE STARTED FROM ───────────────
#
# The shader layer above restyles the ART a HUD element draws. It does NOT
# decide whether the element is drawn, where, how big, how faded or what
# colour -- and the engine has a dedicated switch for every one of those, on
# every element.
#
# THE CENSUS COUNTED 383 `cg_draw*` CVARS. Seventy elements; thirty-two of
# them carry a whole control set -- FragMessage has twenty, Rewards and
# ItemPickups sixteen each. Project profiles set forty-two of the 383. The
# rest were ingested and never offered to the film layer, which is how a HUD
# treatment came to be attempted with shaders first.
#
# These are the right primary surface because they are per-element and they
# are CUEABLE: a cvar is set per capture, so the same moment filmed twice with
# a different value is a cut the editor can place. See `morph.py`.

# The census is COMMITTED, so it is a fact about the CODE, not about the data
# drive -- and the main checkout may sit on a branch that does not carry it.
# Resolving it through PROJECT_ROOT found nothing and reported an empty HUD.
CENSUS = S.CODE_ROOT / "docs" / "reference" / "engine_census_11_3.json"

#: Suffixes that turn a base element name into one of its controls. Longest
#: match wins, so `FadeTime` is not read as `Time`.
CONTROL_SUFFIXES: tuple[str, ...] = (
    "Align", "Alpha", "BackgroundAlpha", "BackgroundColor", "Color", "Count",
    "Fade", "FadeTime", "Filter", "Font", "Icon", "IconScale", "IconSize",
    "IconStyle", "IconXoffset", "IconYoffset", "ImageScale", "LineOffset",
    "Max", "MaxWidth", "MinWidth", "NoText", "Offset", "PointSize", "Scale",
    "SelectedColor", "Separate", "Spacing", "Style", "TextAlpha", "TextColor",
    "TextStyle", "Time", "WideScreen", "X", "Y",
)

#: What a film actually wants to do to an element, and which control does it.
FILM_CONTROLS = {"visibility": "", "position": ("X", "Y"), "size": "Scale",
                 "opacity": "Alpha", "colour": "Color", "dwell": "Time",
                 "fade": ("Fade", "FadeTime")}


@dataclass(frozen=True)
class HudElement:
    """One addressable thing on screen and every knob the engine gives it."""
    name: str                       # e.g. "Rewards"
    switch: str                     # the cvar that draws it at all
    controls: dict = field(default_factory=dict)   # suffix -> cvar name

    def can(self, what: str) -> bool:
        want = FILM_CONTROLS.get(what)
        if want == "":
            return True
        want = (want,) if isinstance(want, str) else want
        return all(w in self.controls for w in want)

    @property
    def control_count(self) -> int:
        return 1 + len(self.controls)


def _census_cvars() -> tuple[str, ...]:
    import json
    if not CENSUS.exists():
        return ()
    data = json.loads(CENSUS.read_text(encoding="utf-8"))
    return tuple(data.get("cvars", {}))


def elements() -> dict[str, HudElement]:
    """Every HUD element the running engine registers, with its controls.

    Derived from the RUNTIME census, not from source: a name the 11.3 binary
    never registered is a silent no-op, and this project has been caught by
    that before.
    """
    names = [c for c in _census_cvars() if c.lower().startswith("cg_draw")]
    by_base: dict[str, dict] = {}
    for cvar in names:
        stem = cvar[len("cg_draw"):]
        hit = None
        for suf in sorted(CONTROL_SUFFIXES, key=len, reverse=True):
            if stem.endswith(suf) and len(stem) > len(suf):
                hit = suf
                break
        base = stem[: -len(hit)] if hit else stem
        e = by_base.setdefault(base, {"switch": None, "controls": {}})
        if hit is None:
            e["switch"] = cvar
        else:
            e["controls"][hit] = cvar
    out = {}
    for base, e in sorted(by_base.items()):
        # An element with no bare switch is still addressable through its
        # controls; name the switch it WOULD have rather than inventing one.
        out[base] = HudElement(base, e["switch"] or f"cg_draw{base}",
                               e["controls"])
    return out


def hide(*names: str) -> dict[str, int]:
    """Turn named elements off. The cheapest HUD effect there is, and the one
    the shader layer was reaching for the hard way."""
    els = elements()
    out = {}
    for n in names:
        if n not in els:
            raise KeyError(f"no such HUD element: {n}")
        out[els[n].switch] = 0
    return out


def restyle(name: str, *, x=None, y=None, scale=None, alpha=None,
            colour=None, dwell=None) -> dict:
    """Move, resize, fade or recolour one element.

    Returns cvar settings for a capture. Only knobs the engine actually
    registered for that element are emitted -- asking for one it does not have
    raises, rather than quietly setting a name the engine will ignore.
    """
    els = elements()
    if name not in els:
        raise KeyError(f"no such HUD element: {name}; known: {sorted(els)[:8]}")
    el = els[name]
    want = {"X": x, "Y": y, "Scale": scale, "Alpha": alpha, "Color": colour,
            "Time": dwell}
    out: dict = {}
    for suffix, value in want.items():
        if value is None:
            continue
        if suffix not in el.controls:
            raise KeyError(
                f"{name} has no {suffix} control in the 11.3 runtime; "
                f"it has {sorted(el.controls)}")
        out[el.controls[suffix]] = value
    return out


def control_report() -> dict:
    """How much of the HUD the film layer can actually address."""
    els = elements()
    rich = {n: e for n, e in els.items() if e.control_count > 2}
    return {
        "census": str(CENSUS),
        "draw_cvars": len([c for c in _census_cvars()
                           if c.lower().startswith("cg_draw")]),
        "elements": len(els),
        "elements_with_a_control_set": len(rich),
        "most_controllable": sorted(
            ((n, e.control_count) for n, e in els.items()),
            key=lambda kv: -kv[1])[:8],
        "can_be_moved": sorted(n for n, e in els.items()
                               if e.can("position")),
        "can_be_faded": sorted(n for n, e in els.items() if e.can("opacity")),
    }
