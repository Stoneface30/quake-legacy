"""The creative corpus: every visual answer the music is allowed to ask for.

This is the vocabulary a ChoreographyPlan draws on. Each entry says which
lane it plays on, what it is FOR, what evidence it needs before it may be
planned, whether the pipeline can render it today, and roughly what it costs.

The register exists so a song is never ranked as fillable on the strength of
effects that do not exist. A CREATIVE_SEED is a real idea and a real plan; it
is not a deliverable, and the ranking must be able to tell the difference.

Sources, all first-class and none dropped: the original idea dump (world
transformations, 1vX visualisation, texture storytelling, physical comedy,
truth-aware results, team rounds, identity match cuts, map construction,
picture-in-picture on world surfaces, chat, motif montages, movement as
transition vocabulary, telefrag and gauntlet grammar, multi-exposure, music
reactive materials, death as material) and the later additions (team identity
morphs, post-win teammate reveal, rhythmic stutter, mosaic interpolation,
micro accents, rail cooldown, damage ledgers, semantic compression, the
danger-cross gag, movement audio matches, hero-then-death rewind, rocket
flyby, wall x-ray, diegetic scoreboard, assisted finishes, NOPE and commit,
speed-scaled slow motion, damage chase, lag stylisation, death motifs,
outshaft duels, enemy POV).
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Sequence

from creative_suite.engine import choreography as ch

CORPUS_VERSION = "creative-corpus-v1.0.0"


@dataclass(frozen=True)
class CorpusEntry:
    """One nameable thing PANTHEON can do."""
    name: str
    lanes: tuple[str, ...]
    purpose: str
    capability: str
    cost: str
    evidence_required: tuple[str, ...]
    summary: str
    origin: str = "USER"          # who asked for it
    gates: tuple[str, ...] = ()   # hard conditions, refused when unmet

    def __post_init__(self) -> None:
        for l in self.lanes:
            if l not in ch.LANES:
                raise ValueError(f"{self.name}: unknown lane {l!r}")
        if self.purpose not in ch.PURPOSES:
            raise ValueError(f"{self.name}: {self.purpose!r} is not a purpose")
        if self.capability not in ch.CAPABILITIES:
            raise ValueError(f"{self.name}: unknown capability {self.capability!r}")
        if self.cost not in ch.COSTS:
            raise ValueError(f"{self.name}: unknown cost {self.cost!r}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


L = ch  # shorthand
_E = CorpusEntry

# ── the register ────────────────────────────────────────────────────────────
# Capability is an honest statement about the pipeline as it stands today.

CORPUS: tuple[CorpusEntry, ...] = (

    # ── world transformation ────────────────────────────────────────────────
    _E("WORLD_STRIP", (L.LANE_WORLD, L.LANE_FX), "SHOW_THREAT",
       L.DESIGNABLE, L.COST_EXPENSIVE, ("map_geometry",),
       "The map dissolves away so only the players remain; used to make a "
       "situation legible rather than to look clever."),
    _E("WORLD_REBUILD", (L.LANE_WORLD, L.LANE_FX), "TRANSITION",
       L.DESIGNABLE, L.COST_EXPENSIVE, ("map_geometry",),
       "Geometry returns, usually on the beat that resumes the action."),
    _E("MAP_CONSTRUCTION_INTRO", (L.LANE_WORLD, L.LANE_MATERIAL), "EXPLAIN_GEOMETRY",
       L.DESIGNABLE, L.COST_EXPENSIVE, ("map_geometry",),
       "Wireframe to geometry to texture to detail: the arena assembles itself."),
    _E("WORLD_MORPH_TO_NEXT_SCENE", (L.LANE_WORLD, L.LANE_TRANSITION), "TRANSITION",
       L.REQUIRES_NEW_TECH, L.COST_RND, ("map_geometry", "scene_pair"),
       "One arena becomes the next without a cut."),
    _E("FLY_INTO_OBJECT", (L.LANE_CAMERA, L.LANE_TRANSITION), "TRANSITION",
       L.DESIGNABLE, L.COST_EXPENSIVE, ("camera_path",),
       "Camera flies into an eye, a rocket, a surface, and out the other side "
       "into the next scene."),
    _E("PROJECTILE_MORPH_BRIDGE", (L.LANE_TRANSITION, L.LANE_MODEL), "TRANSITION",
       L.REQUIRES_NEW_TECH, L.COST_RND, ("projectile_path",),
       "A rocket becomes the object that opens the next scene."),
    _E("LOW_HP_REACTIVE_WORLD", (L.LANE_MATERIAL, L.LANE_WORLD), "BUILD_TENSION",
       L.DESIGNABLE, L.COST_MODERATE, ("player_health",),
       "Materials and light react to the player's real remaining health."),
    _E("WALL_XRAY_REBUILD", (L.LANE_WORLD, L.LANE_CAMERA), "EXPLAIN_GEOMETRY",
       L.DESIGNABLE, L.COST_EXPENSIVE, ("map_geometry", "shot_line"),
       "Freeze, ghost the wall that hides the action, show the real trajectory, "
       "rebuild the wall, then let the frag play."),

    # ── 1vX and threat ──────────────────────────────────────────────────────
    _E("ONE_V_X_ENEMY_REVEAL", (L.LANE_FX, L.LANE_INFORMATION, L.LANE_WORLD),
       "SHOW_THREAT", L.DESIGNABLE, L.COST_EXPENSIVE,
       ("round_context", "alive_state"),
       "Enemies revealed one at a time, each on its own musical attack, with a "
       "count that decrements as they die."),
    _E("ONE_V_X_COUNT_DISPLAY", (L.LANE_INFORMATION,), "SHOW_THREAT",
       L.PROTOTYPE, L.COST_MODERATE, ("alive_state",),
       "The literal number of enemies still standing, from death events."),
    _E("NOPE_RETREAT", (L.LANE_FX, L.LANE_SOUND, L.LANE_TEXT), "COMEDIC_RELEASE",
       L.DESIGNABLE, L.COST_CHEAP, ("alive_state", "movement"),
       "Weapon on cooldown, several enemies together, the player turns around. "
       "A tiny sound and a beat of hesitation."),
    _E("COMMIT_1VX", (L.LANE_NARRATIVE, L.LANE_TIME), "REVEAL_SKILL",
       L.PROVEN_RUNTIME, L.COST_CHEAP, ("round_context", "alive_state"),
       "Same threat, and the player goes in anyway. Escalation, not bravado.",
       "USER", ("ROUND_WIN_FOR_TRIUMPH",)),
    _E("DANGER_CROSS_SIGN", (L.LANE_ANIMATION, L.LANE_TIME), "COMEDIC_RELEASE",
       L.CREATIVE_SEED, L.COST_RND, ("custom_animation", "movement"),
       "Before a dangerous dive: pause, the player strikes a cross/nope pose, "
       "back to first person, the enemy misses, the player kills. Rare."),

    # ── team and identity ───────────────────────────────────────────────────
    _E("TEAM_IDENTITY_MORPH", (L.LANE_MODEL,), "REVEAL_TEAM",
       L.DESIGNABLE, L.COST_EXPENSIVE, ("team_state",),
       "The player's white fullbright Xaero takes the pTn / Nauru treatment in "
       "a real team fight. Enemy treatment only with verified team identity; "
       "semantic identity itself is never changed.",
       "USER", ("MANUAL_VERIFIED_TEAM_IDENTITY",)),
    _E("POST_WIN_TEAMMATE_MODEL_REVEAL", (L.LANE_MODEL, L.LANE_NARRATIVE),
       "ROUND_PAYOFF", L.DESIGNABLE, L.COST_EXPENSIVE,
       ("team_state", "round_result"),
       "Look at a teammate, act, win the round, look back: the teammate now "
       "carries an alternate presentation. Requires a truthful round win.",
       "USER", ("ROUND_WIN",)),
    _E("TEAM_ROUND_STORY", (L.LANE_NARRATIVE, L.LANE_CAMERA), "REVEAL_TEAM",
       L.PROVEN_RUNTIME, L.COST_MODERATE, ("team_state", "round_context"),
       "Two to four teammates as actual tactical storytelling, even when one "
       "player's action density is low."),
    _E("ASSISTED_ROUND_FINISH", (L.LANE_NARRATIVE, L.LANE_PIP), "ROUND_PAYOFF",
       L.PROTOTYPE, L.COST_MODERATE, ("damage_ledger", "round_result", "team_state"),
       "The player does the damage, a teammate takes the kill, the round is "
       "won. The teammate's kill is never credited to the player.",
       "USER", ("ROUND_WIN",)),
    _E("IDENTITY_MATCH_CUT", (L.LANE_TRANSITION, L.LANE_TIME), "TRANSITION",
       L.PROTOTYPE, L.COST_MODERATE, ("pose", "weapon"),
       "Freeze on a player and cut to a similar pose, weapon or framing in "
       "another moment."),

    # ── damage and information ──────────────────────────────────────────────
    _E("DAMAGE_LEDGER_OVER_TARGET", (L.LANE_INFORMATION,), "SHOW_DAMAGE",
       L.DESIGNABLE, L.COST_MODERATE, ("damage_ledger",),
       "Cumulative confirmed damage the player has done, tracked over the enemy "
       "it was done to. Engine truth only."),
    _E("ROUND_DAMAGE_COUNTER", (L.LANE_INFORMATION,), "SHOW_DAMAGE",
       L.DESIGNABLE, L.COST_MODERATE, ("damage_ledger", "round_context"),
       "The player's accumulated damage across a round."),
    _E("DIEGETIC_SCOREBOARD", (L.LANE_INFORMATION, L.LANE_MATERIAL), "EXPLAIN_CA",
       L.DESIGNABLE, L.COST_EXPENSIVE, ("score_state",),
       "Real score and state rendered on advertisement boards, monitors and "
       "map surfaces. The ordinary gameplay HUD stays absent."),
    _E("TEXTURE_COUNTDOWN_TEXT", (L.LANE_MATERIAL, L.LANE_INFORMATION), "BUILD_TENSION",
       L.DESIGNABLE, L.COST_MODERATE, ("score_state",),
       "Countdowns and words written into the world's own textures."),
    _E("RAIL_COOLDOWN_TELEGRAPH", (L.LANE_INFORMATION, L.LANE_FX), "EXPLAIN_CA",
       L.DESIGNABLE, L.COST_MODERATE, ("weapon_state",),
       "Show the remaining rail recovery so tactical waiting and dodging read "
       "as decisions rather than hesitation."),
    _E("SHAFT_DUEL_STAT", (L.LANE_INFORMATION,), "REVEAL_SKILL",
       L.CREATIVE_SEED, L.COST_RND, ("lg_engagement", "damage_ledger"),
       "Outshaft / outshafted as a career statistic and as searchable material; "
       "occasional and stylistic, never an esports overlay."),

    # ── rhythm and image ────────────────────────────────────────────────────
    _E("RHYTHMIC_IMAGE_STUTTER", (L.LANE_FX, L.LANE_GESTURE), "MUSICAL_PUNCTUATION",
       L.PROTOTYPE, L.COST_CHEAP, (),
       "Repeated musical attacks answered by frame stutters. Zero response bias: "
       "a stutter reads at the frame it lands on."),
    _E("MOSAIC_TILE_INTERPOLATION", (L.LANE_FX,), "MUSICAL_PUNCTUATION",
       L.DESIGNABLE, L.COST_EXPENSIVE, (),
       "The image divided into regions that freeze, lag, interpolate and catch "
       "up independently. Screen-space now; depth-aware later."),
    _E("FRAME_ECHO", (L.LANE_FX,), "MUSICAL_PUNCTUATION",
       L.PROTOTYPE, L.COST_CHEAP, (),
       "Offset repeats of the image driven by the music."),
    _E("MULTI_EXPOSURE", (L.LANE_FX,), "REVEAL_SKILL",
       L.DESIGNABLE, L.COST_MODERATE, (),
       "Several instants of one movement held in one frame."),
    _E("TEMPORAL_DECOMPOSITION", (L.LANE_FX, L.LANE_TIME), "REVEAL_SKILL",
       L.DESIGNABLE, L.COST_EXPENSIVE, (),
       "A freeze taken apart in time rather than space."),
    _E("RHYTHMIC_MOTIF_MONTAGE", (L.LANE_TRANSITION, L.LANE_GESTURE), "MUSICAL_PUNCTUATION",
       L.PROVEN_RUNTIME, L.COST_MODERATE, ("motif_group",),
       "Ten to twenty DISTINCT canonical occurrences sharing a weapon, a place, "
       "a screen position or a movement, cut fast to the music."),

    # ── movement ────────────────────────────────────────────────────────────
    _E("MOVEMENT_TRANSITION", (L.LANE_TRANSITION, L.LANE_GAMEPLAY), "TRANSITION",
       L.PROVEN_RUNTIME, L.COST_CHEAP, ("movement",),
       "Doors, teleports, rocket jumps and high-speed runs as the grammar that "
       "joins one scene to the next."),
    _E("STRAFE_JUMP_AUDIO_MATCH", (L.LANE_SOUND, L.LANE_TRANSITION), "TRANSITION",
       L.PROTOTYPE, L.COST_CHEAP, ("movement",),
       "A jump or landing sound in one scene matched to the identical event in "
       "the next."),
    _E("VELOCITY_SIGNATURE", (L.LANE_TIME, L.LANE_FX), "REVEAL_SKILL",
       L.PROVEN_RUNTIME, L.COST_CHEAP, ("movement",),
       "Speed made visible. Jump pad, double jump, rocket jump, grenade jump "
       "and plasma movement all qualify."),
    _E("SPEED_SCALED_SLOWMO", (L.LANE_TIME,), "REVEAL_SKILL",
       L.PROVEN_RUNTIME, L.COST_CHEAP, ("movement",),
       "High relative velocity widens the slow-motion envelope. The music still "
       "picks the exact rate inside it; speed never sets the rate directly."),
    _E("TELEPORTER_WORLD_PASS", (L.LANE_TRANSITION, L.LANE_WORLD), "TRANSITION",
       L.PROTOTYPE, L.COST_MODERATE, ("teleport",),
       "A teleporter as a doorway between two parts of the film."),

    # ── projectiles ─────────────────────────────────────────────────────────
    _E("PROJECTILE_CINEMATIC", (L.LANE_CAMERA, L.LANE_GAMEPLAY), "REVEAL_SKILL",
       L.PROTOTYPE, L.COST_MODERATE, ("projectile_path",),
       "The camera rides a recorded projectile."),
    _E("RECONSTRUCTED_PROJECTILE_CINEMATIC", (L.LANE_CAMERA, L.LANE_GAMEPLAY),
       "REVEAL_SKILL", L.PROTOTYPE, L.COST_MODERATE,
       ("projectile_path", "reconstruction_confidence"),
       "The same, over a stretch the client never saw, using the deterministic "
       "continuation. Provenance travels with it.",
       "USER", ("PRESENTABLE_RECONSTRUCTION",)),
    _E("ROCKET_FLYBY_AUDIO_ANCHOR", (L.LANE_SOUND, L.LANE_CAMERA), "BUILD_TENSION",
       L.PROTOTYPE, L.COST_MODERATE, ("projectile_path",),
       "A projectile passing close to the camera, identified by real geometry, "
       "speed and distance, and sold by the sound everyone knows."),
    _E("GRENADE_ARC_FOLLOW", (L.LANE_CAMERA,), "REVEAL_SKILL",
       L.PROTOTYPE, L.COST_MODERATE, ("projectile_path",),
       "A grenade's bounces as a camera move."),

    # ── death ───────────────────────────────────────────────────────────────
    _E("DEATH_AS_TRANSITION", (L.LANE_TRANSITION,), "TRANSITION",
       L.PROVEN_RUNTIME, L.COST_CHEAP, ("death",),
       "A death is material, not an editorial failure."),
    _E("DEATH_MOTIF_BANK", (L.LANE_TRANSITION, L.LANE_GESTURE), "MUSICAL_PUNCTUATION",
       L.PROVEN_RUNTIME, L.COST_MODERATE, ("death", "motif_group"),
       "The player's own useless deaths, grouped by weapon, explosion, pose, "
       "geometry or screen direction, as three-to-four-frame rhythmic flashes."),
    _E("HERO_THEN_DEATH_REWIND", (L.LANE_TIME, L.LANE_NARRATIVE), "REVEAL_SKILL",
       L.DESIGNABLE, L.COST_MODERATE, ("frag", "death"),
       "A brilliant action followed a second later by death: freeze on the "
       "death, use it as match-cut material, then rewind and replay the action "
       "cleanly. The death does not get to ruin the payoff."),
    _E("TELEFRAG_GRAMMAR", (L.LANE_GAMEPLAY, L.LANE_TRANSITION), "COMEDIC_RELEASE",
       L.DESIGNABLE, L.COST_CHEAP, ("frag", "teleport"),
       "Arriving on top of somebody deserves its own treatment."),
    _E("GAUNTLET_GRAMMAR", (L.LANE_GAMEPLAY, L.LANE_SOUND), "COMEDIC_RELEASE",
       L.DESIGNABLE, L.COST_CHEAP, ("frag", "weapon_state"),
       "The humiliation weapon, played as humiliation."),

    # ── results, rounds, pacing ─────────────────────────────────────────────
    _E("ROUND_WIN_PAYOFF", (L.LANE_NARRATIVE, L.LANE_FX), "ROUND_PAYOFF",
       L.PROVEN_RUNTIME, L.COST_MODERATE, ("round_result",),
       "Release, but only when the round was actually won.",
       "USER", ("ROUND_WIN",)),
    _E("ROUND_LOSS_CONTINUATION", (L.LANE_NARRATIVE, L.LANE_TRANSITION), "TRANSITION",
       L.PROVEN_RUNTIME, L.COST_CHEAP, ("round_result",),
       "Brilliant play that ends in a loss gets a different ending: a "
       "continuation, not a celebration."),
    _E("SEMANTIC_COMPRESSION", (L.LANE_NARRATIVE, L.LANE_TIME, L.LANE_INFORMATION),
       "EXPLAIN_CA", L.DESIGNABLE, L.COST_MODERATE,
       ("round_context", "damage_ledger"),
       "A long won round shown as its meaningful movement, damage, outplay and "
       "kills, with the dead time cut and the context stated up front."),
    _E("DAMAGE_CHASE_ASSIST", (L.LANE_NARRATIVE, L.LANE_PIP), "SHOW_DAMAGE",
       L.PROTOTYPE, L.COST_MODERATE, ("damage_ledger", "death"),
       "Heavy damage, the enemy flees, a teammate finishes it. Freeze, show "
       "where it ended, resolve the round."),

    # ── point of view ───────────────────────────────────────────────────────
    _E("ENEMY_POV_REAL", (L.LANE_CAMERA, L.LANE_PIP), "REVEAL_SKILL",
       L.DESIGNABLE, L.COST_EXPENSIVE, ("multi_demo_recovered",),
       "Another client's actual recording of the same historical moment.",
       "USER", ("MULTI_DEMO_RECOVERED",)),
    _E("ENEMY_POV_RECONSTRUCTED", (L.LANE_CAMERA, L.LANE_PIP), "REVEAL_SKILL",
       L.DESIGNABLE, L.COST_EXPENSIVE, ("enemy_state",),
       "An approximate enemy viewpoint built from recorded enemy state."),
    _E("ENEMY_POV_SYNTHETIC", (L.LANE_CAMERA, L.LANE_PIP), "REVEAL_SKILL",
       L.DESIGNABLE, L.COST_EXPENSIVE, (),
       "A deliberately authored enemy viewpoint. Cinematic, and labelled so."),
    _E("PIP_WORLD_SURFACE", (L.LANE_PIP, L.LANE_MATERIAL), "EXPLAIN_CA",
       L.DESIGNABLE, L.COST_EXPENSIVE, (),
       "Video, a scoreboard, statistics or another viewpoint rendered on an "
       "advertisement board inside the map."),

    # ── text, chat, comedy ──────────────────────────────────────────────────
    _E("CHAT_REACTION", (L.LANE_TEXT, L.LANE_SOUND), "COMEDIC_RELEASE",
       L.PROTOTYPE, L.COST_CHEAP, ("chat",),
       "Real chat around a moment: gg, rage, a meme, timed to the cut. Sender "
       "reduced to a slot; no names leave the index."),
    _E("GRENADE_FOOTBALL_GAG", (L.LANE_ANIMATION, L.LANE_GAMEPLAY), "COMEDIC_RELEASE",
       L.CREATIVE_SEED, L.COST_RND, ("projectile_path", "custom_animation"),
       "Chest control, a headbutt, keepie-uppies with a live grenade."),
    _E("LAG_TELEPORT_STYLIZATION", (L.LANE_FX,), "COMEDIC_RELEASE",
       L.DESIGNABLE, L.COST_MODERATE, ("netcode_anomaly",),
       "A genuine remote-state discontinuity as glitch or fragmentation. The "
       "anomaly stays factual evidence; the effect is authored and labelled."),

    # ── accents ─────────────────────────────────────────────────────────────
    _E("MICRO_ACTION_ACCENT", (L.LANE_FX, L.LANE_SOUND), "MUSICAL_PUNCTUATION",
       L.PROVEN_RUNTIME, L.COST_CHEAP, ("movement",),
       "A weapon switch, a pickup, a gauntlet swap, a jump: small answers to "
       "small musical events. A micro action is never promoted to hero."),
    _E("MUSIC_REACTIVE_MATERIAL", (L.LANE_MATERIAL, L.LANE_GESTURE),
       "MUSICAL_PUNCTUATION", L.DESIGNABLE, L.COST_MODERATE, (),
       "Surfaces that answer the music directly, with no cut involved."),

    # ── framing the episode ─────────────────────────────────────────────────
    _E("PROJECT_INTRO", (L.LANE_NARRATIVE, L.LANE_TEXT), "TRIBUTE",
       L.PROVEN_RUNTIME, L.COST_CHEAP, (),
       "What PANTHEON is, stated once, at the start."),
    _E("CA_EXPLAINER", (L.LANE_NARRATIVE, L.LANE_INFORMATION), "EXPLAIN_CA",
       L.DESIGNABLE, L.COST_MODERATE, ("round_context",),
       "How Clan Arena works, taught through the footage rather than a tutorial: "
       "no respawns, regroup, take your 1v1 when isolated, position, win the round."),
    _E("QUAKE_TRIBUTE_OUTRO", (L.LANE_NARRATIVE, L.LANE_MATERIAL), "TRIBUTE",
       L.PROVEN_RUNTIME, L.COST_MODERATE, (),
       "Why any of this exists: a tribute to Quake."),
)

BY_NAME: dict[str, CorpusEntry] = {e.name: e for e in CORPUS}


def get(name: str) -> CorpusEntry:
    if name not in BY_NAME:
        raise KeyError(f"{name!r} is not in the creative corpus")
    return BY_NAME[name]


def by_lane(lane: str) -> tuple[CorpusEntry, ...]:
    return tuple(e for e in CORPUS if lane in e.lanes)


def by_capability(capability: str) -> tuple[CorpusEntry, ...]:
    return tuple(e for e in CORPUS if e.capability == capability)


def requiring(evidence: str) -> tuple[CorpusEntry, ...]:
    return tuple(e for e in CORPUS if evidence in e.evidence_required)


def capability_report() -> dict[str, Any]:
    """What the corpus can actually do today, by count."""
    caps = {c: 0 for c in ch.CAPABILITIES}
    costs = {c: 0 for c in ch.COSTS}
    lanes = {l: 0 for l in ch.LANES}
    for e in CORPUS:
        caps[e.capability] += 1
        costs[e.cost] += 1
        for l in e.lanes:
            lanes[l] += 1
    return {"entries": len(CORPUS), "by_capability": caps, "by_cost": costs,
            "by_lane": lanes, "version": CORPUS_VERSION}


def element(name: str, start_us: int, end_us: int, *, lane: str | None = None,
            peak_us: int | None = None, trigger: str = "",
            musical_relation: str = "", evidence: Sequence[Any] = (),
            intensity: str = ch.NORMAL, notes: str = ""
            ) -> ch.ChoreographyElement:
    """Build a plan element from a corpus entry, inheriting its purpose,
    capability and cost so a plan cannot quietly claim an effect is cheaper or
    more real than the register says."""
    e = get(name)
    return ch.ChoreographyElement(
        lane=lane or e.lanes[0], action=name, start_us=start_us, end_us=end_us,
        purpose=e.purpose, peak_us=peak_us, trigger=trigger,
        musical_relation=musical_relation, evidence=tuple(evidence),
        capability=e.capability, cost=e.cost, intensity=intensity,
        notes=notes or e.summary)
