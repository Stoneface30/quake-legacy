"""THE DIRECTOR'S OWN WORDS, UNEDITED.

`ideas.py` holds the consolidated 306-item list. This file holds the notes it
was consolidated FROM -- the original free-form paragraphs, exactly as written,
typos and all. They are kept because a summary loses things: several ideas
here never reached the numbered list at all, and the phrasing carries intent
that a tidied sentence does not.

NOTHING IN THIS FILE IS PARSED DESTRUCTIVELY. The text is the record. Intent
kinds and recipe matches are derived on demand by `creative_intent.read()`,
and a note with no route is not a problem with the note.
"""
from __future__ import annotations

from dataclasses import dataclass

# (id, verbatim text)
_NOTES: tuple[tuple[str, str], ...] = (
    ("N01", "When we have clips from a teamfight we can pause transform my xearo ( the cpm white full bright is my skin ) to the team one ( nauri colors ) and the enemy team colors ( this can be reviewed manually with our database ) ."),
    ("N02", "having the skin / model / texture when round end or when I look a teammate I do the frag we win and then I look him back he could have another model or something of the sort ."),
    ("N03", "Also in the effect there are a lot of rhythm when the image stutter with the beat / or the interpoled images like 2meter by 2 meter instead of the full video is something I really appreciate too ."),
    ("N04", "Like when I swap gauntlet and just hit one or when I Use item this are good signals for a little effect ."),
    ("N05", "having the rail cooldown before I jump them or dodge them"),
    ("N06", "having the damage I deal to the enemy that stays on top of their head in some situation ( so viewer know im not just finishing and I inflic a lot of damage ) also for the fpv view we could use my overall damage a the start of the round as a big number ."),
    ("N07", "the first episode should be the initiation for the spectator , we would present it as the project first then the action than the reason ( tribute to quake ) and explain how CA work where you regroup how you should take your 1v1 if not at the group point , explain a little bit the strategies ."),
    ("N08", "when round are long but I still win we can use a technique where we show like game info or score and only show the moment when I deal damage or move like a god , then cut to the next damage / kill , and finish with a special round win finish ( with the database of animation / 3d / stuff we will have"),
    ("N09", "before having a dangerous dive an excellent effect would be to pause and view my skin doing a cross sign , then we go back in first person when the enemy miss and finish the kill !"),
    ("N10", "for an easy transition when I straff jump multiple time we could just sync the sound of the jump for the next clip sync perfectly"),
    ("N11", "sometime I do reallllllly nice frags but I die less then a second after so a good idea would be to freeze the moment I die and the way I die and then transition to another clip when I die shortly after the nice action , rewind and let it play again ( for example I die from a rocket I explode you can transition to another scene where I die in a rocket and explode and then rewind ) ."),
    ("N12", "when a rocket fly close to a player or the camera in fpv it does a really loud and recognisable sound , this could also be used to recognize the moment I dodge rocket for slowmo or fpv / pip or anything and then also used for transition when we follow a long rocket ."),
    ("N13", "when I shoot through a wall we could like remove the wall when the action happen pause after the frag and do a animation like we rebuilt the wall and show the real frag !"),
    ("N14", "Instead of hiding completely the scoreboard we could render it live in the ad space / we also need to remove scoreboard from death if we want the clean transitions from my previous idea ."),
    ("N15", "also when I do a nice action and the guy don't die and it's my teammate that get him and not me but round win could just be nice to show the last frag quickly for the transition/animation/effect ."),
    ("N16", "the double jump I do when taking a jumpad could be a nice effect too and the jumpad rocket jump are good plasma wall are also quite good when in the action and also grenade jumps ."),
    ("N17", "when there is a cooldown and there are 3/4 enemy regroup and im like Nope and go back , or similar when I see im 1vsx on the fight and I still go in and win this would be great to have effect for this ! like a big Nope / or even extra sound ."),
    ("N18", "also quick one on the frags , when enemy movespeed is real fast and I make contact with anything its really good for cinematic effect ( faster the movespeed better the slomo ) ."),
    ("N19", "when for example I do a lot of damage the enemy flee and someone else kill him we could pause switch with a fpv and just show the guy death ."),
    ("N20", "also when the enemy lag or teleport it could be used for an animation or ragebait ( optional )."),
    ("N21", "we can use death from me that are useless for when I die on a good action to have the same type of display like 3/4 frame of the other death then stop and one with a good action before rewind and play it fully ."),
    ("N22", "could be a nice stat to have to know how I outshaft and how I get ourshafted ( should be one on one data and no air/jumppad shaft , too easy ) ."),
    ("N23", "see the enemy pov when they get preshot or big kill"),
    ("N24", "also add the frag to lookup for double rail triple rail ( one shot multiple hits )"),
    ("N25", "we could also look for funny things like when I fall in void or when I miss rocket jump or when I take the same bump multiple time"),
    ("N26", "on the teaching fast fps educational side of the video we could prepare a video ( because sometime im 200 100 not at regroup finishing people ) like round 1 no one regroup round 2 no one so the nyou start to play be yourself ( that could be the revenges story sometime on some games / effect or transition animation like we loose because no one regroup then I stop regrouping we win , or something similar ."),
    ("N27", "on the introduction side, we can also explain the competitiveness of the quake , the configuration , we show the effect of all the command like picmip drawgun , all the competitor dont car eabout graphic they care about response time and precision , quake is the purest form of it we could prove that this is intemporal and all the modern game also reduce graphic or settings if that give them the edge"),
    ("N28", "we could take really nice rail and animate it so the slow motion show the rail building and follow it  ( like when they follow the bullets in wanted ( the movie ))."),
)


@dataclass(frozen=True)
class DirectorNote:
    note_id: str
    text: str

    def as_dict(self) -> dict:
        return {"note_id": self.note_id, "text": self.text}


NOTES: tuple[DirectorNote, ...] = tuple(DirectorNote(*n) for n in _NOTES)
BY_ID = {n.note_id: n for n in NOTES}


# WHAT THESE NOTES ASK FOR THAT THE NUMBERED LIST DOES NOT.
#
# Each entry is a semantic requirement read out of a note, with the note it
# came from. Written by hand, deliberately: a keyword parser would have
# flattened "the rail building and follow it" into "camera" and lost the idea.
# Nothing here replaces the note; the note is above, unedited.
NEW_REQUIREMENTS: tuple[dict, ...] = (
    {"from": "N01", "requirement": "TEAM_IDENTITY_MORPH_MID_CLIP",
     "means": "Pause a teamfight and transform the recorder's own white CPM "
              "Xaero into the team's colours and the enemy team's colours, "
              "reviewed by hand against the database.",
     "needs_truth": ("ROSTER", "TRANSFORM"), "carried_by": "MODEL_MORPH"},
    {"from": "N04", "requirement": "WEAPON_SWAP_AND_ITEM_ACCENTS",
     "means": "A gauntlet swap that lands one hit, or an item pickup, is a "
              "cue for a small effect -- not a feature-sized one.",
     "needs_truth": ("WEAPON_STATE", "EVENTS"), "carried_by": None},
    {"from": "N05", "requirement": "RAIL_COOLDOWN_TELEGRAPH",
     "means": "Show the rail's cooldown before the dodge or the jump, so the "
              "viewer understands the window being played.",
     "needs_truth": ("WEAPON_STATE", "EVENTS"), "carried_by": None},
    {"from": "N06", "requirement": "DAMAGE_OVER_HEAD",
     "means": "Damage dealt stays above the enemy's head, and the round's "
              "total appears as a big number in FPV -- so nobody thinks it "
              "was only a finish.",
     "needs_truth": ("EVENTS", "HEALTH"), "carried_by": None,
     "caution": "pain events do not give exact damage totals; anything shown "
                "must come from real damage truth or say NOT_DERIVABLE"},
    {"from": "N08", "requirement": "LONG_ROUND_COMPRESSION",
     "means": "A long won round plays as score/info plus only the damage and "
              "the god-tier movement, cut to cut, with a special finish.",
     "needs_truth": ("ROUND", "EVENTS", "TRANSFORM"), "carried_by": None},
    {"from": "N09", "requirement": "PRE_DIVE_CROSS_SIGN",
     "means": "Before a dangerous dive, pause on the recorder's own skin "
              "making a cross sign, then return to first person as the enemy "
              "misses.",
     "needs_truth": ("ROSTER", "ACTION"), "carried_by": "DIEGETIC_PRESENTER"},
    {"from": "N10", "requirement": "JUMP_SOUND_MATCH_CUT",
     "means": "Repeated strafe jumps cut on the jump sound, so the next clip "
              "lands exactly on it.",
     "needs_truth": ("EVENTS",), "carried_by": None},
    {"from": "N11", "requirement": "DEATH_ECHO_TRANSITION",
     "means": "A great frag followed by dying within a second: freeze the "
              "death, transition to another clip whose death matches it "
              "(rocket to rocket), then rewind and play it through.",
     "needs_truth": ("EVENTS", "ACTION"), "carried_by": None},
    {"from": "N12", "requirement": "ROCKET_FLYBY_AS_DETECTOR",
     "means": "The loud close-pass rocket sound marks a dodge -- usable to "
              "FIND the moment, not only to score it, and as the seam when "
              "following a long rocket.",
     "needs_truth": ("PROJECTILE_PATH", "EVENTS"), "carried_by": None},
    {"from": "N13", "requirement": "WALL_REBUILD_ANIMATION",
     "means": "Remove the wall for a shot through it, then after the frag "
              "pause and animate the wall rebuilding before showing the real "
              "frag.",
     "needs_truth": ("MAP_GEOGRAPHY", "TRANSFORM"),
     "carried_by": "WALL_REMOVE_XRAY",
     "caution": "the rebuild is the new part: removal alone is the existing "
                "recipe"},
    {"from": "N14", "requirement": "SCOREBOARD_IN_AD_SPACE",
     "means": "Render the live scoreboard onto the map's ad surfaces instead "
              "of hiding it, and remove the death scoreboard so the clean "
              "transitions survive.",
     "needs_truth": ("SCOREBOARD",), "carried_by": "DIEGETIC_SCOREBOARD"},
    {"from": "N16", "requirement": "MOVEMENT_TRICK_ACCENTS",
     "means": "Double jump off a pad, jump-pad rocket jump, plasma wall, "
              "grenade jump -- each is worth its own accent.",
     "needs_truth": ("TRANSFORM", "EVENTS"), "carried_by": None},
    {"from": "N17", "requirement": "NOPE_AND_COMMIT_MARKERS",
     "means": "A big NOPE, or an extra sound, when the fight is refused; the "
              "same device when the outnumbered fight is taken and won.",
     "needs_truth": ("ACTION", "OTHER_POV"), "carried_by": None},
    {"from": "N18", "requirement": "SPEED_SCALED_SLOWMO",
     "means": "The faster the enemy was moving at contact, the stronger the "
              "slow motion.",
     "needs_truth": ("TRANSFORM",), "carried_by": "HIGH_SPEED_RETIME"},
    {"from": "N19", "requirement": "HANDOFF_KILL_POV_SWITCH",
     "means": "Heavy damage, the enemy flees, someone else finishes: pause "
              "and switch to a POV that shows that death.",
     "needs_truth": ("OTHER_POV", "EVENTS"), "carried_by": "PIP_ALT_POV"},
    {"from": "N21", "requirement": "DEATH_LIBRARY_FOR_RHYTHM",
     "means": "Ordinary useless deaths become material: three or four frames "
              "of them, stop, then the good one, rewind, play it fully.",
     "needs_truth": ("EVENTS",), "carried_by": None},
    {"from": "N22", "requirement": "OUTSHAFT_STAT",
     "means": "Who out-shafted whom, one on one only, excluding air and "
              "jump-pad shafts because those are too easy.",
     "needs_truth": ("EVENTS", "OTHER_POV", "TRANSFORM"), "carried_by": None},
    {"from": "N23", "requirement": "ENEMY_POV_ON_PRESHOT",
     "means": "See the enemy's point of view when they get preshot or take a "
              "big kill.",
     "needs_truth": ("ENEMY_POV",), "carried_by": "ENEMY_POV_REPLAY"},
    {"from": "N24", "requirement": "MULTI_HIT_RAIL_LOOKUP",
     "means": "Find double and triple rails: one shot, several hits.",
     "needs_truth": ("EVENTS",), "carried_by": None},
    {"from": "N25", "requirement": "MISHAP_CORPUS",
     "means": "Falls into the void, missed rocket jumps, taking the same bump "
              "repeatedly -- funny material, deliberately collected.",
     "needs_truth": ("EVENTS", "TRANSFORM"), "carried_by": None},
    {"from": "N26", "requirement": "REGROUP_STORY_ARC",
     "means": "Rounds where nobody regroups, then the choice to stop "
              "regrouping and win -- a revenge story told across rounds.",
     "needs_truth": ("ROUND", "OTHER_POV", "MAP_GEOGRAPHY"), "carried_by": None},
    {"from": "N27", "requirement": "CONFIG_AS_ARGUMENT",
     "means": "Show what picmip, drawgun and the rest actually do, to argue "
              "that competitors trade graphics for response and precision, "
              "and that this is timeless.",
     "needs_truth": (), "carried_by": None,
     "caution": "this is a claim about the game, shown by A/B captures"},
    {"from": "N28", "requirement": "RAIL_BUILD_SLOWMO",
     "means": "Slow motion that shows the rail beam BUILDING along its path "
              "and follows it, the way Wanted follows a bullet.",
     "needs_truth": ("PROJECTILE_PATH", "EVENTS"), "carried_by": None,
     "caution": "the rail is hitscan: the beam has no observed flight, so "
                "this is a reconstruction and must be labelled one"},
)


def get(note_id: str) -> DirectorNote:
    return BY_ID[note_id]


def requirements_from(note_id: str) -> tuple[dict, ...]:
    return tuple(r for r in NEW_REQUIREMENTS if r["from"] == note_id)


def uncarried() -> tuple[dict, ...]:
    """Requirements no recipe carries yet. The honest backlog, from the
    director's own words rather than from a summary of them."""
    return tuple(r for r in NEW_REQUIREMENTS if not r.get("carried_by"))


def with_cautions() -> tuple[dict, ...]:
    """Requirements that would produce a false claim if built naively."""
    return tuple(r for r in NEW_REQUIREMENTS if r.get("caution"))


def seed_intents() -> dict:
    """Put every note in the intent store, verbatim, so the reviewer can see
    them beside the moments they belong to."""
    from engine.pantheon import creative_intent as CI
    for n in NOTES:
        CI.capture(n.text, subject=None, note_id=n.note_id)
    return CI.report()


def report() -> dict:
    from engine.pantheon import creative_intent as CI
    kinds: dict[str, int] = {}
    for n in NOTES:
        for k in CI.read(n.text)[0]:
            kinds[k] = kinds.get(k, 0) + 1
    return {"notes": len(NOTES), "requirements_read": len(NEW_REQUIREMENTS),
            "not_carried_by_any_recipe": len(uncarried()),
            "with_truth_cautions": len(with_cautions()),
            "intent_kinds": kinds}
