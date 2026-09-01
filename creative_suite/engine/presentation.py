"""Camera mode -> capture profile (directive 3-5).

THE HARD RULE. Anything that is not first person renders CINEMATIC_CLEAN:
zero HUD. No weapon overlay, crosshair, status, frag message, kill feed,
medals, scoreboard, notify or console. FPV keeps the restrained gameplay
feedback the V2 master profile already defines.

WHY THIS IS A RESOLVER AND NOT ANOTHER PROFILE. The clean profiles exist
and already provide the zero-HUD state; what was missing was the
integration. ``build_capture_cfg`` exec'd ``PROFILE_NAME`` for every
capture regardless of camera, which is how a PROJECTILE shot came back
with "You fragged" burned into it. The profile is now a FUNCTION of the
camera mode, and a non-FPV camera paired with a gameplay-HUD profile is an
error rather than a picture.

The resolved profile is part of the visual identity: the same camera under
a different HUD is a different frame.
"""
from __future__ import annotations

from creative_suite.engine import master_profile

FPV_MODES = frozenset({"FPV"})
CINEMATIC_MODES = frozenset({
    "PROJECTILE", "SIDE", "LEAD", "CHASE", "ORBIT", "FREECAM",
    "THIRD_PERSON", "FOLLOW", "SPLINE"})

# The two presentations, named for what the viewer sees rather than for a
# cfg filename, so the mapping to a profile can change without renaming
# every call site.
FPV_GAMEPLAY = "FPV_GAMEPLAY"
CINEMATIC_CLEAN = "CINEMATIC_CLEAN"
PRESENTATIONS = (FPV_GAMEPLAY, CINEMATIC_CLEAN)

# Verified against master_profile.PROFILES, not taken from a prompt.
PROFILE_FOR = {
    FPV_GAMEPLAY: master_profile.PROFILE_NAME,        # TR4SH_GAMEPLAY_MASTER_V2
    CINEMATIC_CLEAN: "TR4SH_MASTER_POV_CLEAN",
}

# A profile is "gameplay HUD" when it draws the 2D layer at all. Anything
# with cg_draw2D 0 is clean by construction; the frag-message and kill-feed
# gates are TIME cvars and are covered by the same switch.
HUD_CVARS = ("cg_draw2D", "cg_drawGun", "cg_drawCrosshair", "cg_drawStatus",
             "cg_drawFragMessageTime", "cg_obituaryTime", "con_notifytime")


class InvalidPresentation(ValueError):
    """A camera/profile pairing that must not render."""


def presentation_for(camera_mode: str) -> str:
    mode = str(camera_mode).upper()
    if mode in FPV_MODES:
        return FPV_GAMEPLAY
    if mode in CINEMATIC_MODES:
        return CINEMATIC_CLEAN
    raise InvalidPresentation(f"unknown camera mode: {camera_mode}")


def profile_for(camera_mode: str) -> str:
    """The capture profile a camera mode must use."""
    return PROFILE_FOR[presentation_for(camera_mode)]


def profile_draws_hud(profile: str) -> bool:
    cvars = master_profile.PROFILES[profile]
    return int(cvars.get("cg_draw2D", 0)) != 0


def validate(camera_mode: str, profile: str) -> str:
    """Reject a non-FPV camera under a HUD profile. Returns the profile."""
    if profile not in master_profile.PROFILES:
        raise InvalidPresentation(f"unknown profile: {profile}")
    if presentation_for(camera_mode) == CINEMATIC_CLEAN and profile_draws_hud(profile):
        raise InvalidPresentation(
            f"{camera_mode} is a cinematic camera and must capture "
            f"CINEMATIC_CLEAN; {profile} draws the HUD "
            f"(cg_draw2D={master_profile.PROFILES[profile].get('cg_draw2D')})")
    return profile


def cfg_file_for(camera_mode: str) -> str:
    return master_profile._CFG_FILES[profile_for(camera_mode)]


def hud_expectation(camera_mode: str) -> dict:
    """What a frame from this camera is allowed to contain -- for QA."""
    p = presentation_for(camera_mode)
    return {"presentation": p,
            "hud_allowed": p == FPV_GAMEPLAY,
            "profile": PROFILE_FOR[p],
            "profile_id": master_profile.profile_id(PROFILE_FOR[p])}
