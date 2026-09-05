"""DOCUMENTARY_COLOR_FORMAT -- decided by PROOF 0, on pixels.

THE ANSWER. The rail colour family is read as a single INTEGER in 0xRRGGBB
form. `0x`-prefixed hex works, and so does the same number in plain decimal. A
space-separated triple does NOT: it is read as its first number and the beam
goes nearly black.

    cg_teamRailColor1 "0x2a8000"   -> measured core (44, 110, 6)   GREEN
    cg_teamRailColor1 "2785280"    -> measured core (67, 106, 7)   GREEN
    cg_teamRailColor1 "2752512"    -> 0x2a0000, beam collapses to a dim residual
    cg_teamRailColor1 "42 128 0"   -> read as 42 = 0x00002a, same collapse
    cg_teamRailColor1 ""           -> (226, 4, 5), the shooter's own c1

THE SOURCE SAID OTHERWISE AND THE SOURCE WAS WRONG. `Cvar_Set` computes
`var->integer` with plain `atoi`, and `atoi("0x2a8000")` is 0 in C. The frame
says hex parses anyway. Per the standing rule, the film follows runtime; the
mechanism is a question for later and changes nothing about what is allowed on
screen.

THE FORMAT IS PER-FAMILY, NOT GLOBAL. `cg_whColor` goes through
`SC_ParseColorFromStr`, which rejects anything that is not a digit or a space,
and takes `"40 255 40"` -- also proven on frames, in an earlier sprint. So two
colour cvars in the same cgame want two different syntaxes, and writing one in
the other's form is a silent no-op. That is exactly what this module exists to
prevent.
"""
from __future__ import annotations

RGB = tuple[int, int, int]


class ColorSyntax:
    PACKED_INT = "PACKED_INT"      # 0xRRGGBB (or its decimal equal)
    DECIMAL_TRIPLE = "DECIMAL_TRIPLE"   # "R G B"


# Which cvar wants which syntax. Only families measured on frames appear here;
# an unlisted name is a name nobody has proven, and `format_for` says so rather
# than guessing.
SYNTAX = {
    # PROOF 0, 2026-09-05 -- five variants, one rail, one camera.
    "cg_teamrailcolor1": ColorSyntax.PACKED_INT,
    "cg_teamrailcolor2": ColorSyntax.PACKED_INT,
    "cg_enemyrailcolor1": ColorSyntax.PACKED_INT,
    "cg_enemyrailcolor2": ColorSyntax.PACKED_INT,
    "cg_railitemcolor": ColorSyntax.PACKED_INT,
    "cg_teamrailitemcolor": ColorSyntax.PACKED_INT,
    "cg_enemyrailitemcolor": ColorSyntax.PACKED_INT,
    # PROOF B, 2026-09-05: measured, not inferred. cg_teamLegsColor
    # "0x00ff00" put a keel/bright teammate at (102,225,98) and
    # cg_enemyLegsColor "0xff00ff" put a keel/bright enemy at (251,83,249),
    # against neutral (203,201,163) / (213,185,161) with the family cleared.
    "cg_enemylegscolor": ColorSyntax.PACKED_INT,
    "cg_enemytorsocolor": ColorSyntax.PACKED_INT,
    "cg_enemyheadcolor": ColorSyntax.PACKED_INT,
    "cg_teamlegscolor": ColorSyntax.PACKED_INT,
    "cg_teamtorsocolor": ColorSyntax.PACKED_INT,
    "cg_teamheadcolor": ColorSyntax.PACKED_INT,
    # Proven in an earlier sprint on cg_wh frames: this family is the OTHER
    # syntax, and hex is rejected outright with "invalid color string".
    "cg_whcolor": ColorSyntax.DECIMAL_TRIPLE,
    "cg_whenemycolor": ColorSyntax.DECIMAL_TRIPLE,
    "cg_whteamcolor": ColorSyntax.DECIMAL_TRIPLE,
}

# Names whose syntax is inferred from a shipped default rather than measured.
# Empty since PROOF B: every colour family this project writes has been filmed.
INFERRED: set[str] = set()


def syntax_for(cvar: str) -> str:
    key = cvar.lower()
    if key not in SYNTAX:
        raise KeyError(
            f"{cvar!r} has no MEASURED colour syntax. Two families in this "
            f"cgame want incompatible forms and writing the wrong one is a "
            f"silent no-op, so a colour may not go on screen for a cvar "
            f"nobody has filmed. Add it to a proof first.")
    return SYNTAX[key]


def format_for(cvar: str, rgb: RGB) -> str:
    """The one representation this cvar actually accepts."""
    r, g, b = (int(c) for c in rgb)
    for c in (r, g, b):
        if not 0 <= c <= 255:
            raise ValueError(f"{rgb} is not an 8-bit RGB triple")
    kind = syntax_for(cvar)
    if kind == ColorSyntax.PACKED_INT:
        return f'"0x{r:02x}{g:02x}{b:02x}"'
    return f'"{r} {g} {b}"'


def is_inferred(cvar: str) -> bool:
    """True when the syntax is taken from a shipped default, not a frame."""
    return cvar.lower() in INFERRED


# ── the analysis tint, as cvars ───────────────────────────────────────────
# Moved here from engine.pantheon.instruction (2026-09-05, HL-1): the
# instruction layer states the intent -- an RGB and "same team as the POV" --
# and this backend-side module turns it into the cvar family the engine
# classifies by.

def analysis_visual_cvars(*, same_team_as_pov: bool,
                          rgb: tuple[int, int, int] | None = None) -> dict:
    """Cvars that colour the analysis body and leave history alone.

    `same_team_as_pov` decides which half of the family to write, because the
    engine classifies by team relation and not by anything the instruction
    layer controls.
    """
    if rgb is None:
        from engine.pantheon.instruction import PANTHEON_GREEN
        rgb = PANTHEON_GREEN
    fam = "cg_team" if same_team_as_pov else "cg_enemy"
    return {f"{fam}{part}Color": format_for(f"{fam}{part}Color", rgb)
            for part in ("Legs", "Torso", "Head")}
