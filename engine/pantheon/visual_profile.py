"""VisualProfile — how footage should LOOK, said in film words.

A caller asks for `ENEMY_READABLE`. It does not know that the enemy model is
a cvar, that colour is one 0xRRGGBB integer rather than a triple, that some
of these are latched and must ride the command line, or that the teammate
family is a separate set of cvars from the enemy family. All of that is the
backend's business and lives behind `CapabilityRegistry`.

THE REVIEW PROFILE, IN THE USER'S WORDS. Ordinary review footage must make
the enemy unmistakable: Keel, the bright skin, strong green. Teammates do
NOT become Keel. The recorder does NOT become Keel. Those three are
controlled by three different things and a profile that cannot say so is not
a profile.

WHAT A PROFILE CANNOT DO. `resolve()` returns cvars only for capabilities
the backend has EXECUTION_PROVEN; anything weaker raises rather than writing
a cvar the engine will accept and ignore. That refusal is the whole point:
this project has three times concluded "the enemy is green" from a cfg that
the client silently discarded.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from engine.pantheon import capabilities as CAP


class Appearance(Enum):
    """Who a body looks like."""
    AUTHENTIC = "AUTHENTIC"          # exactly what the demo authored
    READABLE = "READABLE"            # forced to the review silhouette
    UNCHANGED = "UNCHANGED"          # leave whatever the client has


class WorldExposure(Enum):
    AUTHENTIC = "AUTHENTIC"
    REVIEW_DARK_READABLE = "REVIEW_DARK_READABLE"   # lift the dark maps


class Hud(Enum):
    AUTHENTIC = "AUTHENTIC"
    REVIEW_MINIMAL = "REVIEW_MINIMAL"   # no names, no obituaries, no gun
    NONE = "NONE"


# The review silhouette, as film direction rather than engine values.
KEEL = "keel"
BRIGHT = "bright"
PANTHEON_GREEN = (60, 235, 90)      # readable on grey arena stone, and not
                                    # the nuclear 0x00ff00 of the first test


@dataclass(frozen=True)
class VisualProfile:
    """One look. Every field is a film statement; none is an engine value."""
    name: str
    enemy: Appearance = Appearance.AUTHENTIC
    teammate: Appearance = Appearance.AUTHENTIC
    self_view: Appearance = Appearance.AUTHENTIC
    enemy_model: str = KEEL
    enemy_skin: str = BRIGHT
    enemy_colour: tuple[int, int, int] = PANTHEON_GREEN
    world_exposure: WorldExposure = WorldExposure.AUTHENTIC
    hud: Hud = Hud.AUTHENTIC
    xray_enemy: bool = False
    xray_colour: tuple[int, int, int] = PANTHEON_GREEN
    # THE OVERLAY ALPHA IS 0-255, NOT A FRACTION.
    #
    # The engine registers cg_whAlpha and cg_whEnemyAlpha with a default of
    # 30, and the 2026-09-05 proof that put this capability in the registry
    # used 190. This profile wrote 0.55, meaning "55 per cent" -- which the
    # engine read as an alpha of zero, so the overlay drew nothing at all and
    # the first end-to-end recipe came back with an empty frame twice.
    xray_alpha: int = 190
    extra: dict[str, Any] = field(default_factory=dict)

    # -- what this profile needs a backend to be able to do -------------
    def required_capabilities(self) -> list[str]:
        need: list[str] = ["BEAUTY_PASS"]
        if self.enemy is Appearance.READABLE:
            need += ["FORCE_ENEMY_MODEL", "FORCE_ENEMY_SKIN", "FORCE_ENEMY_COLOUR"]
        if self.teammate is Appearance.READABLE:
            need += ["FORCE_TEAM_MODEL", "FORCE_TEAM_SKIN", "FORCE_TEAM_COLOUR"]
        if self.xray_enemy:
            need.append("XRAY_PLAYER")
        return need

    def check(self, backend: str = "WOLFCAM_REFERENCE") -> list[CAP.Capability]:
        """Raises CapabilityUnavailable on the first thing the backend cannot
        actually do. Call before rendering, not after."""
        return [CAP.require(n, backend) for n in self.required_capabilities()]

    # -- the one place film words become engine values ------------------
    def resolve(self, backend: str = "WOLFCAM_REFERENCE") -> dict[str, Any]:
        """Backend values for this look. The ONLY function in the project
        allowed to turn a profile into cvars."""
        self.check(backend)
        from engine.pantheon.color_format import format_for

        c: dict[str, Any] = {}

        # SELF and TEAMMATE are left alone unless asked: clearing the whole
        # family is what makes the demo's own characters survive. A stale
        # q3config once held cg_enemyHeadModel "keel/bright" and every player
        # rendered as the same flat figure.
        if self.enemy is Appearance.AUTHENTIC:
            c.update({"cg_enemyModel": '""', "cg_enemyHeadModel": '""',
                      "cg_enemyLegsSkin": '""', "cg_enemyTorsoSkin": '""',
                      "cg_enemyHeadSkin": '""'})
        elif self.enemy is Appearance.READABLE:
            model = f"{self.enemy_model}/{self.enemy_skin}"
            c.update({"cg_enemyModel": f'"{model}"',
                      "cg_enemyHeadModel": f'"{model}"',
                      "cg_enemyLegsSkin": f'"{self.enemy_skin}"',
                      "cg_enemyTorsoSkin": f'"{self.enemy_skin}"',
                      "cg_enemyHeadSkin": f'"{self.enemy_skin}"'})
            for part in ("Legs", "Torso", "Head"):
                cvar = f"cg_enemy{part}Color"
                c[cvar] = format_for(cvar, self.enemy_colour)

        if self.teammate is Appearance.AUTHENTIC:
            c.update({"cg_teamModel": '""', "cg_teamHeadModel": '""',
                      "cg_teamLegsSkin": '""', "cg_teamTorsoSkin": '""',
                      "cg_teamHeadSkin": '""'})

        # cg_forceModel would override EVERY player, self and teammate
        # included, so a profile that distinguishes them must turn it off.
        if self.enemy is not Appearance.UNCHANGED or self.teammate is not Appearance.UNCHANGED:
            c["cg_forceModel"] = 0

        if self.hud is Hud.REVIEW_MINIMAL:
            c.update({"cg_draw2D": 1, "cg_drawGun": 0, "cg_drawFPS": 0,
                      "cg_drawSpeed": 0,
                      # names must never burn in: these are DURATIONS, not booleans
                      "cg_obituaryTime": 0, "cg_drawFragMessageTime": 0,
                      "cg_drawCrosshairNames": 0, "cg_drawPlayerNames": 0,
                      "cg_drawTeamOverlay": 0, "cg_scoreBoardWhenDead": 0})
        elif self.hud is Hud.NONE:
            c["cg_draw2D"] = 0

        if self.world_exposure is WorldExposure.REVIEW_DARK_READABLE:
            c.update({"r_mapoverbrightbits": 3, "r_intensity": 1.5})

        c["cg_wh"] = 1 if self.xray_enemy else 0
        if self.xray_enemy:
            # THE X-RAY FAMILY DOES NOT TAKE THE RAIL FAMILY'S SYNTAX. The
            # rail colours are read as a packed integer and accept 0xRRGGBB;
            # the wh colours go through SC_ParseColorFromStr, which rejects
            # anything that is not digits and spaces. Writing hex here is a
            # SILENT no-op -- the overlay draws in whatever colour was already
            # set -- which is precisely what color_format exists to stop, and
            # what this profile was doing until 2026-09-06.
            from engine.pantheon import color_format as CF
            for name in ("cg_whEnemyColor", "cg_whColor"):
                c[name] = CF.format_for(name, self.xray_colour)
            c.update({"cg_whEnemyAlpha": self.xray_alpha,
                      "cg_whAlpha": self.xray_alpha})
        c.update(self.extra)
        return c

    def as_dict(self) -> dict:
        return {"name": self.name, "enemy": self.enemy.value,
                "teammate": self.teammate.value, "self_view": self.self_view.value,
                "enemy_model": self.enemy_model, "enemy_skin": self.enemy_skin,
                "enemy_colour": list(self.enemy_colour),
                "world_exposure": self.world_exposure.value, "hud": self.hud.value,
                "xray_enemy": self.xray_enemy,
                "requires": self.required_capabilities()}


# ── the named profiles ─────────────────────────────────────────────────────

AUTHENTIC = VisualProfile(
    "AUTHENTIC",
    enemy=Appearance.AUTHENTIC, teammate=Appearance.AUTHENTIC,
    self_view=Appearance.AUTHENTIC, hud=Hud.REVIEW_MINIMAL)

REVIEW = VisualProfile(
    "REVIEW",
    # The enemy is unmistakable. Nobody else changes.
    enemy=Appearance.READABLE, enemy_model=KEEL, enemy_skin=BRIGHT,
    enemy_colour=PANTHEON_GREEN,
    teammate=Appearance.AUTHENTIC, self_view=Appearance.AUTHENTIC,
    world_exposure=WorldExposure.REVIEW_DARK_READABLE, hud=Hud.REVIEW_MINIMAL)

REVIEW_XRAY = VisualProfile(
    "REVIEW_XRAY",
    enemy=Appearance.READABLE, teammate=Appearance.AUTHENTIC,
    self_view=Appearance.AUTHENTIC, world_exposure=WorldExposure.REVIEW_DARK_READABLE,
    hud=Hud.REVIEW_MINIMAL, xray_enemy=True)

PROFILES = {p.name: p for p in (AUTHENTIC, REVIEW, REVIEW_XRAY)}


def profile(name: str) -> VisualProfile:
    if name not in PROFILES:
        raise KeyError(f"no visual profile {name!r}; known: {sorted(PROFILES)}")
    return PROFILES[name]
