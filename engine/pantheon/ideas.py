"""THE DIRECTOR'S MASTER LIST, VERBATIM.

306 ideas, in the user's own words, consolidated by them on 2026-09-06 from
every dump and every addition made while the system was being built. This file
is the record. The text of an idea is never edited, never summarised into a
recipe id, and never deleted because something else now implements it.

Everything else here is ADDITIVE: a category so the list can be read by
subject, and -- where one exists -- the EffectRecipe that carries the idea's
semantics. An idea with no recipe is not a gap in the list; it is a gap in the
engine, and `unimplemented()` is the honest backlog.

The columns the director asked for are DERIVED, never stored:

    IDEA                 the verbatim text below
    CATEGORY             here
    REQUIRED TRUTH       from the linked recipe
    BEST BACKEND         from the backend planner
    STATUS               from the recipe, the capability and the proof registry
    VISUAL PROOF         from the visual proof registry
    REVIEW TAG           here, where the idea names one
    PRODUCTION PRIORITY  a human field; the machine does not rank the director

Storing a status in this file would mean editing 306 rows every time a
capability moved. Deriving it means the list cannot go stale.
"""
from __future__ import annotations

from dataclasses import dataclass

# category, recipe (or None), review tag (or None), verbatim text
_RAW: tuple[tuple[int, str, str | None, str | None, str], ...] = (
    (1, "MUSIC", None, None, "Music is a major part of the filmmaking — roughly 60% of the editorial impact in your view."),
    (2, "MUSIC", None, None, "HITS ARE BEATS — important gameplay actions should land on musical beats."),
    (3, "MUSIC", None, None, "One song can define an entire episode/movie rather than constantly changing tracks."),
    (4, "MUSIC", None, None, "Music should not wait for a frag; the song asks for a visual event, which can be movement, impact, death, transition, reveal, etc."),
    (5, "TRUTH_RULE", None, None, "Use timing manipulation to perfect an already-real opportunity rather than invent an action that never happened."),
    (6, "TIMING", None, None, "Use TRIM."),
    (7, "TIMING", "HIGH_SPEED_RETIME", None, "Use RETIME."),
    (8, "TIMING", "FREEZE_AND_EXPLAIN", None, "Use FREEZE."),
    (9, "TIMING", None, None, "Use INSERT."),
    (10, "TIMING", None, None, "Use REPLAY."),
    (11, "TIMING", None, None, "Use REPEAT."),
    (12, "TIMING", "REPLAY_STUTTER", None, "Use STUTTER."),
    (13, "TIMING", None, None, "Use OVERLAP."),
    (14, "TIMING", None, None, "Use REPLACE."),
    (15, "RECONSTRUCTION", None, None, "Use SYNTHETIC INSERTS when clearly appropriate/provenanced."),
    (16, "TIMING", "HIGH_SPEED_RETIME", None, "Use speed-scaled retiming, especially where movement/action intensity can naturally drive time treatment."),
    (17, "TIMING", None, None, "Never use “catch-up” acceleration simply to repay time borrowed by a slow-motion section."),
    (18, "EFFECT_WEIGHT", None, None, "Use very small micro-action accents for tiny gameplay moments rather than making every effect enormous."),
    (19, "EFFECT", "REPLAY_STUTTER", None, "Use image stutter as a rhythmic visual technique."),
    (20, "TRANSITION", None, None, "Use mosaic/interpolation effects for selected transitions or impacts."),
    (21, "EFFECT", None, None, "Use an optional lag/glitch visual where it fits stylistically."),
    (22, "MONTAGE", None, None, "Use semantic compression: condense long gameplay into the meaningful tactical/action information rather than random cuts."),
    (23, "MONTAGE", None, None, "Use deaths as recurring motifs, not merely failures to cut away from."),
    (24, "MONTAGE", None, None, "Use hero-then-death moments deliberately because sometimes the death completes the sequence."),
    (25, "AUDIO", None, None, "Use a rocket flyby as an audio anchor."),
    (26, "AUDIO", None, None, "Match strafe-jump/movement sounds to music."),
    (27, "TRANSITION", None, None, "Use projectile/background motion as transition material."),
    (28, "TRANSITION", None, None, "Morph one background/projectile/world state into another shot as a transition."),
    (29, "TRANSITION", None, None, "Fly the camera into an eye and emerge somewhere else."),
    (30, "TRANSITION", "PROJECTILE_FLYTHROUGH", None, "Fly into a rocket/projectile and transition through it."),
    (31, "TRANSITION", None, None, "Fly into another game-world object as a transition portal."),
    (32, "TRANSITION", None, None, "Use movement itself as a transition between clips."),
    (33, "TRANSITION", None, None, "Use doors as transitions."),
    (34, "TRANSITION", None, None, "Use teleports as transitions."),
    (35, "MONTAGE", None, None, "Match different clips using the same player position."),
    (36, "MONTAGE", None, None, "Match clips using the same weapon."),
    (37, "MONTAGE", None, None, "Match clips using the same enemy/model."),
    (38, "MONTAGE", None, None, "Build montages around repeated spatial or semantic relationships rather than only chronology."),
    (39, "CAMERA", "PIP_ALT_POV", None, "Use PIP / picture-in-picture for alternate POVs or contextual action."),
    (40, "EFFECT", None, None, "Use screens/adboards/world surfaces as places to display another shot or visual information."),
    (41, "EFFECT", None, "funny", "Use chat bubbles or game-world speech visualization where funny/useful."),
    (42, "EFFECT", None, "funny", "Use memes selectively inside the Quake visual language."),
    (43, "EFFECT", "MODEL_MORPH", None, "Use texture/skin transformations."),
    (44, "EFFECT", "WORLD_HIDE_REVEAL", None, "Use world-material transformations."),
    (45, "EFFECT", "MAP_WIREFRAME_REVEAL", None, "Have a map appear as wireframe → geometry → textures → details, essentially building the Quake world in front of the viewer."),
    (46, "EFFECT", None, None, "Use texture countdowns / world text instead of ordinary 2D titles where possible."),
    (47, "EFFECT", "LOW_HP_REACTION", None, "Let low HP affect the world/model/effect treatment."),
    (48, "EFFECT", "LOW_HP_REACTION", None, "Make critical-health situations physically/visually feel more dangerous."),
    (49, "EFFECT", "WORLD_HIDE_REVEAL", None, "Use world disappearance/reappearance as an explanatory device."),
    (50, "TACTICAL", "WORLD_HIDE_REVEAL", "clutch", "For a 1vX, reveal the situation, freeze it, remove/hide unnecessary world information, explain the remaining opponents, then restore it."),
    (51, "TACTICAL", "DIEGETIC_SCOREBOARD", "clutch", "During a 1vX, visually decrement the remaining enemy/player count as people die."),
    (52, "TACTICAL", None, None, "Use NOPE_RETREAT moments — realizing the fight is wrong and escaping."),
    (53, "TACTICAL", None, "clutch", "Use COMMIT_1VX moments — consciously committing into the outnumbered fight."),
    (54, "TACTICAL", None, None, "Use a rare-danger cross / warning device when something tactically dangerous is about to happen."),
    (55, "TRUTH_RULE", None, None, "Use a truthful damage ledger where actual damage truth exists."),
    (56, "TRUTH_RULE", None, None, "Never fake damage numbers just because they would look good."),
    (57, "TACTICAL", None, None, "Use damage-chase sequences where the camera/visual explanation follows sustained pressure through a fight."),
    (58, "TACTICAL", None, "teamplay", "Use assisted finishes as meaningful narrative moments rather than only solo kills."),
    (59, "TACTICAL", None, "rail", "Use rail cooldown/reload timing as a visual telegraph."),
    (60, "MONTAGE", None, "movement", "Show movement techniques explicitly when they are interesting, not only the final kill."),
    (61, "XRAY", "WALL_REMOVE_XRAY", None, "Use wall removal / X-ray to explain hidden spatial relationships."),
    (62, "XRAY", "XRAY_ACTOR", None, "True X-ray should keep the wall present while revealing the hidden player."),
    (63, "XRAY", "XRAY_ACTOR", None, "X-ray should disappear or change once normal line of sight exists."),
    (64, "XRAY", "XRAY_ACTOR", None, "Avoid a generic blue scan/wash or fake sci-fi overlay just because “X-ray” usually looks that way."),
    (65, "XRAY", "XRAY_ACTOR", None, "Use X-ray to explain actual tactical information: two players approaching opposite sides of a wall, hidden enemy movement, etc."),
    (66, "TACTICAL", "DIEGETIC_SCOREBOARD", None, "Use a diegetic scoreboard rather than only conventional HUD graphics."),
    (67, "TACTICAL", "DIEGETIC_SCOREBOARD", None, "Show alive state visually, e.g. 4–4 → 4–3 → 3–3, with dead players/pips going dark."),
    (68, "TACTICAL", "TACTICAL_ROUND_STORY", "teamplay", "Build pTn tactical-round stories from whole rounds rather than isolated frags."),
    (69, "CAMERA", "TACTICAL_ROUND_STORY", None, "For tactical rounds, use a high establishing camera to show teams."),
    (70, "TACTICAL", "TACTICAL_ROUND_STORY", None, "Show the teams moving into their opening positions."),
    (71, "CAMERA", "TACTICAL_ROUND_STORY", None, "Descend toward the first meaningful contact/damage."),
    (72, "CAMERA", "TACTICAL_ROUND_STORY", None, "Move into free camera/explanatory views during important tactical moments."),
    (73, "TIMING", "FREEZE_KILLER", None, "Freeze key players/relationships."),
    (74, "TACTICAL", "TACTICAL_ROUND_STORY", "teamplay", "Keep all teammates represented in an important ClanWar/round explanation."),
    (75, "TACTICAL", "TACTICAL_ROUND_STORY", None, "Use a Matrix-like tactical explanation of what players are doing."),
    (76, "TRUTH_RULE", None, None, "Only show a victory as victory if the historical round was actually won."),
    (77, "TRUTH_RULE", None, None, "If the round was lost, allow the story to end truthfully rather than inventing a win."),
    (78, "TRUTH_RULE", None, None, "Potentially show an alternate loss outcome where useful, but keep provenance clear."),
    (79, "CHARACTER", "MODEL_MORPH", None, "Use a pTn/Nauru visual morph for team identity."),
    (80, "CHARACTER", "MODEL_MORPH", None, "Use the specific Xaero CPM white → pTn/Nauru transformation idea you raised."),
    (81, "CHARACTER", None, "teamplay", "Reveal teammate identity/model as part of an effect instead of presenting everyone normally from frame one."),
    (82, "TIMING", "FREEZE_KILLER", None, "Freeze the killer after a death."),
    (83, "TIMING", "FREEZE_KILLER", None, "Freeze the player who died when the death itself is narratively useful."),
    (84, "CAMERA", "ENEMY_POV_REPLAY", "alternate POV", "Use enemy POV, with provenance clearly known."),
    (85, "CAMERA", "PIP_ALT_POV", "alternate POV", "Switch to an alternate genuine observer POV when it explains an action better."),
    (86, "CAMERA", None, None, "Use reconstructed fixed cameras where the recorded POV cannot explain the geometry."),
    (87, "RECONSTRUCTION", "PROJECTILE_FOLLOW", None, "Use synthetic/reconstructed projectile views when necessary and clearly labeled."),
    (88, "TACTICAL", "GRENADE_SEQUENCE", "grenade", "For grenade sequences, show them one grenade at a time, not an incomprehensible mosaic."),
    (89, "TACTICAL", "GRENADE_SEQUENCE", "grenade", "Grenade grammar: FPV/fire → best explanatory view → impact/result → next grenade."),
    (90, "CAMERA", "GRENADE_SEQUENCE", "grenade", "Use the genuine target POV as a preferred alternate grenade view when available."),
    (91, "CAMERA", "GRENADE_SEQUENCE", "alternate POV", "Use a genuine alternate observer POV next."),
    (92, "RECONSTRUCTION", "GRENADE_SEQUENCE", "grenade", "Use reconstructed impact/projectile views when recorded views are insufficient."),
    (93, "TACTICAL", "GRENADE_SEQUENCE", "grenade", "The objective for grenade chaos is chaos → comprehension."),
    (94, "EFFECT", None, "funny", "A grenade could visually hit someone in the chest/head."),
    (95, "EFFECT", None, "funny", "Treat a grenade like someone headbutting it."),
    (96, "EFFECT", None, "funny", "Use a football/soccer-style grenade gag where a believable gameplay moment supports it."),
    (97, "CORPUS", None, "funny", "Gauntlet + jump-pad moments are especially funny and worth surfacing."),
    (98, "CORPUS", None, "iconic", "Telefrags deserve their own documentary/special treatment."),
    (99, "CORPUS", None, "iconic", "Gauntlet kills deserve special attention because of rarity/personality."),
    (100, "TRANSITION", None, None, "A telefrag can itself be a visual transition."),
    (101, "CAMERA", "PROJECTILE_FOLLOW", None, "Use projectiles as cameras or camera guides."),
    (102, "CAMERA", "PROJECTILE_FOLLOW", "rocket", "Follow a rocket in flight."),
    (103, "CAMERA", "PROJECTILE_FLYTHROUGH", "rocket", "Fly through/along a rocket trajectory."),
    (104, "EXPLAINER", "PROJECTILE_FOLLOW", "prediction", "Use actual projectile trajectories to explain prediction."),
    (105, "EXPLAINER", None, "prediction", "Use rocket prediction moments as instructional content."),
    (106, "CORPUS", None, "prediction", "Highlight near misses where the near miss itself is impressive."),
    (107, "EXPLAINER", None, "rocket", "Treat an air rocket or highly predictive projectile as something worth explaining even before the frag."),
    (108, "CORPUS", None, "aim", "Include big mouse flicks even when they do not result in a kill."),
    (109, "CORPUS", None, "aim", "Include pixel/tiny-window shots or suggestions where visibility supports the idea."),
    (110, "CORPUS", None, "clutch", "Include clutch action even if there is no kill."),
    (111, "CORPUS", None, None, "Include moments with very high pressure/damage-like activity over a short period, while being honest that pain events do not give exact damage totals."),
    (112, "CORPUS", None, None, "Surface high-pressure / no-kill action as its own meaningful review material."),
    (113, "CORPUS", None, None, "Surface a fight where the final frag is only the ending, but the buildup was the video-worthy part."),
    (114, "REVIEW", None, "context", "Link that buildup into the same Scene rather than making it a disconnected duplicate."),
    (115, "CORPUS", None, "prediction", "Find projectile near misses even without kills."),
    (116, "CORPUS", None, "aim", "Find high-flick no-kill actions."),
    (117, "CORPUS", None, "clutch", "Find no-kill clutches."),
    (118, "CORPUS", None, "prediction", "Find predictive movement/aim that made an important action possible."),
    (119, "CORPUS", None, "movement", "Mine movement separately enough that we can discover interesting motion even when no frag anchors it."),
    (120, "CORPUS", None, "movement", "Use the complete demo corpus to understand natural Quake movement rather than authoring robotic movement ourselves."),
    (121, "RECONSTRUCTION", None, None, "Treat real demos as executable performance specifications."),
    (122, "RECONSTRUCTION", None, None, "If you show PANTHEON a player taking a jump pad and hitting a sick rocket, it should be able to extract that exact motion/action into code."),
    (123, "RECONSTRUCTION", None, None, "Preserve the player's actual map location."),
    (124, "RECONSTRUCTION", None, None, "Preserve/derive the player's model location."),
    (125, "RECONSTRUCTION", None, None, "Preserve the aim location and yaw/pitch curve."),
    (126, "RECONSTRUCTION", None, None, "Preserve weapon state."),
    (127, "RECONSTRUCTION", None, None, "Preserve projectile trajectory."),
    (128, "RECONSTRUCTION", None, None, "Preserve impact timing."),
    (129, "RECONSTRUCTION", None, None, "Preserve animations."),
    (130, "RECONSTRUCTION", None, None, "Preserve jump-pad/teleport/world interaction state."),
    (131, "RECONSTRUCTION", None, None, "Retarget that real performance onto another model such as Slash, Crash, Anarki, Keel, etc."),
    (132, "RECONSTRUCTION", "ANALYSIS_ACTOR_WALKOUT", None, "Characters in synthetic/explanatory scenes should move using real Quake performances, not generic easing curves."),
    (133, "RECONSTRUCTION", None, None, "Stop using robotic `move_to` animation as the normal character-performance system."),
    (134, "RECONSTRUCTION", None, None, "Real run → stop → turn performances should become reusable templates."),
    (135, "RECONSTRUCTION", None, "aim", "Natural aim should include real tracking, micro-corrections, flicks, overshoot, etc., not just `look_at()`."),
    (136, "TRUTH_RULE", None, None, "Movement, aim, animation, weapon, projectile and result should be treated as one connected action."),
    (137, "PRESENTER", "DIEGETIC_PRESENTER", "voice", "The narrator should physically exist inside Quake."),
    (138, "PRESENTER", "ANALYSIS_ACTOR_WALKOUT", None, "The narrator can walk through the map."),
    (139, "PRESENTER", "DIEGETIC_PRESENTER", None, "The narrator can look at the camera."),
    (140, "PRESENTER", "DIEGETIC_PRESENTER", None, "The narrator can turn toward another player."),
    (141, "PRESENTER", "DIEGETIC_PRESENTER", None, "The narrator can gesture."),
    (142, "PRESENTER", "DIEGETIC_PRESENTER", "voice", "The narrator can talk."),
    (143, "PRESENTER", "ANALYSIS_ACTOR_WALKOUT", None, "The narrator can walk toward the thing being explained."),
    (144, "AUDIO", None, "voice", "The narrator should use voice from game files where possible."),
    (145, "AUDIO", None, "voice", "Extend missing dialogue using local AI/TTS."),
    (146, "AUDIO", None, "voice", "You already have Piper/Whisper tooling and wanted that incorporated."),
    (147, "AUDIO", None, "voice", "Use actual game character voices/barks as identity anchors."),
    (148, "AUDIO", None, "voice", "Use AI-generated full sentences where the game never recorded the required line."),
    (149, "PRESENTER", "DIEGETIC_PRESENTER", "voice", "Have green Keel turn toward the camera, gesture and say “Hello, I’m the enemy.”"),
    (150, "ROSTER", "DIEGETIC_PRESENTER", None, "Use Crash as a possible tutorial/guide character, because she has actual Quake Live instructional voice assets."),
    (151, "ROSTER", None, None, "But do not use Crash as the narrator for every film."),
    (152, "ROSTER", "DIEGETIC_PRESENTER", None, "Use different iconic Quake characters as dedicated presenters for different videos/chapters."),
    (153, "ROSTER", None, "iconic", "Showcase Anarki."),
    (154, "ROSTER", None, "iconic", "Showcase Slash."),
    (155, "ROSTER", None, "iconic", "Showcase Orbb."),
    (156, "ROSTER", None, "iconic", "Showcase Keel."),
    (157, "ROSTER", None, "iconic", "Showcase Crash."),
    (158, "ROSTER", None, "iconic", "Showcase the rest of the famous/recognizable Quake roster and skins over the project."),
    (159, "ROSTER", None, None, "Let each video have its own character/personality."),
    (160, "ROSTER", None, None, "Use other models as cameos, enemies, teammates and demonstrators."),
    (161, "ROSTER", None, "legacy", "Let the character roster itself become part of showing the history/style of Quake."),
    (162, "ROSTER", None, None, "Do not paint every presenter in one universal PANTHEON skin."),
    (163, "ROSTER", None, "legacy", "Preserve the actual distinctive appearance of the different Quake heroes."),
    (164, "ROSTER", None, None, "Green Keel is a good enemy role, not necessarily the project mascot."),
    (165, "PRESENTER", None, "voice", "Potentially give different characters different speaking styles/personality."),
    (166, "AUDIO", None, "voice", "Let presenters use subtle spatial audio so they sound like they exist in the world."),
    (167, "AUDIO", None, "voice", "Pan character speech according to actor/camera position."),
    (168, "AUDIO", None, "voice", "Use modest distance attenuation."),
    (169, "AUDIO", None, "voice", "Use light room/reverb treatment without destroying speech clarity."),
    (170, "AUDIO", None, "voice", "Use optional subtitles tied directly to dialogue timing."),
    (171, "BACKEND", None, None, "Custom directional pointing can later be done in Blender if native MD3 animation cannot provide it."),
    (172, "BACKEND", None, None, "Use native animation first where it is sufficient."),
    (173, "PRESENTER", "ANALYSIS_ACTOR_WALKOUT", None, "A presenter/analysis actor can walk out of a frozen historical action."),
    (174, "TIMING", "FREEZE_AND_EXPLAIN", None, "Historical action freezes."),
    (175, "TRUTH_RULE", None, None, "Historical actors remain completely immutable."),
    (176, "PRESENTER", "ANALYSIS_ACTOR_WALKOUT", None, "A separate analysis/presenter client appears."),
    (177, "PRESENTER", "ANALYSIS_ACTOR_WALKOUT", None, "That actor walks around the frozen scene."),
    (178, "PRESENTER", "DIEGETIC_PRESENTER", None, "That actor turns to us and explains what happened."),
    (179, "EXPLAINER", None, None, "Tactical lines/arrows can appear in world space."),
    (180, "PRESENTER", "ANALYSIS_ACTOR_WALKOUT", None, "Then the explanatory actor leaves/disappears."),
    (181, "TIMING", "FREEZE_AND_EXPLAIN", None, "Historical action resumes exactly where it stopped."),
    (182, "TRUTH_RULE", None, None, "The explanatory actor must not affect alive counts."),
    (183, "TRUTH_RULE", None, None, "Must not affect score."),
    (184, "TRUTH_RULE", None, None, "Must not create real damage or obituaries."),
    (185, "TRUTH_RULE", None, None, "Must remain clearly separate from historical truth."),
    (186, "PRESENTER", None, None, "Support both ANALYSIS COPY of the historical actor and an independent PRESENTER character."),
    (187, "PRESENTER", "ANALYSIS_ACTOR_WALKOUT", None, "Example: historical Keel remains frozen while Crash walks in and explains him."),
    (188, "TIMING", None, None, "The analysis/presenter timeline should advance while historical server time stays frozen."),
    (189, "CAMERA", None, None, "Camera should also move during that frozen edit-time interval."),
    (190, "AUDIO", None, "voice", "Dialogue should run on the same edit-time clock."),
    (191, "EXPLAINER", None, None, "Analytical graphics should run on the same clock."),
    (192, "CAMERA", None, None, "Use a camera orbit around frozen action."),
    (193, "CAMERA", None, None, "Use camera movement as a teaching device, not just decoration."),
    (194, "CAMERA", None, None, "The camera can approach the presenter after they perform a real entrance."),
    (195, "TRUTH_RULE", None, None, "Don't distort a good real movement trace simply to bring the actor closer to camera."),
    (196, "CAMERA", None, None, "Keep the actual tactical relationship in frame behind/around the presenter."),
    (197, "CAMERA", None, None, "For a Keel→target explanation, ensure both source and target remain readable."),
    (198, "CAMERA", None, None, "Camera geometry must respect actual BSP collision."),
    (199, "CAMERA", None, None, "Camera line-of-sight must be checked separately from collision."),
    (200, "CAMERA", None, None, "Camera composition must also be checked separately from both."),
    (201, "CAMERA", None, None, "Camera should never casually pass through a wall."),
    (202, "EXPLAINER", None, None, "World-space arrows/labels must stay anchored while both player and camera move."),
    (203, "EXPLAINER", None, None, "Use FrameTruth to drive those world-space overlays."),
    (204, "XRAY", "XRAY_ACTOR", None, "Use `XRAY` exactly when it explains a hidden tactical relationship."),
    (205, "XRAY", "XRAY_ACTOR", None, "Make X-ray disappear when the target is normally visible."),
    (206, "CAMERA", None, None, "Use a high camera when map geometry makes lower explanatory framing impossible, but it still has to feel cinematic."),
    (207, "EXPLAINER", None, None, "Create separate videos: QUAKE PRESENTATION, CLAN ARENA EXPLAINER, later PANTHEON / ARCHIVE PRESENTATION."),
    (208, "EXPLAINER", None, None, "Do not merge those three into one confused intro."),
    (209, "EXPLAINER", None, None, "The Quake presentation should explain Quake itself."),
    (210, "EXPLAINER", None, None, "The Clan Arena video should explain the mode using actual game behavior."),
    (211, "EXPLAINER", None, "legacy", "The archive/PANTHEON presentation can later explain the historical corpus/project."),
    (212, "EXPLAINER", None, None, "Do not use abstract boxes/dots as the primary way to explain Quake."),
    (213, "EXPLAINER", None, None, "The explainer must be made out of Quake itself."),
    (214, "EXPLAINER", None, None, "Use real map/player/demo imagery as the explanation."),
    (215, "EXPLAINER", "TACTICAL_ROUND_STORY", None, "Show teams physically moving inside the real map."),
    (216, "EXPLAINER", None, None, "Show one life per round through the actual sequence of action."),
    (217, "EXPLAINER", None, None, "Usually show CA as four-a-side where historically appropriate, without falsely saying every CA round is universally 4v4."),
    (218, "EXPLAINER", "DIEGETIC_SCOREBOARD", None, "Use the alive counter progression as part of teaching CA."),
    (219, "EXPLAINER", None, None, "Show the round reset afterward."),
    (220, "TIMING", None, None, "Keep the normal game largely at 1× speed during explanation."),
    (221, "TIMING", "FREEZE_AND_EXPLAIN", None, "Slow/freeze only where it helps explain something."),
    (222, "RECONSTRUCTION", None, None, "Build a whole Clan Arena teaching round synthetically when needed."),
    (223, "RECONSTRUCTION", None, None, "Use a real historical round as protocol/gameplay grammar for synthetic CA."),
    (224, "REVIEW", None, None, "Every frag exists and should be watchable."),
    (225, "REVIEW", None, None, "The machine organizes; you decide."),
    (226, "REVIEW", None, None, "Use five editorial roles rather than a simple quality score: FEATURE/FX, TRANSITION, RHYTHM/MONTAGE, KEEP NORMAL, PASS/FILLER."),
    (227, "REVIEW", None, "GOLDEN", "Preserve a separate GOLDEN flag."),
    (228, "REVIEW", None, "KEEP_CONTEXT", "Preserve KEEP_CONTEXT."),
    (229, "REVIEW", None, "WORKSHOP", "Preserve SEND TO WORKSHOP for a moment that is worth having but has bad/missing footage."),
    (230, "REVIEW", None, "WORKSHOP", "Workshop reasons can include no camera, off-screen, bad angle, obscured, etc."),
    (231, "REVIEW", None, None, "Preserve separate human tags for themes such as rail, LG, rocket, grenade, aim, prediction, movement, teamplay, clutch, multikill, funny, voice, legacy, iconic, clean POV, alternate POV, context."),
    (232, "REVIEW", None, "alternate POV", "Surface multiple POVs when the same event exists in several demos."),
    (233, "REVIEW", None, "alternate POV", "Tell you which is actor POV, victim POV, teammate POV, other observer, etc."),
    (234, "REVIEW", None, "clean POV", "Surface camera quality."),
    (235, "REVIEW", None, "alternate POV", "Let you select/use alternate POVs as part of directing."),
    (236, "CORPUS", None, "iconic", "Keep a separate telefrag documentary corpus."),
    (237, "CORPUS", None, "funny", "Have a quick gauntlet + jump-pad situation filter."),
    (238, "CORPUS", None, None, "Have a separate lane/corpus for high-pressure/no-kill actions."),
    (239, "REVIEW", None, None, "Have a separate denominator for action review rather than polluting frag progress."),
    (240, "REVIEW", None, None, "The reviewer should automatically advance after a verdict."),
    (241, "REVIEW", None, None, "Never show an already-reviewed canonical occurrence again unless deliberately requested."),
    (242, "REVIEW", None, None, "Later you changed the review order to best → worst rather than the original worst-first calibration idea."),
    (243, "REVIEW", None, None, "Prioritize your own + pTn material before unrelated players."),
    (244, "REVIEW", None, "legacy", "Keep other-player archive material available afterward."),
    (245, "REVIEW", None, None, "For a single-frag round, use the short frag proxy by default."),
    (246, "REVIEW", "MULTI_FRAG_ROUND", "context", "For a round with 2+ of your frags, automatically play the whole round as context."),
    (247, "REVIEW", None, None, "But keep T1–T5 attached to the individual frag/action, not the whole round."),
    (248, "REVIEW", "MULTI_FRAG_ROUND", None, "Within a multi-frag round, verdict F1 → seek F2 in the same round video, rather than loading a separate clip."),
    (249, "REVIEW", "MULTI_FRAG_ROUND", None, "Continue F2 → F3 → F4 through the same asset."),
    (250, "REVIEW", None, "context", "Have one persistent round/scene direction note for the whole sequence."),
    (251, "REVIEW", None, None, "Keep a separate event-specific note for one frag/action."),
    (252, "REVIEW", None, None, "This lets you write things like “music buildup through all four frags; xray F3; big finish F4” once."),
    (253, "REVIEW", None, "context", "Put meaningful non-frag actions on the same scene rail."),
    (254, "REVIEW", None, None, "Let the event rail behave like a compact storyboard."),
    (255, "REVIEW", None, "context", "Keep high-pressure buildup visible before the final frag."),
    (256, "REVIEW", None, "context", "Use round context so you can design effects/animations for the scene, not merely isolated 6-second clips."),
    (257, "REVIEW", None, None, "Reviewer should be fast, compact and low-clutter."),
    (258, "REVIEW", None, None, "Use faster review media, around 720p30, rather than master render quality."),
    (259, "REVIEW", None, None, "Keep filters collapsed by default."),
    (260, "REVIEW", None, None, "Keep deep technical detail collapsed."),
    (261, "REVIEW", None, None, "Put verdict buttons immediately next to/below the video."),
    (262, "REVIEW", None, None, "Make phone review usable without scrolling through useless information first."),
    (263, "REVIEW", None, None, "Keep essential facts immediately visible: weapon, HP/AP, accuracy/NOT DERIVABLE, F#/round, result, etc."),
    (264, "REVIEW", None, None, "Enemy should be very easy to read in review footage."),
    (265, "REVIEW", None, None, "Specifically use bright green Keel for enemy review visualization."),
    (266, "REVIEW", None, None, "Preserve teammate/self distinction."),
    (267, "TRUTH_RULE", None, "LG", "Never claim LG accuracy if it cannot be derived."),
    (268, "TRUTH_RULE", None, None, "Show `NOT DERIVABLE` instead of silently omitting information."),
    (269, "TRUTH_RULE", None, "context", "Review should use full-round context where valuable but never pretend a 0-second/one-frag extract is a full round."),
    (270, "CORPUS", None, None, "Detect fragment demos that are subsequences of longer demos."),
    (271, "CORPUS", None, "context", "Prefer the complete containing demo for round/scene context."),
    (272, "CORPUS", None, "legacy", "Preserve the fragment as potentially useful alternate/legacy footage rather than deleting it."),
    (273, "REVIEW", None, None, "Human review attaches to the canonical event, not the file."),
    (274, "CORPUS", None, None, "Use map localization from all the position data in the corpus."),
    (275, "CORPUS", None, None, "Learn real fight regions/floors from player activity."),
    (276, "CORPUS", None, None, "Learn jump-pad launch/landing areas."),
    (277, "CORPUS", None, None, "Learn teleport entrances/exits."),
    (278, "CORPUS", None, None, "Learn common routes."),
    (279, "CORPUS", None, None, "Learn combat geography."),
    (280, "CORPUS", None, None, "Use those locations in the dossier and future reconstruction."),
    (281, "RECONSTRUCTION", None, None, "Use location/map understanding to help retarget synthetic performance."),
    (282, "REVIEW", None, None, "Use the reviewer as a control room, not just a voting page."),
    (283, "REVIEW", None, None, "For each moment, show what PANTHEON understands about what happened."),
    (284, "REVIEW", None, None, "Also show what could be done with the moment."),
    (285, "REVIEW", None, None, "Potential treatments include FPV, alt POV, freecam, freeze, replay, retime, X-ray, projectile camera, wall removal, presenter, PIP, round story, reconstruction, synthetic insert, Blender candidate, etc."),
    (286, "REVIEW", None, None, "Let PANTHEON suggest compatible filmmaking treatments based on factual capabilities."),
    (287, "TRUTH_RULE", None, None, "Suggestions remain machine suggestions, never human decisions."),
    (288, "TRUTH_RULE", None, None, "Free-form human notes remain authoritative."),
    (289, "REVIEW", None, None, "Unknown crazy ideas should be stored even when the implementation route is not known yet."),
    (290, "REVIEW", None, None, "Repeated useful ideas can later become reusable Effect Recipes."),
    (291, "PROOF", None, None, "Treat visual proof as something that can be banked."),
    (292, "PROOF", None, None, "If green Keel is visually proven for a given backend/profile, do not repeatedly rediscover it."),
    (293, "PROOF", None, None, "Let automated checks prove technical facts."),
    (294, "PROOF", None, None, "Let you perform final visual/artistic confirmation when that is genuinely the right tool."),
    (295, "PROOF", None, None, "The AI should hand you a concise A/B sheet/video rather than rerender the same thing ten times to chase a noisy metric."),
    (296, "PROOF", None, None, "Your feedback such as “wrong guy,” “camera goes through wall,” “too dark,” “that looks sick,” etc. should become durable project knowledge."),
    (297, "EFFECT_WEIGHT", None, None, "Use effect weights such as MICRO / SUPPORT / FEATURE / HERO / SIGNATURE so not every idea gets the same visual intensity."),
    (298, "BACKEND", None, None, "PANTHEON should eventually use the best backend for each job, rather than forcing everything through one renderer."),
    (299, "BACKEND", None, None, "Use the Quake/offscreen renderer for faithful normal Quake imagery."),
    (300, "BACKEND", None, None, "Keep Wolfcam/Q3MME capabilities available where they are genuinely useful."),
    (301, "BACKEND", None, None, "Use Blender later for custom character poses, precise pointing, wall removal, masks, depth/normals, custom geometry/world transforms and impossible cameras."),
    (302, "BACKEND", None, None, "Use FFmpeg/compositor for final assembly."),
    (303, "BACKEND", None, None, "Use ComfyUI later only for controlled stylization, not for deciding game truth."),
    (304, "TRUTH_RULE", None, None, "Never let AI invent whether a shot hit, where a player was, who won, or when the event happened."),
    (305, "VISION", None, None, "Ultimately you want a system where you can look at a moment and say something like: “This is the guy taking a jump pad and hitting a sick rocket — now use that movement/action in this scene with Slash, freeze here, bring Crash in, X-ray the enemy, camera follows the rocket, hit the beat there.”"),
    (306, "VISION", None, None, "And PANTHEON should understand enough of the demo, map, performance, camera, effects and renderer capabilities to actually turn that direction into a reproducible shot."),
)


@dataclass(frozen=True)
class Idea:
    n: int
    category: str
    recipe: str | None
    review_tag: str | None
    text: str

    def as_dict(self) -> dict:
        return {"n": self.n, "category": self.category, "recipe": self.recipe,
                "review_tag": self.review_tag, "text": self.text}


IDEAS: tuple[Idea, ...] = tuple(Idea(*r) for r in _RAW)
BY_N = {i.n: i for i in IDEAS}
CATEGORIES = tuple(sorted({i.category for i in IDEAS}))


def get(n: int) -> Idea:
    return BY_N[n]


def by_category(category: str) -> tuple[Idea, ...]:
    return tuple(i for i in IDEAS if i.category == category)


def by_recipe(recipe_id: str) -> tuple[Idea, ...]:
    """Every idea a recipe was built to carry. A recipe with no ideas behind
    it is one I invented; a recipe with many is one the director asked for
    repeatedly."""
    return tuple(i for i in IDEAS if i.recipe == recipe_id)


def unimplemented() -> tuple[Idea, ...]:
    """Ideas no recipe carries. This is the backlog, and it is long on
    purpose -- naming the gap is the point."""
    return tuple(i for i in IDEAS if i.recipe is None)


def row(n: int, *, backend: str = "PANTHEON_QUAKE_OFFSCREEN",
        profile: str = "REVIEW") -> dict:
    """The director's columns, derived rather than stored."""
    from engine.pantheon import effect_recipes as ER
    from engine.pantheon import visual_proof as VP

    idea = get(n)
    out = {"idea": idea.text, "n": n, "category": idea.category,
           "review_tag": idea.review_tag, "recipe": idea.recipe,
           "required_truth": None, "best_backend": None,
           "status": "NO_RECIPE_YET", "visual_proof": "UNTESTED",
           "production_priority": "HUMAN_FIELD"}
    if idea.recipe:
        r = ER.get(idea.recipe)
        out["required_truth"] = list(r.required_truth)
        out["best_backend"] = (r.preferred_backends[0]
                               if r.preferred_backends else None)
        out["status"] = ER.status(idea.recipe, backend=backend, profile=profile).value
        if r.visual_proof:
            out["visual_proof"] = VP.status(r.visual_proof, backend=backend,
                                            profile=profile).value
    return out


def report(**inputs) -> dict:
    rows = [row(i.n, **inputs) for i in IDEAS]
    by_status: dict[str, int] = {}
    by_category: dict[str, int] = {}
    for r in rows:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
        by_category[r["category"]] = by_category.get(r["category"], 0) + 1
    return {"ideas": len(IDEAS), "categories": by_category,
            "by_status": by_status,
            "carried_by_a_recipe": sum(1 for r in rows if r["recipe"]),
            "no_recipe_yet": len(unimplemented())}


def main() -> int:                                           # pragma: no cover
    import argparse
    import json
    ap = argparse.ArgumentParser(description="the director's master idea list")
    ap.add_argument("--category")
    ap.add_argument("--recipe")
    ap.add_argument("--unimplemented", action="store_true")
    ap.add_argument("-n", type=int)
    a = ap.parse_args()
    if a.n:
        print(json.dumps(row(a.n), indent=1))
    elif a.category:
        for i in by_category(a.category):
            print(f"{i.n:3d}  {i.text}")
    elif a.recipe:
        for i in by_recipe(a.recipe):
            print(f"{i.n:3d}  {i.text}")
    elif a.unimplemented:
        for i in unimplemented():
            print(f"{i.n:3d}  [{i.category}] {i.text}")
    else:
        print(json.dumps(report(), indent=1))
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
