"""The cast: Quake Live's own character roster, read from the installed paks.

WHY PANTHEON DOES NOT HAVE A MASCOT. The game ships twenty-six characters, each
with a silhouette, a taunt, pain and death barks, and an animation set. Painting
one of them green and using him for every explanation would throw that away.
Each film, chapter or scene casts a presenter from this roster, and the roster
is read from `pak00.pk3` -- not from Quake III documentation, which does not
know about Quake Live's `bright` skins or the trainer skin Crash wears in the
tutorial.

WHAT A PROFILE IS. `PresenterProfile` is what film authoring touches: a role
name, a model, a skin, a voice, and whether the model can gesture. It resolves
against the inventory, so a profile naming a skin that is not installed fails
at authoring time and not at capture time. Nothing downstream of it handles
CS_PLAYERS, animation numbers or sound paths.

WHAT THE INVENTORY DOES NOT CLAIM. Suitability tags are creative suggestions.
The factual columns are: which skins exist, whether a bright skin exists,
which native sounds exist, and how many frames the gesture animation has --
that last one is the reason Orbb cannot gesture (his TORSO_GESTURE is one
frame) and it was found by reading `animation.cfg`, not by assuming every
model matches Sarge.
"""
from __future__ import annotations

import json
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

PAK00 = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Quake Live\baseq3\pak00.pk3")
INVENTORY = Path("docs/reference/character_roster.json")

# animation.cfg rows are in animNumber_t order (bg_public.h). Row 6 is
# TORSO_GESTURE. A gesture of one frame is a still, not a gesture.
TORSO_GESTURE_ROW = 6
MIN_GESTURE_FRAMES = 8


@dataclass
class CharacterAssets:
    model: str
    skins: list[str]
    bright_skin: bool
    animation_cfg: bool
    gesture_frames: int
    sex: str                              # 'm' / 'f' / 'n' from animation.cfg
    sounds: list[str]                     # names under sound/player/<model>/
    file_count: int

    @property
    def can_gesture(self) -> bool:
        return self.gesture_frames >= MIN_GESTURE_FRAMES

    @property
    def has_taunt(self) -> bool:
        return "taunt.wav" in self.sounds

    def as_dict(self) -> dict:
        return {**self.__dict__, "can_gesture": self.can_gesture,
                "has_taunt": self.has_taunt}


def read_inventory(pak: Path = PAK00) -> dict[str, CharacterAssets]:
    """Every player model in the pak, with what actually ships for it."""
    z = zipfile.ZipFile(pak)
    skins: dict[str, set[str]] = {}
    files: dict[str, int] = {}
    anim: dict[str, str] = {}
    sounds: dict[str, set[str]] = {}
    for n in z.namelist():
        m = re.match(r"models/players/([^/]+)/(.+)$", n)
        if m:
            model, rest = m.group(1).lower(), m.group(2)
            files[model] = files.get(model, 0) + 1
            sk = re.match(r"(?:head|upper|lower)_(.+)\.skin$", rest)
            if sk:
                skins.setdefault(model, set()).add(sk.group(1))
            if rest == "animation.cfg":
                anim[model] = z.read(n).decode("latin-1")
        s = re.match(r"sound/player/([^/]+)/([^/]+\.(?:wav|ogg))$", n, re.I)
        if s:
            sounds.setdefault(s.group(1).lower(), set()).add(s.group(2).lower())

    out = {}
    for model, count in files.items():
        cfg = anim.get(model, "")
        rows = [l.split() for l in cfg.splitlines()
                if re.match(r"^\s*\d+\s+\d+\s+\d+\s+\d+", l)]
        gest = int(rows[TORSO_GESTURE_ROW][1]) if len(rows) > TORSO_GESTURE_ROW else 0
        sex = re.search(r"^\s*sex\s+(\w)", cfg, re.M)
        out[model] = CharacterAssets(
            model=model, skins=sorted(skins.get(model, ())),
            bright_skin="bright" in skins.get(model, ()),
            animation_cfg=bool(cfg), gesture_frames=gest,
            sex=sex.group(1).lower() if sex else "?",
            sounds=sorted(sounds.get(model, ())), file_count=count)
    return out


def save_inventory(path: Path = INVENTORY, pak: Path = PAK00) -> dict:
    inv = read_inventory(pak)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"source": str(pak), "models": {k: v.as_dict()
                                            for k, v in sorted(inv.items())}}
    path.write_text(json.dumps(data, indent=1), encoding="utf-8")
    return data


def load_inventory(path: Path = INVENTORY) -> dict[str, CharacterAssets]:
    if not path.exists():
        save_inventory(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    out = {}
    for k, v in data["models"].items():
        v = {kk: vv for kk, vv in v.items() if kk not in ("can_gesture", "has_taunt")}
        out[k] = CharacterAssets(**v)
    return out


# ── the authoring surface ─────────────────────────────────────────────────

@dataclass
class PresenterProfile:
    """A character cast in a role. Film authoring names this and nothing lower.

    `voice` is the CharacterVoiceProfile key (engine.pantheon.voice.PROFILES);
    `personality` is a note for the dialogue writer, not a mechanism.
    """
    role: str
    model: str
    skin: str = "default"
    voice: str = "GUIDE"
    personality: str = ""
    treatment: str = "NONE"               # NONE | TEAM_TINT | ENEMY_TINT

    def resolve(self, inv: dict[str, CharacterAssets] | None = None
                ) -> CharacterAssets:
        """Fail here, at authoring time, if the pak does not have this."""
        inv = inv or load_inventory()
        a = inv.get(self.model.lower())
        if a is None:
            raise KeyError(f"{self.role}: no player model {self.model!r} in "
                           f"pak00 -- choose from {sorted(inv)}")
        if self.skin not in a.skins:
            raise KeyError(f"{self.role}: {self.model} has no skin "
                           f"{self.skin!r}; it has {a.skins}")
        return a

    def gesture_ok(self, inv=None) -> bool:
        return self.resolve(inv).can_gesture


# Suggested casting. Creative, revisable, and every model here resolves.
CAST = {
    "GUIDE": PresenterProfile(
        "GUIDE", "crash", "trainer", voice="GUIDE",
        personality="clear, instructional -- she is the game's own trainer, "
                    "and forty of her tutorial lines are real recordings"),
    "ENEMY_DEMONSTRATOR": PresenterProfile(
        "ENEMY_DEMONSTRATOR", "keel", "bright", voice="KEEL",
        personality="short, deadpan, intimidating", treatment="ENEMY_TINT"),
    "MOVEMENT": PresenterProfile(
        "MOVEMENT", "anarki", "default", voice="ANARKI",
        personality="fast, irreverent -- the hoverboard punk"),
    "TACTICAL": PresenterProfile(
        "TACTICAL", "slash", "default", voice="SLASH",
        personality="sharp, energetic"),
    "COMEDY": PresenterProfile(
        "COMEDY", "orbb", "default", voice="ORBB",
        personality="strange, playful -- an eye on legs; cannot gesture"),
    "VETERAN": PresenterProfile(
        "VETERAN", "sarge", "default", voice="SARGE",
        personality="gruff, plain-spoken"),
    "ARCHIVE": PresenterProfile(
        "ARCHIVE", "ranger", "default", voice="RANGER",
        personality="the original Quake protagonist; history's own witness"),
}
