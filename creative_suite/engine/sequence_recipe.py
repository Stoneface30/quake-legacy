"""SequenceRecipe: the smallest useful multi-scene assembly (directive 15-16).

SceneRecipeV2 is NOT touched. A sequence REFERENCES scenes by recipe_id and
owns exactly one new thing: a fourth mapping stage that places each scene's
own edit clock into the finished programme.

    demo_us --TimeMap--> edit_us --SequencePlacement--> sequence_edit_us
                             |
                             +--MusicPlacement--> music_us

A scene keeps its own ``demo_us -> edit_us`` mapping untouched and remains
individually authoritative: a scene that renders correctly alone renders
identically inside a sequence, only offset. Nothing here flattens or
rewrites a TimeMap.

WHY SCENES CARRY A TRIM. A sequence rarely wants a whole preview window --
the bridge, for instance, uses Scene A's last 1.8 s ending on its impact.
``use_start_us``/``use_end_us`` select the part of the scene's edit clock
the sequence plays. They are offsets INTO the scene's clock, so they do not
disturb it.

IDENTITY. ``sequence_id`` is a sha256 over the canonical form, matching
SceneRecipeV2.recipe_id and SceneTransition.transition_id.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import hashlib
import json
import sqlite3
from typing import Any

SEQUENCE_SCHEMA_VERSION = 1

# Output profile names. A sequence records which one it was built for so a
# render is reproducible; the profile itself lives with the render code.
PROFILE_REVIEW = "REVIEW_720P60"
PROFILE_MASTER = "MASTER_1080P60"
OUTPUT_PROFILES = (PROFILE_REVIEW, PROFILE_MASTER)


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)


@dataclass(frozen=True)
class SequenceScene:
    """One scene's slot in the programme."""
    recipe_id: str
    order: int
    use_start_us: int          # offset into the scene's own edit clock
    use_end_us: int            # ditto, exclusive
    seq_start_us: int          # where it lands in sequence_edit_us
    label: str = ""
    transition_id: str | None = None   # transition OUT of this scene

    def __post_init__(self) -> None:
        for name in ("order", "use_start_us", "use_end_us", "seq_start_us"):
            v = getattr(self, name)
            if not isinstance(v, int) or isinstance(v, bool):
                raise ValueError(name + " must be an int")
        if self.use_end_us <= self.use_start_us:
            raise ValueError("scene must play a positive span")
        if self.use_start_us < 0 or self.seq_start_us < 0:
            raise ValueError("offsets must be non-negative")

    @property
    def duration_us(self) -> int:
        return self.use_end_us - self.use_start_us

    @property
    def seq_end_us(self) -> int:
        return self.seq_start_us + self.duration_us

    def to_sequence_us(self, scene_edit_us: int) -> int:
        """Map a time in the SCENE's edit clock to the sequence clock."""
        if not isinstance(scene_edit_us, int) or isinstance(scene_edit_us, bool):
            raise ValueError("scene_edit_us must be an int")
        return self.seq_start_us + (scene_edit_us - self.use_start_us)


@dataclass(frozen=True)
class SequenceRecipe:
    """An ordered programme of scenes joined by transitions."""
    scenes: tuple[SequenceScene, ...]
    music_strategy: str = "CONTINUOUS"
    music_track_hashes: tuple[str, ...] = ()
    music_volume: float = 0.75
    game_volume: float = 0.85
    mix_trim: float = 0.62
    # Measured, not inferred. alimiter works on SAMPLE peak; the AAC stage
    # adds inter-sample overshoot it cannot see. A 0.74 ceiling measured
    # -0.9 dBTP post-encode on the first micro-sequence -- a fail by
    # 0.1 dB. 0.66 measured -1.9 dBTP on the same programme.
    true_peak_ceiling: float = 0.66
    output_profile: str = PROFILE_REVIEW
    title: str = ""
    schema_version: int = SEQUENCE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.scenes:
            raise ValueError("a sequence needs at least one scene")
        if self.output_profile not in OUTPUT_PROFILES:
            raise ValueError("unknown output profile: "
                             + str(self.output_profile))
        orders = [s.order for s in self.scenes]
        if orders != sorted(orders) or len(set(orders)) != len(orders):
            raise ValueError("scene order must be strictly increasing")
        # The programme must be gapless and non-overlapping: a hole would
        # render as black and an overlap would render as a dropped frame,
        # and neither should be expressible.
        for prev, nxt in zip(self.scenes, self.scenes[1:]):
            if nxt.seq_start_us != prev.seq_end_us:
                raise ValueError(
                    f"scene {nxt.order} starts at {nxt.seq_start_us} but the "
                    f"previous scene ends at {prev.seq_end_us}")
        if self.scenes[0].seq_start_us != 0:
            raise ValueError("the first scene must start the sequence clock")

    @property
    def duration_us(self) -> int:
        return self.scenes[-1].seq_end_us

    @property
    def scene_count(self) -> int:
        return len(self.scenes)

    @property
    def transition_count(self) -> int:
        return sum(1 for s in self.scenes if s.transition_id)

    def canonical(self) -> dict:
        d = asdict(self)
        d["scenes"] = [asdict(s) for s in self.scenes]
        d["music_track_hashes"] = list(self.music_track_hashes)
        return d

    def canonical_json(self) -> str:
        return canonical_json(self.canonical())

    @property
    def sequence_id(self) -> str:
        return hashlib.sha256(
            self.canonical_json().encode("utf-8")).hexdigest()


def lay_out(specs: list[dict]) -> tuple[SequenceScene, ...]:
    """Place scenes back to back on the sequence clock.

    ``specs`` are dicts with recipe_id / use_start_us / use_end_us and
    optionally label and transition_id. The sequence clock is derived, not
    authored, so a caller cannot accidentally leave a hole.
    """
    out: list[SequenceScene] = []
    cursor = 0
    for i, spec in enumerate(specs):
        scene = SequenceScene(
            recipe_id=str(spec["recipe_id"]), order=i,
            use_start_us=int(spec["use_start_us"]),
            use_end_us=int(spec["use_end_us"]),
            seq_start_us=cursor, label=str(spec.get("label", "")),
            transition_id=spec.get("transition_id"))
        out.append(scene)
        cursor = scene.seq_end_us
    return tuple(out)


def from_canonical(d: dict) -> SequenceRecipe:
    return SequenceRecipe(
        scenes=tuple(SequenceScene(
            recipe_id=s["recipe_id"], order=int(s["order"]),
            use_start_us=int(s["use_start_us"]),
            use_end_us=int(s["use_end_us"]),
            seq_start_us=int(s["seq_start_us"]),
            label=s.get("label", ""),
            transition_id=s.get("transition_id")) for s in d["scenes"]),
        music_strategy=d.get("music_strategy", "CONTINUOUS"),
        music_track_hashes=tuple(d.get("music_track_hashes") or ()),
        music_volume=float(d.get("music_volume", 0.75)),
        game_volume=float(d.get("game_volume", 0.85)),
        mix_trim=float(d.get("mix_trim", 0.62)),
        true_peak_ceiling=float(d.get("true_peak_ceiling", 0.66)),
        output_profile=d.get("output_profile", PROFILE_REVIEW),
        title=d.get("title", ""),
        schema_version=int(d.get("schema_version", SEQUENCE_SCHEMA_VERSION)))


_SCHEMA = """
CREATE TABLE IF NOT EXISTS sequence_recipes (
    sequence_id   TEXT PRIMARY KEY,
    title         TEXT NOT NULL,
    duration_us   INTEGER NOT NULL,
    sequence_json TEXT NOT NULL
)
"""


def _conn(db_path) -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    con.execute(_SCHEMA)
    return con


def persist(seq: SequenceRecipe, db_path) -> str:
    con = _conn(db_path)
    try:
        con.execute(
            "INSERT OR REPLACE INTO sequence_recipes (sequence_id, title,"
            " duration_us, sequence_json) VALUES (?,?,?,?)",
            (seq.sequence_id, seq.title, seq.duration_us,
             seq.canonical_json()))
        con.commit()
    finally:
        con.close()
    return seq.sequence_id


def load(sequence_id: str, db_path) -> SequenceRecipe | None:
    con = _conn(db_path)
    try:
        row = con.execute("SELECT sequence_json FROM sequence_recipes"
                          " WHERE sequence_id = ?", (sequence_id,)).fetchone()
    finally:
        con.close()
    return None if row is None else from_canonical(json.loads(row[0]))
