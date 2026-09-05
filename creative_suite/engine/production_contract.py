"""The production-facing contract for ActionTruth and Scene.

WHY THIS FILE EXISTS. `action_truth` and `scene` already say what happened.
What they do not say is which of their statements a downstream planner is
allowed to treat as fact. An effect selector that reads `alive_after` (an
arithmetic guess) with the same confidence as `health_at_frag` (a byte the
server sent) will eventually build a clutch treatment on a moment that was
not a clutch. So every field a consumer can read is classified here, once,
and the classification travels WITH the value.

FOUR CLASSES, AND THE LINE THAT MATTERS MOST.

    OBSERVED            the demo said this. A server fact.
    DERIVED             arithmetic over observed facts. Correct where its
                        assumption holds, and the assumption is written down.
    MACHINE_SUGGESTION  the recogniser's opinion. Its own scale, never a
                        percentage, never a verdict.
    HUMAN               the director wrote it. The only creative truth.

The line that matters most is the last one. A machine trait and a human note
can both say "clutch"; only one of them decides how the film treats it, and
a planner that cannot tell them apart will average them.

UNKNOWN IS A FIFTH THING AND NOT A CLASS. A field whose value is None is
UNAVAILABLE: not observed, not derived, not zero. Half this corpus has no
health value and never will (see review_observability_matrix.md). Every
consumer must be able to ask, and none may substitute a default.

WHAT THIS MODULE IS NOT. It computes nothing. It re-labels and re-shapes what
`action_truth.for_item` and `scene.build_scene` already returned. If a number
appears here that did not come from one of those two, that is a bug -- the
reviewer and the film must be looking at the same arithmetic.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

CONTRACT_VERSION = "production-contract-v1"

# -- the four classes, plus the absence -------------------------------------

OBSERVED = "OBSERVED"
DERIVED = "DERIVED"
MACHINE_SUGGESTION = "MACHINE_SUGGESTION"
HUMAN = "HUMAN"
UNAVAILABLE = "UNAVAILABLE"

CLASSES = (OBSERVED, DERIVED, MACHINE_SUGGESTION, HUMAN, UNAVAILABLE)

# Only these two may drive a factual claim on screen. A MACHINE_SUGGESTION
# may drive a RANKING (which moment to look at first) and never a STATEMENT
# (what happened), because it is an opinion on its own scale.
FACTUAL = (OBSERVED, DERIVED)

# -- the field table --------------------------------------------------------
#
# Keyed by dotted path into the ActionTruth dict. A path absent from this
# table is UNCLASSIFIED and `classify()` refuses it rather than guessing --
# a new field that silently defaults to OBSERVED is exactly the failure this
# table exists to prevent.

FIELD_PROVENANCE: dict[str, str] = {
    # The obituary. A server event, true for every actor whether or not they
    # held the camera.
    "event.occurrence_id": OBSERVED,
    "event.actor": OBSERVED,
    "event.opponent": OBSERVED,
    "event.weapon": OBSERVED,
    "event.map": OBSERVED,
    "event.round": OBSERVED,
    "event.time_in_round_ms": DERIVED,      # event time minus round start
    "event.camera": OBSERVED,
    "event.is_actor_pov": OBSERVED,
    "event.death_cause": OBSERVED,
    "event.n_observations": OBSERVED,
    "event.machine_score": MACHINE_SUGGESTION,
    "event.machine_score_version": MACHINE_SUGGESTION,
    "event.career_rank": MACHINE_SUGGESTION,   # a rank OF the machine score
    "event.career_total": OBSERVED,

    # The recorder's own player state. OBSERVED where it exists at all --
    # and it exists for 47.3% of the corpus. See `stack.available`.
    "stack.available": OBSERVED,
    "stack.reason": OBSERVED,
    "stack.provenance": OBSERVED,
    "stack.at_frag.health": OBSERVED,
    "stack.at_frag.armor": OBSERVED,
    "stack.start.health": OBSERVED,
    "stack.start.armor": OBSERVED,
    "stack.min.health": OBSERVED,
    "stack.min.armor": OBSERVED,
    "stack.biggest_drop": DERIVED,          # differences along the series
    "stack.health_recovered": DERIVED,
    "stack.tags": DERIVED,                  # thresholds applied to health

    # Outgoing action. Shots are the recorder's own trigger; hits are pain
    # events attributed under a stated confidence.
    "action.weapon": OBSERVED,
    "action.weapon_wp": OBSERVED,
    "action.window_ms": DERIVED,
    "action.shots": OBSERVED,
    "action.accuracy_upper_pct": DERIVED,
    "action.damage_dealt": OBSERVED,
    "action.target": OBSERVED,
    "action.hits_confirmed": DERIVED,
    "action.hits_ambiguous": DERIVED,
    "action.accuracy_pct": DERIVED,
    "action.engagement_ms": DERIVED,
    "action.confidence": DERIVED,
    "action.unit": OBSERVED,
    "action.note": OBSERVED,

    "damage.available": OBSERVED,
    "damage.lg_dealt_3s": OBSERVED,
    "damage.taken_in_fight": OBSERVED,
    "damage.lowest_health_in_fight": OBSERVED,
    "damage.scope": OBSERVED,

    "geometry.distance_units": OBSERVED,
    "geometry.flick_degrees": DERIVED,      # angle delta over a window
    "geometry.flick_duration_ms": DERIVED,
    "geometry.flick_deg_per_s": DERIVED,
    "geometry.target_visible_ms": DERIVED,

    "movement.speed_at_frag": OBSERVED,
    "movement.victim_speed": OBSERVED,
    "movement.victim_air_height": OBSERVED,
    "movement.percentile": DERIVED,         # this speed against the corpus
    "movement.moment": OBSERVED,            # a run of observed positions

    # Round shape. Counts are observed obituaries; the alive curve is team
    # size minus deaths, which assumes one life per round -- true in CA.
    "round.round_no": OBSERVED,
    "round.map_name": OBSERVED,
    "round.duration_ms": OBSERVED,
    "round.user_kills": OBSERVED,
    "round.team_kills": OBSERVED,
    "round.enemy_kills": OBSERVED,
    "round.user_died": OBSERVED,
    "round.team_size": OBSERVED,
    # Team size minus observed deaths. True while every player has one life
    # per round, which is Clan Arena -- and the reason it is not OBSERVED.
    "round.alive_curve": DERIVED,
    "round.alive_provenance": DERIVED,
    "round.is_story_candidate": MACHINE_SUGGESTION,
    "round.story_reasons": MACHINE_SUGGESTION,
    "round.coverage_note": OBSERVED,

    "timing.available": OBSERVED,
    "timing.frag_index": DERIVED,
    "timing.frags_in_scene": DERIVED,
    "timing.ms_to_next_user_frag": DERIVED,
    "timing.ms_since_previous_user_frag": DERIVED,
    "timing.offset_in_scene_ms": DERIVED,
    "timing.scene_duration_ms": DERIVED,
    "timing.nearest_scene_event": DERIVED,

    "scene.scene_id": DERIVED,
    "scene.mode": DERIVED,
    "scene.user_frags": OBSERVED,
    "scene.total_kills": OBSERVED,
    "scene.media_start_ms": DERIVED,
    "scene.media_end_ms": DERIVED,

    # Machine semantics. HIGH_SPEED, CLUTCH_1V2, LOW_HP_ACTION -- every one
    # of these is the recogniser naming a pattern it thinks it sees.
    "traits": MACHINE_SUGGESTION,

    # Production lifecycle. A fact about this repository, not about the game.
    "usage.state": OBSERVED,
    "usage.detail": OBSERVED,
}


class UnclassifiedField(KeyError):
    """A production consumer asked for a field with no provenance class."""


def classify(path: str) -> str:
    """The provenance class of one ActionTruth field.

    Raises rather than guessing. A field nobody has classified is a field
    nobody has decided the trust level of, and defaulting it to OBSERVED
    would launder an opinion into a fact.
    """
    if path in FIELD_PROVENANCE:
        return FIELD_PROVENANCE[path]
    head = path.split(".", 1)[0]
    if head in FIELD_PROVENANCE:
        return FIELD_PROVENANCE[head]
    raise UnclassifiedField(
        f"{path!r} has no provenance class. Add it to FIELD_PROVENANCE "
        f"before a planner is allowed to read it.")


def _get(truth: dict[str, Any], path: str) -> Any:
    cur: Any = truth
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def provenance_of(truth: dict[str, Any], path: str) -> str:
    """The class of a field AS IT STANDS in this particular moment.

    A field that is classified OBSERVED but holds no value in this moment is
    UNAVAILABLE here, not OBSERVED-with-a-null. Half this corpus has no
    health; a consumer asking "is this observed?" must be told no.
    """
    cls = classify(path)
    return cls if _get(truth, path) is not None else UNAVAILABLE


def is_factual(truth: dict[str, Any], path: str) -> bool:
    """May a downstream statement about the film rest on this field?"""
    return provenance_of(truth, path) in FACTUAL


# -- ActionTruth, production view -------------------------------------------

@dataclass(frozen=True)
class ActionTruthRef:
    """A production-facing handle on one moment.

    Deliberately a REFERENCE plus a small classified read-out, not a copy of
    the whole dossier. The planner that wants everything calls
    `action_truth.for_item`; the planner that wants to decide whether this
    moment can carry a low-health treatment wants exactly this.
    """
    occurrence_id: int | None
    item_id: str | None
    is_actor_pov: bool
    weapon: str | None
    map_name: str | None
    round_no: int | None
    t_ms: int | None
    values: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, str] = field(default_factory=dict)
    contract_version: str = CONTRACT_VERSION

    def get(self, path: str) -> Any:
        return self.values.get(path)

    def factual(self, path: str) -> bool:
        return self.provenance.get(path, UNAVAILABLE) in FACTUAL

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# The fields a planner is expected to reach for. Kept short on purpose: a
# contract that exports everything is not a contract.
PLANNER_FIELDS = (
    "event.weapon", "event.is_actor_pov", "event.machine_score",
    "stack.available", "stack.at_frag.health", "stack.at_frag.armor",
    "stack.min.health", "stack.tags",
    "action.shots", "action.accuracy_pct", "action.accuracy_upper_pct",
    "action.confidence", "action.unit",
    "damage.lg_dealt_3s",
    "geometry.distance_units", "geometry.flick_deg_per_s",
    "geometry.target_visible_ms",
    "movement.speed_at_frag", "movement.victim_speed",
    "movement.victim_air_height",
    "round.user_kills", "round.user_died", "round.alive_curve",
    "timing.frag_index", "timing.frags_in_scene",
    "timing.ms_to_next_user_frag", "timing.scene_duration_ms",
    "traits",
)


def action_truth_ref(truth: dict[str, Any]) -> ActionTruthRef:
    """Wrap one `action_truth.for_item` result in its production contract."""
    if not truth.get("available"):
        raise ValueError(f"no canonical occurrence for {truth.get('item_id')}")
    ev = truth.get("event") or {}
    values = {p: _get(truth, p) for p in PLANNER_FIELDS}
    prov = {p: provenance_of(truth, p) for p in PLANNER_FIELDS}
    sc = truth.get("scene") or {}
    return ActionTruthRef(
        occurrence_id=ev.get("occurrence_id"),
        item_id=truth.get("item_id"),
        is_actor_pov=bool(ev.get("is_actor_pov")),
        weapon=ev.get("weapon"),
        map_name=ev.get("map"),
        round_no=ev.get("round"),
        t_ms=(sc.get("media_start_ms") if sc else None),
        values=values,
        provenance=prov,
    )


# -- Scene, production view -------------------------------------------------

@dataclass(frozen=True)
class SceneEventRef:
    """One rail event, by reference.

    `occurrence_id` is the canonical identity where the event has one. A
    movement run does not, and `takes_verdict` says so -- a planner must not
    invent a frag out of a jump pad.
    """
    event_id: str
    kind: str
    t_ms: int
    offset_ms: int
    label: str
    occurrence_id: int | None
    takes_verdict: bool
    is_user: bool
    frag_index: int | None
    human_role: str | None
    human_note: str
    human_note_provenance: str
    # WHAT THE MOMENT IS FOR, as opposed to how good it is. `T4` alone tells
    # an editor almost nothing six months later; `T4 + PREDICTION + ROCKET +
    # CLEAN_POV` tells them where the clip belongs. Captured at review time
    # because it cannot be recovered afterwards.
    human_tags: tuple[str, ...]
    # An instruction, not a score: no ranking, sampling or downselect may
    # hide this moment.
    golden: bool
    # The frag is not the unit here -- the sequence around it is.
    keep_context: bool
    # How many cameras filmed it. A brilliant event from a useless POV and
    # an ordinary event from a perfect POV are different assets.
    n_povs: int
    usage_state: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SceneRef:
    """A scene as production reads it: identity, bounds, refs, human truth.

    No moment data is duplicated here. `events` carry ids and times; the
    planner that needs a moment's full truth resolves the occurrence id
    through `action_truth`. Two copies of the same frag with two different
    health numbers is the failure this shape exists to prevent.
    """
    scene_id: str
    mode: str
    round_no: int
    map_name: str | None
    start_ms: int
    end_ms: int
    media_start_ms: int
    media_end_ms: int
    user_frags: int
    total_kills: int
    events: tuple[SceneEventRef, ...] = ()
    round_note: str = ""
    round_note_provenance: str = UNAVAILABLE
    contract_version: str = CONTRACT_VERSION

    @property
    def duration_ms(self) -> int:
        return self.media_end_ms - self.media_start_ms

    @property
    def golden_ids(self) -> tuple[int, ...]:
        """Documentary anchors in this scene. Never downselect these."""
        return tuple(e.occurrence_id for e in self.events
                     if e.golden and e.occurrence_id is not None)

    @property
    def keep_context_ids(self) -> tuple[int, ...]:
        return tuple(e.occurrence_id for e in self.events
                     if e.keep_context and e.occurrence_id is not None)

    @property
    def occurrence_ids(self) -> tuple[int, ...]:
        return tuple(e.occurrence_id for e in self.events
                     if e.occurrence_id is not None)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["duration_ms"] = self.duration_ms
        return d


def scene_ref(scene, round_note: dict[str, Any] | None = None,
              tags: dict[int, list[str]] | None = None,
              povs: dict[int, int] | None = None) -> SceneRef:
    """Wrap one `scene.Scene` in its production contract.

    `round_note` is whatever `creative_annotation.get_round_annotation`
    returned, or None. Its text is copied VERBATIM.
    """
    from creative_suite.engine import review_tags as rt
    tg = tags or {}
    pv = povs or {}
    events = []
    for e in scene.events:
        t = tuple(tg.get(e.occurrence_id, ()) if e.occurrence_id else ())
        events.append(SceneEventRef(
            event_id=e.event_id, kind=e.kind, t_ms=e.t_ms,
            offset_ms=e.offset_ms, label=e.label,
            occurrence_id=e.occurrence_id, takes_verdict=e.takes_verdict,
            is_user=e.is_user, frag_index=e.frag_index,
            human_role=e.human_role, human_note=e.annotation,
            human_note_provenance=getattr(e, "annotation_provenance", "") or "",
            human_tags=t, golden=rt.GOLDEN in t,
            keep_context=rt.KEEP_CONTEXT in t,
            n_povs=int(pv.get(e.occurrence_id, 0) or 0),
            usage_state=e.usage_state))
    events = tuple(events)
    note = (round_note or {}).get("annotation", "") or ""
    prov = ((round_note or {}).get("provenance") or UNAVAILABLE) if note \
        else UNAVAILABLE
    return SceneRef(
        scene_id=scene.scene_id, mode=scene.mode, round_no=scene.round_no,
        map_name=scene.map_name, start_ms=scene.start_ms,
        end_ms=scene.end_ms, media_start_ms=scene.media_start_ms,
        media_end_ms=scene.media_end_ms, user_frags=scene.user_frags,
        total_kills=scene.total_kills, events=events,
        round_note=note, round_note_provenance=prov)


# -- the bridge to choreography ---------------------------------------------

# Which review provenances are the director speaking. AI_SUGGESTION and TEST
# are not, and must never reach a planner as direction.
HUMAN_PROVENANCES = ("HUMAN_USER", "IMPORTED_LEGACY_HUMAN")


@dataclass(frozen=True)
class DirectionNote:
    """One thing the director actually wrote, and where they wrote it.

    `text` is byte-for-byte what they typed. Nothing in this pipeline
    rewrites, summarises, normalises or "cleans" it: a note is an
    instruction, and an instruction that has been paraphrased is somebody
    else's instruction. `intent` is a machine READING of that text, offered
    alongside and never in place of it.
    """
    scope: str                      # SCENE | EVENT
    target: str                     # scene_id, or event_id
    text: str
    provenance: str = HUMAN
    role: str | None = None
    intent: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ChoreographyInput:
    """Everything the planning layer needs about one scene, and nothing else.

    THE THREE INPUTS, KEPT SEPARATE ON PURPOSE:

        scene       story context -- what happened, in what order, over what
                    span of time.
        actions     game truth -- one classified reference per canonical
                    occurrence in the scene.
        direction   the director's own words, verbatim, scoped to the scene
                    or to one event on its rail.

    A `ChoreographyPlan` is built FROM this. It is not built here: this
    module knows nothing about lanes, effects, cameras or music, and that is
    the point of the boundary. What it guarantees is that when a planner
    finally reads "music buildup here", it is reading what the director
    typed, attached to the exact event they typed it on.
    """
    scene: SceneRef
    actions: tuple[ActionTruthRef, ...] = ()
    direction: tuple[DirectionNote, ...] = ()
    contract_version: str = CONTRACT_VERSION

    def notes_for(self, target: str) -> tuple[DirectionNote, ...]:
        return tuple(n for n in self.direction if n.target == target)

    @property
    def scene_notes(self) -> tuple[DirectionNote, ...]:
        return tuple(n for n in self.direction if n.scope == "SCENE")

    def action_for(self, occurrence_id: int) -> ActionTruthRef | None:
        for a in self.actions:
            if a.occurrence_id == occurrence_id:
                return a
        return None

    def to_dict(self) -> dict[str, Any]:
        return {"scene": self.scene.to_dict(),
                "actions": [a.to_dict() for a in self.actions],
                "direction": [n.to_dict() for n in self.direction],
                "contract_version": self.contract_version}


def choreography_input(scene, truths: list[dict[str, Any]] | None = None,
                       round_note: dict[str, Any] | None = None,
                       tags: dict[int, list[str]] | None = None,
                       povs: dict[int, int] | None = None,
                       ) -> ChoreographyInput:
    """Convert one Scene (+ any ActionTruths already built for it) to the
    planning layer's input.

    `truths` are `action_truth.for_item` results. They are passed in rather
    than fetched so this boundary stays free of database access -- and so a
    test can prove the conversion without a corpus.
    """
    ref = scene_ref(scene, round_note, tags, povs)
    actions = tuple(action_truth_ref(t) for t in (truths or [])
                    if t.get("available"))

    notes: list[DirectionNote] = []
    if ref.round_note and ref.round_note_provenance in HUMAN_PROVENANCES:
        notes.append(DirectionNote(
            scope="SCENE", target=ref.scene_id, text=ref.round_note,
            intent=_intent(ref.round_note)))
    for e in ref.events:
        # Same gate as the round note. A note written by a test fixture or by
        # a suggestion engine is not direction, wherever it is attached.
        if e.human_note and e.human_note_provenance in HUMAN_PROVENANCES:
            notes.append(DirectionNote(
                scope="EVENT", target=e.event_id, text=e.human_note,
                role=e.human_role, intent=_intent(e.human_note)))
    return ChoreographyInput(scene=ref, actions=actions,
                             direction=tuple(notes))


def _intent(text: str) -> dict[str, Any]:
    """A machine reading of a note. Advisory, never authoritative."""
    from creative_suite.engine import creative_annotation as ca
    try:
        return ca.parse_intent(text)
    except Exception:                                          # noqa: BLE001
        # A parser failure must never cost the director their words.
        return {}


def input_for_item(item_id: str, db: Path | None = None) -> ChoreographyInput:
    """The whole bridge, for one review item, against the live caches."""
    from creative_suite.engine import action_truth as at
    from creative_suite.engine import creative_annotation as ca
    from creative_suite.engine import scene as sc

    kw = {"db": db} if db is not None else {}
    truth = at.for_item(item_id, **kw)
    if truth is None or not truth.get("available"):
        raise ValueError(f"no canonical occurrence for {item_id!r}")
    s = sc.scene_for_item(item_id, **kw)
    if s is None:
        raise ValueError(f"no scene for {item_id!r}")
    note = ca.get_round_annotation(s.content_hash, s.round_no)
    return choreography_input(s, [truth], note)


# -- the production entrypoint -----------------------------------------------
#
# WHY THIS FUNCTION EXISTS AND WHY IT TAKES A scene_id.
#
# A bridge with no production caller is not integration. Until this existed,
# `choreography_input` could only be reached by handing it a Scene object
# somebody had already built -- which in practice meant a test fixture with
# the notes already attached. That proves the bridge preserves a note it was
# handed. It does not prove the director's note ever leaves the database.
#
# So this takes a scene_id -- a durable address, the same one the reviewer
# shows on the rail -- and does the whole job from storage: resolve the
# scene, build it, load its notes, build ActionTruth for every occurrence in
# it, and return the planning layer's input. Nothing is passed in but a
# string.


class SceneNotFound(LookupError):
    """No scene in the corpus answers to this scene_id."""


def resolve_scene_id(scene_id: str, db: Path | None = None):
    """`SCENE:<hash prefix>:<round>` back to a real Scene from storage.

    The id carries only twelve hex characters of the demo hash, which is
    plenty to be unique here and deliberately not enough to be a filename.
    The full hash is recovered from the occurrence cache rather than being
    carried around in the open.
    """
    from creative_suite.engine import scene as sc

    parts = str(scene_id).split(":")
    if len(parts) != 3 or parts[0] != "SCENE":
        raise SceneNotFound(f"not a scene id: {scene_id!r}")
    prefix, round_txt = parts[1], parts[2]
    try:
        round_no = int(round_txt)
    except ValueError:
        raise SceneNotFound(f"not a round number: {round_txt!r}") from None
    if round_no == sc.NO_ROUND:
        # Round 0 is the no-round-system sentinel. Grouping by it once
        # produced a "round" of 105 frags spanning a whole match.
        raise SceneNotFound("round 0 is a sentinel, not a round")

    kw = {"db": db} if db is not None else {}
    # The hash lives on the OBSERVATION, not on the occurrence: one kill can
    # have been recorded by several demos, and the occurrence is the kill.
    with sc._conn(**kw) as c:
        rows = c.execute(
            "SELECT DISTINCT k.content_hash AS content_hash "
            "FROM kill_occurrences_v1 o JOIN kill_events_v1 k "
            "ON k.kill_event_id = o.best_observation_id "
            "WHERE k.content_hash LIKE ? AND o.round = ?",
            (prefix + "%", round_no)).fetchall()
    if not rows:
        raise SceneNotFound(f"no scene for {scene_id!r}")
    if len(rows) > 1:
        # Never guess between two demos. An ambiguous id is a bug in whoever
        # minted it, and picking one would silently plan the wrong round.
        raise SceneNotFound(f"{scene_id!r} matches {len(rows)} demos")
    return sc.build_scene(rows[0]["content_hash"], round_no, **kw)


def build_choreography_input_for_scene(scene_id: str, db: Path | None = None
                                       ) -> ChoreographyInput:
    """The production entrypoint: a scene_id in, planning input out.

    Everything comes from storage -- the scene, its canonical occurrences,
    the director's notes on the rail and on the round. This is what a
    choreographer, effect selector, camera planner or music planner calls.
    """
    from creative_suite.engine import action_truth as at
    from creative_suite.engine import creative_annotation as ca

    scene = resolve_scene_id(scene_id, db=db)
    kw = {"db": db} if db is not None else {}

    # One ActionTruth per verdict-bearing occurrence on the rail. Built from
    # the occurrence id, not from a review item, because production plans a
    # historical kill and not a queue position.
    truths: list[dict[str, Any]] = []
    for e in scene.events:
        if not e.takes_verdict or e.occurrence_id is None:
            continue
        t = at.for_item(f"USER_FRAG:{e.occurrence_id}", **kw)
        if t and t.get("available"):
            truths.append(t)

    note = ca.get_round_annotation(scene.content_hash, scene.round_no)

    # The review-time capture, loaded from storage exactly like the notes.
    # Tags that only the reviewer's page could see would be no more use to
    # the film than a note the scene builder never read.
    from creative_suite.engine import pov_cluster as pv
    from creative_suite.engine import review_tags as rt
    occ = [e.occurrence_id for e in scene.events if e.occurrence_id]
    tags = rt.tags_for_many(occ)
    povs = {o: pv.povs_for(o, **kw)["n_povs"] for o in occ}
    return choreography_input(scene, truths, note, tags, povs)
