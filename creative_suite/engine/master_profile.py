"""Frozen capture/analysis profiles for pTn.Tr4sH V2 masters.

Four deliberate profiles (definitive-master mandate B1-B4), one cfg each,
written into the staging game dir. Every generated AVI records
capture_profile_id = sha256(cfg + launch sets)[:12] — no session drift.

Evidence base (output/demo_v2/_bench + docs/reference/moviemaking-feature-
matrix.md, 2026-08-30):
  codec  : MJPEG q90 (q80 smears floor speckle; huffyuv 196MB/s and raw
           376MB/s rejected on size; ffmpeg FFV1 pipe is documented working
           in source but the bench attempt silently fell back to the AVI
           writer — deferred, not used for masters)
  AA     : r_useFbo + 4x MSAA; ALSO structurally removes external overlay
           contamination (NVIDIA toast present in window-framebuffer capture,
           absent in FBO capture of the same scene)
  FOV    : 90/105/115/122 benchmarked on the same fight; 115 frozen — best
           speed/context gain with targets still clearly readable.
           cg_useDemoFov is a protocol>=91 no-op on our .dm_73 corpus.
  clean  : cg_drawGun 0 preserves the LG beam explicitly
           (cg_weapons.c:2800-2811); killfeed/frag-message have TIME gates
           (cg_obituaryTime / cg_drawFragMessageTime), not booleans; follow
           text needs cg_drawFollowing AND wolfcam_drawFollowing.
  memory : LAA flag on staged exe + com_zoneMegs 96 / com_hunkMegs 256
           (UHD set Z_Malloc crash at defaults; VM_Create fail at hunk 512
           without LAA)
  renderer: gl1 (cl_renderer default) — mature FBO+mme path, faithful QL look.

MME capability audit: motion blur SUPPORTED (mme_blurFrames accumulation;
cl_aviFrameRateDivider is DECIMATION, leave 1); DoF SUPPORTED (mme_dof* +
keyframed dof cmd); q3mme camera paths SUPPORTED (catmullrom/bezier smoothing,
quaternion angles, CAM_FOV channel); depth passes SUPPORTED (mme_saveDepth);
supersampling = MSAA-in-FBO only. Gameplay masters stay clean — no baked
blur/DoF; those belong to TR4SH_CINEMATIC_REPLAY.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from creative_suite.engine.wolfcam_capture import write_engine_file

REPO_ROOT = Path(__file__).resolve().parents[2]

WOLFCAM_VERSION = "wolfcamql-11.3+laa"
RESOLUTION = (1920, 1080)
FPS = 60
CODEC = "mjpeg"
JPEG_QUALITY = 90
MASTER_POV_FOV = 115

# LATCH cvars -> command line +set (renderer reads them once at startup).
LAUNCH_SETS = {
    "r_picmip": 0,
    "r_texturebits": 32,
    "r_colorbits": 32,
    "r_ext_max_anisotropy": 16,
    "r_ext_compressed_textures": 0,
    "r_detailtextures": 1,
    "r_simpleMipMaps": 0,
    "r_roundImagesDown": 0,
    "r_ignorehwgamma": 1,
    "r_useFbo": 1,
    "r_fboAntiAlias": 4,
    "sv_pure": 0,
    "com_zoneMegs": 96,
    "com_hunkMegs": 256,
}

_QUALITY = {
    "cl_aviFrameRate": FPS,
    "cl_aviCodec": CODEC,
    "r_jpegCompressionQuality": JPEG_QUALITY,
    "cl_aviAllowLargeFiles": 1,
    "r_lodbias": -2,
    "r_lodCurveError": 10000,
    "r_subdivisions": 1,
    "r_vertexLight": 0,
    "r_dynamiclight": 1,
    "r_finish": 1,
    "r_textureMode": "GL_LINEAR_MIPMAP_LINEAR",
    "cg_shadows": 1,
    "cg_marks": 1,
    "cg_railQL": 1,
    "cl_noprint": 1,
    "s_volume": 1.0,
}

# B1 - the clean-frame contract: every 2D element and the gun model off,
# every world effect on (beams, trails, projectiles, explosions, models).
# Proven by bench frames pf_clean_pov / pf_clean_72.
_CLEAN_POV = {
    "cg_draw2D": 0,
    "cg_drawGun": 0,
    "cg_drawCrosshair": 0,
    "cg_drawStatus": 0,
    "cg_drawScores": 0,
    "cg_drawTimer": 0,
    "cg_drawVote": 0,
    "cg_drawTeamVote": 0,
    "cg_drawFollowing": 0,
    "wolfcam_drawFollowing": 0,
    "cg_drawSpecMessages": 0,
    "cg_drawItemPickups": 0,
    "cg_drawFragMessageTime": 0,   # frag message gate is a TIME cvar
    "cg_obituaryTime": 0,          # killfeed gate is a TIME cvar
    "cg_chatTime": 0,
    "cg_chatLines": 0,
    "con_notifytime": 0,
    "cg_drawFPS": 0,
    "cg_drawSpeed": 0,
    "cg_fov": MASTER_POV_FOV,
}

# 2A - the MAIN frag footage: HUD clutter gone, but the frag feed and a
# tuned frag confirmation stay — gameplay must not feel empty (mandate 2A/3/4).
# Feed/message styling via wolfcam's per-element cvars (cg_main.c:2253-2272).
_GAMEPLAY_MASTER = {
    **_CLEAN_POV,
    # restore the information layer, tuned
    "cg_draw2D": 1,
    "cg_obituaryTime": 2500,            # killfeed on, brisk
    "cg_drawFragMessageTime": 1800,     # confirmation on, short
    "cg_drawFragMessageScale": 0.22,    # subtle, not arcade
    "cg_drawFragMessageFadeTime": 250,
    "cg_drawFragMessageTokens": "You fragged %v",
    # keep the clutter suppressed even with draw2D on
    "cg_drawStatus": 0,
    "cg_drawScores": 0,
    "cg_drawTimer": 0,
    "cg_drawAmmoWarning": 0,
    "cg_lagometer": 0,
    "cg_drawAttacker": 0,
    "cg_drawRewards": 0,
    "cg_drawPickupItem": 0,
    "cg_weaponBar": 0,           # left ammo/weapon list (validation frame)
    "cg_drawFullWeaponBar": 0,
}

# V2 - THE gameplay master (supersedes hidden-weapon _GAMEPLAY_MASTER,
# kept as historical): weapon VISIBLE, dot crosshair, tuned feed/message,
# hit beeps ON, kill chime OFF. All cvars source-verified in
# docs/reference/visible-weapon-master-config.md.
_GAMEPLAY_MASTER_V2 = {
    **_CLEAN_POV,               # start from full suppression, re-enable below
    "cg_draw2D": 1,
    "cg_drawGun": 1,            # visible with natural bob; 2 = steady variant
    "cg_gunX": 0, "cg_gunY": 0, "cg_gunZ": 0,
    "cg_gunSize": 1.0,
    "cg_fallKick": 1,
    # point crosshair (shape 25 = pure dot; 24 ~ 9px at 1080p)
    "cg_drawCrosshair": 25,
    "cg_crosshairSize": 24,
    "cg_crosshairColor": "0xffffff",
    "cg_crosshairAlpha": 255,
    "cg_crosshairPulse": 0,
    "cg_crosshairHealth": 0,
    # tuned frag feed (recorder-first, old-school)
    "cg_obituaryTime": 2500,
    "cg_obituaryFadeTime": 600,
    "cg_obituaryStack": 3,
    "cg_obituaryTokens": "%k %i %v",
    "cg_obituaryIconScale": 1.2,
    # tuned frag confirmation — MUST run through the SEPARATE draw path:
    # with Separate=0 the message routes through CENTER PRINT at
    # cg_drawCenterPrintScale 0.35 and every cg_drawFragMessage* tune is
    # ignored (cg_event.c:465/490/516 -> cg_draw.c:8340). This was the
    # "names too big" frag-message half of the defect.
    "cg_drawFragMessageSeparate": 1,
    "cg_drawFragMessageTime": 2000,
    "cg_drawFragMessageScale": 0.22,
    "cg_drawFragMessageFadeTime": 250,
    "cg_drawFragMessageX": 320,
    "cg_drawFragMessageY": 110,
    "cg_drawFragMessageAlign": 1,
    "cg_drawFragMessageStyle": 6,
    "cg_drawFragMessageTokens": "You fragged %v",
    # medals kept (fragmovie candy) but premium-scaled, brief, spam-capped
    "cg_drawRewards": 1,
    "cg_drawRewardsImageScale": 0.8,
    "cg_drawRewardsTime": 2000,
    "cg_drawRewardsMax": 3,
    # cinematic gait: wolfcam ships all view bob at 0 (competitive
    # convention); original Q3 values restore the filmed-from-the-eyes feel
    "cg_bobup": 0.005,
    "cg_bobpitch": 0.002,
    "cg_bobroll": 0.002,
    # damage felt, never blowing out the grade
    "cg_screenDamageAlpha": 120,
    # world reads better on 60fps cuts
    "cg_railTrailTime": 600,
    "cg_markTime": 20000,
    # audio: hits audible, kill chime gone (cg_event.c:120-124 separation)
    "cg_hitBeep": 2,
    "cg_killBeep": 0,
    "s_killBeepVolume": 0,
    # MOVIEMAKING de-gaming (user frame review 2026-08-31): authentic
    # player models instead of forced bright keel, no floating names, no
    # oversized friend sprites, ad boards neutralized (ad_content textures
    # are not shipped -> beige panels otherwise)
    "cg_enemyModel": "",
    "cg_teamModel": "",
    "cg_forceModel": 0,
    "cg_drawPlayerNames": 0,
    "cg_drawFriend": 0,
    # ads RENDER — boards carry PANTHEON branding via zzz_pantheon_ads.pk3
    # (creative_suite/engine/pantheon_ads.py); override stays available as a
    # kill-switch if a map requests an aspect the pack does not cover
    "cg_adShaderOverride": 0,
    "cg_enemyRailColor1": "",
    "cg_enemyRailColor2": "",
    # center-screen kill notice ("<killer> <icon> <victim>") was the
    # oversized floating name in the defect frame; the small top-left obit
    # feed already carries this information
    "cg_drawCenterPrint": 0,
    # top-right follow bar (name/location/health/ammo) is spectator UI
    "cg_drawTeamOverlay": 0,
    # names of players passing under the crosshair, drawn center-screen —
    # THE oversized floating names in the defect frame (fading draws of
    # consecutive targets overlap into a ghosted jumble)
    "cg_drawCrosshairNames": 0,
    "cg_drawCrosshairTeammateHealth": 0,
    # scoreboard never pops (auto-shows on death / round end / warmup /
    # intermission in CA demos) and console notify lines stay dark
    "cg_scoreBoardWhenDead": 0,
    "cg_roundScoreBoard": 0,
    "cg_scoreBoardAtIntermission": 0,
    "cg_scoreBoardWarmup": 0,
    "con_notifylines": 0,
    # wolfcam floats a cyan self/demo-taker icon over the recorder's corpse
    # while dead (validation frame sb_death2) — off for movie footage
    "cg_drawSelf": 0,
    # clutter that returns with cg_draw2D 1 (weapon bar seen in fov grid)
    "cg_weaponBar": 0,
    "cg_drawFullWeaponBar": 0,
    "cg_drawAmmoWarning": 0,
    "cg_lagometer": 0,
    "cg_drawAttacker": 0,
    "cg_drawPickupItem": 0,
    # fov frozen from the VISIBLE-GUN benchmark grid (v2fov_grid.png):
    # 115 stretches the gun; 110 = build design point, keeps speed feel.
    "cg_fov": 110,
}

# B2 - verification profile: enough HUD to prove POV/frag/health on screen.
_REFERENCE_POV = {
    "cg_draw2D": 1,
    "cg_drawGun": 1,
    "cg_drawStatus": 1,
    "cg_drawFPS": 0,
    "cg_drawSpeed": 0,
    "cg_drawItemPickups": 0,
    "cg_fov": MASTER_POV_FOV,
}

# B3 - later premium alternate-angle pass; documented, not used by the batch.
_CINEMATIC_REPLAY = {
    **_CLEAN_POV,
    "mme_blurFrames": 8,           # accumulation sub-frames per output frame
    "mme_blurType": "gaussian",
    "cl_aviFrameRateDivider": 1,   # divider is DECIMATION - keep 1 with blur
    "mme_dofFrames": 0,            # enable per shot with the dof command
    "cg_railTrailTime": 1200,      # longer cinematic rail persistence
}

# B4 - archive-wide analysis rendering: speed over beauty; projection math
# (fov) must match masters so screen-space measurements transfer.
_ANALYSIS_HEADLESS = {
    "cg_draw2D": 0,
    "cg_drawGun": 0,
    "cg_fov": MASTER_POV_FOV,
    "s_volume": 0.0,
    "cg_shadows": 0,
    "cg_marks": 0,
    "r_dynamiclight": 0,
    "cl_aviFrameRate": 30,
    "cl_aviCodec": "mjpeg",
    "r_jpegCompressionQuality": 60,
}

# Live-director session (Path A — docs/reference/replay-runtime-feasibility.md):
# a human physically flies freecam in a VISIBLE wolfcam window. Based on
# _CLEAN_POV (no HUD clutter — the user is looking at the world, not the
# game) with no gameplay-feed additions, since nobody is filming a POV kill
# here. cg_fov is a baseline only: creative_suite.engine.director_session
# writes an explicit `cg_fov <value>` line into the per-session cgamepostinit
# hook (after this cfg is exec'd) so the caller's requested fov always wins.
# freecam itself is armed by that same per-session hook, not by this profile
# (freecam needs a servertime seek immediately before it, which varies per
# launch and can't be a frozen cfg).
_DIRECTOR_SESSION = {
    **_CLEAN_POV,
}

# Movement review. The engine measures speed itself and can print it, which
# is ground truth where our derivation is an estimate: movement moments are
# reconstructed from inter-jump displacement, and this is the number the game
# actually had.
#
# The cvar is cg_drawSpeedometer, NOT cg_speedometer. `cg_speedometer` is the
# Quake Live client's name for it; every capture here goes through WolfcamQL,
# whose own cvar inventory lists cg_drawSpeedometer plus Scale, Pos, Format
# and Alignment. Setting the QL name in a wolfcam cfg does nothing at all.
#
# cg_draw2D must be ON or the whole 2D layer is suppressed and the readout
# with it -- which is why the clean-POV profile cannot simply have the
# speedometer added to it.
# ── the review capture profile ──────────────────────────────────────────────
# Review is not production. This view exists so a person can JUDGE a moment:
# see the enemy, read the aim, tell a wall from a floor. It is a normalized
# instrument view and is never the historical master presentation, which is
# why it carries its own profile id and its own cache identity.
#
# TWO DEFECTS THE FIRST REAL REVIEW EXPOSED, both traced to this file.
#
# ENEMIES WERE INVISIBLE-ISH. The gameplay profile sets cg_enemyModel to ""
# (line ~201), deliberately, to de-game the cinematic view. Wolfcam's own
# defaults are already what review wants -- cg_enemyModel "keel/bright" with
# cg_enemyHeadColor / TorsoColor / LegsColor at 0x2a8000, a green -- so the
# fix is to stop clearing them, not to invent a scheme.
# cg_disallowEnemyModelForTeammates defaults to 1, so teammates keep their
# own presentation and SELF / TEAMMATE / ENEMY stay distinguishable.
#
# THE PICTURE WAS BLOWN OUT. r_mapOverBrightBits defaults to 2, which
# multiplies the lightmap by four, and the profile additionally forced
# r_ignorehwgamma 1 while setting no gamma of its own. Together they push
# floors and walls to white and destroy the texture detail needed to judge
# distance, aim and composition. Both are CVAR_LATCH, so they are read at
# startup and belong on the command line, not in a live cfg.
_REVIEW_V2 = {
    # Enemy readability.
    "cg_enemyModel": "keel/bright",
    "cg_enemyHeadModel": "keel/bright",
    "cg_enemyHeadColor": "0x2a8000",
    "cg_enemyTorsoColor": "0x2a8000",
    "cg_enemyLegsColor": "0x2a8000",
    "cg_forceModel": 1,
    "cg_disallowEnemyModelForTeammates": 1,
    # Clan Arena is a team game, and cg_players.c forces red/blue TEAM SKINS
    # over the enemy model whenever cg_useDefaultTeamSkins is on
    # (cg_players.c:402 and :483). That is why the enemy stayed orange after
    # cg_enemyModel started applying: the model changed, the skin did not.
    # The enemy COLOUR block at cg_players.c:6097 is additionally gated on
    # cg_useCustomRedBlueModels != 2.
    "cg_useDefaultTeamSkins": 0,
    "cg_useCustomRedBlueModels": 0,
    # CAPTURE DETERMINISM. Wolfcam archives CVAR_ARCHIVE values into its own
    # config, so anything ever set in an interactive session survives into
    # the next launch -- a 242ups speedometer appeared in a review capture
    # that no review cvar had asked for. A review clip must look the same
    # whoever last used the engine, so every HUD element the review view does
    # not want is set explicitly rather than left to whatever was archived.
    # Movement metrics belong in the dossier, not burned into the footage.
    "cg_drawSpeed": 0,
    "cg_drawSpeedometer": 0,
    "cg_drawFPS": 0,
    "cg_lagometer": 0,
    "cg_drawAmmoWarning": 0,
    "cg_drawAttacker": 0,
    "cg_drawRewards": 0,
    "cg_drawKeys": 0,
    "cg_drawPickupItems": 0,
    # Exposure lives in REVIEW_LAUNCH_SETS below, NOT here. Every cvar that
    # controls it is CVAR_LATCH: the renderer reads it once at startup, so a
    # value written into a cfg is read, stored, and has no effect on the
    # picture. Setting r_mapOverBrightBits here would have looked like a fix
    # and changed nothing.
    # r_gamma is set in REVIEW_LAUNCH_SETS with the rest of the exposure.
}

# Command-line sets for a REVIEW capture. The exposure cvars are CVAR_LATCH
# and belong here.
#
# r_ignorehwgamma is 1 for the gameplay master -- it bakes gamma into the
# textures at load, which is deterministic for a render farm but is half of
# why the review picture is blown out. Review turns it back to the engine
# default of 0.
#
# r_mapOverBrightBits defaults to 2, a x4 lightmap multiply. 1 halves that
# rather than removing it; 0 crushes the shadowed areas the other way, which
# is the opposite failure and just as bad for judging a dark corner.
REVIEW_LAUNCH_SETS = {
    **LAUNCH_SETS,
    "r_ignorehwgamma": 0,
    "r_mapOverBrightBits": 1,
    "r_mapOverBrightBitsValue": 1.0,
    # Measured on one real frame against three alternatives, with the LG beam
    # and impact bloom masked OUT -- a whole-frame clipping number is the
    # wrong instrument, because effects are SUPPOSED to burn.
    #
    #   variant                 env mean   blown%   crushed%   contrast
    #   overbright 1 (was)          79.7     8.54       9.22       85.0
    #   overbright 0                21.8     6.03      85.79       65.8   <-- unusable
    #   overbright 0, gamma .9      20.4     5.33      86.18       63.8   <-- unusable
    #   THIS: gamma/intensity .85   65.8     6.36      16.90       76.2
    #
    # r_mapOverBrightBits 0 is the obvious next move and it is wrong: it
    # crushes 86% of the environment to near-black. Darkening through gamma
    # and intensity instead keeps the shadows readable.
    "r_intensity": 0.85,
    "r_gamma": 0.85,
}

_SPEED_REVIEW = {
    **_GAMEPLAY_MASTER_V2,
    "cg_draw2D": 1,
    "cg_drawSpeedometer": 1,
    # Noted while adding this, NOT fixed here: the other profiles carry
    # "cg_drawSpeed", which appears ZERO times in wolfcam's cvar inventory
    # while cg_drawSpeedometer appears five. It has always been a no-op.
    # Nothing is visually wrong -- the clean profiles suppress the readout
    # with cg_draw2D 0 regardless -- and correcting it would change their
    # profile_id, which is part of the proxy cache key and would orphan every
    # cached review clip. Left alone deliberately.
    "cg_drawSpeedometerScale": 1.0,
    "cg_drawSpeedometerAlignment": "center",
}

# ── the public-export capture profile ───────────────────────────────────────
# THE ONLY PROFILE THAT MAY FILM SOMETHING A STRANGER WILL SEE.
#
# public_clip_export.py promises, in its own docstring, that no name is burned
# in and that "identity travels as data, not as pixels" -- a field can be
# withheld after a vote, a pixel cannot be un-shown. That promise was made by
# the export module and then broken by this one: the export called
# wolfcam_capture.capture_demo() without a profile argument, so it captured
# with PROFILE_NAME (TR4SH_GAMEPLAY_MASTER_V2, id 091901df0daf), and that
# profile deliberately draws cg_drawFragMessageTokens "You fragged %v".
# Measured on the review proxies captured with that same id: the victim's
# handle, centred, around y 210-265 of a 1920x1080 frame, for two seconds
# after every kill.
#
# The gameplay master is NOT changed. "You fragged <name>" is a deliberate
# old-school fragmovie beat in the user's own film, where the names are the
# point. It is only wrong when the audience is strangers and the clip is a
# blind vote. Two audiences, two profiles -- the same reasoning that already
# gives review its own profile.
#
# EVERY NAME-BEARING CVAR IS RE-PINNED HERE, including ones the base profiles
# already set to 0. This profile's guarantee must be readable in one place and
# must not depend on three dicts up the inheritance chain keeping their
# current values -- a future edit to _CLEAN_POV or _GAMEPLAY_MASTER_V2 must
# not be able to quietly re-open a disclosure path.
#
# The two that were actually leaking are gated by TIME cvars, not booleans
# (the same trap noted at _CLEAN_POV): setting cg_drawFragMessage 0 or
# cg_obituary 0 would do nothing, because neither cvar exists.
_PUBLIC_EXPORT = {
    **_GAMEPLAY_MASTER_V2,
    # -- the two that were measured burning names into shipped frames --
    "cg_drawFragMessageTime": 0,     # was 2000: "You fragged %v", %v = victim
    "cg_obituaryTime": 0,            # was 2500: "%k %i %v", killer AND victim
    # -- re-pinned: every other channel that can put a handle on screen --
    "cg_drawCenterPrint": 0,
    "cg_drawCrosshairNames": 0,
    "cg_drawCrosshairTeammateHealth": 0,
    "cg_drawPlayerNames": 0,
    "cg_drawFriend": 0,
    "cg_drawTeamOverlay": 0,
    "cg_drawAttacker": 0,
    "cg_drawFollowing": 0,
    "wolfcam_drawFollowing": 0,
    "cg_drawSpecMessages": 0,
    "cg_drawSelf": 0,
    # chat and console carry names verbatim
    "cg_chatTime": 0,
    "cg_chatLines": 0,
    "con_notifytime": 0,
    "con_notifylines": 0,
    # the scoreboard is a list of names, and it pops itself on death and at
    # round end -- both of which fall inside a +/-5s public window
    "cg_scoreBoardWhenDead": 0,
    "cg_roundScoreBoard": 0,
    "cg_scoreBoardAtIntermission": 0,
    "cg_scoreBoardWarmup": 0,
    "cg_drawScores": 0,
}

FAST_REVIEW_LAUNCH_SETS = {
    **REVIEW_LAUNCH_SETS,
    "r_customwidth": 1280,
    "r_customheight": 720,
    "r_fboAntiAlias": 2,
}

PROFILES = {
    "TR4SH_FAST_REVIEW_V1": {
        **_QUALITY, **_GAMEPLAY_MASTER_V2, **_REVIEW_V2,
        "cl_aviFrameRate": 30,
        "r_jpegCompressionQuality": 80,
    },
    "TR4SH_PUBLIC_EXPORT": {**_QUALITY, **_PUBLIC_EXPORT},
    "TR4SH_REVIEW_V2": {**_QUALITY, **_GAMEPLAY_MASTER_V2, **_REVIEW_V2},
    "TR4SH_SPEED_REVIEW": {**_QUALITY, **_SPEED_REVIEW},
    "TR4SH_GAMEPLAY_MASTER_V2": {**_QUALITY, **_GAMEPLAY_MASTER_V2},
    "TR4SH_GAMEPLAY_MASTER": {**_QUALITY, **_GAMEPLAY_MASTER},   # historical
    "TR4SH_MASTER_POV_CLEAN": {**_QUALITY, **_CLEAN_POV},
    "TR4SH_REFERENCE_POV": {**_QUALITY, **_REFERENCE_POV},
    "TR4SH_CINEMATIC_REPLAY": {**_QUALITY, **_CINEMATIC_REPLAY},
    "TR4SH_ANALYSIS_HEADLESS": {**_QUALITY, **_ANALYSIS_HEADLESS},
    "TR4SH_DIRECTOR_SESSION": {**_QUALITY, **_DIRECTOR_SESSION},
}

_CFG_FILES = {
    "TR4SH_FAST_REVIEW_V1": "wolfcam_tr4sh_fast_review_v1.cfg",
    "TR4SH_PUBLIC_EXPORT": "wolfcam_tr4sh_public_export.cfg",
    "TR4SH_REVIEW_V2": "wolfcam_tr4sh_review_v2.cfg",
    "TR4SH_SPEED_REVIEW": "wolfcam_tr4sh_speed_review.cfg",
    "TR4SH_GAMEPLAY_MASTER_V2": "wolfcam_tr4sh_master_capture.cfg",
    "TR4SH_GAMEPLAY_MASTER": "wolfcam_tr4sh_gameplay_v1_historical.cfg",
    "TR4SH_MASTER_POV_CLEAN": "wolfcam_tr4sh_cinematic_clean.cfg",
    "TR4SH_REFERENCE_POV": "wolfcam_tr4sh_reference.cfg",
    "TR4SH_CINEMATIC_REPLAY": "wolfcam_tr4sh_cinematic.cfg",
    "TR4SH_ANALYSIS_HEADLESS": "wolfcam_tr4sh_analysis.cfg",
    "TR4SH_DIRECTOR_SESSION": "wolfcam_tr4sh_director_session.cfg",
}

PROFILE_NAME = "TR4SH_GAMEPLAY_MASTER_V2"   # weapon visible (display mandate)
DIRECTOR_PROFILE_NAME = "TR4SH_DIRECTOR_SESSION"
# Used for movement moments so the user sees the engine's own UPS
# beside our derived figure.
SPEED_PROFILE_NAME = "TR4SH_SPEED_REVIEW"
# The profile every review proxy is captured with. Changing it changes
# profile_id, which is part of the proxy cache key -- so old over-bright
# clips can never be served as current review clips. Regeneration is on
# demand; nothing is mass recaptured.
REVIEW_PROFILE_NAME = "TR4SH_REVIEW_V2"
# Lightweight on-demand proxies retain the review look; master captures and
# existing director capture intents keep their frozen quality settings.
FAST_REVIEW_PROFILE_NAME = "TR4SH_FAST_REVIEW_V1"
# The profile every clip that leaves this repository is captured with. It is
# separate from the batch profile on purpose: the batch profile films the
# user's own movie, where "You fragged <name>" is a deliberate beat, and this
# one films for strangers, where a name in the picture is a disclosure that
# cannot be taken back. public_clip_export.py must pass this and nothing else.
PUBLIC_EXPORT_PROFILE_NAME = "TR4SH_PUBLIC_EXPORT"


# ── capture intents ─────────────────────────────────────────────────────────
# WHAT A CAPTURE IS FOR, which is the only question a caller should have to
# answer. Everything below the intent -- which cvars, which token gates, which
# profile hash -- is this module's problem, and asking a caller to remember
# cg_drawFragMessageTokens is how a name reached a public clip in the first
# place.
#
# PUBLIC_BLIND is the load-bearing one: it is the ONLY intent whose output may
# be shown to someone outside this repository, and it is the only one that
# carries a no-identity guarantee. Every other intent films for the director or
# for the user's own movie, where names on screen are correct and wanted.
#
# Adding an intent means adding a profile, not loosening one. If a new caller
# needs public output with different framing, give it its own profile that also
# satisfies public_clip_export.assert_capture_profile_is_nameless.
CAPTURE_INTENT = {
    "PUBLIC_BLIND":      PUBLIC_EXPORT_PROFILE_NAME,   # strangers, blind vote
    "GAMEPLAY_MASTER":   PROFILE_NAME,                 # the user's own film
    "DIRECTOR_REVIEW":   REVIEW_PROFILE_NAME,          # judging a moment
    "MOVEMENT_REVIEW":   SPEED_PROFILE_NAME,           # engine UPS readout
    "DIRECTOR_SESSION":  DIRECTOR_PROFILE_NAME,        # live freecam
    "ARCHIVE_ANALYSIS":  "TR4SH_ANALYSIS_HEADLESS",    # measurement, not beauty
}

# The one intent that may leave this repository. Named separately so a reader
# does not have to infer it from a comment.
PUBLIC_INTENT = "PUBLIC_BLIND"


def profile_for_intent(intent: str) -> str:
    """Resolve a capture intent to its frozen profile name.

    Raises rather than defaulting. A typo must not silently fall back to the
    batch profile -- that fallback is the exact defect this indirection exists
    to prevent (see docs/reference/public-export-name-disclosure.md).
    """
    try:
        return CAPTURE_INTENT[intent]
    except KeyError:
        raise KeyError(
            f"unknown capture intent {intent!r}; "
            f"known: {sorted(CAPTURE_INTENT)}") from None


def cfg_text(profile: str = PROFILE_NAME) -> str:
    lines = [f"// {profile} - frozen profile ({WOLFCAM_VERSION})"]
    for k, v in PROFILES[profile].items():
        lines.append(f"seta {k} {v}" if not isinstance(v, str)
                     else f'seta {k} "{v}"')
    return "\n".join(lines) + "\n"


def launch_sets_for(profile: str = PROFILE_NAME) -> dict:
    """The command line a profile is captured with.

    Latched renderer cvars only take effect from here, so the review profile
    has its own set -- and profile_id must include it or two visually
    different captures would share a cache key and the old washed-out clips
    would keep being served.
    """
    if profile == FAST_REVIEW_PROFILE_NAME:
        return FAST_REVIEW_LAUNCH_SETS
    return REVIEW_LAUNCH_SETS if profile == REVIEW_PROFILE_NAME else LAUNCH_SETS


def profile_id(profile: str = PROFILE_NAME) -> str:
    payload = cfg_text(profile) + json.dumps(launch_sets_for(profile),
                                             sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:12]


def write(staging_gamedir: Path) -> str:
    """Write all four cfgs + the JSON record; returns the master profile id."""
    for profile, fname in _CFG_FILES.items():
        # LF-only: see wolfcam_capture.write_engine_file for why every
        # engine-parsed file goes through one writer.
        write_engine_file(staging_gamedir / fname, cfg_text(profile))
    record = {
        "wolfcam_version": WOLFCAM_VERSION,
        "resolution": f"{RESOLUTION[0]}x{RESOLUTION[1]}",
        "fps": FPS, "codec": CODEC, "jpeg_quality": JPEG_QUALITY,
        "master_pov_fov": MASTER_POV_FOV,
        "launch_sets": LAUNCH_SETS,
        "profiles": {p: {"cfg_file": _CFG_FILES[p],
                         "capture_profile_id": profile_id(p),
                         "cvars": PROFILES[p]} for p in PROFILES},
        "batch_profile": PROFILE_NAME,
    }
    out = REPO_ROOT / "output" / "demo_v2" / "master_capture_profile.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=1), encoding="utf-8")
    return profile_id()
