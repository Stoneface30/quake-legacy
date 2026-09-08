"""THE PROJECT'S OWN DEFAULTS, AS VERSIONED PROFILES.

There are no magic numbers scattered through the pipeline. What "review"
means, what "film" means, what a public export may contain -- each is a named,
versioned profile, and its id changes when its contents change, so anything
cached against it can tell that it is stale.

The values are the project's, learned the hard way and cited where they were:
720p30 for review because the reviewer is meant to be fast and usable on a
phone; 1080p60 for film; the enemy readable in review and authentic in film;
nothing that can burn a name into a public frame.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field


@dataclass(frozen=True)
class FilmProfile:
    name: str
    version: str
    purpose: str
    width: int
    height: int
    fps: int
    visual_profile: str          # a name in engine.pantheon.visual_profile
    master_profile: str          # the engine cfg profile the capture execs
    hud: str                     # CLEAN | NONE | DIEGETIC
    notes: tuple[str, ...] = ()
    why: dict = field(default_factory=dict)

    @property
    def id(self) -> str:
        payload = json.dumps({k: v for k, v in self.__dict__.items()
                              if k != "why"}, sort_keys=True, default=str)
        return f"{self.name}@{hashlib.sha256(payload.encode()).hexdigest()[:8]}"

    def as_dict(self) -> dict:
        return {**{k: v for k, v in self.__dict__.items()},
                "notes": list(self.notes), "id": self.id}


REVIEW_V1 = FilmProfile(
    name="REVIEW_V1", version="1",
    purpose="Judging a moment quickly, including on a phone.",
    width=1280, height=720, fps=30,
    visual_profile="REVIEW", master_profile="TR4SH_REVIEW_V2", hud="CLEAN",
    notes=("the enemy is a green Keel and is meant to be unmistakable",
           "teammates and the recorder keep the look the demo authored",
           "a fact that cannot be derived reads NOT_DERIVABLE, never blank"),
    why={"720p30": "review media is for deciding, not for delivery; the "
                   "reviewer has to load fast and work on a phone",
         "green enemy": "proven on pixels 2026-09-06, and banked so it is not "
                        "re-proven"})

FPV_FILM_V1 = FilmProfile(
    name="FPV_FILM_V1", version="1",
    purpose="The delivered first-person picture.",
    width=1920, height=1080, fps=60,
    visual_profile="AUTHENTIC", master_profile="TR4SH_GAMEPLAY_MASTER_V2",
    hud="CLEAN",
    notes=("the demo's own cast survives: nothing is forced",
           "the weapon stays visible -- it is part of the first-person image"),
    why={"1080p60": "the delivery format of the series",
         "authentic": "a film frame should look like Quake looked"})

CINEMATIC_CLEAN_V1 = FilmProfile(
    name="CINEMATIC_CLEAN_V1", version="1",
    purpose="Non-first-person shots: free camera, follow, projectile camera.",
    width=1920, height=1080, fps=60,
    visual_profile="AUTHENTIC", master_profile="TR4SH_GAMEPLAY_MASTER_V2",
    hud="NONE",
    notes=("no HUD at all: a third-person frame with a first-person HUD reads "
           "as a mistake",),
    why={"no hud": "the camera is not a player"})

ANALYSIS_V1 = FilmProfile(
    name="ANALYSIS_V1", version="1",
    purpose="Explaining: frozen action, presenters, world-space graphics.",
    width=1920, height=1080, fps=60,
    visual_profile="REVIEW", master_profile="TR4SH_REVIEW_V2", hud="DIEGETIC",
    notes=("readability beats authenticity here: the enemy is forced so the "
           "viewer can follow the explanation",
           "graphics live in world space and are driven by FrameTruth"),
    why={"readable enemy": "an explanation the viewer cannot follow explains "
                           "nothing"})

PUBLIC_EXPORT_V1 = FilmProfile(
    name="PUBLIC_EXPORT_V1", version="1",
    purpose="Anything that leaves this machine.",
    width=1920, height=1080, fps=60,
    visual_profile="AUTHENTIC", master_profile="TR4SH_PUBLIC_EXPORT",
    hud="NONE",
    notes=("no name, nickname or identifier may appear in the frame",
           "the obituary feed and the centre print are off, because both "
           "burned an opponent's name into a clip once"),
    why={"no feed": "measured, not assumed: the batch master profile burned "
                    "'You fragged <name>' into a public clip"})

PROFILES: dict[str, FilmProfile] = {
    p.name: p for p in (REVIEW_V1, FPV_FILM_V1, CINEMATIC_CLEAN_V1,
                        ANALYSIS_V1, PUBLIC_EXPORT_V1)}

DEFAULT_REVIEW = REVIEW_V1.name
DEFAULT_FILM = FPV_FILM_V1.name


def get(name: str) -> FilmProfile:
    try:
        return PROFILES[name]
    except KeyError:
        raise KeyError(f"no such film profile: {name}; "
                       f"known: {sorted(PROFILES)}") from None


def report() -> dict:
    return {"profiles": {n: p.id for n, p in PROFILES.items()},
            "default_review": DEFAULT_REVIEW, "default_film": DEFAULT_FILM}
