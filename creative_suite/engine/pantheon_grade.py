"""PANTHEON colour grade — ``scripts/colorcorrect.fs`` overrides in a pk3.

Mechanism (proven, free_wins_proof.md proof 3): ``colorcorrect.fs`` ships
inside ``pak00.pk3`` and is compiled from the game VFS at renderer init
(``R_InitFragmentShader``, tr_init.c:610). A pk3 in the wolfcam GAMEDIR
beats ``baseq3``, and a ``zzz_*`` name sorts after the ``zzz_uhd_*`` texture
packs, so dropping one file into ``zzz_zz_pantheon_grade.pk3`` replaces the
whole post-process stage. Same override convention as
``pantheon_ads.py``/ENG-2.

HARD constraint, and it is a hard ENGINE ABORT rather than a silent no-op:
``RB_ColorCorrect`` (tr_backend.c:1092) resolves FOUR uniforms —
``backBufferTex``, ``p_gammaRecip``, ``p_overbright``, ``p_contrast`` — and
calls ``ri.Error(ERR_FATAL, ...)`` if any lookup fails. GLSL compilers strip
uniforms that the shader never reads, so every variant here must genuinely
CONSUME all four. ``_STOCK_PREAMBLE`` and the mandatory
``gammaColor``/``contrastColor`` computation exist for that reason and must
not be "optimised away"; ``assert_consumes_all_uniforms`` is the guard.

Three formal grades, and ``GRADE_ORIGINAL`` is deliberately a REAL variant
that writes the stock math verbatim rather than meaning "ship no pk3".
That way an A/B/C look comparison runs all three through the identical
override code path and the only difference between frames is the colour
maths — not "pk3 present vs absent", which would confound the comparison
with search-path and shader-recompile differences.

The look is a grade, not a stunt: gentle S-curve contrast, controlled
desaturation, a cool/warm split-tone, and a light vignette. Explicitly NOT
orange-and-teal blockbuster. Quake readability is a constraint, not a
preference — shadows are LIFTED before the curve so an enemy in a dark
corner does not disappear, and the vignette is capped well short of
darkening anything a player would need to see.
"""
from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PK3_NAME = "zzz_zz_pantheon_grade.pk3"
SHADER_PATH = "scripts/colorcorrect.fs"

GRADE_ORIGINAL = "GRADE_ORIGINAL"
GRADE_PANTHEON_SUBTLE = "GRADE_PANTHEON_SUBTLE"
GRADE_PANTHEON_HERO = "GRADE_PANTHEON_HERO"
GRADES = (GRADE_ORIGINAL, GRADE_PANTHEON_SUBTLE, GRADE_PANTHEON_HERO)

# Every uniform RB_ColorCorrect resolves. A variant that fails to reference
# one of these compiles fine and then kills the engine at renderer init.
REQUIRED_UNIFORMS = ("backBufferTex", "p_gammaRecip", "p_overbright",
                     "p_contrast")

_STOCK_PREAMBLE = """\
uniform sampler2DRect backBufferTex;
uniform float p_gammaRecip;
uniform float p_overbright;
uniform float p_contrast;

const vec3 avgLuminance = vec3(0.5, 0.5, 0.5);
"""

# The stock body, byte-for-byte equivalent to pak00's shipped shader.
_ORIGINAL_BODY = """\
void main()
{
    vec4 backBuffer = texture2DRect( backBufferTex, gl_TexCoord[0].xy );
    vec3 gammaRecipVec = vec3(p_gammaRecip, p_gammaRecip, p_gammaRecip);
    vec3 gammaColor = p_overbright * pow( backBuffer.rgb, gammaRecipVec );
    vec3 contrastColor = mix( avgLuminance, gammaColor, p_contrast );
    gl_FragColor = vec4( contrastColor, 1.0 );
}
"""

# Per-grade look constants. Kept as a table so the two PANTHEON variants are
# provably the same maths at two strengths — SUBTLE is not a different look,
# it is the same look turned down, which is what makes an intensity ladder
# meaningful rather than three unrelated grades.
_LOOK = {
    GRADE_PANTHEON_SUBTLE: {
        "saturation": 0.92,      # controlled desaturation, not a bleach
        "contrast_s": 0.10,      # S-curve strength around mid grey
        "shadow_lift": 0.012,    # protect Quake visibility in dark corners
        "cool_shadow": (-0.010, 0.000, 0.022),   # shadows toward steel blue
        "warm_high": (0.020, 0.006, -0.014),     # highlights toward warm
        "vignette": 0.14,        # gentle
    },
    # Retuned after frame review: at contrast_s 0.18 / sat 0.86 the HERO
    # grade was measurably present but visually indistinguishable from
    # SUBTLE (0.0% of pixels differed by >8 at t=0.45), which makes it a
    # label rather than a level. Strengthened until the two rungs are
    # actually separable, while staying inside the same restraint envelope
    # the tests enforce (sat >= 0.80, vignette <= 0.35, tint <= 0.05).
    GRADE_PANTHEON_HERO: {
        "saturation": 0.80,
        "contrast_s": 0.34,
        "shadow_lift": 0.022,
        "cool_shadow": (-0.028, 0.000, 0.048),
        "warm_high": (0.046, 0.014, -0.034),
        "vignette": 0.32,
    },
}


def _pantheon_body(look: dict, width: int, height: int) -> str:
    cs, wh = look["cool_shadow"], look["warm_high"]
    return f"""\
// PANTHEON grade. Screen size is baked because gl_TexCoord[0].xy is in
// PIXELS for sampler2DRect, so a normalised vignette needs the resolution.
const vec2  screenSize = vec2({width}.0, {height}.0);
const vec3  lumaWeights = vec3(0.2126, 0.7152, 0.0722);
const float saturation  = {look['saturation']};
const float contrastS   = {look['contrast_s']};
const float shadowLift  = {look['shadow_lift']};
const vec3  coolShadow  = vec3({cs[0]}, {cs[1]}, {cs[2]});
const vec3  warmHigh    = vec3({wh[0]}, {wh[1]}, {wh[2]});
const float vignette    = {look['vignette']};

void main()
{{
    // --- stock stage: all four required uniforms genuinely consumed ---
    vec4 backBuffer = texture2DRect( backBufferTex, gl_TexCoord[0].xy );
    vec3 gammaRecipVec = vec3(p_gammaRecip, p_gammaRecip, p_gammaRecip);
    vec3 gammaColor = p_overbright * pow( backBuffer.rgb, gammaRecipVec );
    vec3 color = mix( avgLuminance, gammaColor, p_contrast );

    // --- shadow lift FIRST: never crush detail we then try to grade ---
    color = shadowLift + color * (1.0 - shadowLift);

    // --- gentle S-curve around mid grey (smoothstep, not a hard pow) ---
    vec3 sCurve = smoothstep(0.0, 1.0, color);
    color = mix(color, sCurve, contrastS);

    // --- controlled desaturation against true luma ---
    float luma = dot(color, lumaWeights);
    color = mix(vec3(luma), color, saturation);

    // --- split tone: cool the shadows, warm the highlights ---
    color += coolShadow * (1.0 - luma) + warmHigh * luma;

    // --- light vignette, floored so nothing gameplay-relevant goes black --
    vec2 uv = gl_TexCoord[0].xy / screenSize;
    float r = length(uv - vec2(0.5, 0.5)) * 1.41421356;
    color *= 1.0 - vignette * smoothstep(0.55, 1.0, r);

    gl_FragColor = vec4( clamp(color, 0.0, 1.0), 1.0 );
}}
"""


def shader_source(grade: str, width: int = 1920, height: int = 1080) -> str:
    if grade not in GRADES:
        raise ValueError(f"unknown grade {grade!r}; expected one of {list(GRADES)}")
    header = f"// {grade} -- PANTHEON scene canary 01\n"
    if grade == GRADE_ORIGINAL:
        return header + _STOCK_PREAMBLE + "\n" + _ORIGINAL_BODY
    return header + _STOCK_PREAMBLE + "\n" + _pantheon_body(
        _LOOK[grade], width, height)


def assert_consumes_all_uniforms(source: str) -> None:
    """Guard against the ERR_FATAL failure mode described in the docstring.

    A uniform that is DECLARED but never READ is stripped by the GLSL
    compiler and then fails ``qglGetUniformLocation``, which is a fatal
    engine abort — so a declaration alone is not enough; each name must
    appear at least twice (declaration + at least one use).
    """
    for name in REQUIRED_UNIFORMS:
        if source.count(name) < 2:
            raise ValueError(
                f"grade shader declares {name!r} but never reads it — the GLSL "
                "compiler will strip it and RB_ColorCorrect will "
                "ri.Error(ERR_FATAL) at renderer init")


def build_pack(grade: str, gamedir: Path, width: int = 1920,
               height: int = 1080) -> Path:
    """Write ``<gamedir>/zzz_zz_pantheon_grade.pk3`` holding one shader."""
    source = shader_source(grade, width, height)
    assert_consumes_all_uniforms(source)
    path = Path(gamedir) / PK3_NAME
    # ZIP_STORED + a fixed date_time keeps the pk3 byte-deterministic, so a
    # runtime manifest's grade_pack hash means "this grade", not "this build
    # ran at this second".
    info = zipfile.ZipInfo(SHADER_PATH, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_STORED
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(info, source.encode("ascii"))
    return path


def remove_pack(gamedir: Path) -> None:
    """Drop the override so the next capture uses pak00's stock shader."""
    path = Path(gamedir) / PK3_NAME
    if path.exists():
        path.unlink()


def grade_hash(grade: str, width: int = 1920, height: int = 1080) -> str:
    return hashlib.sha256(
        shader_source(grade, width, height).encode("ascii")).hexdigest()
